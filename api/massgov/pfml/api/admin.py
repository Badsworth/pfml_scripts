from typing import Any, Dict

import connexion
from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authentication import (
    build_access_token,
    build_auth_code_flow,
    build_logout_flow,
)
from massgov.pfml.api.authorization.flask import READ, ensure
from massgov.pfml.api.models.users.requests import AdminTokenRequest
from massgov.pfml.api.models.users.responses import (
    AdminTokenResponse,
    AdminUserResponse,
    AuthURIResponse,
)
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail
from massgov.pfml.db.models.employees import AzureUser, LkAzurePermission

logger = massgov.pfml.util.logging.get_logger(__name__)

SERVICE_UNAVAILABLE_MESSAGE = "Azure AD is not configured."


def admin_authorization_url():
    authCodeParams = build_auth_code_flow()
    if authCodeParams is None:
        raise ServiceUnavailable(description=SERVICE_UNAVAILABLE_MESSAGE)
    return response_util.success_response(
        data=AuthURIResponse.parse_obj(authCodeParams).__dict__,
        message="Retrieved authorization url!",
    ).to_api_response()


def admin_token():
    request = AdminTokenRequest.parse_obj(connexion.request.json)
    try:
        tokens = build_access_token(request.authURIRes.__dict__, request.authCodeRes.__dict__)

    except ValueError:  # Usually caused by CSRF, simply ignore them
        logger.error("admins_token value error.")
        return response_util.error_response(
            status_code=BadRequest,
            message="Invalid code while attempting to acquire a token",
            errors=[
                ValidationErrorDetail(
                    field="authURIRes", message="Value error", type=IssueType.invalid,
                )
            ],
        ).to_api_response()

    if tokens is None:
        raise ServiceUnavailable(description=SERVICE_UNAVAILABLE_MESSAGE)

    if "error" in tokens:
        logger.error("admins_token error in tokens.", extra={"error": tokens["error"]})
        return response_util.error_response(
            status_code=BadRequest,
            message="Unknown error while attempting to acquire a token",
            errors=[
                ValidationErrorDetail(
                    field="authURIRes", message=tokens["error"], type=IssueType.invalid,
                )
            ],
        ).to_api_response()

    return response_util.success_response(
        data=AdminTokenResponse.parse_obj(tokens).__dict__, message="Successfully logged in!",
    ).to_api_response()


def admin_login():
    # decode_jwt is automatically called and will validate the token.
    azure_user = app.azure_user()
    # This should not ever be the case.
    if azure_user is None:
        raise NotFound
    ensure(READ, azure_user)
    return response_util.success_response(
        data=azure_user_response(azure_user), message="Successfully logged in!",
    ).to_api_response()


def admin_logout():
    logout_uri = build_logout_flow()
    if logout_uri is None:
        raise ServiceUnavailable(description=SERVICE_UNAVAILABLE_MESSAGE)
    return response_util.success_response(
        data={"logout_uri": logout_uri}, message="Retrieved logout url!",
    ).to_api_response()


def azure_user_response(user: AzureUser) -> Dict[str, Any]:
    response = user.__dict__.copy()

    with app.db_session() as db_session:
        permissions = (
            db_session.query(LkAzurePermission)
            .filter(LkAzurePermission.azure_permission_id.in_(user.permissions))
            .all()
        )

    response["permissions"] = [
        f"{permission.azure_permission_resource}_{permission.azure_permission_action}".upper()
        for permission in permissions
    ]
    return AdminUserResponse.parse_obj(response).__dict__
