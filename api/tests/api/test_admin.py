from unittest.mock import patch

from flask import g
from jose import jwt
from jose.constants import ALGORITHMS

from massgov.pfml.api.admin import SERVICE_UNAVAILABLE_MESSAGE
from massgov.pfml.db.models.azure import AzureGroup, AzureGroupPermission, AzurePermission
from massgov.pfml.db.models.factories import UserFactory

FAKE_AUTH_URI_RESPONSE = {
    "auth_uri": "test",
    "code_verifier": "test",
    "nonce": "test",
    "redirect_uri": "test",
    "scope": ["test"],
    "state": "test",
}


@patch("massgov.pfml.api.admin.build_auth_code_flow")
def test_admin_authorize_unavailable(mock_build, client):
    mock_build.return_value = None
    response = client.get("/v1/admin/authorize")
    assert response.status_code == 503
    json = response.get_json()
    assert json.get("detail") == SERVICE_UNAVAILABLE_MESSAGE


@patch("massgov.pfml.api.admin.build_auth_code_flow")
def test_admin_authorize_success(mock_build, client, mock_azure):
    mock_build.return_value = FAKE_AUTH_URI_RESPONSE
    response = client.get("/v1/admin/authorize")
    assert response.status_code == 200
    json = response.get_json()
    assert json.get("data").get("auth_uri") == "test"


def test_admin_login_success(
    client, app, mock_azure, auth_claims_unit, azure_auth_private_key, test_db_session
):
    azure_token = auth_claims_unit.copy()
    azure_token["groups"] = [
        AzureGroup.NON_PROD.azure_group_guid,
        AzureGroup.NON_PROD_DEV.azure_group_guid,
    ]
    azure_token["unique_name"] = "email@example.com"
    test_db_session.add(
        AzureGroupPermission(
            azure_group_id=AzureGroup.NON_PROD_DEV.azure_group_id,
            azure_permission_id=AzurePermission.USER_READ.azure_permission_id,
        )
    )
    test_db_session.add(
        AzureGroupPermission(
            azure_group_id=AzureGroup.NON_PROD_DEV.azure_group_id,
            azure_permission_id=AzurePermission.USER_EDIT.azure_permission_id,
        )
    )
    encoded = jwt.encode(
        azure_token,
        azure_auth_private_key,
        algorithm=ALGORITHMS.RS256,
        headers={"kid": azure_auth_private_key.get("kid")},
    )
    with app.app.test_request_context("/v1/admin/login"):
        response = client.get("/v1/admin/login", headers={"Authorization": f"Bearer {encoded}"})
        data = response.get_json().get("data")
        assert response.status_code == 200
        assert g.azure_user.sub_id == "foo"
        assert g.azure_user.permissions == [
            AzurePermission.USER_READ.azure_permission_id,
            AzurePermission.USER_EDIT.azure_permission_id,
        ]
        assert data.get("email_address") == "email@example.com"
        assert data.get("permissions") == ["USER_READ", "USER_EDIT"]


def test_admin_login_unauthorized(client, app, mock_azure, auth_token_unit):
    with app.app.test_request_context("/v1/admin/login"):
        response = client.get(
            "/v1/admin/login", headers={"Authorization": f"Bearer {auth_token_unit}"}
        )
        assert g.get("azure_user") is None
        assert response.status_code == 401


def test_admin_login_unauthorized_no_permissions(client, app, mock_azure, azure_auth_token_unit):
    with app.app.test_request_context("/v1/admin/login"):
        response = client.get(
            "/v1/admin/login", headers={"Authorization": f"Bearer {azure_auth_token_unit}"}
        )
        assert g.get("azure_user") is None
        assert response.status_code == 401


@patch("massgov.pfml.api.admin.build_logout_flow")
def test_admin_logout_service_unavailable(mock_build, client):
    mock_build.return_value = None
    response = client.get("/v1/admin/logout")
    assert response.status_code == 503
    json = response.get_json()
    assert json.get("detail") == SERVICE_UNAVAILABLE_MESSAGE


