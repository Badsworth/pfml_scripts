import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.db as db
import massgov.pfml.util.logging
from massgov.pfml.api.db.models import Status, User

logger = massgov.pfml.util.logging.get_logger(__name__)

# since there is no DB connection, dictionary will hold all users
users = {}


def users_get(user_id):
    session = db.get_session()
    u = session.query(User).get(user_id)
    session.commit()
    if u is not None:
        return (
            {
                "user_id": u.user_id,
                "active_directory_id": u.active_directory_id,
                "status": u.status.status_description,
            },
            200,
        )
    else:
        raise NotFound()


def users_post():
    body = connexion.request.json
    u = User(
        user_id=body.get("user_id"),
        active_directory_id=body.get("active_directory_id"),
        status=Status(status_description=body.get("status")),
    )

    session = db.get_session()

    try:
        logger.info("creating user", extra={"user_id": u.user_id})
        session.add(u)
        session.commit()
        res = {
            "user_id": u.user_id,
            "active_directory_id": u.active_directory_id,
            "status": u.status.status_description,
        }
        logger.info("successfully created user")
        return (res, 200)
    except Exception as e:
        logger.error(e)
        session.rollback()
        raise e
