#
# Authentication using JWT tokens, AWS Cognito and Azure AD.
#

import json
from typing import Any, Optional, Union

import flask
import jose
import msal
import newrelic.agent
import requests
from jose import jwt
from jose.constants import ALGORITHMS
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm.session import Session
from werkzeug.exceptions import Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.api.authentication.azure import (
    AzureClientConfig,
    AzureUser,
    create_azure_client_config,
)
from massgov.pfml.db.models.azure import (
    AzureGroup,
    AzureGroupPermission,
    LkAzureGroup,
    LkAzurePermission,
)
from massgov.pfml.db.models.employees import Role, User
from massgov.pfml.util.users import get_user_log_attributes, has_role_in

logger = massgov.pfml.util.logging.get_logger(__name__)

public_keys = None
azure_config: Optional[AzureClientConfig] = None


def get_public_keys(userpool_keys_url):
    """Retrieves cognito public keys"""
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


def configure_azure_ad() -> Optional[AzureClientConfig]:
    global azure_config

    if azure_config is None:
        azure_config = create_azure_client_config()
    if azure_config is not None:
        azure_config.update_keys()
    return azure_config


def _decode_jwt(token: str, is_azure_token: bool = False) -> dict[str, Any]:
    decoded_token = jwt.decode(
        token,
        # Only one of the public keys has to be valid if an iterable is passed.
        azure_config.public_keys if is_azure_token else public_keys,  # type: ignore
        algorithms=[ALGORITHMS.RS256],
        options=dict(require_exp=True, require_sub=True),
        audience=azure_config.client_id if is_azure_token else None,  # type: ignore
    )
    return decoded_token


def _is_azure_token(token: str) -> bool:
    # Assume cognito is being used if azure is not configured.
    if not azure_config or not azure_config.public_keys:
        return False
    azure_config.update_keys()
    headers = jwt.get_unverified_header(token)
    pick_public_key = [
        key for key in azure_config.public_keys if key.get("kid") == headers.get("kid")
    ]
    # Found one public key to decode this token
    return len(pick_public_key) == 1


def _process_azure_token(db_session: Session, decoded_token: dict[str, Any]) -> None:
    group_guids = decoded_token.get("groups", [])

    # If it's gotten into _process_azure_token then azure_config is not None.
    parent_group = AzureGroup.get_instance(db_session, description=azure_config.parent_group)  # type: ignore
    access = parent_group.azure_group_guid in group_guids

    if not access:
        raise Unauthorized("You do not have the correct group to access the Admin Portal.")

    filter_params = [
        # Find permissions for this user using its groups
        LkAzureGroup.azure_group_guid.in_(group_guids),
        # But only for the current access group
        LkAzureGroup.azure_group_parent_id == parent_group.azure_group_id,
    ]
    permissions = (
        db_session.query(LkAzurePermission)
        .join(AzureGroupPermission)
        .join(LkAzureGroup)
        .filter(*filter_params)
        .distinct()
        .all()
    )

    if len(permissions) == 0:
        raise Unauthorized("You do not have the correct permissions to access the Admin Portal.")

    # Not using "current_user" to prevent it from being mistakenly used as User type
    # as it could be an azure user instead.
    auth_id = decoded_token.get("sub")
    azure_user = AzureUser(
        sub_id=auth_id,
        first_name=decoded_token.get("given_name"),
        last_name=decoded_token.get("family_name"),
        email_address=decoded_token.get("unique_name"),
        groups=group_guids,
        permissions=[permission.azure_permission_id for permission in permissions],
    )

    flask.g.azure_user = azure_user
    newrelic.agent.add_custom_parameter("azure_user.sub_id", auth_id)
    flask.g.azure_user_sub_id = str(auth_id)
    logger.info("Azure auth token decode succeeded", extra={"auth_id": auth_id, "user": azure_user})


def _process_cognito_token(db_session: Session, decoded_token: dict[str, Any]) -> None:
    auth_id = decoded_token.get("sub")
    try:
        user = db_session.query(User).filter(User.sub_id == auth_id).one()
    except (NoResultFound, MultipleResultsFound) as e:
        logger.exception("user query failed: %s", type(e), extra={"auth_id": auth_id, "error": e})
        raise Unauthorized

    flask.g.current_user = user
    user_attributes = get_user_log_attributes(user)

    # Read attributes for logging, so that db calls are not made during logging.
    flask.g.current_user_log_attributes = user_attributes
    newrelic.agent.add_custom_parameters(user_attributes.items())

    if has_role_in(user, [Role.PFML_CRM]):
        mass_pfml_agent_id = flask.request.headers.get("Mass-PFML-Agent-ID", None)
        if mass_pfml_agent_id is None or mass_pfml_agent_id.strip() == "":
            raise Unauthorized("Invalid required header: Mass-PFML-Agent-ID")
        newrelic.agent.add_custom_parameter("mass_pfml_agent_id", mass_pfml_agent_id)

    logger.info("Cognito auth token decode succeeded", extra={"auth_id": auth_id, "user": user})


def decode_jwt(token):
    """Decode a Bearer token and validate signature against public keys.

    This is called automatically by Connexion. See x-bearerInfoFunc and x-tokenInfoFunc lines in
    openapi.yaml.

    See also https://connexion.readthedocs.io/en/latest/security.html
    """
    is_azure_token = None
    try:
        is_azure_token = _is_azure_token(token)
    except jose.JOSEError as e:
        logger.exception("token header decode failed: %s %s", type(e), str(e), extra={"error": e})
        raise Unauthorized

    try:
        decoded_token = _decode_jwt(token, is_azure_token)
    except jose.JOSEError as e:
        logger.exception("auth token decode failed: %s %s", type(e), str(e), extra={"error": e})

        if is_azure_token:
            raise Unauthorized("Your session has expired. Please log in to continue.")
        else:
            raise Unauthorized

    with app.db_session() as db_session:
        process_token = _process_azure_token if is_azure_token else _process_cognito_token
        process_token(db_session, decoded_token)
    return decoded_token


def build_auth_code_flow() -> Optional[dict[str, Optional[Union[str, list]]]]:
    """
    The first step in the authentication code flow
    Returns state, code verifier and auth_uri
    """
    if azure_config is None:
        return None
    msal_app = _build_msal_app()
    if msal_app is None:
        return None
    return msal_app.initiate_auth_code_flow(
        azure_config.scopes, redirect_uri=azure_config.redirect_uri
    )


def build_access_token(
    auth_uri_res: dict[str, Optional[Union[str, list]]], auth_code_res: dict[str, str]
) -> Optional[dict[str, str]]:
    """
    The second step in the authentication code flow
    Gets the access_token
    """
    msal_app = _build_msal_app()
    if msal_app is None:
        return None
    return msal_app.acquire_token_by_auth_code_flow(auth_uri_res, auth_code_res)


def _build_msal_app() -> Optional[msal.ConfidentialClientApplication]:
    """
    Build the Confidential Client Application
    """

    if azure_config is None:
        return None

    return msal.ConfidentialClientApplication(
        azure_config.client_id,
        authority=azure_config.authority,
        client_credential=azure_config.client_secret,
    )


def build_logout_flow() -> Optional[str]:
    if azure_config is None:
        return None
    return azure_config.logout_uri
