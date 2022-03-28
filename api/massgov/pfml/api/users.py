import connexion
import flask
from werkzeug.exceptions import BadRequest

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.api.models.users.requests import (
    UserConvertEmployerRequest,
    UserCreateRequest,
    UserUpdateRequest,
)
from massgov.pfml.api.models.users.responses import UserResponse
from massgov.pfml.api.services.users import update_user
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail
from massgov.pfml.api.validation.user_rules import (
    get_users_convert_employer_issues,
    get_users_patch_issues,
    get_users_post_employer_issues,
    get_users_post_required_fields_issues,
)
from massgov.pfml.cognito.exceptions import CognitoValidationError
from massgov.pfml.db.models.employees import Employer, Role, User
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.users import add_leave_admin_and_role, register_user

logger = massgov.pfml.util.logging.get_logger(__name__)


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
        data = UserResponse.from_orm(user).dict()
    logger.info("users_post success - account created", extra={"is_employer": str(is_employer)})

    return response_util.success_response(
        data=data,
        message="Successfully created user. User needs to verify email address next.",
        status_code=201,
    ).to_api_response()


def users_get(user_id):
    with app.db_session() as db_session:
        u = get_or_404(db_session, User, user_id)
        data = UserResponse.from_orm(u).dict()
    ensure(READ, u)
    return response_util.success_response(
        message="Successfully retrieved user", data=data
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
                    ValidationErrorDetail(
                        type=IssueType.require_employer,
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
        data = UserResponse.from_orm(updated_user).dict()
    logger.info(
        "users_convert_employer success - account converted",
        extra={"employer_id": employer.employer_id},
    )

    return response_util.success_response(
        message="Successfully converted user", status_code=201, data=data
    ).to_api_response()


def users_current_get():
    """Return the currently authenticated user"""
    current_user = app.current_user()

    ensure(READ, current_user)
    data = UserResponse.from_orm(current_user).dict()

    return response_util.success_response(
        message="Successfully retrieved current user", data=data
    ).to_api_response()


def users_patch(user_id):
    """This endpoint modifies the user specified by the user_id"""
    body = UserUpdateRequest.parse_obj(connexion.request.json)

    issues = get_users_patch_issues(body)
    if issues:
        logger.info("users_patch failure - request has invalid fields")
        return response_util.error_response(
            status_code=BadRequest,
            message="Request does not include valid fields.",
            errors=issues,
            data={},
        ).to_api_response()

    with app.db_session() as db_session:
        user = get_or_404(db_session, User, user_id)

        ensure(EDIT, user)

    headers = flask.request.headers
    auth_header = headers.get("Authorization")
    assert auth_header
    # todo (PORTAL-1828): Remove X-FF-Sync-Cognito-Preferences feature flag header
    save_mfa_preference_to_cognito = headers.get("X-FF-Sync-Cognito-Preferences", None) == "true"
    cognito_auth_token = auth_header[7:]

    updated_user = update_user(
        db_session, user, body, save_mfa_preference_to_cognito, cognito_auth_token
    )
    data = UserResponse.from_orm(updated_user).dict()

    return response_util.success_response(
        message="Successfully updated user",
        data=data,
    ).to_api_response()
