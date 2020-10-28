#
# Tests for massgov.pfml.service_now.factory.
#

from massgov.pfml.servicenow.client import ServiceNowClient
from massgov.pfml.servicenow.factory import ServiceNowClientConfig, create_client
from massgov.pfml.servicenow.mock_client import MockServiceNowClient


def test_service_now_client_config_from_env(monkeypatch):
    monkeypatch.setenv("SERVICE_NOW_BASE_URL", "service_now_base_url")
    monkeypatch.setenv("SERVICE_NOW_USERNAME", "service_now_username")
    monkeypatch.setenv("SERVICE_NOW_PASSWORD", "service_now_password")

    config = ServiceNowClientConfig.from_env()
    assert config == ServiceNowClientConfig(
        base_url="service_now_base_url",
        username="service_now_username",
        password="service_now_password",
    )


def test_mock_client_setup(monkeypatch):
    monkeypatch.setenv("ENABLE_MOCK_SERVICE_NOW_CLIENT", "1")
    client = create_client()
    assert type(client) == MockServiceNowClient


def test_create_client_from_env(monkeypatch):
    monkeypatch.setenv("ENABLE_MOCK_SERVICE_NOW_CLIENT", "")
    monkeypatch.setenv("SERVICE_NOW_BASE_URL", "service_now_base_url")
    monkeypatch.setenv("SERVICE_NOW_USERNAME", "service_now_username")
    monkeypatch.setenv("SERVICE_NOW_PASSWORD", "service_now_password")

    client = create_client()
    assert type(client) == ServiceNowClient
    assert client._base_url == "service_now_base_url"
    assert client._username == "service_now_username"
    assert client._password == "service_now_password"
