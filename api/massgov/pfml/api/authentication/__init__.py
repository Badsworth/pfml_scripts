#
# Authentication using JWT tokens, AWS Cognito and Azure AD.
#
from datetime import datetime
import json

import flask
import jose
import msal
import newrelic.agent
import requests
from jose import jwt
from jose.constants import ALGORITHMS
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from werkzeug.exceptions import Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Role, User
from massgov.pfml.api.authentication.msalConfig import MSALClientConfig

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None
azure_config = None


def get_public_keys(userpool_keys_url):
    """ For AWS Cognito """
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


def _decode_jwt_token(token, keys, audience=None):
    decoded_token = jwt.decode(
        token,
        keys,
        algorithms=[ALGORITHMS.RS256],
        options=dict(require_exp=True, require_sub=True),
        audience=audience
    )
    return decoded_token


def decode_cognito_token(token):
    """Decode a Bearer token and validate signature against public keys.

    This is called automatically by Connexion. See x-bearerInfoFunc and x-tokenInfoFunc lines in
    openapi.yaml.

    See also https://connexion.readthedocs.io/en/latest/security.html
    """
    try:
        decoded_token = _decode_jwt_token(token, public_keys)
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


def configure_azure_ad():
    global azure_config

    now = datetime.now()
    seconds_in_24_hours = 86400

    # Some of the public keys might be rotated or updated on a reasonable period of 24h
    if azure_config is None or (now - azure_config.public_keys_last_updated).total_seconds() > seconds_in_24_hours:
        azure_config = MSALClientConfig.from_env()

    return azure_config


def decode_azure_ad_token(token):
    try:
        # The public keys should be refreshed every day 
        # https://docs.microsoft.com/en-us/azure/active-directory/develop/access-tokens#validating-tokens
        configure_azure_ad()
        
        headers = jwt.get_unverified_header(token)
        pick_public_key = [key for key in azure_config.public_keys if key.get("kid") == headers.get("kid")]
        if len(pick_public_key) < 1:
            raise jose.JOSEError("Invalid key!")
        
        decoded_token = _decode_jwt_token(token, pick_public_key[0], azure_config.client_id)
        
        # if azure_config.admin_group not in decoded_token.get("groups"):
        #     logger.exception("user missing required permissions")
        #     raise Unauthorized

        user_id = decoded_token.get("sub")
        flask.g.admin_user = {
            "name": decoded_token.get("email") or decoded_token.get("unique_name")
        }
        newrelic.agent.add_custom_parameter(
            "admin_user.auth_id", user_id,
        )

        # Read attributes for logging, so that db calls are not made during logging.
        flask.g.admin_user_user_id = str(user_id)
        flask.g.admin_user_auth_id = str(user_id)
        # flask.g.admin_user_role_ids = decoded_token.get("roles")
    
        logger.info("auth token decode succeeded", extra={"admin_user.auth_id": user_id})
        return decoded_token
    except jose.JOSEError as e:
        logger.exception("auth token decode failed: %s %s", type(e), str(e), extra={"error": e})
        raise Unauthorized

def build_auth_code_flow(authority=None, scopes=None):
    """
    The first step in the authentication code flow
    Returns state, code verifier and auth_uri
    """
    return _build_msal_app(
        authority=authority or azure_config.authority
    ).initiate_auth_code_flow(scopes or azure_config.scopes, redirect_uri=azure_config.redirect_uri)


def build_access_token(authURIRes, authCodeRes, scopes = None):
    """
    The second step in the authentication code flow
    Gets the access_token
    """
    return _build_msal_app().acquire_token_by_auth_code_flow(
        authURIRes, authCodeRes, scopes=scopes
    )


def _build_msal_app(cache=None, authority=None):
    """
    Build the Confidential Client Application
    """
    return msal.ConfidentialClientApplication(
        azure_config.client_id,
        authority=authority or azure_config.authority,
        client_credential=azure_config.client_secret,
        token_cache=cache,
    )


def build_logout_flow():
    return azure_config.logout_url