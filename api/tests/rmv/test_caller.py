import os

import boto3
import moto
import pytest
from requests import Session
from requests.exceptions import HTTPError
from requests.models import Response

from massgov.pfml.rmv.caller import LazyZeepApiCaller, RmvConfig
from tests.helpers.certs import generate_x509_cert_and_key, p12_encoded_cert


@pytest.fixture(scope="session")
def pkcs12_data():
    """
    Generate self-signed client certificate.
    """
    return p12_encoded_cert(generate_x509_cert_and_key()).export(passphrase="abcd".encode("utf-8"))


@pytest.fixture
def mock_wsdl_200(monkeypatch):
    """
    Mock a successful WSDL response from ./api.wsdl.
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


def test_zeep_caller_rmv_config_from_env_and_secrets_manager(reset_aws_env_vars, monkeypatch):
    # Test that the RmvConfig logic runs properly and retrieves values
    # from the environment and secrets manager.

    # patch all required environment variables
    monkeypatch.setenv("RMV_CLIENT_CERTIFICATE_BINARY_ARN", "arn")
    monkeypatch.setenv("RMV_CLIENT_BASE_URL", "https://fake-rmv-url.com")
    monkeypatch.setenv("RMV_CLIENT_CERTIFICATE_PASSWORD", "pw")

    # the call to get_secret_value in RmvConfig.from_env_and_secrets_manager
    # needs this as the client does not specify a region and the
    # `reset_aws_env_vars` fixture resets the default env var to 'testing'
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    with moto.mock_secretsmanager():
        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
        secrets_client.create_secret(Name="arn", SecretBinary=str.encode("hello"))

        # Generate the RMV Config and verify parsed attributes
        config = RmvConfig.from_env_and_secrets_manager()
        assert config.base_url == "https://fake-rmv-url.com"
        assert config.pkcs12_pw == "pw"
        assert config.pkcs12_data == str.encode("hello")
