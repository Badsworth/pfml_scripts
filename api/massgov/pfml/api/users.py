from typing import Any, Dict

import connexion
from pydantic import UUID4, Field
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import EDIT, READ, ensure
from massgov.pfml.db.models.employees import User
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import MaskedEmailStr
from massgov.pfml.util.sqlalchemy import get_or_404

logger = massgov.pfml.util.logging.get_logger(__name__)


##########################################
# Handlers
##########################################


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


class UserUpdateRequest(PydanticBaseModel):
    consented_to_data_sharing: bool


class UserResponse(PydanticBaseModel):
    """Response object for a given User result """

    user_id: UUID4
    auth_id: str = Field(alias="active_directory_id")
    email_address: MaskedEmailStr
    consented_to_data_sharing: bool


def user_response(user: User) -> Dict[str, Any]:
    return UserResponse.from_orm(user).dict()
