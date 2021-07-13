#
# Authentication using JWT tokens and AWS Cognito.
#

import json

import flask
import jose
import newrelic.agent
import requests
from jose import jwt
from jose.constants import ALGORITHMS
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from werkzeug.exceptions import Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import User

from typing import Optional
from massgov.pfml.api.authentication.msalConfig import MSALClient, MSALClientConfig

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None

msal = None
authCodeRequest = None
tokenRequest = None

def get_sso_auth_code():
    global authCodeRequest, tokenRequest
    
    if msal is not None:
        # prepare the request
        authCodeRequest.authority = config.authority
        authCodeRequest.scopes = config.scopes
        authCodeRequest.state = "SIGN_IN"

        tokenRequest.authority = config.authority;

        # request an authorization code to exchange for a token
        # msal.getAuthCodeUrl(authCodeRequest)

        # res.redirect(response);
    
    # res.status(500).send(error);
    
    return redirect("www.google.com", code=302)

def get_msal_client(config: Optional[MSALClientConfig]):
    global authCodeRequest, tokenRequest, msal

    logger.info("Initiating Microsoft Authentication Library")
    authCodeRequest = {}
    tokenRequest = {}
    msal = MSALClient(config)
    logger.info("MSAL successfully initiated")

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
    decoded_token = jwt.decode(
        token,
        public_keys,
        algorithms=[ALGORITHMS.RS256],
        options=dict(require_exp=True, require_sub=True),
    )
    return decoded_token


def decode_cognito_token(token):
    """Decode a Bearer token and validate signature against public keys.

    This is called automatically by Connexion. See x-bearerInfoFunc and x-tokenInfoFunc lines in
    openapi.yaml.

    See also https://connexion.readthedocs.io/en/latest/security.html
    """
    try:
        decoded_token = _decode_cognito_token(token)
        auth_id = decoded_token.get("sub")
        with app.db_session() as db_session:
            user = db_session.query(User).filter(User.sub_id == auth_id).one()

            flask.g.current_user = user

            newrelic.agent.add_custom_parameter("current_user.user_id", user.user_id)
            newrelic.agent.add_custom_parameter(
                "current_user.auth_id", user.sub_id,
            )

            # Read attributes for logging, so that db calls are not made during logging.
            flask.g.current_user_user_id = str(user.user_id)
            flask.g.current_user_auth_id = str(user.sub_id)
            flask.g.current_user_role_ids = ",".join(str(role.role_id) for role in user.roles)

        logger.info("auth token decode succeeded", extra={"current_user.auth_id": auth_id})
        return decoded_token
    except jose.JOSEError as e:
        logger.exception("auth token decode failed: %s %s", type(e), str(e), extra={"error": e})
        raise Unauthorized
    except (NoResultFound, MultipleResultsFound) as e:
        logger.exception(
            "user query failed: %s", type(e), extra={"current_user.auth_id": auth_id, "error": e,},
        )
        raise Unauthorized
