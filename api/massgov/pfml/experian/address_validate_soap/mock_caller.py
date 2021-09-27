import json
from functools import cached_property
from typing import Any, Dict

from massgov.pfml.db.models.employees import Address
from massgov.pfml.experian.address_validate_soap.caller import ApiCaller, LazyApiCaller
from massgov.pfml.experian.address_validate_soap.models import (
    DPVStatus,
    SearchAddress,
    SearchAddressLine,
    SearchAddressLineContentType,
    SearchResponse,
    VerifyLevel,
)
from massgov.pfml.experian.address_validate_soap.service import (
    Constants,
    address_to_experian_search_text,
)
from massgov.pfml.experian.experian_util import (
    MockExperianException,
    experian_search_request_to_address,
)


class MockVerificationZeepCaller(LazyApiCaller, ApiCaller):
    """
    A mock caller to back the Experian SOAP API. This is
    only implemented to handle requests where the Engine is "Verification"
    and the layout is "StateMA" which is all that is currently used.
    """

    search_responses: Dict[str, SearchResponse]
    fallback_verify_level: VerifyLevel
    call_count: int

    def __init__(self, fallback_verify_level: VerifyLevel = VerifyLevel.VERIFIED) -> None:
        self.search_responses = {}
        self.fallback_verify_level = fallback_verify_level
        self.call_count = 0

    def get(self) -> ApiCaller:
        return self

    @cached_property
    def _caller(self) -> ApiCaller:
        return self.get()

    def DoSearch(self, **kwargs: Any) -> Dict[str, Any]:
        self.call_count += 1
        # Note that these kwargs are created by turning the
        # SearchRequest object into a json/dictionary object
        address_text = kwargs.get("Search")
        if type(address_text) is not str:
            raise MockExperianException(
                f"Search text is required to be a string. Received: {address_text}"
            )

        response = self.search_responses.get(address_text)
        if not response:
            address = experian_search_request_to_address(address_text)
            response = self.add_mock_search_response(address, self.fallback_verify_level)

        resp_body = json.loads(response.json(by_alias=True))

        return {
            "header": {
                "information_header": {"StateTransition": "SearchResults", "CreditsUsed": 1}
            },
            "body": resp_body,
        }

    def add_mock_search_response(
        self, address: Address, verify_level: VerifyLevel
    ) -> SearchResponse:
        address_text = address_to_experian_search_text(address)

        # Verified + Interaction Required return an address section
        if verify_level in [VerifyLevel.VERIFIED, VerifyLevel.INTERACTION_REQUIRED]:
            response = self._build_search_response(address, verify_level)
        else:  # None, Street Partial, Premises Partial
            # These scenarios return a picklist rather than a
            # specific address response. We don't try to parse
            # the picklist, so we also leave that unset for now
            response = SearchResponse(address=None, verify_level=verify_level)

        self.search_responses[address_text] = response
        return response

    def _build_search_response(self, address: Address, verify_level: VerifyLevel) -> SearchResponse:
        address_lines = [
            SearchAddressLine(
                label=Constants.STATE_MA_LINE_1,
                line=address.address_line_one,
                line_content=SearchAddressLineContentType.NONE,
            ),
            SearchAddressLine(
                label=Constants.STATE_MA_LINE_2,
                line=address.address_line_two,
                line_content=SearchAddressLineContentType.NONE,
            ),
            SearchAddressLine(
                label=Constants.STATE_MA_CITY,
                line=address.city,
                line_content=SearchAddressLineContentType.ADDRESS,
            ),
            SearchAddressLine(
                label=Constants.STATE_MA_STATE,
                line=address.geo_state.geo_state_description if address.geo_state else None,
                line_content=SearchAddressLineContentType.ADDRESS,
            ),
            SearchAddressLine(
                label=Constants.STATE_MA_ZIP,
                line=f"{address.zip_code[:5]}-1234" if address.zip_code else None,
                line_content=SearchAddressLineContentType.ADDRESS,
            ),
        ]
        search_address = SearchAddress(address_lines=address_lines, dpv_status=DPVStatus.CONFIRMED)

        return SearchResponse(address=search_address, verify_level=verify_level)
