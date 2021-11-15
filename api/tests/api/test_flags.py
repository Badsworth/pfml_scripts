import pytest
from mock import mock_open, patch

from massgov.pfml.util.feature_gate import FeaturesCache

# There are also feature flag related tests in massgov/pfml/util/feature_gate/features_cache.py


@pytest.fixture(autouse=True)
def features_cache_mock():
    "Disable caching so the features can be checked one by one"
    with patch("massgov.pfml.util.feature_gate.get_features_cache") as features_cache_mock:
        features_cache_mock.return_value = FeaturesCache(file_path="fake", ttl=0)
        yield


def test_flags_get_enabled_feature_flag_with_start_end_options(client):
    mock_features_file = """
maintenance:
    start: "2021-06-26 17:00:00-04"
    end: "2021-06-26 18:00:00-04"
    enabled: 1
    options:
      page_routes:
       - /applications/*
       - /employers/*
"""
    with patch("massgov.pfml.util.files.open_stream", mock_open(read_data=mock_features_file)):
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
    mock_features_file = """
"""
    with patch("massgov.pfml.util.files.open_stream", mock_open(read_data=mock_features_file)):
        response = client.get("/v1/flags")
        print(response.get_json().get("data"))
        assert response.status_code == 200
        response_data = response.get_json().get("data")
        assert len(response_data) == 0


def test_flags_get_invalid_datetime(client):
    mock_features_file = """
maintenance:
    start: "2021-04"
    end: "2021-06-26 18:00:00-04"
    enabled: 1
    options:
      page_routes:
       - /applications/*
       - /employers/*
"""
    with patch("massgov.pfml.util.files.open_stream", mock_open(read_data=mock_features_file)):
        response = client.get("/v1/flags")
        assert response.status_code == 400
        errors = response.get_json().get("errors")
        assert len(errors) == 1
        assert errors[0] == {
            "field": "start",
            "message": 'Error in field: "start". Invalid datetime format.',
            "type": "value_error.datetime",
        }


def test_flags_get_invalid_enabled(client):
    mock_features_file = """
maintenance:
    start: "2021-06-26 17:00:00-04"
    end: "2021-06-26 18:00:00-04"
    enabled: "2021-06-26 18:00:00-04"
    options:
      page_routes:
       - /applications/*
       - /employers/*
"""
    with patch("massgov.pfml.util.files.open_stream", mock_open(read_data=mock_features_file)):
        response = client.get("/v1/flags")
        assert response.status_code == 400
        errors = response.get_json().get("errors")
        assert len(errors) == 1
        assert errors[0] == {
            "field": "enabled",
            "message": 'Error in field: "enabled". Value could not be parsed to a boolean.',
            "type": "type_error.bool",
        }


def test_flags_get_invalid_options(client):
    mock_features_file = """
maintenance:
    start: "2021-06-26 17:00:00-04"
    end: "2021-06-26 18:00:00-04"
    enabled: 1
    options:
       - /applications/*
       - /employers/*
"""
    with patch("massgov.pfml.util.files.open_stream", mock_open(read_data=mock_features_file)):
        response = client.get("/v1/flags")
        assert response.status_code == 400
        errors = response.get_json().get("errors")
        assert len(errors) == 1
        assert errors[0] == {
            "field": "options",
            "message": 'Error in field: "options". Value is not a valid dict.',
            "type": "type_error.dict",
        }
