import json
import urllib.request

from jose import JWTError, jwt
from werkzeug.exceptions import Unauthorized

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None


def get_public_keys(userpool_keys_url):
    global public_keys

    logger.info("Retrieving public keys")
    with urllib.request.urlopen(userpool_keys_url, timeout=5) as f:  # nosec
        response = f.read()
        public_keys = json.loads(response.decode("utf-8"))["keys"]

        logger.info("Public keys successfully retrieved")


def _decode_cognito_token(token):
    decoded_token = jwt.decode(token, public_keys, options=dict(require_exp=True))
    return decoded_token


def decode_cognito_token(token):
    try:
        decoded_token = _decode_cognito_token(token)
        logger.info("Auth token decode successful")
        return decoded_token
    except JWTError:
        logger.info("Auth token decode unsuccessful")
        raise Unauthorized