def test_admin_logout_success(client, mock_azure):
    response = client.get("/v1/admin/logout")
    assert response.status_code == 200
    json = response.get_json()
    assert (
        json.get("data").get("logout_uri")
        == "https://example.com/tenant_id/oauth2/v2.0/logout?post_logout_redirect_uri=http://localhost:3001?logged_out=true"
    )
    assert json.get("message") == "Retrieved logout url!"


@patch("massgov.pfml.api.admin.build_access_token")
def test_admin_token_error_in_tokens(mock_build, client):
    mock_build.return_value = {"error": "Test error"}
    post_body = {
        "auth_uri_res": FAKE_AUTH_URI_RESPONSE,
        "auth_code_res": {"code": "test", "session_state": "test", "state": "test"},
    }
    response = client.post("/v1/admin/token", json=post_body)
    json = response.get_json()
    errors = json.get("errors")
    assert errors is not None
    assert len(errors) == 1
    assert errors[0].get("message") == "Test error"
    assert errors[0].get("field") == "auth_uri_res"
    assert errors[0].get("type") == "invalid"
    assert response.status_code == 400


def test_admin_token_missing_request_body(client):
    response = client.post("/v1/admin/token")
    json = response.get_json()
    errors = json.get("errors")
    assert errors is not None
    assert len(errors) == 1
    assert errors[0].get("message") == "Missing request body"
    assert response.status_code == 400


@patch("massgov.pfml.api.admin.build_access_token")
def test_admin_token_service_unavailable(mock_build, client):
    mock_build.return_value = None
    post_body = {
        "auth_uri_res": FAKE_AUTH_URI_RESPONSE,
        "auth_code_res": {"code": "test", "session_state": "test", "state": "test"},
    }
    response = client.post("/v1/admin/token", json=post_body)
    json = response.get_json()
    assert json.get("detail") == "Azure AD is not configured."
    assert json.get("title") == "Service Unavailable"
    assert response.status_code == 503


@patch("massgov.pfml.api.admin.build_access_token")
def test_admin_token_success(mock_build, client):
    mock_build.return_value = {"access_token": "test", "refresh_token": "test", "id_token": "test"}
    post_body = {
        "auth_uri_res": FAKE_AUTH_URI_RESPONSE,
        "auth_code_res": {"code": "test", "session_state": "test", "state": "test"},
    }
    response = client.post("/v1/admin/token", json=post_body)
    json = response.get_json()
    errors = json.get("errors")
    data = json.get("data")
    assert errors is None
    assert json.get("message") == "Successfully logged in!"
    assert data.get("access_token") == "test"
    assert data.get("refresh_token") == "test"
    assert data.get("id_token") == "test"
    assert response.status_code == 200


@patch("massgov.pfml.api.admin.build_access_token")
def test_admin_token_value_error(mock_build, client):
    mock_build.side_effect = ValueError
    mock_build.return_value = None
    post_body = {
        "auth_uri_res": FAKE_AUTH_URI_RESPONSE,
        "auth_code_res": {"code": "test", "session_state": "test", "state": "test"},
    }
    response = client.post("/v1/admin/token", json=post_body)
    errors = response.get_json().get("errors")
    assert errors is not None
    assert len(errors) == 1
    assert errors[0].get("field") == "auth_uri_res"
    assert errors[0].get("message") == "Value error"
    assert errors[0].get("type") == "invalid"
    assert response.status_code == 400


