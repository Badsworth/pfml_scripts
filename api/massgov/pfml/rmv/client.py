from functools import cached_property
from typing import Optional

import zeep.helpers as zeep_helpers

import massgov.pfml.util.logging
from massgov.pfml.rmv.caller import ApiCaller, LazyApiCaller, LazyZeepApiCaller
from massgov.pfml.rmv.config import RmvConfig
from massgov.pfml.rmv.errors import RmvUnknownError
from massgov.pfml.rmv.models import VendorLicenseInquiryRequest, VendorLicenseInquiryResponse

logger = massgov.pfml.util.logging.get_logger(__name__)


class RmvClient:
    """
    Client for accessing the Registry of Motor Vehicles (RMV) API.
    """

    def __init__(self, caller: Optional[LazyApiCaller] = None, config: Optional[RmvConfig] = None):
        self._cached_caller = caller or LazyZeepApiCaller(config)

    @cached_property
    def _caller(self) -> ApiCaller:
        return self._cached_caller.get()

    def vendor_license_inquiry(
        self, request: VendorLicenseInquiryRequest
    ) -> VendorLicenseInquiryResponse:
        """
        Does a lookup for a valid license.

        @raises RmvUnknownError - an unknown error occurred.
        """
        req_body = request.dict(by_alias=True)
        req_body["DOB"] = req_body["DOB"].strftime("%Y%m%d")

        try:
            res = self._caller.VendorLicenseInquiry(**req_body)
        except Exception as e:
            logger.exception("Error making RMV VendorLicenseInquiry request")
            raise RmvUnknownError(cause=e)

        return VendorLicenseInquiryResponse(**zeep_helpers.serialize_object(res))
