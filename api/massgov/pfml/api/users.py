from dataclasses import dataclass
from typing import Optional

import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import User
from massgov.pfml.db.status import UserStatusDescription, get_or_make_status

logger = massgov.pfml.util.logging.get_logger(__name__)


##########################################
# Handlers
##########################################


def users_get(user_id):
    with app.db_session() as db_session:
        u = db_session.query(User).get(user_id)

    if u is None:
        raise NotFound()

    return user_response(u)


def users_post():
    body = UserCreateRequest(**connexion.request.json)

    with app.db_session() as db_session:
        status = get_or_make_status(db_session, UserStatusDescription.unverified)

        u = User(
            active_directory_id=body.auth_id,
            status=status,
            email_address=body.email_address,
            consented_to_data_sharing=body.consented_to_data_sharing,
        )

        logger.info("creating user", extra={"active_directory_id": u.active_directory_id})

        db_session.add(u)

    logger.info("successfully created user", extra={"user_id": u.user_id})
    return user_response(u)


##########################################
# Data types and helpers
##########################################


@dataclass
class UserCreateRequest:
    auth_id: str
    email_address: str
    consented_to_data_sharing: bool


@dataclass
class UserResponse:
    user_id: Optional[str]
    auth_id: Optional[str]
    status: Optional[str]
    email_address: Optional[str]
    consented_to_data_sharing: Optional[bool]


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        auth_id=user.active_directory_id,
        status=user.status.status_description,
        email_address=user.email_address,
        consented_to_data_sharing=user.consented_to_data_sharing,
    )
