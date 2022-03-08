from massgov.pfml.db.models.flags import FeatureFlag, FeatureFlagValue

# There are also feature flag related tests in tests/massgov/pfml/util/feature_gate/features_cache.py


def test_flags_get_enabled_feature_flag_with_start_end_options(client, test_db_session):
    flag_name = "maintenance"
    flag = FeatureFlag.get_instance(test_db_session, description=flag_name)
    feature_flag_value = FeatureFlagValue()
    feature_flag_value.feature_flag = flag
    feature_flag_value.enabled = True
    feature_flag_value.end = "2021-06-26 18:00:00-04"
    feature_flag_value.start = "2021-06-26 17:00:00-04"
    feature_flag_value.options = dict(page_routes=["/applications/*", "/employers/*"])
    feature_flag_value.email_address = "johndoe@example.com"
    feature_flag_value.sub_id = "1234"
    feature_flag_value.family_name = "doe"
    feature_flag_value.given_name = "john"
    feature_flag_value.action = "INSERT"
    test_db_session.add(feature_flag_value)
    response = client.get(f"/v1/flags/{flag_name}")
    assert response.status_code == 200
    flag_response = response.get_json().get("data")
    assert flag_response.get("enabled") is True
    assert flag_response.get("start") == "2021-06-26T17:00:00-04:00"
    assert flag_response.get("end") == "2021-06-26T18:00:00-04:00"
    assert flag_response.get("options") == {"page_routes": ["/applications/*", "/employers/*"]}


def test_flags_get_enabled_feature_flags_with_start_end_options(client, test_db_session):
    flag = FeatureFlag.get_instance(test_db_session, description="maintenance")
    feature_flag_value = FeatureFlagValue()
    feature_flag_value.feature_flag = flag
    feature_flag_value.enabled = True
    feature_flag_value.end = "2021-06-26 18:00:00-04"
    feature_flag_value.start = "2021-06-26 17:00:00-04"
    feature_flag_value.options = dict(page_routes=["/applications/*", "/employers/*"])
    feature_flag_value.email_address = "johndoe@example.com"
    feature_flag_value.sub_id = "1234"
    feature_flag_value.family_name = "doe"
    feature_flag_value.given_name = "john"
    feature_flag_value.action = "INSERT"
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


def test_flags_get_enabled_feature_flag_no_start_end_options(client):
    mock_features_file = """
maintenance:
    enabled: 1
"""
    with patch("massgov.pfml.util.files.open_stream", mock_open(read_data=mock_features_file)):
        response = client.get("/v1/flags")
        assert response.status_code == 200
        response_data = response.get_json().get("data")
        assert len(response_data) == 1
        flag_response = response_data[0]
        assert flag_response.get("enabled") is True
        assert flag_response.get("start") is None
        assert flag_response.get("end") is None
        assert flag_response.get("options") is None


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
