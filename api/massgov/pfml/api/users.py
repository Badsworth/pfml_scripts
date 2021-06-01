from typing import Any, Dict

import connexion
from werkzeug.exceptions import BadRequest, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.reductions.config as reductions_config
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.api.models.users.requests import (
    UserConvertEmployerRequest,
    UserCreateRequest,
    UserUpdateRequest,
)
from massgov.pfml.api.models.users.responses import UserLeaveAdminResponse, UserResponse
from massgov.pfml.api.services.user_rules import (
    get_users_convert_employer_issues,
    get_users_post_employer_issues,
    get_users_post_required_fields_issues,
)
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.db.models.employees import Employer, Role, User
from massgov.pfml.util.aws.cognito import CognitoValidationError
from massgov.pfml.util.aws.ses import EmailRecipient, send_email
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.strings import sanitize_fein, mask_fein
from massgov.pfml.util.users import initial_link_user_leave_admin, register_user
from massgov.pfml.util.aws.ses import EmailRecipient, send_email

import massgov.pfml.reductions.config as reductions_config

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

def users_getAll():
    with app.db_session() as db_session:
        # todo: authentication / check role as Admin
        users = db_session.query(User).all()
        
    users_response = [user_response(u) for u in users]

    return response_util.success_response(
        message="Successfully retrieved users", data=users_response,
    ).to_api_response()

def users_convert_employer_email(user_id):
    # todo: authentication / check role as Admin
    with app.db_session() as db_session:
        user = db_session.query(User).one()
        
    email_config = reductions_config.get_email_config()
    sender = email_config.pfml_email_address
    bounce_forwarding_email_address_arn = email_config.bounce_forwarding_email_address_arn
    email_recipient = EmailRecipient(to_addresses=[user.email_address])
    subject = f"Convert your account now"
    body = f"Yes click here"
    send_email(
      recipient=email_recipient,
      subject=subject,
      body_text=body,
      sender=sender,
      bounce_forwarding_email_address_arn=bounce_forwarding_email_address_arn,
    )

    return response_util.success_response(
        message="Successfully retrieved users", data=True,
    ).to_api_response()

def users_convert_employer(user_id):
    """This endpoint converts the user specified by the user_id to an employer"""
    body = UserConvertEmployerRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        updated_user = get_or_404(db_session, User, user_id)
        ensure(EDIT, updated_user)

        employer_fein = sanitize_fein(body.employer_fein)
        employer = (
            db_session.query(Employer).filter(Employer.employer_fein == employer_fein).one_or_none()
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
        employer_issues = get_users_convert_employer_issues(updated_user, employer, db_session)
        if employer_issues:
            logger.info("users_patch failure - Couldn't convert user to employer account")
            return response_util.error_response(
                status_code=BadRequest,
                message="Couldn't convert user to employer account!",
                errors=employer_issues,
                data={},
            ).to_api_response()
        else:
            initial_link_user_leave_admin(db_session, updated_user, employer)
            db_session.commit()
            db_session.refresh(updated_user)

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
