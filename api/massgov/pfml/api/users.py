from typing import Any, Dict, List

import connexion
from pydantic import UUID4, Field
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.db.models.employees import User
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.sqlalchemy import get_or_404
from massgov.pfml.util.strings import mask_fein
from massgov.pfml.util.users import register_user

logger = massgov.pfml.util.logging.get_logger(__name__)


##########################################
# Handlers
##########################################


def users_post():
    """Create a new user account"""
    body = UserCreateRequest.parse_obj(connexion.request.json)

    # TODO (CP-1763): Enforce required fields are present
    with app.db_session() as db_session:
        user = register_user(
            db_session,
            body.email_address,
            body.password,
            app.get_config().cognito_user_pool_client_id,
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

        ensure(EDIT, updated_user)
        for key in body.__fields_set__:
            value = getattr(body, key)
            setattr(updated_user, key, value)

    return response_util.success_response(
        message="Successfully updated user", data=user_response(updated_user),
    ).to_api_response()


##########################################
# Data types and helpers
##########################################


class UserCreateRequest(PydanticBaseModel):
    email_address: str
    password: str


class UserUpdateRequest(PydanticBaseModel):
    consented_to_data_sharing: bool


class RoleResponse(PydanticBaseModel):
    role_id: int
    role_description: str


class EmployerResponse(PydanticBaseModel):
    employer_dba: str
    employer_fein: str
    employer_id: UUID4
    has_verification_data: bool


class UserLeaveAdminResponse(PydanticBaseModel):
    employer: EmployerResponse
    verified: bool


class UserResponse(PydanticBaseModel):
    """Response object for a given User result """

    user_id: UUID4
    auth_id: str = Field(alias="active_directory_id")
    email_address: str
    consented_to_data_sharing: bool
    roles: List[RoleResponse]
    user_leave_administrators: List[UserLeaveAdminResponse]


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
        "employer_fein": mask_fein(leave_admin_dict["employer"]["employer_fein"]),
        "employer_id": leave_admin_dict["employer"]["employer_id"],
        "verified": leave_admin_dict["verified"],
        "has_verification_data": leave_admin_dict["employer"]["has_verification_data"],
    }
