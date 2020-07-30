from collections import defaultdict
from datetime import date
from typing import NoReturn, Optional, Union

import pytest

from massgov.pfml.rmv.caller import ApiCaller, LazyApiCaller
from massgov.pfml.rmv.client import RmvAcknowledgement, RmvClient
from massgov.pfml.rmv.errors import RmvUnexpectedResponseError, RmvUnknownError, RmvValidationError
from massgov.pfml.rmv.models import VendorLicenseInquiryRequest


class MockZeepCaller(LazyApiCaller[dict], ApiCaller[dict]):
    """
    Zeep caller object mock to track calls and provided arguments.

    Takes in an RmvAcknowledgement code and always returns a proper dict response with the
    given acknowledgement.
    """

    def __init__(
        self,
        acknowledgement: Optional[Union[str, RmvAcknowledgement]],
        customer_inactive: bool = False,
        cfl_sanctions: bool = False,
        cfl_sanctions_active: bool = False,
    ):

        self.args = defaultdict(lambda: [])
        self.calls = defaultdict(int)

        if isinstance(acknowledgement, RmvAcknowledgement):
            acknowledgement = acknowledgement.value

        class AttrDict(dict):
            def __init__(self, *args, **kwargs):
                super(AttrDict, self).__init__(*args, **kwargs)
                self.__dict__ = self

        self.response = AttrDict(
            **{
                "CustomerKey": "12345",
                "LicenseID": "ABC12345",
                "License1ExpirationDate": "20210204",
                "LicenseSSN": "12345678",
                "CustomerInActive": customer_inactive,
                "CFLSanctions": cfl_sanctions,
                "CFLSanctionsActive": cfl_sanctions_active,
                "OtherStuff": None,
                "Acknowledgement": acknowledgement,
            }
        )

    def get(self) -> ApiCaller[dict]:
        return self

    def VendorLicenseInquiry(self, **kwargs) -> dict:
        self.args["VendorLicenseInquiry"].append(kwargs)
        self.calls["VendorLicenseInquiry"] += 1
        return self.response


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


def test_rmv_client_vendor_license_inquiry_200_none_acknowledgement(inquiry_request):
    expected_args = {
        "FirstName": "FirstNameTest",
        "LastName": "LastNameTest",
        "DOB": "20200203",
        "Last4SSN": "1443",
        "LicenseID": "ABC12345",
    }

    caller = MockZeepCaller(None)
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert caller.calls["VendorLicenseInquiry"] == 1
    assert caller.args["VendorLicenseInquiry"][0] == expected_args

    assert response.customer_key == caller.response["CustomerKey"]
    assert response.license_id == caller.response["LicenseID"]
    assert response.license1_expiration_date == date(2021, 2, 4)
    assert response.cfl_sanctions is False
    assert response.cfl_sanctions_active is False
    assert response.is_customer_inactive is False


def test_rmv_client_vendor_license_inquiry_200_empty_str_acknowledgement(inquiry_request):
    expected_args = {
        "FirstName": "FirstNameTest",
        "LastName": "LastNameTest",
        "DOB": "20200203",
        "Last4SSN": "1443",
        "LicenseID": "ABC12345",
    }

    caller = MockZeepCaller("")
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert caller.calls["VendorLicenseInquiry"] == 1
    assert caller.args["VendorLicenseInquiry"][0] == expected_args

    assert response.customer_key == caller.response["CustomerKey"]
    assert response.license_id == caller.response["LicenseID"]
    assert response.license1_expiration_date == date(2021, 2, 4)
    assert response.cfl_sanctions is False
    assert response.cfl_sanctions_active is False
    assert response.is_customer_inactive is False


def test_rmv_client_vendor_license_inquiry_cfl_sanctions_active(inquiry_request):
    caller = MockZeepCaller(None, cfl_sanctions=True, cfl_sanctions_active=True)

    rmv_client = RmvClient(caller)
    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert response.cfl_sanctions is True
    assert response.cfl_sanctions_active is True


def test_rmv_client_vendor_license_inquiry_customer_inactive(inquiry_request):
    caller = MockZeepCaller(None, customer_inactive=True)
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert response.is_customer_inactive is True


def test_rmv_client_vendor_license_inquiry_200_validation_error(inquiry_request):
    caller = MockZeepCaller(RmvAcknowledgement.REQUIRED_FIELDS_MISSING)
    rmv_client = RmvClient(caller)

    with pytest.raises(RmvValidationError):
        rmv_client.vendor_license_inquiry(inquiry_request)


def test_rmv_client_vendor_license_inquiry_200_not_found(inquiry_request):
    caller = MockZeepCaller(RmvAcknowledgement.CUSTOMER_NOT_FOUND)
    rmv_client = RmvClient(caller)

    response = rmv_client.vendor_license_inquiry(inquiry_request)
    assert response is None


def test_rmv_client_vendor_license_inquiry_200_unexpected_acknowledgement(inquiry_request):
    caller = MockZeepCaller("SOMETHING_BAD")
    rmv_client = RmvClient(caller)

    with pytest.raises(RmvUnexpectedResponseError) as e:
        rmv_client.vendor_license_inquiry(inquiry_request)

    assert "SOMETHING_BAD" in str(e)


def test_rmv_client_vendor_license_inquiry_unknown_error(inquiry_request):
    caller = RuntimeErrorZeepCaller()
    rmv_client = RmvClient(caller)

    with pytest.raises(RmvUnknownError):
        rmv_client.vendor_license_inquiry(inquiry_request)
