import pytest

from massgov.pfml.experian.physical_address.client import (
    Client,
    ExperianConfig,
    build_simple_address_search_request,
)


@pytest.fixture
def mock_requests_session(mocker):
    mock_session = mocker.patch("requests.Session", autospec=True)
    mock_session.headers = dict()
    return mock_session


@pytest.fixture
def mock_requests_session_empty_response(mock_requests_session, mocker):
    mock_response = mocker.patch("requests.Response", autospec=True)
    mock_response.text = "{}"
    mock_requests_session.request.return_value = mock_response

    return mock_requests_session


@pytest.mark.parametrize("timeout", [None, 0, 1, (3.1, 5)])
def test_client_request_different_timeout(mock_requests_session_empty_response, timeout):
    client = Client(
        config=ExperianConfig(auth_token="foo"), session=mock_requests_session_empty_response
    )

    client._request("GET", "foo", timeout=timeout)
    mock_requests_session_empty_response.request.assert_called_with(
        "GET", f"{client.config.base_url}/foo", timeout=timeout
    )


def test_client_search(mock_requests_session_empty_response):
    client = Client(
        config=ExperianConfig(auth_token="foo"), session=mock_requests_session_empty_response
    )

    assert "Auth-Token" in mock_requests_session_empty_response.headers
    assert mock_requests_session_empty_response.headers["Auth-Token"] == "foo"

    client.search(build_simple_address_search_request("bar"))
    mock_requests_session_empty_response.request.assert_called_with(
        "POST",
        f"{client.config.base_url}/address/search/v1",
        data='{"country_iso": "USA", "components": {"unspecified": ["bar"]}}',
        headers={},
        timeout=16,
    )

    client.search(build_simple_address_search_request("bar"), reference_id="123")
    mock_requests_session_empty_response.request.assert_called_with(
        "POST",
        f"{client.config.base_url}/address/search/v1",
        data='{"country_iso": "USA", "components": {"unspecified": ["bar"]}}',
        headers={"Reference-Id": "123"},
        timeout=16,
    )

    client.search(build_simple_address_search_request("bar"), timeout_seconds=12)
    mock_requests_session_empty_response.request.assert_called_with(
        "POST",
        f"{client.config.base_url}/address/search/v1",
        data='{"country_iso": "USA", "components": {"unspecified": ["bar"]}}',
        headers={"Timeout-Seconds": "12"},
        timeout=16,
    )


def test_client_search_error(mock_requests_session):
    client = Client(config=ExperianConfig(auth_token="foo"), session=mock_requests_session)
    mock_requests_session.request.side_effect = Exception()

    with pytest.raises(Exception):
        client.search(build_simple_address_search_request("bar"))


def test_client_format(mock_requests_session):
    client = Client(config=ExperianConfig(auth_token="foo"), session=mock_requests_session)

    assert "Auth-Token" in mock_requests_session.headers
    assert mock_requests_session.headers["Auth-Token"] == "foo"

    client.format("bar")
    mock_requests_session.request.assert_called_with(
        "GET",
        f"{client.config.base_url}/address/format/v1/bar",
        headers={"Add-Components": "true", "Add-Metadata": "true"},
        timeout=16,
    )

    client.format("bar", add_metadata=False)
    mock_requests_session.request.assert_called_with(
        "GET",
        f"{client.config.base_url}/address/format/v1/bar",
        headers={"Add-Components": "true", "Add-Metadata": "false"},
        timeout=16,
    )

    client.format("bar", add_components=False)
    mock_requests_session.request.assert_called_with(
        "GET",
        f"{client.config.base_url}/address/format/v1/bar",
        headers={"Add-Components": "false", "Add-Metadata": "true"},
        timeout=16,
    )

    client.format("bar", add_metadata=None)
    mock_requests_session.request.assert_called_with(
        "GET",
        f"{client.config.base_url}/address/format/v1/bar",
        headers={"Add-Components": "true"},
        timeout=16,
    )

    client.format("bar", add_components=None)
    mock_requests_session.request.assert_called_with(
        "GET",
        f"{client.config.base_url}/address/format/v1/bar",
        headers={"Add-Metadata": "true"},
        timeout=16,
    )

    client.format("bar", reference_id="123")
    mock_requests_session.request.assert_called_with(
        "GET",
        f"{client.config.base_url}/address/format/v1/bar",
        headers={"Add-Components": "true", "Add-Metadata": "true", "Reference-Id": "123"},
        timeout=16,
    )

    client.format("bar", timeout_seconds=12)
    mock_requests_session.request.assert_called_with(
        "GET",
        f"{client.config.base_url}/address/format/v1/bar",
        headers={"Add-Components": "true", "Add-Metadata": "true", "Timeout-Seconds": "12"},
        timeout=16,
    )


def test_client_format_error(mock_requests_session):
    client = Client(config=ExperianConfig(auth_token="foo"), session=mock_requests_session)
    mock_requests_session.request.side_effect = Exception()

    with pytest.raises(Exception):
        client.format("bar")
