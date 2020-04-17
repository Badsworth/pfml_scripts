import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.generate_fake_data as fake
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)

# since there is no DB connection, dictionary will hold all users
users = {}


def users_get(user_id):
    try:
        user = users[user_id]
    except KeyError:
        raise NotFound()

    return user


def users_post():
    body = connexion.request.json
    email = body.get("email")
    auth_id = body.get("auth_id")

    # generate fake user
    user = fake.create_user(email, auth_id)
    user_id = user["user_id"]

    # to simulate db, place user in dictionary so it can be fetched by id at GET /users
    users[user_id] = user
    logger.info("created user", extra={"user_id": user_id})
    return user
