#
# Tests for massgov.pfml.fineos.fineos_client.
#

import datetime

import pytest
import requests
import requests_oauthlib

import massgov.pfml.fineos.exception
import massgov.pfml.fineos.fineos_client
import massgov.pfml.fineos.models


def fake_fetch_token(session, token_url, client_id, client_secret, timeout):
    return {"token_type": "Bearer", "expires_in": 3600, "expires_at": 1595434193.373}


def test_constructor_ok(monkeypatch):
    # The FINEOSClient constructor attempts to fetch an OAuth token. For this test case we do not
    # want any real network calls to occur.
    monkeypatch.setattr(requests_oauthlib.OAuth2Session, "fetch_token", fake_fetch_token)

    client = massgov.pfml.fineos.fineos_client.FINEOSClient(
        customer_api_url="https://1.abc.test/customerapi/",
        wscomposer_url="https://1.def.test/wscomposer/",
        oauth2_url="https://1.ghi.test/oauth2/token",
        client_id="1234567890abcdefghij",
        client_secret="abcdefghijklmnopqrstuvwxyz",
    )
    assert client.customer_api_url == "https://1.abc.test/customerapi/"
    assert client.wscomposer_url == "https://1.def.test/wscomposer/"
    assert client.oauth2_url == "https://1.ghi.test/oauth2/token"


def test_constructor_request_error():
    with pytest.raises(
        massgov.pfml.fineos.exception.FINEOSClientError, match="InvalidURL: Failed to parse"
    ):
        massgov.pfml.fineos.fineos_client.FINEOSClient(
            customer_api_url="https://2.abc.test/customerapi/",
            wscomposer_url="https://2.def.test/wscomposer/",
            oauth2_url="https://localhost:99999999/oauth2/token",  # Invalid URL due to the port
            client_id="1234567890abcdefghij",
            client_secret="abcdefghijklmnopqrstuvwxyz",
        )


def test_constructor_oauth2_error():
    with pytest.raises(
        massgov.pfml.fineos.exception.FINEOSClientError, match="InsecureTransportError:"
    ):
        massgov.pfml.fineos.fineos_client.FINEOSClient(
            customer_api_url="https://2.abc.test/customerapi/",
            wscomposer_url="https://2.def.test/wscomposer/",
            oauth2_url="http://localhost/oauth2",  # Causes an OAuth2Error due to http:
            client_id="1234567890abcdefghij",
            client_secret="abcdefghijklmnopqrstuvwxyz",
        )


@pytest.fixture
def fineos_client(monkeypatch):
    monkeypatch.setattr(requests_oauthlib.OAuth2Session, "fetch_token", fake_fetch_token)

    return massgov.pfml.fineos.fineos_client.FINEOSClient(
        customer_api_url="http://a/",
        wscomposer_url="https://3.def/wscomp/",
        oauth2_url="https://3.ghi.test/oauth2/token",
        client_id="1234567890abcdefghij",
        client_secret="abcdefghijklmnopqrstuvwxyz",
    )


@pytest.fixture
def fineos_client_capture_requests(monkeypatch, fineos_client):
    fineos_client.capture = []
    fineos_client.fake_responses = [FakeResponse(200)]
    fineos_client.capture_count = 0

    def fake_request(self, method, url, headers, **args):
        fineos_client.capture.append((method, url, headers, args))
        fineos_client.capture_count += 1
        return fineos_client.fake_responses[fineos_client.capture_count - 1]

    monkeypatch.setattr(fineos_client, "_request", fake_request)

    return fineos_client


class FakeResponse:
    def __init__(self, status_code, text="TEST", json_data={}):
        self.status_code = status_code
        self.content_length = 2048
        self.content_type = "application/json"
        self.data = b'{"status": "ok"}'
        self.text = text
        self.json_data = json_data
        self.elapsed = datetime.timedelta(milliseconds=125)

    def json(self):
        return self.json_data


def test_request(fineos_client):
    def request_function(method, url, **args):
        return FakeResponse(200)

    response = fineos_client._request(request_function, "GET", "https://test/url", {})
    assert response.status_code == 200


