#
# Script is used to create fineos app client user with FINEOS role. The app client id is read from AWS_SSM and set
# as the environment variable COGNITO_FINEOS_APP_CLIENT_ID by ecs_task.
#
from pydantic import BaseSettings, Field
from sqlalchemy.orm.session import Session

import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Role, User, UserRole

logger = massgov.pfml.util.logging.get_logger(__name__)


class Config(BaseSettings):
    fineos_app_client_id: str = Field(..., min_length=1, env="COGNITO_FINEOS_APP_CLIENT_ID")


def create_fineos_user_helper(db_session: Session) -> None:
    config = Config()

    fineos_user = User(active_directory_id=config.fineos_app_client_id)
    user_role = UserRole(user=fineos_user, role_id=Role.FINEOS.role_id)
    db_session.add(user_role)
    db_session.commit()


def create_fineos_user():
    db_session_raw = db.init()

    with db.session_scope(db_session_raw) as db_session:
        create_fineos_user_helper(db_session)
