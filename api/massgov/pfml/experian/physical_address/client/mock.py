from typing import Dict, List, Optional, cast

from massgov.pfml.db.models.employees import Address
from massgov.pfml.experian.experian_util import (
    MockExperianException,
    experian_search_request_to_address,
)
from massgov.pfml.experian.physical_address.service import (
    address_to_experian_search_request,
    address_to_experian_suggestion_text_format,
)

from .base import BaseClient
from .models import (
    AddressFormatV1Address,
    AddressFormatV1Components,
    AddressFormatV1Response,
    AddressFormatV1Result,
    AddressSearchV1MatchedResult,
    AddressSearchV1Request,
    AddressSearchV1Response,
    AddressSearchV1Result,
    Confidence,
)


class MockClient(BaseClient):
    """
        Mock client for accessing the Experian Address Validation API endpoints.
    """

    search_responses: Dict[str, AddressSearchV1Response]
    format_responses: Dict[str, AddressFormatV1Response]
    address_count: int
    fallback_confidence: Confidence
    multiple_count: int  # When producing multiple responses, how many to make

    def __init__(
        self, fallback_confidence: Confidence = Confidence.VERIFIED_MATCH, multiple_count: int = 3
    ) -> None:
        self.search_responses = {}
        self.format_responses = {}
        self.address_count = 1
        self.fallback_confidence = fallback_confidence
        self.multiple_count = multiple_count

    def _get_global_address_key(self) -> str:
        global_address_key = f"address_{str(self.address_count)}"
        self.address_count += 1
        return global_address_key

    def _add_format_response(
        self,
        address: Address,
        matched_result: AddressSearchV1MatchedResult,
        zip_code_extension: int,
    ) -> None:
        format_response = AddressFormatV1Response(
            result=AddressFormatV1Result(
                global_address_key=matched_result.global_address_key,
                address=AddressFormatV1Address(
                    address_line_1=address.address_line_one,
                    address_line_2=address.address_line_two if address.address_line_two else "",
                    address_line_3="",
                    locality=address.city,
                    region=address.geo_state.geo_state_description if address.geo_state else "",
                    postal_code=f"{address.zip_code[:5]}-{str(zip_code_extension).zfill(4)}"
                    if address.zip_code
                    else str(zip_code_extension).zfill(5),
                    country="UNITED STATES OF AMERICA",
                ),
                components=AddressFormatV1Components(country_iso_3="USA"),
            )
        )
        self.format_responses[cast(str, matched_result.global_address_key)] = format_response

    def _add_format_responses(
        self, address: Address, matched_results: List[AddressSearchV1MatchedResult]
    ) -> None:
        for count, matched_result in enumerate(matched_results):
            self._add_format_response(address, matched_result, count)

    def _build_matched_result(self, raw_address: str) -> AddressSearchV1MatchedResult:
        global_address_key = self._get_global_address_key()

        return AddressSearchV1MatchedResult(
            global_address_key=global_address_key,
            text=raw_address,  # Always make this the raw address for now
            matched=[[0, 1]],
            format="https://api.experianaperture.io/address/format/v1/baz",
        )

    def add_mock_address_response(
        self, address: Address, confidence: Confidence, suggestion: Optional[str] = None,
    ) -> AddressSearchV1Response:
        # Pull out the raw address as text as the process will later see it.
        expected_request = address_to_experian_search_request(address)
        raw_address = expected_request.components.unspecified[0]
        suggestion_text_address = suggestion or address_to_experian_suggestion_text_format(address)

        suggestions = []

        if confidence == Confidence.VERIFIED_MATCH:
            suggestions.append(self._build_matched_result(suggestion_text_address))

        elif confidence == Confidence.MULTIPLE_MATCHES:
            for _ in range(self.multiple_count):
                suggestions.append(self._build_matched_result(suggestion_text_address))

        # For NO_MATCHES or INSUFFICIENT_SEARCH_TERMS, we just
        # don't add suggestions, their responses just have the confidence value
        # They also won't have any formatted responses.

        self._add_format_responses(address, suggestions)

        response = AddressSearchV1Response(
            result=AddressSearchV1Result(
                more_results_available=False, confidence=confidence, suggestions=suggestions,
            )
        )
        self.search_responses[raw_address] = response
        return response

    def search(
        self,
        req: AddressSearchV1Request,
        *,
        reference_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AddressSearchV1Response:

        # If we pre-generated expected responses, find that
        lookup_address = req.components.unspecified[0]
        response = self.search_responses.get(lookup_address)
        if response:
            return response

        # Otherwise the behavior is based on the fallback confidence
        # For the scenarios where we expect responses, we also store
        # the responses in case the same address is called again it
        # will consistently return the same data. This also sets up
        # the format data so it can return results as well.
        address = experian_search_request_to_address(lookup_address)
        response = self.add_mock_address_response(address, self.fallback_confidence)
        return response

    def format(
        self,
        global_address_key: str,
        *,
        add_metadata: Optional[bool] = True,
        add_components: Optional[bool] = True,
        reference_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AddressFormatV1Response:
        response = self.format_responses.get(global_address_key)
        if response:
            return response

        # The real Experian client returns a 503 error
        # with an invalid global_address_key, so throw
        # an exception as it's not a valid scenario.
        raise MockExperianException(
            "No mock scenario setup for global_address_key=%s" % global_address_key
        )
