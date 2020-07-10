import os

import boto3
import botocore
import pytest
from botocore.stub import Stubber
from requests import Session
from requests.exceptions import HTTPError
from requests.models import Response

from massgov.pfml.rmv.client import RmvClient, RmvConfig


def mock_response(status_code):
    res = Response()
    res.status_code = status_code

    # Load fake minimal version of the RMV API WSDL.
    wsdlpath = os.path.join(os.path.dirname(__file__), "./api.wsdl")
    with open(wsdlpath, "rb") as file:
        res._content = file.read()

    def mock_get(*args, **kwargs):
        return res

    return mock_get


@pytest.fixture
def pkcs12_data():
    # Load self-signed client certificate. This was generated for testing
    # with no expiration using the following commands:
    #
    #   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 0
    #   openssl pkcs12 -export -out certificate.p12 -inkey key.pem -in cert.pem
    #
    certpath = os.path.join(os.path.dirname(__file__), "./certificate.p12")
    with open(certpath, "rb") as file:
        data = file.read()

    return data


def test_rmv_client_get_client_200(monkeypatch, pkcs12_data):
    monkeypatch.setattr(Session, "get", mock_response(200))

    client = RmvClient(
        RmvConfig(base_url="https://fake-rmv-url.com", pkcs12_data=pkcs12_data, pkcs12_pw="abcd")
    )

    api_client = client.client
    assert api_client.wsdl


def test_rmv_client_get_client_500(monkeypatch, pkcs12_data):
    monkeypatch.setattr(Session, "get", mock_response(500))

    client = RmvClient(
        RmvConfig(base_url="https://fake-rmv-url.com", pkcs12_data=pkcs12_data, pkcs12_pw="abcd")
    )

    with pytest.raises(HTTPError):
        client.client


def test_rmv_client_from_env_and_secrets_manager(monkeypatch):
    monkeypatch.setenv("RMV_CLIENT_CERTIFICATE_BINARY_ARN", "arn")
    monkeypatch.setenv("RMV_CLIENT_BASE_URL", "https://fake-rmv-url.com")
    monkeypatch.setenv("RMV_CLIENT_CERTIFICATE_PASSWORD", "pw")

    client = botocore.session.get_session().create_client("secretsmanager", region_name="us-east-1")
    monkeypatch.setattr(boto3, "client", lambda name: client)

    with Stubber(client) as stubber:
        stubber.add_response(
            "get_secret_value",
            expected_params={"SecretId": "arn"},
            service_response={"SecretBinary": str.encode("hello")},
        )

        config = RmvConfig.from_env_and_secrets_manager()
        assert config.base_url == "https://fake-rmv-url.com"
        assert config.pkcs12_pw == "pw"
        assert config.pkcs12_data == str.encode("hello")
        stubber.assert_no_pending_responses()
