from enum import Enum
from typing import Union

import massgov.pfml.db as db
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Status

logger = massgov.pfml.util.logging.get_logger(__name__)


class UserStatusDescription(Enum):
    unverified = "unverified"
    verified = "verified"


StatusDescription = Union[UserStatusDescription]


def get_or_make_status(db_session: db.Session, status_description: StatusDescription) -> Status:
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
