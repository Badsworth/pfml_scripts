from dataclasses import dataclass
from enum import Enum

import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.db as db
import massgov.pfml.util.logging
from massgov.pfml.db.models import Status, User

logger = massgov.pfml.util.logging.get_logger(__name__)


##########################################
# Handlers
##########################################


def users_get(user_id):
    with db.session_scope() as db_session:
        u = db_session.query(User).get(user_id)

    if u is None:
        raise NotFound()

    return user_response(u)


def users_post():
    body = UserCreateRequest(**connexion.request.json)

    with db.session_scope() as db_session:
        status = get_or_make_status(db_session, UserStatusDescription.unverified)

        u = User(active_directory_id=body.auth_id, status=status, email_address=body.email_address)

        logger.info("creating user", extra={"user_id": u.user_id})

        db_session.add(u)

    logger.info("successfully created user")
    return user_response(u)


##########################################
# Data types and helpers
##########################################


@dataclass
class UserCreateRequest:
    auth_id: str
    email_address: str


@dataclass
class UserResponse:
    user_id: str
    auth_id: str
    status: str
    email_address: str


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        auth_id=user.active_directory_id,
        status=user.status.status_description,
        email_address=user.email_address,
    )


class UserStatusDescription(Enum):
    unverified = "unverified"
    verified = "verified"


def get_or_make_status(db_session, status_description: UserStatusDescription) -> Status:
    status = (
        db_session.query(Status)
        .filter(Status.status_description == status_description.value)
        .one_or_none()
    )

    if status is None:
        logger.info(
            "creating missing status", extra={"status_description": status_description.value}
        )
        status = Status(status_description=status_description.value)
        db_session.add(status)

    return status
