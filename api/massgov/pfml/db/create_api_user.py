#
# Script is used to create fineos app client user with FINEOS role. The app client id is read from AWS_SSM and set
# as the environment variable COGNITO_FINEOS_APP_CLIENT_ID by ecs_task.
#
# See /bin/run-ecs-task/README.md for more details.
# Usage: ./bin/run-ecs-task/run-task.sh <env> db-create-fineos-user <firstname>.<lastname>
#
from pydantic import BaseSettings, Field
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm.session import Session

import massgov.pfml.util.logging
import massgov.pfml.util.logging.audit
from massgov.pfml import db
from massgov.pfml.db.models.employees import Role, User, UserRole

logger = massgov.pfml.util.logging.get_logger(__name__)


class Config(BaseSettings):
    fineos_app_client_id: str = Field(..., min_length=1, env="COGNITO_FINEOS_APP_CLIENT_ID")
    internal_fineos_role_app_client_id: str = Field(
        ..., min_length=1, env="COGNITO_INTERNAL_FINEOS_ROLE_APP_CLIENT_ID"
    )


def create_fineos_user_helper(db_session: Session) -> None:
    config = Config()

    for client_name, client_id in config.__dict__.items():
        try:
            db_session.query(User).filter(User.active_directory_id == client_id).one()
            logger.info("App client for %s already exists", client_name)

        except NoResultFound:
            api_user = User(active_directory_id=client_id)
            user_role = UserRole(user=api_user, role_id=Role.FINEOS.role_id)
            db_session.add(user_role)
            db_session.commit()

            logger.info("User created for app client %s", client_name)

        except MultipleResultsFound as e:
            logger.exception(
                "Multiple users with the same client_id exist for %s",
                client_name,
                extra={"error": e},
            )


def create_fineos_user():
    massgov.pfml.util.logging.init("db-create-fineos-user")
    massgov.pfml.util.logging.audit.init_security_logging()
    db_session_raw = db.init()

    with db.session_scope(db_session_raw) as db_session:
        create_fineos_user_helper(db_session)
