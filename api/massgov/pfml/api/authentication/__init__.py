#
# Authentication using JWT tokens and AWS Cognito.
#

import flask
import requests
from jose import JWTError, jwt
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
    response = requests.get(userpool_keys_url, timeout=5)
    public_keys = response.json()["keys"]

    logger.info("Public keys successfully retrieved")


def _decode_cognito_token(token):
    decoded_token = jwt.decode(token, public_keys, options=dict(require_exp=True, require_sub=True))
    return decoded_token


def decode_cognito_token(token):
    try:
        decoded_token = _decode_cognito_token(token)
        with app.db_session() as db_session:
            user = (
                db_session.query(User)
                .filter(User.active_directory_id == decoded_token.get("sub"))
                .one()
            )

            flask.g.current_user = user

        logger.info("Auth token decode successful")
        return decoded_token
    except JWTError:
        logger.info("Auth token decode unsuccessful")
        raise Unauthorized
    except (NoResultFound, MultipleResultsFound) as e:
        logger.error("Auth token decode unsuccessful", extra={"error": e})
        raise Unauthorized
