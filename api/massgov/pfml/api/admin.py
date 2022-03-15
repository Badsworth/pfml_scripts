from typing import Any, Dict, Optional

import connexion
import flask
from sqlalchemy_utils import escape_like
from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authentication import (
    build_access_token,
    build_auth_code_flow,
    build_logout_flow,
)
from massgov.pfml.api.authentication.azure import AzureUser
from massgov.pfml.api.authorization.flask import READ, ensure
from massgov.pfml.api.models.users.requests import AdminTokenRequest
from massgov.pfml.api.models.users.responses import (
    AdminTokenResponse,
    AdminUserResponse,
    AuthURIResponse,
    UserResponse,
)
from massgov.pfml.api.util.paginate.paginator import PaginationAPIContext, page_for_api_context
from massgov.pfml.api.validation.exceptions import IssueType, ValidationErrorDetail
from massgov.pfml.db.models.azure import AzurePermission, LkAzurePermission
from massgov.pfml.db.models.employees import User

logger = massgov.pfml.util.logging.get_logger(__name__)

SERVICE_UNAVAILABLE_MESSAGE = "Azure AD is not configured."


def admin_authorization_url():
    auth_code_params = build_auth_code_flow()
    if auth_code_params is None:
        raise ServiceUnavailable(description=SERVICE_UNAVAILABLE_MESSAGE)
    return response_util.success_response(
        data=AuthURIResponse.parse_obj(auth_code_params).__dict__,
        message="Retrieved authorization url!",
    ).to_api_response()


def admin_token():
    request = AdminTokenRequest.parse_obj(connexion.request.json)
    try:
        tokens = build_access_token(request.auth_uri_res.__dict__, request.auth_code_res.__dict__)

    except ValueError:  # Usually caused by CSRF, simply ignore them
        logger.error("admins_token value error.")
        return response_util.error_response(
            status_code=BadRequest,
            message="Invalid code while attempting to acquire a token",
            errors=[
                ValidationErrorDetail(
                    field="auth_uri_res", message="Value error", type=IssueType.invalid
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
                    field="auth_uri_res", message=tokens["error"], type=IssueType.invalid
                )
            ],
        ).to_api_response()

    return response_util.success_response(
        data=AdminTokenResponse.parse_obj(tokens).__dict__, message="Successfully logged in!"
    ).to_api_response()


def admin_login():
    # decode_jwt is automatically called and will validate the token.
    azure_user = app.azure_user()
    # This should never be the case.
    if azure_user is None:
        raise NotFound
    ensure(READ, azure_user)
    return response_util.success_response(
        data=azure_user_response(azure_user), message="Successfully logged in!"
    ).to_api_response()


def admin_logout():
    logout_uri = build_logout_flow()
    if logout_uri is None:
        raise ServiceUnavailable(description=SERVICE_UNAVAILABLE_MESSAGE)
    return response_util.success_response(
        data={"logout_uri": logout_uri}, message="Retrieved logout url!"
    ).to_api_response()


def admin_get_flag_logs(name):
    return response_util.success_response(
        data={}, message=f"Successfully retrieved flag {name}"
    ).to_api_response()


def admin_flags_patch(name):
    return response_util.success_response(
        message=f"Successfully updated feature flag {name}", data={}
    ).to_api_response()


def admin_users_get(email_address: Optional[str] = "") -> flask.Response:
    azure_user = app.azure_user()
    # This should never be the case.
    if azure_user is None:
        raise Unauthorized
    ensure(READ, azure_user)
    ensure(READ, AzurePermission.USER_READ)
    with PaginationAPIContext(User, request=flask.request) as pagination_context:
        with app.db_session() as db_session:
            query = db_session.query(User)
            if email_address:
                query = query.filter(
                    User.email_address.ilike("%" + escape_like(email_address) + "%")
                )
            page = page_for_api_context(pagination_context, query)
    return response_util.paginated_success_response(
        message="Successfully retrieved users",
        model=UserResponse,
        page=page,
        context=pagination_context,
        status_code=200,
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
        f"{permission.azure_permission_description}" for permission in permissions
    ]
    return AdminUserResponse.parse_obj(response).__dict__
