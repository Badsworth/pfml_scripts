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

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None
azure_config = None
azure_public_keys_last_updated = None
azure_public_keys = None
session = {}

#
# AWS Cognito
#
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

#
# Azure AD Single Sign on for admins 
#
def get_azure_ad_public_keys(config):
    global azure_config, azure_public_keys, azure_public_keys_last_updated

    now = datetime.now()
    seconds_in_24_hours = 86400

    if azure_public_keys_last_updated is None or (now - azure_public_keys_last_updated).total_seconds() > seconds_in_24_hours:
        azure_config = config
        logger.info("Retrieving public keys from %s", config.publicKeysUrl)
        data = get_url_as_json(config.publicKeysUrl)
        azure_public_keys = get_url_as_json(config.publicKeysUrl)["keys"]
        azure_public_keys_last_updated = now
        logger.info("Public keys successfully retrieved!")


def _decode_azure_ad_token(token):
    # The public keys should be refreshed every day https://docs.microsoft.com/en-us/azure/active-directory/develop/access-tokens#validating-tokens
    get_azure_ad_public_keys(azure_config)

    headers = jwt.get_unverified_header(token)
    pick_public_key = [key for key in azure_public_keys if key.get("kid") == headers.get("kid")]
    if len(pick_public_key) == 1:
        decoded_token = jwt.decode(
            token,
            pick_public_key[0],
            algorithms=[ALGORITHMS.RS256],
            options=dict(require_exp=True, require_sub=True),
            audience=azure_config.clientId,
        )
        return decoded_token
    raise jose.JOSEError("Invalid key!")


def decode_azure_ad_token(token):
    try:
        decoded_token = _decode_azure_ad_token(token)
        auth_id = decoded_token.get("sub")
        email = decoded_token.get("email")

        with app.db_session() as db_session:
            user = (
                db_session.query(User)
                .filter(User.sub_id == auth_id and User.email_address == email)
                .one()
            )

            flask.g.current_user = user
            newrelic.agent.add_custom_parameter("current_user.user_id", user.user_id)
            newrelic.agent.add_custom_parameter(
                "current_user.auth_id", user.sub_id,
            )
            # Read attributes for logging, so that db calls are not made during logging.
            flask.g.current_user_user_id = str(user.user_id)
            flask.g.current_user_auth_id = str(user.sub_id)
            flask.g.current_user_role_ids = ",".join(str(role.role_id) for role in user.roles)

        # @todo: verification if admin has full or just partial access
        is_admin = [role for role in user.roles if role.role_id is Role.ADMIN.role_id]
        if len(is_admin) == 0:
            raise NoResultFound

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


def _build_logout_flow():
    return f"{azure_config.authority}/oauth2/v2.0/logout?post_logout_redirect_uri={azure_config.postLogoutRedirectUri}"


def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(
        authority=authority or azure_config.authority
    ).initiate_auth_code_flow(scopes or azure_config.scopes, redirect_uri=azure_config.redirectUri)


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        azure_config.clientId,
        authority=authority or azure_config.authority,
        client_credential=azure_config.clientSecret,
        token_cache=cache,
    )


def _load_cache():
    return msal.SerializableTokenCache()