def test_admin_no_permissions(client, app, mock_azure, auth_claims_unit, azure_auth_private_key):
    azure_token = auth_claims_unit.copy()
    azure_token["groups"] = [
        AzureGroup.NON_PROD.azure_group_guid,
        AzureGroup.NON_PROD_DEV.azure_group_guid,
    ]
    encoded = jwt.encode(
        azure_token,
        azure_auth_private_key,
        algorithm=ALGORITHMS.RS256,
        headers={"kid": azure_auth_private_key.get("kid")},
    )
    with app.app.test_request_context("/v1/admin/users"):
        response = client.get(
            "/v1/admin/users?page_size=10", headers={"Authorization": f"Bearer {encoded}"}
        )
        assert response.status_code == 401


def test_admin_users_cognito(client, app, mock_azure, auth_token):
    response = client.get("/v1/admin/users", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 401


def test_admin_users_success(
    client, app, mock_azure, auth_claims_unit, azure_auth_private_key, test_db_session
):
    azure_token = auth_claims_unit.copy()
    azure_token["groups"] = [
        AzureGroup.NON_PROD.azure_group_guid,
        AzureGroup.NON_PROD_DEV.azure_group_guid,
    ]
    test_db_session.add(
        AzureGroupPermission(
            azure_group_id=AzureGroup.NON_PROD_DEV.azure_group_id,
            azure_permission_id=AzurePermission.USER_READ.azure_permission_id,
        )
    )
    encoded = jwt.encode(
        azure_token,
        azure_auth_private_key,
        algorithm=ALGORITHMS.RS256,
        headers={"kid": azure_auth_private_key.get("kid")},
    )
    UserFactory.create_batch(50)
    with app.app.test_request_context("/v1/admin/users"):
        response = client.get(
            "/v1/admin/users?page_size=10", headers={"Authorization": f"Bearer {encoded}"}
        )
        assert response.status_code == 200
        assert g.azure_user.sub_id == "foo"
        assert g.azure_user.permissions == [AzurePermission.USER_READ.azure_permission_id]
        response_json = response.get_json()
        data = response_json.get("data")
        paging = response_json.get("meta").get("paging")

        assert paging.get("order_by") == "created_at"
        assert paging.get("order_direction") == "descending"
        assert paging.get("page_offset") == 1
        assert paging.get("page_size") == 10
        assert paging.get("total_pages") == 5
        assert paging.get("total_records") == 50
        assert len(data) == 10


def test_admin_users_email_address_filter(
    client, app, mock_azure, auth_claims_unit, azure_auth_private_key, test_db_session
):
    azure_token = auth_claims_unit.copy()
    azure_token["groups"] = [
        AzureGroup.NON_PROD.azure_group_guid,
        AzureGroup.NON_PROD_DEV.azure_group_guid,
    ]
    test_db_session.add(
        AzureGroupPermission(
            azure_group_id=AzureGroup.NON_PROD_DEV.azure_group_id,
            azure_permission_id=AzurePermission.USER_READ.azure_permission_id,
        )
    )
    encoded = jwt.encode(
        azure_token,
        azure_auth_private_key,
        algorithm=ALGORITHMS.RS256,
        headers={"kid": azure_auth_private_key.get("kid")},
    )
    for x in range(3):
        UserFactory.create(email_address=f"janeDo+{x}@example.com")
    for x in range(3):
        UserFactory.create(email_address=f"johnDo+{x}@example.com")
    with app.app.test_request_context("/v1/admin/users"):
        # Just showing that it is case insensitive.
        response = client.get(
            "/v1/admin/users?page_size=10&email_address=anedo",
            headers={"Authorization": f"Bearer {encoded}"},
        )
        assert response.status_code == 200
        assert g.azure_user.sub_id == "foo"
        assert g.azure_user.permissions == [AzurePermission.USER_READ.azure_permission_id]
        response_json = response.get_json()
        data = response_json.get("data")
        paging = response_json.get("meta").get("paging")

        assert paging.get("order_by") == "created_at"
        assert paging.get("order_direction") == "descending"
        assert paging.get("page_offset") == 1
        assert paging.get("page_size") == 10
        assert paging.get("total_pages") == 1
        assert paging.get("total_records") == 3
        assert len(data) == 3
