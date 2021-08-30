#
# Tests for massgov.pfml.fineos.factory.
#

import requests_oauthlib

import massgov.pfml.fineos.factory


def test_fineos_client_config_from_env_default():
    config = massgov.pfml.fineos.factory.FINEOSClientConfig.from_env()
    assert config == massgov.pfml.fineos.factory.FINEOSClientConfig(
        integration_services_api_url=None,
        customer_api_url=None,
        group_client_api_url=None,
        wscomposer_api_url=None,
        wscomposer_user_id="CONTENT",
        oauth2_url=None,
        oauth2_client_id=None,
        oauth2_client_secret=None,
    )


def test_fineos_client_config_from_env(monkeypatch):
    monkeypatch.setenv(
        "FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL", "https://2.abc.test/integrationservicesapi/"
    )
    monkeypatch.setenv("FINEOS_CLIENT_GROUP_CLIENT_API_URL", "https://2.abc.test/groupclientapi/")
    monkeypatch.setenv("FINEOS_CLIENT_CUSTOMER_API_URL", "https://1.abc.test/customerapi/")
    monkeypatch.setenv("FINEOS_CLIENT_WSCOMPOSER_API_URL", "https://1.def.test/wscomposer/")
    monkeypatch.setenv("FINEOS_CLIENT_WSCOMPOSER_USER_ID", "ABC1")
    monkeypatch.setenv("FINEOS_CLIENT_OAUTH2_URL", "https://1.ghi.test/oauth2/token")
    monkeypatch.setenv("FINEOS_CLIENT_OAUTH2_CLIENT_ID", "1234567890abcdefghij")
    monkeypatch.setenv("FINEOS_CLIENT_OAUTH2_CLIENT_SECRET", "abcdefghijklmnopqrstuvwxyz")

    config = massgov.pfml.fineos.factory.FINEOSClientConfig.from_env()
    assert config == massgov.pfml.fineos.factory.FINEOSClientConfig(
        integration_services_api_url="https://2.abc.test/integrationservicesapi/",
        group_client_api_url="https://2.abc.test/groupclientapi/",
        customer_api_url="https://1.abc.test/customerapi/",
        wscomposer_api_url="https://1.def.test/wscomposer/",
        wscomposer_user_id="ABC1",
        oauth2_url="https://1.ghi.test/oauth2/token",
        oauth2_client_id="1234567890abcdefghij",
        oauth2_client_secret="abcdefghijklmnopqrstuvwxyz",
    )


def test_create_client_default_is_mock():
    client = massgov.pfml.fineos.factory.create_client()
    assert type(client) == massgov.pfml.fineos.mock_client.MockFINEOSClient


def fake_fetch_token(session, token_url, client_id, client_secret, timeout):
    return {"token_type": "Bearer", "expires_in": 3600, "expires_at": 1595434193.373}


def test_create_client_from_env(monkeypatch):
    monkeypatch.setenv(
        "FINEOS_CLIENT_INTEGRATION_SERVICES_API_URL", "https://2.abc.test/integrationservicesapi/"
    )
    monkeypatch.setenv("FINEOS_CLIENT_GROUP_CLIENT_API_URL", "https://1.abc.test/groupclientapi/")
    monkeypatch.setenv("FINEOS_CLIENT_CUSTOMER_API_URL", "https://2.abc.test/customerapi/")
    monkeypatch.setenv("FINEOS_CLIENT_WSCOMPOSER_API_URL", "https://2.def.test/wscomposer/")
    monkeypatch.setenv("FINEOS_CLIENT_OAUTH2_URL", "https://2.ghi.test/oauth2/token")
    monkeypatch.setenv("FINEOS_CLIENT_OAUTH2_CLIENT_ID", "1234567890abcdefghij")
    monkeypatch.setenv("FINEOS_CLIENT_OAUTH2_CLIENT_SECRET", "abcdefghijklmnopqrstuvwxyz")

    # The FINEOSClient constructor attempts to fetch an OAuth token. For this test case we only
    # want to ensure that create_client() is constructing the correct class so this disables the
    # OAuth network call.
    monkeypatch.setattr(requests_oauthlib.OAuth2Session, "fetch_token", fake_fetch_token)

    client = massgov.pfml.fineos.factory.create_client()
    assert type(client) == massgov.pfml.fineos.fineos_client.FINEOSClient
    assert client.integration_services_api_url == "https://2.abc.test/integrationservicesapi/"
    assert client.group_client_api_url == "https://1.abc.test/groupclientapi/"
    assert client.customer_api_url == "https://2.abc.test/customerapi/"
    assert client.wscomposer_url == "https://2.def.test/wscomposer/"
    assert client.oauth2_url == "https://2.ghi.test/oauth2/token"


def test_create_client_from_config(monkeypatch):
    config = massgov.pfml.fineos.factory.FINEOSClientConfig(
        integration_services_api_url="https://2.abc.test/integrationservicesapi/",
        group_client_api_url="https://1.abc.test/groupclientapi/",
        customer_api_url="https://3.abc.test/customerapi/",
        wscomposer_api_url="https://3.def.test/wscomposer/",
        wscomposer_user_id="ABC3",
        oauth2_url="https://3.ghi.test/oauth2/token",
        oauth2_client_id="1234567890abcdefghij",
        oauth2_client_secret="abcdefghijklmnopqrstuvwxyz",
    )

    # The FINEOSClient constructor attempts to fetch an OAuth token. For this test case we only
    # want to ensure that create_client() is constructing the correct class so this disables the
    # OAuth network call.
    monkeypatch.setattr(requests_oauthlib.OAuth2Session, "fetch_token", fake_fetch_token)

    client = massgov.pfml.fineos.factory.create_client(config)
    assert type(client) == massgov.pfml.fineos.fineos_client.FINEOSClient
    assert client.integration_services_api_url == "https://2.abc.test/integrationservicesapi/"
    assert client.group_client_api_url == "https://1.abc.test/groupclientapi/"
    assert client.customer_api_url == "https://3.abc.test/customerapi/"
    assert client.wscomposer_url == "https://3.def.test/wscomposer/"
    assert client.wscomposer_user_id == "ABC3"
    assert client.oauth2_url == "https://3.ghi.test/oauth2/token"
