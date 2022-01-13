from flask import g
from jose import jwt
from jose.constants import ALGORITHMS

from massgov.pfml.db.models.employees import AzureGroup, AzureGroupPermission, AzurePermission
from massgov.pfml.db.models.flags import FeatureFlag, FeatureFlagValue

# There are also feature flag related tests in tests/massgov/pfml/util/feature_gate/features_cache.py


def test_flags_get_enabled_feature_flag_with_start_end_options(client, test_db_session):
    flag = FeatureFlag.get_instance(test_db_session, description="maintenance")
    feature_flag_value = FeatureFlagValue()
    feature_flag_value.feature_flag = flag
    feature_flag_value.enabled = True
    feature_flag_value.end = "2021-06-26 18:00:00-04"
    feature_flag_value.start = "2021-06-26 17:00:00-04"
    feature_flag_value.options = dict(page_routes=["/applications/*", "/employers/*"])
    test_db_session.add(feature_flag_value)
    response = client.get("/v1/flags")
    assert response.status_code == 200
    response_data = response.get_json().get("data")
    assert len(response_data) == 1
    flag_response = response_data[0]
    assert flag_response.get("enabled") is True
    assert flag_response.get("start") == "2021-06-26T17:00:00-04:00"
    assert flag_response.get("end") == "2021-06-26T18:00:00-04:00"
    assert flag_response.get("options") == {"page_routes": ["/applications/*", "/employers/*"]}


def test_flags_get_empty(client):
    response = client.get("/v1/flags")
    assert response.status_code == 200
    response_data = response.get_json().get("data")
    assert len(response_data) == 1
    flag = response_data[0]
    assert flag.get("name") == "maintenance"
    assert flag.get("enabled") is False
    assert flag.get("start") is None
    assert flag.get("end") is None
    assert flag.get("options") is None


def test_flags_post_success(app, client, test_db_session, auth_claims_unit, azure_auth_private_key):
    azure_token = auth_claims_unit.copy()
    azure_token["unique_name"] = "johndo@example.com"
    azure_token["given_name"] = "john"
    azure_token["family_name"] = "doe"
    azure_token["groups"] = [
        AzureGroup.NON_PROD.azure_group_guid,
        AzureGroup.NON_PROD_DEV.azure_group_guid,
    ]
    test_db_session.add(
        AzureGroupPermission(
            azure_group_id=AzureGroup.NON_PROD_DEV.azure_group_id,
            azure_permission_id=AzurePermission.MAINTENANCE_EDIT.azure_permission_id,
        )
    )
    encoded = jwt.encode(
        azure_token,
        azure_auth_private_key,
        algorithm=ALGORITHMS.RS256,
        headers={"kid": azure_auth_private_key.get("kid")},
    )
    post_body = {
        "enabled": True,
        "start": "2022-01-14T00:00:00-05:00",
        "end": "2022-01-15T00:00:00-05:00",
        "options": {
            "name": "applications and custom",
            "page_routes": ["/applications/*", "/custom/*"],
        },
    }
    with app.app.test_request_context("/v1/admin/users"):
        response = client.post(
            "/v1/flags/maintenance", headers={"Authorization": f"Bearer {encoded}"}, json=post_body
        )
        assert response.status_code == 201
        assert g.azure_user.sub_id == "foo"
        assert g.azure_user.permissions == [
            AzurePermission.MAINTENANCE_EDIT.azure_permission_id,
        ]
        response_json = response.get_json()
        data = response_json.get("data")
        assert data.get("enabled") is True
        assert data.get("start") == "2022-01-14T00:00:00-05:00"
        assert data.get("end") == "2022-01-15T00:00:00-05:00"
        assert data.get("options").get("name") == "applications and custom"
        assert len(data.get("options").get("page_routes")) == 2
        assert data.get("options").get("page_routes") == ["/applications/*", "/custom/*"]
