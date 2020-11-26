#
# Authentication using JWT tokens and AWS Cognito.
#

import json

import flask
import jose
import requests
from jose import jwt
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from werkzeug.exceptions import Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import User

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None


def get_public_keys(userpool_keys_url):
    global public_keys

    logger.info("Retrieving public keys from %s", userpool_keys_url)
    data = get_url_as_json(userpool_keys_url)
    public_keys = data["keys"]
    logger.info("Public keys successfully retrieved")


def get_url_as_json(url):
    """Retrieve the given URL (file or http[s]) as JSON data."""
    if url.startswith("file://"):
        path = url.partition("//")[-1]
        return json.load(open(path))
    else:
        response = requests.get(url, timeout=5)
        return response.json()


def _decode_cognito_token(token):
    decoded_token = jwt.decode(token, public_keys, options=dict(require_exp=True, require_sub=True))
    return decoded_token


def decode_cognito_token(token):
    """Decode a Bearer token and validate signature against public keys.

    This is called automatically by Connexion. See x-bearerInfoFunc and x-tokenInfoFunc lines in
    openapi.yaml.

    See also https://connexion.readthedocs.io/en/latest/security.html
    """
    try:
        decoded_token = _decode_cognito_token(token)
        with app.db_session() as db_session:
            user = (
                db_session.query(User)
                .filter(User.active_directory_id == decoded_token.get("sub"))
                .one()
            )

            flask.g.current_user = user

        logger.info(
            "auth token decode succeeded:",
            extra={
                "current_user": {
                    "user_id": user.user_id,
                    "auth_id": user.active_directory_id,
                    "role_ids": [role.role_id for role in user.roles],
                }
            },
        )
        return decoded_token
    except jose.JOSEError as e:
        logger.error("auth token decode failed: %s %s", type(e), str(e), extra={"error": e})
        raise Unauthorized
    except (NoResultFound, MultipleResultsFound) as e:
        logger.error("user query failed: %s", type(e), extra={"error": e})
        raise Unauthorized
