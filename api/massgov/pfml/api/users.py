import sys
from typing import Any, Dict

import connexion
from werkzeug.exceptions import BadRequest, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authentication import (
    _build_auth_code_flow,
    _build_msal_app,
    _load_cache,
    decode_azure_ad_token,
)
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.api.models.users.requests import (
    UserConvertEmployerRequest,
    UserCreateRequest,
    UserUpdateRequest,
    AdminTokenRequest,
)
from massgov.pfml.api.models.users.responses import (
    UserLeaveAdminResponse, 
    UserResponse,
    AuthURIResponse,
    AuthCodeResponse,
    AdminTokenResponse,
)
from massgov.pfml.api.services.user_rules import (
    get_users_convert_employer_issues,
    get_users_post_employer_issues,
    get_users_post_required_fields_issues,
)
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.db.models.employees import Employer, Role, User, UserRole
from massgov.pfml.util.aws.cognito import CognitoValidationError
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.users import add_leave_admin_and_role, register_user

logger = massgov.pfml.util.logging.get_logger(__name__)


def admins_authorization_url():
    authCodeParams = _build_auth_code_flow()
    return response_util.success_response(
        data=AuthURIResponse.parse_obj(authCodeParams).__dict__,
        message="Retrieved authorization url!",
        status_code=200,
    ).to_api_response()


def admins_token():
    tokens = {}
    request = AdminTokenRequest.parse_obj(connexion.request.json)
    try:
        cache = _load_cache()

        tokens = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            request.authURIRes.__dict__, request.authCodeRes.__dict__, scopes=None
        )

        if "error" in tokens:
            logger.info(f"admins_token failure - {tokens['error']}")
            return response_util.error_response(
                status_code=BadRequest, message=tokens["error"], errors=tokens["error"], data={},
            ).to_api_response()

        # _save_cache(cache)

    except ValueError: # Usually caused by CSRF, simply ignore them
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(f"ValueError {exc_value}")

    return response_util.success_response(
        data=AdminTokenResponse.parse_obj(tokens).__dict__,
        message="Successfully logged in!",
        status_code=200,
    ).to_api_response()


def admins_login():
    # get token from header
    logger.info("admins_login")
    access_token = connexion.request.headers["Authorization"]
    logger.info(access_token)
    decoded_token, user = decode_azure_ad_token(access_token)
    # @todo: verification if admin has full or just partial access
    return response_util.success_response(
        data=user_response(user),
        message="Successfully logged in!",
        status_code=200,
    ).to_api_response()


def admins_logout():
    config = app.get_app_config().azure_sso
    # Wipe out user and its token cache from session
    # Also logout from your tenant's web session
    return f"{config.authority}/oauth2/v2.0/logout?post_logout_redirect_uri={config.postLogoutRedirectUri}"


def users_post():
    """Create a new user account"""
    body = UserCreateRequest.parse_obj(connexion.request.json)
    required_fields_issues = get_users_post_required_fields_issues(body)

    if required_fields_issues:
        logger.info("users_post failure - request missing required fields")

        return response_util.error_response(
            status_code=BadRequest,
            message="Request does not include valid fields.",
            errors=required_fields_issues,
            data={},
        ).to_api_response()

    with app.db_session() as db_session:
        employer = None
        is_employer = deepgetattr(body, "role.role_description") == Role.EMPLOYER.role_description

        if is_employer:
            employer_fein = deepgetattr(body, "user_leave_administrator.employer_fein")
            employer = (
                db_session.query(Employer)
                .filter(Employer.employer_fein == employer_fein)
                .one_or_none()
            )
            employer_issues = get_users_post_employer_issues(employer)

            if employer_issues:
                logger.info("users_post failure - Employer not valid")
                return response_util.error_response(
                    status_code=BadRequest,
                    message="Employer not valid",
                    errors=employer_issues,
                    data={},
                ).to_api_response()

        try:
            user = register_user(
                db_session,
                app.get_config().cognito_user_pool_id,
                app.get_config().cognito_user_pool_client_id,
                deepgetattr(body, "email_address"),
                deepgetattr(body, "password"),
                employer,
            )
        except CognitoValidationError as e:
            logger.info(
                "users_post failure - Cognito account creation failed with user error",
                extra={"issueField": e.issue.field, "issueType": e.issue.type},
            )

            return response_util.error_response(
                status_code=BadRequest,
                message="Cognito account creation failed.",
                errors=[e.issue],
                data={},
            ).to_api_response()

    logger.info(
        "users_post success - account created", extra={"is_employer": str(is_employer)},
    )

    return response_util.success_response(
        data=user_response(user),
        message="Successfully created user. User needs to verify email address next.",
        status_code=201,
    ).to_api_response()


