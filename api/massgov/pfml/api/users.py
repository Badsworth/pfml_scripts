from dataclasses import dataclass
from typing import Optional

from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import User

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


##########################################
# Data types and helpers
##########################################


@dataclass
class UserResponse:
    user_id: Optional[str]
    auth_id: Optional[str]
    email_address: Optional[str]
    consented_to_data_sharing: Optional[bool]


def user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        auth_id=user.active_directory_id,
        email_address=user.email_address,
        consented_to_data_sharing=user.consented_to_data_sharing,
    )
