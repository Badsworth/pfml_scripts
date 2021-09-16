from functools import cached_property
from typing import Optional, Union

import flask
import newrelic.agent
import zeep.helpers as zeep_helpers

import massgov.pfml.util.logging
from massgov.pfml.api.config import RMVAPIBehavior
from massgov.pfml.rmv.caller import ApiCaller, LazyApiCaller, LazyZeepApiCaller
from massgov.pfml.rmv.errors import RmvUnknownError
from massgov.pfml.rmv.models import (
    RmvAcknowledgement,
    VendorLicenseInquiryRequest,
    VendorLicenseInquiryResponse,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


def is_test_record(first_name: str, last_name: str) -> bool:
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

    return (first_name, last_name) in test_records


def is_mocked(rmv_mocking_behavior: RMVAPIBehavior, first_name: str, last_name: str) -> bool:
    return rmv_mocking_behavior is RMVAPIBehavior.MOCK or (
        rmv_mocking_behavior is RMVAPIBehavior.PARTIAL_MOCK
        and not is_test_record(first_name, last_name)
    )


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
            rmv_acknowledgement = RmvAcknowledgement(res.Acknowledgement)

            if rmv_acknowledgement is RmvAcknowledgement.REQUIRED_FIELDS_MISSING:
                logger.info(
                    "Unable to retrieve record from RMV API",
                    extra={
                        "first_name_length": len(req_body["FirstName"]),
                        "last_name_length": len(req_body["LastName"]),
                        "license_id_length": len(req_body["LicenseID"])
                        if req_body["LicenseID"] is not None
                        else 0,
                        "license_id_supplied": req_body["LicenseID"] is not None,
                        "acknowledgement": res.Acknowledgement,
                    },
                )

            return rmv_acknowledgement

        return VendorLicenseInquiryResponse(**zeep_helpers.serialize_object(res))