def users_get(user_id):
    with app.db_session() as db_session:
        u = get_or_404(db_session, User, user_id)

    ensure(READ, u)
    return response_util.success_response(
        message="Successfully retrieved user", data=user_response(u),
    ).to_api_response()


def users_convert_employer(user_id):
    """This endpoint converts the user specified by the user_id to an employer"""
    body = UserConvertEmployerRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        updated_user = get_or_404(db_session, User, user_id)
        ensure(EDIT, updated_user)

        employer = (
            db_session.query(Employer)
            .filter(Employer.employer_fein == body.employer_fein)
            .one_or_none()
        )
        if not employer or not employer.fineos_employer_id:
            logger.info("users_convert failure - Employer not found!")
            return response_util.error_response(
                status_code=BadRequest,
                message="Invalid FEIN",
                errors=[
                    response_util.custom_issue(
                        type=response_util.IssueType.require_employer,
                        message="Invalid FEIN",
                        field="employer_fein",
                    )
                ],
                data={},
            ).to_api_response()

        # verify that we can convert the account
        issues = get_users_convert_employer_issues(updated_user, db_session)
        if issues:
            logger.info(
                "users_convert_employer failure - Couldn't convert user to employer account",
                extra={"employer_id": employer.employer_id},
            )
            return response_util.error_response(
                status_code=BadRequest,
                message="Couldn't convert user to employer account!",
                errors=issues,
                data={},
            ).to_api_response()
        else:
            add_leave_admin_and_role(db_session, updated_user, employer)
            db_session.commit()
            db_session.refresh(updated_user)

    logger.info(
        "users_convert_employer success - account converted",
        extra={"employer_id": employer.employer_id},
    )

    return response_util.success_response(
        message="Successfully converted user", status_code=201, data=user_response(updated_user),
    ).to_api_response()


def users_current_get():
    """Return the currently authenticated user"""
    current_user = app.current_user()

    # this should not ever be the case once authentication is required
    if current_user is None:
        raise NotFound

    ensure(READ, current_user)
    return response_util.success_response(
        message="Successfully retrieved current user", data=user_response(current_user),
    ).to_api_response()


def users_patch(user_id):
    """This endpoint modifies the user specified by the user_id"""
    body = UserUpdateRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        updated_user = get_or_404(db_session, User, user_id)

        ensure(EDIT, updated_user)
        for key in body.__fields_set__:
            value = getattr(body, key)
            setattr(updated_user, key, value)

    return response_util.success_response(
        message="Successfully updated user", data=user_response(updated_user),
    ).to_api_response()


##########################################
# Data helpers
##########################################


def user_response(user: User) -> Dict[str, Any]:
    response = UserResponse.from_orm(user).dict()
    response["user_leave_administrators"] = [
        normalize_user_leave_admin_response(ula) for ula in response["user_leave_administrators"]
    ]
    return response


def normalize_user_leave_admin_response(
    leave_admin_response: UserLeaveAdminResponse,
) -> Dict[str, Any]:
    leave_admin_dict = dict(leave_admin_response)
    return {
        "employer_dba": leave_admin_dict["employer"]["employer_dba"],
        "employer_fein": leave_admin_dict["employer"]["employer_fein"],
        "employer_id": leave_admin_dict["employer"]["employer_id"],
        "has_fineos_registration": leave_admin_dict["has_fineos_registration"],
        "verified": leave_admin_dict["verified"],
        "has_verification_data": leave_admin_dict["employer"]["has_verification_data"],
    }
