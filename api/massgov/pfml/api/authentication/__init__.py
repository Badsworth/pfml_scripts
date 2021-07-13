#
# Authentication using JWT tokens and AWS Cognito.
#

import json

import flask
from flask import session
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

import msal
from typing import Optional

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None

def get_authorization_url():
    config = app.get_app_config()
    session["flow"] = _build_auth_code_flow(scopes=config.azure_sso.scopes)
    auth_url = session["flow"]["auth_uri"]
    return auth_url

def login_admin():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return True

def logout_admin():
    config = app.get_app_config()
    # Wipe out user and its token cache from session
    session.clear()
    # Also logout from your tenant's web session
    return redirect(
        config.azure_sso.authority + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + config.azure_sso.postLogoutRedirectUri
    )

def _build_auth_code_flow(authority=None, scopes=None):
    config = app.get_app_config()
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=config.azure_sso.redirectUri
    )

def _build_msal_app(cache=None, authority=None):
    config = app.get_app_config()
    return msal.ConfidentialClientApplication(
        config.azure_sso.clientId, authority=authority or config.azure_sso.authority,
        client_credential=config.azure_sso.clientSecret, token_cache=cache)

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    sso = _build_msal_app(cache=cache)
    accounts = sso.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = sso.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result


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
        logger.info("wtf is happening")
        decoded_token = _decode_cognito_token(token)
        logger.info("wtf is happening")
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
