from typing import Any, Dict

import connexion
from werkzeug.exceptions import BadRequest, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.api.models.users.requests import UserCreateRequest, UserUpdateRequest, UserConvertRequest
from massgov.pfml.api.models.users.responses import UserLeaveAdminResponse, UserResponse, RoleResponse
from massgov.pfml.api.services.user_rules import (
    get_users_post_employer_issues,
    get_users_post_required_fields_issues,
)
from massgov.pfml.api.util.deepgetattr import deepgetattr
from massgov.pfml.db.models.employees import Employer, Role, User, UserLeaveAdministrator, UserRole, LkRole
from massgov.pfml.util.aws.cognito import CognitoValidationError
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.strings import mask_fein
from massgov.pfml.util.users import register_user, convert_user
logger = massgov.pfml.util.logging.get_logger(__name__)


def users_convert(user_id):
    user = None
    """Converts a user account from employee to leave admin"""
    with app.db_session() as db_session:
        user = get_or_404(db_session, User, user_id)

    ensure(EDIT, user)

    body = UserConvertRequest.parse_obj(connexion.request.json)
    # required_fields_issues = get_users_post_required_fields_issues(body)
    employer_for_leave_admin = deepgetattr(body, "employer_for_leave_admin")

    if not user or not employer_for_leave_admin:
        return response_util.error_response(
            status_code=BadRequest,
            message="Invalid identification",
            errors=["Invalid identification"],
            data={},
        ).to_api_response()

    with app.db_session() as db_session:
        employer = (
            db_session.query(Employer)
            .filter(Employer.employer_fein == employer_for_leave_admin)
            .one_or_none()
        )
        if employer is None:
            return response_util.error_response(
                status_code=BadRequest,
                message="Invalid Employer EIN",
                errors=["Invalid Employer EIN"],
                data={},
            ).to_api_response()

        user = convert_user(db_session, user, employer)

    return response_util.success_response(
        data=user_response(user),
        message="Successfully converted user.",
        status_code=201,
    ).to_api_response()


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

        role_description = deepgetattr(body, "role.role_description")
        employer_fein = deepgetattr(body, "user_leave_administrator.employer_fein")

        if role_description:
            existing_roles = [role.role_description for role in
                              updated_user.roles]
            if Role.EMPLOYER.role_description not in existing_roles:
                user_role = UserRole(user=updated_user, role_id=Role.EMPLOYER.role_id)
                db_session.add(user_role)

        if employer_fein:
            employer = (
                db_session.query(Employer)
                .filter(Employer.employer_fein == employer_fein.replace("-", "", 10))
                .one_or_none()
            )
            # TODO why does this generate an error?
            employer_issues = None  # employer_issues = get_users_post_employer_issues(employer)

            if employer_issues:
                logger.info("users_post failure - Employer not valid")
                return response_util.error_response(
                    status_code=BadRequest,
                    message="Employer not valid",
                    errors=employer_issues,
                    data={},
                ).to_api_response()

            user_leave_admin = UserLeaveAdministrator(
                user=updated_user, employer=employer, fineos_web_id=None,
            )
            db_session.add(user_leave_admin)

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

    logger.info(f'MP_{response}')
    with app.db_session() as db_session:
        userRoles = db_session.query(UserRole, LkRole).filter(LkRole.role_id == UserRole.role_id and UserRole.user_id == user.user_id).all()

        logger.info(f'MP_{userRoles}')
        response["roles"] = [normalize_user_role(ur) for ur in userRoles]
    
    response["user_leave_administrators"] = [
        normalize_user_leave_admin_response(ula) for ula in response["user_leave_administrators"]
    ]
    
    logger.info(f'MP_{response}')
    return response


def normalize_user_role(
    userRole,
) -> Dict[str, Any]:
    role = userRole[1]
    return dict(RoleResponse(role_id=role.role_id, role_description=role.role_description))


def normalize_user_leave_admin_response(
    leave_admin_response: UserLeaveAdminResponse,
) -> Dict[str, Any]:
    leave_admin_dict = dict(leave_admin_response)
    return {
        "employer_dba": leave_admin_dict["employer"]["employer_dba"],
        "employer_fein": mask_fein(leave_admin_dict["employer"]["employer_fein"]),
        "employer_id": leave_admin_dict["employer"]["employer_id"],
        "verified": leave_admin_dict["verified"],
        "has_verification_data": leave_admin_dict["employer"]["has_verification_data"],
    }
