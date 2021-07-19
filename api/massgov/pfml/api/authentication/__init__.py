#
# Authentication using JWT tokens and AWS Cognito.
#

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
from massgov.pfml.db.models.employees import User, Role

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None
azure_config = None
azure_public_keys = None
session = {}


def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or azure_config.scopes, redirect_uri=azure_config.redirectUri
    )


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        azure_config.clientId,
        authority=authority or azure_config.authority,
        client_credential=azure_config.clientSecret,
        token_cache=cache,
    )


def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
        logger.info(f"token_cache {session.get('token_cache')}")
    return cache


# def _get_token_from_cache(scope=None):
#     cache = _load_cache()  # This web app maintains one cache per session
#     msal_app = _build_msal_app(cache=cache)
#     accounts = msal_app.get_accounts()
#     if accounts:  # So all account(s) belong to the current signed-in user
#         result = msal_app.acquire_token_silent(scope, account=accounts[0])
#         _save_cache(cache)
#         return result


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


def get_azure_ad_public_keys(azure_ad_config):
    global azure_config, azure_public_keys

    azure_config = azure_ad_config
    logger.info("Retrieving public keys from %s", azure_config.publicKeysUrl)
    data = get_url_as_json(azure_config.publicKeysUrl)
    azure_public_keys = data["keys"]
    logger.info("Public keys successfully retrieved")


def _decode_azure_ad_token(token):
    headers = jwt.get_unverified_header(token)
    pick_public_keys = [key for key in azure_public_keys if key.get("kid") == headers.get("kid")]
    if len(pick_public_keys) == 1:
        decoded_token = jwt.decode(
            token,
            pick_public_keys[0],
            algorithms=[ALGORITHMS.RS256],
            options=dict(require_exp=True, require_sub=True),
            audience=azure_config.clientId
        )
        return decoded_token
    raise jose.JOSEError("No public keys found!")


def decode_azure_ad_token(token):
    try:
        decoded_token = _decode_azure_ad_token(token)
        auth_id = decoded_token.get("sub")
        logger.info(decoded_token)
        logger.info(auth_id)
        with app.db_session() as db_session:
            user = db_session.query(User).filter(User.sub_id == auth_id).one()

            flask.g.current_user = user
            # newrelic.agent.add_custom_parameter("current_user.user_id", user.user_id)
            # newrelic.agent.add_custom_parameter(
            #     "current_user.auth_id", user.sub_id,
            # )
            # Read attributes for logging, so that db calls are not made during logging.
            flask.g.current_user_user_id = str(user.user_id)
            flask.g.current_user_auth_id = str(user.sub_id)
            flask.g.current_user_role_ids = ",".join(str(role.role_id) for role in user.roles)
        
        is_admin = [role for role in user.roles if role.role_id is Role.ADMIN.role_id]
        if len(is_admin) > 0:
            logger.info("auth token decode succeeded", extra={"current_user.auth_id": auth_id})
            return decoded_token

        raise NoResultFound
    except jose.JOSEError as e:
        logger.exception("auth token decode failed: %s %s", type(e), str(e), extra={"error": e})
        raise Unauthorized
    except (NoResultFound, MultipleResultsFound) as e:
        logger.exception(
            "user query failed: %s", type(e), extra={"current_user.auth_id": auth_id, "error": e,},
        )
        raise Unauthorized

