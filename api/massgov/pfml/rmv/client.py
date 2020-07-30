from functools import cached_property
from typing import Optional

import zeep.helpers as zeep_helpers

import massgov.pfml.util.logging
from massgov.pfml.rmv.caller import ApiCaller, LazyZeepApiCaller
from massgov.pfml.rmv.errors import (
    RmvMultipleCustomersError,
    RmvNoCredentialError,
    RmvUnexpectedResponseError,
    RmvUnknownError,
    RmvValidationError,
)
from massgov.pfml.rmv.models import (
    RmvAcknowledgement,
    VendorLicenseInquiryRequest,
    VendorLicenseInquiryResponse,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


class RmvClient:
    """
    Client for accessing the Registry of Motor Vehicles (RMV) API.
    """

    def __init__(self, caller: Optional[ApiCaller] = None):
        if caller is None:
            caller = LazyZeepApiCaller()

        self._cached_caller = caller

    @cached_property
    def _caller(self):
        return self._cached_caller.get()

    def vendor_license_inquiry(
        self, request: VendorLicenseInquiryRequest
    ) -> Optional[VendorLicenseInquiryResponse]:
        """
        Does a lookup for a valid license.

        @returns a response if the license was found, or None if license was not found.

        @raises RmvUnknownError - an unknown error occurred.
                RmvValidationError - the request body had RMV-side validation errors.
                RmvUnexpectedResponseError - the RMV API returned an unexpected acknowledgement response.
        """
        req_body = request.dict(by_alias=True)
        req_body["DOB"] = req_body["DOB"].strftime("%Y%m%d")

        try:
            res = self._caller.VendorLicenseInquiry(**req_body)
        except Exception as e:
            logger.exception("Error making RMV VendorLicenseInquiry request")
            raise RmvUnknownError(cause=e)

        acknowledgement = res.Acknowledgement
        if acknowledgement == RmvAcknowledgement.CUSTOMER_NOT_FOUND.value:
            return None
        elif acknowledgement == RmvAcknowledgement.REQUIRED_FIELDS_MISSING.value:
            raise RmvValidationError()
        elif acknowledgement == RmvAcknowledgement.MULTIPLE_CUSTOMERS_FOUND.value:
            raise RmvMultipleCustomersError()
        elif acknowledgement == RmvAcknowledgement.CREDENTIAL_NOT_FOUND.value:
            raise RmvNoCredentialError()
        elif acknowledgement:
            raise RmvUnexpectedResponseError(acknowledgement)

        return VendorLicenseInquiryResponse(**zeep_helpers.serialize_object(res))
