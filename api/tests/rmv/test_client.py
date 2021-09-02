from datetime import date
from typing import NoReturn

import pydantic
import pytest

from massgov.pfml.rmv.caller import ApiCaller, LazyApiCaller, MockZeepCaller
from massgov.pfml.rmv.client import RmvClient, is_test_record
from massgov.pfml.rmv.errors import RmvUnknownError
from massgov.pfml.rmv.models import RmvAcknowledgement, VendorLicenseInquiryRequest


class RuntimeErrorZeepCaller(LazyApiCaller[None], ApiCaller[None]):
    def __init__(self):
        pass

    def get(self):
        return self

    def VendorLicenseInquiry(self, **kwargs) -> NoReturn:
        raise RuntimeError()


@pytest.fixture
def inquiry_request():
    """
    Returns a standard, re-usable inquiry request object.
    """
    return VendorLicenseInquiryRequest(
        first_name="FirstNameTest",
        last_name="LastNameTest",
        date_of_birth=date(2020, 2, 3),
        ssn_last_4="1443",
        license_id="ABC12345",
    )


def test_is_test_record():
    test_records = {
        ("Steve", "Tester"),
        ("Charles", "Presley"),
        ("Willis", "Sierra"),
        ("Lilibeth", "Perozo"),
        ("Roseangela", "Leite Da Silva"),
        ("Vida", "King"),
        ("John", "Pinkham"),
        ("Jonathan", "Day"),
        ("Linda", "Bellabe"),
    }

    for f_name, l_name in test_records:
        assert is_test_record(f_name, l_name) is True


def test_rmv_client_vendor_license_inquiry_200_none_acknowledgement(inquiry_request):
    expected_args = {
        "FirstName": "FirstNameTest",
        "LastName": "LastNameTest",
        "DOB": "20200203",
        "Last4SSN": "1443",
        "LicenseID": "ABC12345",
    }

    caller = MockZeepCaller({"Acknowledgement": None})
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert caller.calls["VendorLicenseInquiry"] == 1
    assert caller.args["VendorLicenseInquiry"][0] == expected_args

    assert response.customer_key == caller.response["CustomerKey"]
    assert response.license_id == caller.response["LicenseID"]
    assert isinstance(response.license1_expiration_date, date)
    assert response.license1_expiration_date > date.today()
    assert response.cfl_sanctions is False
    assert response.cfl_sanctions_active is False
    assert response.is_customer_inactive is False


def test_rmv_client_vendor_license_inquiry_200_empty_str_acknowledgement(inquiry_request):
    caller = MockZeepCaller({"Acknowledgement": ""})
    rmv_client = RmvClient(caller)

    with pytest.raises(pydantic.ValidationError):
        rmv_client.vendor_license_inquiry(inquiry_request)


def test_rmv_client_vendor_license_inquiry_cfl_sanctions_active(inquiry_request):
    caller = MockZeepCaller({"CFLSanctions": True, "CFLSanctionsActive": True})

    rmv_client = RmvClient(caller)
    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert response.cfl_sanctions is True
    assert response.cfl_sanctions_active is True


def test_rmv_client_vendor_license_inquiry_customer_inactive(inquiry_request):
    caller = MockZeepCaller({"CustomerInActive": True})
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert response.is_customer_inactive is True


def test_rmv_client_vendor_license_inquiry_200_validation_error(inquiry_request):
    caller = MockZeepCaller({"Acknowledgement": "INVALIDINPUT_REQUIRED_FIELDS_MISSING"})
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)

    assert response is RmvAcknowledgement.REQUIRED_FIELDS_MISSING


def test_rmv_client_vendor_license_inquiry_200_not_found(inquiry_request):
    caller = MockZeepCaller({"Acknowledgement": "INVALIDRESULTS_CUSTOMER_NOT_FOUND"})
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)

    assert response is RmvAcknowledgement.CUSTOMER_NOT_FOUND


def test_rmv_client_vendor_license_inquiry_200_unexpected_acknowledgement(inquiry_request):
    caller = MockZeepCaller({"Acknowledgement": "SOMETHING_BAD"})
    rmv_client = RmvClient(caller)

    with pytest.raises(ValueError):
        rmv_client.vendor_license_inquiry(inquiry_request)


def test_rmv_client_vendor_license_inquiry_unknown_error(inquiry_request):
    caller = RuntimeErrorZeepCaller()
    rmv_client = RmvClient(caller)

    with pytest.raises(RmvUnknownError):
        rmv_client.vendor_license_inquiry(inquiry_request)