def test_request_requests_exception(fineos_client):
    def request_function(method, url, **args):
        raise requests.exceptions.ConnectTimeout()

    with pytest.raises(massgov.pfml.fineos.exception.FINEOSClientError, match="ConnectTimeout:"):
        fineos_client._request(request_function, "GET", "https://test/url", {})


def test_request_unexpected_response(fineos_client):
    def request_function(method, url, **args):
        return FakeResponse(404)

    with pytest.raises(
        massgov.pfml.fineos.exception.FINEOSClientBadResponse, match="expected 200, but got 404"
    ):
        fineos_client._request(request_function, "GET", "https://test/url", {})


def test_register_api_user(fineos_client_capture_requests):
    employee_registration = massgov.pfml.fineos.models.EmployeeRegistration(
        user_id="user_4321",
        customer_number=9191,
        date_of_birth=datetime.date(1960, 12, 24),
        email="test_642@mass.gov",
        employer_id=2121,
        first_name="Example",
        last_name="Testcase",
    )

    fineos_client_capture_requests.register_api_user(employee_registration)

    assert fineos_client_capture_requests.capture == [
        (
            "POST",
            "https://3.def/wscomp/webservice?userid=CONTENT&config=EmployeeRegisterService",
            {"Content-Type": "application/xml"},
            {
                "data": """<?xml version='1.0' encoding='UTF-8'?>
<ns0:WSUpdateRequest xmlns:ns0="http://www.fineos.com/wscomposer/EmployeeRegisterService">
    <config-name>EmployeeRegisterService</config-name>
    <update-data>
        <EmployeeRegistrationDTO>
            <CustomerNumber>9191</CustomerNumber>
            <DateOfBirth>1960-12-24</DateOfBirth>
            <Email>test_642@mass.gov</Email>
            <EmployeeExternalId>user_4321</EmployeeExternalId>
            <EmployerId>2121</EmployerId>
            <FirstName>Example</FirstName>
            <LastName>Testcase</LastName>
            <NationalInsuranceNo />
        </EmployeeRegistrationDTO>
    </update-data>
</ns0:WSUpdateRequest>
"""
            },
        )
    ]


def test_health_check(fineos_client_capture_requests):
    health = fineos_client_capture_requests.health_check("u1")

    assert fineos_client_capture_requests.capture == [
        ("GET", "http://a/healthcheck", {"Content-Type": "application/json", "userid": "u1"}, {})
    ]
    assert health is False


def test_health_check_true(fineos_client_capture_requests):
    fineos_client_capture_requests.fake_responses = [FakeResponse(200, text="ALIVE")]

    health = fineos_client_capture_requests.health_check("u1")

    assert fineos_client_capture_requests.capture == [
        ("GET", "http://a/healthcheck", {"Content-Type": "application/json", "userid": "u1"}, {})
    ]
    assert health is True


def test_read_customer_details(fineos_client_capture_requests):
    fineos_client_capture_requests.fake_responses = [
        FakeResponse(
            200,
            json_data={"firstName": "Tester", "lastName": "Testing", "dateOfBirth": "1990-05-07"},
        )
    ]

    customer = fineos_client_capture_requests.read_customer_details("u1")

    assert fineos_client_capture_requests.capture == [
        (
            "GET",
            "http://a/customer/readCustomerDetails",
            {"Content-Type": "application/json", "userid": "u1"},
            {},
        )
    ]
    assert customer == massgov.pfml.fineos.models.customer_api.Customer(
        firstName="Tester", lastName="Testing", dateOfBirth=datetime.date(1990, 5, 7)
    )


# def test_health_check():
#     assert False
#
#
# def test_read_customer_details():
#     assert False
#
#
# def test_start_absence():
#     assert False
#
#
# def test_complete_intake():
#     assert False
#
#
# def test_get_absences():
#     assert False
#
#
# def test_get_absence():
#     assert False
#
#
# def test_add_payment_preference():
#     assert False
