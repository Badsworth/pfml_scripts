# Testing Mocked API responses
from unittest import mock

import pytest

from massgov.pfml.rmv.caller import MockZeepCaller


@pytest.fixture
def rmv_full_mock(monkeypatch):
    new_env = monkeypatch.setenv("RMV_CHECK_BEHAVIOR", "fully_mocked")
    return new_env


@pytest.fixture
def rmv_partial_mock(monkeypatch):
    new_env = monkeypatch.setenv("RMV_CHECK_BEHAVIOR", "partially_mocked")
    return new_env


@pytest.fixture
def rmv_no_mock(monkeypatch):
    new_env = monkeypatch.setenv("RMV_CHECK_BEHAVIOR", "not_mocked")
    return new_env


@pytest.fixture
def rmv_toggle_success(monkeypatch):
    new_env = monkeypatch.setenv("RMV_CHECK_MOCK_SUCCESS", "0")
    return new_env


body = {
    "absence_case_id": "string",
    "date_of_birth": "1970-01-01",
    "first_name": "Jane",
    "last_name": "Doe",
    "mass_id_number": "S99988801",
    "residential_address_city": "Boston",
    "residential_address_line_1": "123 Main St.",
    "residential_address_line_2": "Apt. 123",
    "residential_address_zip_code": "12345",
    "ssn_last_4": "9999",
}


def test_rmv_check_fully_mocked(rmv_full_mock, rmv_toggle_success, client):
    response = client.post("/v1/rmv-check", json=body)
    response_body = response.get_json().get("data")

    assert response.status_code == 200
    assert response_body["verified"] is True
    assert response_body["description"] == "Verification check passed."


def test_rmv_check_failed_fully_mocked(rmv_full_mock, client):
    response = client.post("/v1/rmv-check", json=body)
    response_body = response.get_json().get("data")

    assert response.status_code == 200
    assert response_body["verified"] is False
    assert (
        response_body["description"]
        == "Verification failed because no record could be found for given ID information."
    )


@mock.patch("massgov.pfml.api.rmv_check.RmvClient.__init__", return_value=None)
def test_rmv_check_partial_mock_steve(monkeypatch, rmv_partial_mock, rmv_toggle_success, client):
    # This tests one of the pre-loaded test cases for the stage env
    body = {
        "absence_case_id": "testing_the_env",
        "date_of_birth": "1970-01-01",
        "first_name": "Steve",
        "last_name": "Tester",
        "mass_id_number": "S99988801",
        "residential_address_city": "Boston",
        "residential_address_line_1": "123 Main St.",
        "residential_address_line_2": "Apt. 123",
        "residential_address_zip_code": "12345",
        "ssn_last_4": "9999",
    }
    mock_rmv_caller = MockZeepCaller(
        {
            "LicenseID": "S99988801",
            "Street1": "123 Main St.",
            "Street2": "Apt. 123",
            "City": "Boston",
            "Zip": "12345",
        }
    )
    with mock.patch("massgov.pfml.api.rmv_check.RmvClient._caller", mock_rmv_caller) as MockCaller:
        response = client.post("/v1/rmv-check", json=body)
        response_body = response.get_json().get("data")

    assert response.status_code == 200
    assert MockCaller.calls["VendorLicenseInquiry"] == 1
    assert response_body["verified"] is True
    assert response_body["description"] == "Verification check passed."


def test_failed_partial_mock_rmv_check(rmv_partial_mock, client):
    body = {
        "absence_case_id": "testing_the_env",
        "date_of_birth": "1970-01-01",
        "first_name": "John",
        "last_name": "Doe",
        "mass_id_number": "S99988801",
        "residential_address_city": "Boston",
        "residential_address_line_1": "123 Main St.",
        "residential_address_line_2": "Apt. 123",
        "residential_address_zip_code": "12345",
        "ssn_last_4": "9999",
    }
    response = client.post("/v1/rmv-check", json=body)
    response_body = response.get_json().get("data")
    assert response.status_code == 200
    assert response_body["verified"] is False
    assert (
        response_body["description"]
        == "Verification failed because no record could be found for given ID information."
    )


def test_partial_mock_rmv_check(rmv_partial_mock, rmv_toggle_success, client):
    body = {
        "absence_case_id": "testing_the_env",
        "date_of_birth": "1970-01-01",
        "first_name": "John",
        "last_name": "Doe",
        "mass_id_number": "S99988801",
        "residential_address_city": "Boston",
        "residential_address_line_1": "123 Main St.",
        "residential_address_line_2": "Apt. 123",
        "residential_address_zip_code": "12345",
        "ssn_last_4": "9999",
    }
    response = client.post("/v1/rmv-check", json=body)
    response_body = response.get_json().get("data")
    assert response.status_code == 200
    assert response_body["verified"] is True
    assert response_body["description"] == "Verification check passed."


@mock.patch("massgov.pfml.api.rmv_check.RmvClient.__init__", return_value=None)
def test_rmv_check_no_mocking(monkeypatch, rmv_no_mock, client):
    mock_rmv_caller = MockZeepCaller(
        {
            "LicenseID": "S99988801",
            "Street1": "123 Main St.",
            "Street2": "Apt. 123",
            "City": "Boston",
            "Zip": "12345",
        }
    )
    with mock.patch("massgov.pfml.api.rmv_check.RmvClient._caller", mock_rmv_caller) as MockCaller:
        response = client.post("/v1/rmv-check", json=body)
        response_body = response.get_json().get("data")

    assert response.status_code == 200
    assert MockCaller.calls["VendorLicenseInquiry"] == 1
    assert response_body["verified"] is True
    assert response_body["description"] == "Verification check passed."
