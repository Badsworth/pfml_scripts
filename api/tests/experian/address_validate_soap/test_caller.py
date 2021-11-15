import os

import pytest
from requests import Session
from requests.exceptions import HTTPError
from requests.models import Response

from massgov.pfml.experian.address_validate_soap.caller import (
    ApiCaller,
    ExperianSOAPConfig,
    LazyZeepApiCaller,
)


@pytest.fixture
def mock_wsdl_200(monkeypatch):
    """
    Mock a successful WSDL response.
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

    # Load fake WSDL.
    #
    # Based on # https://ws2.ondemand.qas.com/ProOnDemand/V3/ProOnDemandService.asmx?WSDL
    # but with externally imported schemas removed and the URLs adjusted to
    # https://fake-url.com
    wsdlpath = os.path.join(os.path.dirname(__file__), "./api.wsdl")
    with open(wsdlpath, "rb") as file:
        res._content = file.read()

    def mock_get(*args, **kwargs):
        return res

    return mock_get


def test_zeep_caller_get_200(mock_wsdl_200):
    # Client should be able to retrieve and parse WSDL from a given source.
    caller = LazyZeepApiCaller(
        ExperianSOAPConfig(soap_wsdl_uri="https://fake-url.com", auth_token="foo")
    )
    assert caller.get()


def test_zeep_caller_get_500(mock_wsdl_500):
    # Client should raise an HTTP error when failing to retrieve the WSDL on first call.
    caller = LazyZeepApiCaller(
        ExperianSOAPConfig(soap_wsdl_uri="https://fake-url.com", auth_token="foo")
    )

    with pytest.raises(HTTPError):
        caller.get()


def test_zeep_caller_do_search(mock_wsdl_200, mocker):
    caller = LazyZeepApiCaller(
        ExperianSOAPConfig(soap_wsdl_uri="https://fake-url.com", auth_token="foo")
    )

    mock_service_proxy = mocker.Mock(spec=ApiCaller)

    caller.get = mocker.Mock(return_value=mock_service_proxy)

    caller.DoSearch()

    # ensure the underlying DoSearch operation was called
    mock_service_proxy.DoSearch.assert_called_once()


def test_zeep_caller_caches_service_proxy(mock_wsdl_200, mocker):
    caller = LazyZeepApiCaller(
        ExperianSOAPConfig(soap_wsdl_uri="https://fake-url.com", auth_token="foo")
    )

    mock_service_proxy = mocker.Mock(spec=ApiCaller)

    caller.get = mocker.Mock(return_value=mock_service_proxy)

    # call operation twice
    caller.DoSearch()
    caller.DoSearch()

    # but ensure the service proxy was only loaded once
    caller.get.assert_called_once()
