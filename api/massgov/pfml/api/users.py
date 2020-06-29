from typing import Any, Dict

import connexion
from pydantic import UUID4, Field
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import User
from massgov.pfml.util.pydantic import PydanticBaseModel

# import massgov.pfml.api.authorization.flask as authz

logger = massgov.pfml.util.logging.get_logger(__name__)


##########################################
# Handlers
##########################################

# @authz.requires(authz.READ, "User")
def users_get(user_id):
    with app.db_session() as db_session:
        u = db_session.query(User).get(user_id)

    if u is None:
        raise NotFound()

    return user_response(u)


def users_current_get():
    """Return the currently authenticated user"""
    current_user = app.current_user()

    # this should not ever be the case once authentication is required
    if current_user is None:
        raise NotFound

    return user_response(current_user)


def users_patch(user_id):
    """This endpoint modifies the user specified by the user_id"""
    body = UserUpdateRequest.parse_obj(connexion.request.json)

    with app.db_session() as db_session:
        updated_user = db_session.query(User).get(user_id)

        if updated_user is None:
            raise NotFound()

        for key in body.__fields_set__:
            value = getattr(body, key)
            setattr(updated_user, key, value)

    return user_response(updated_user)


##########################################
# Data types and helpers
##########################################


class UserUpdateRequest(PydanticBaseModel):
    consented_to_data_sharing: bool


class UserResponse(PydanticBaseModel):
    """Response object for a given User result """

    user_id: UUID4
    auth_id: str = Field(alias="active_directory_id")
    email_address: str
    consented_to_data_sharing: bool


def user_response(user: User) -> Dict[str, Any]:
    return UserResponse.from_orm(user).dict()
