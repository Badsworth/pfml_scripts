from functools import cached_property
from typing import Optional, Union

import flask
import newrelic.agent
import zeep.helpers as zeep_helpers

import massgov.pfml.util.logging
from massgov.pfml.rmv.caller import ApiCaller, LazyApiCaller, LazyZeepApiCaller
from massgov.pfml.rmv.errors import RmvUnknownError
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

    def __init__(self, caller: Optional[LazyApiCaller] = None):
        self._cached_caller = caller or LazyZeepApiCaller()

    @cached_property
    def _caller(self) -> ApiCaller:
        return self._cached_caller.get()

    def vendor_license_inquiry(
        self, request: VendorLicenseInquiryRequest
    ) -> Union[VendorLicenseInquiryResponse, RmvAcknowledgement]:
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

            has_flask_context = flask.has_request_context()
            newrelic.agent.record_custom_event(
                "RmvError",
                {
                    "error.class": type(e).__name__,
                    "error.message": str(e),
                    "request.method": flask.request.method if has_flask_context else None,
                    "request.uri": flask.request.path if has_flask_context else None,
                    "request.headers.x-amzn-requestid": flask.request.headers.get(
                        "x-amzn-requestid", None
                    )
                    if has_flask_context
                    else None,
                },
            )

            raise RmvUnknownError(cause=e)

        # If the RMV responds with an Acknowledgement value, all other fields
        # will be None, so just return the Acknowledgement
        if res.Acknowledgement:
            return RmvAcknowledgement(res.Acknowledgement)

        return VendorLicenseInquiryResponse(**zeep_helpers.serialize_object(res))
