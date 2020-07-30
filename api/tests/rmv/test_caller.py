import os

import boto3
import botocore
import pytest
from botocore.stub import Stubber
from requests import Session
from requests.exceptions import HTTPError
from requests.models import Response

from massgov.pfml.rmv.caller import LazyZeepApiCaller, RmvConfig


@pytest.fixture
def pkcs12_data():
    """
    Load self-signed client certificate. This was generated for testing
    with no expiration using the following commands:

      openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 0
      openssl pkcs12 -export -out certificate.p12 -inkey key.pem -in cert.pem
    """
    certpath = os.path.join(os.path.dirname(__file__), "./certificate.p12")
    with open(certpath, "rb") as file:
        data = file.read()

    return data


@pytest.fixture
def mock_wsdl_200(monkeypatch):
    """
    Mock a succesful WSDL response from ./api.wsdl.
    """
    monkeypatch.setattr(Session, "get", mock_wsdl_response(200))


@pytest.fixture
def mock_wsdl_500(monkeypatch):
    """
    Mock a 500 WSDL response.
    """
    monkeypatch.setattr(Session, "get", mock_wsdl_response(500))


def mock_wsdl_response(status_code):
    res = Response()
    res.status_code = status_code

    # Load fake minimal version of the RMV API WSDL.
    wsdlpath = os.path.join(os.path.dirname(__file__), "./api.wsdl")
    with open(wsdlpath, "rb") as file:
        res._content = file.read()

    def mock_get(*args, **kwargs):
        return res

    return mock_get


def test_zeep_caller_get_200(mock_wsdl_200, pkcs12_data):
    # RMV Client should be able to retrieve and parse WSDL from a given source.
    caller = LazyZeepApiCaller(
        RmvConfig(base_url="https://fake-rmv-url.com", pkcs12_data=pkcs12_data, pkcs12_pw="abcd")
    )
    assert caller.get()


def test_zeep_caller_get_500(mock_wsdl_500, pkcs12_data):
    # RMV Client should raise an HTTP error when failing to retrieve the WSDL on first call.
    caller = LazyZeepApiCaller(
        RmvConfig(base_url="https://fake-rmv-url.com", pkcs12_data=pkcs12_data, pkcs12_pw="abcd")
    )

    with pytest.raises(HTTPError):
        caller.get()


def test_zeep_caller_rmv_config_from_env_and_secrets_manager(monkeypatch):
    # Test that the RmvConfig logic runs properly and retrieves values
    # from the environment and secrets manager.

    # patch all required environment variables
    monkeypatch.setenv("RMV_CLIENT_CERTIFICATE_BINARY_ARN", "arn")
    monkeypatch.setenv("RMV_CLIENT_BASE_URL", "https://fake-rmv-url.com")
    monkeypatch.setenv("RMV_CLIENT_CERTIFICATE_PASSWORD", "pw")

    # patch a custom secretsmanager client into all boto3 sessions
    client = botocore.session.get_session().create_client("secretsmanager", region_name="us-east-1")
    monkeypatch.setattr(boto3, "client", lambda name: client)

    with Stubber(client) as stubber:
        # Add a response to the custom client
        stubber.add_response(
            "get_secret_value",
            expected_params={"SecretId": "arn"},
            service_response={"SecretBinary": str.encode("hello")},
        )

        # Generate the RMV Config and verify parsed attributes
        config = RmvConfig.from_env_and_secrets_manager()
        assert config.base_url == "https://fake-rmv-url.com"
        assert config.pkcs12_pw == "pw"
        assert config.pkcs12_data == str.encode("hello")
        stubber.assert_no_pending_responses()
