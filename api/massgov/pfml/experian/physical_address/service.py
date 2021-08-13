from typing import Optional

from massgov.pfml.db.models.employees import Address, Country, GeoState
from massgov.pfml.experian.physical_address.client import (
    AddressFormatV1Response,
    AddressSearchV1InputComponent,
    AddressSearchV1Request,
)


def address_to_experian_search_request(address: Address) -> AddressSearchV1Request:
    """Generate Experian address search request for PFML Address"""
    address_parts = [
        str(p)
        for p in [
            address.address_line_one,
            address.address_line_two,
            address.city,
            address.geo_state.geo_state_description if address.geo_state else None,
            address.zip_code,
        ]
        if p
    ]

    return AddressSearchV1Request(
        country_iso=address.country.country_description
        if address.country and address.country.country_description
        else "USA",
        components=AddressSearchV1InputComponent(unspecified=[",".join(address_parts)]),
    )


def address_to_experian_suggestion_text_format(address: Address) -> str:
    """Format an Address object in a way that matches the address format that is returned by
    Experian's AddressSearchV1MatchedResult.text field for the benefit of comparing input addresses
    and addresses returned by the Experian API in CSV reports we create.

    | line 1    | | line 2|  |city||st||zip|
    125 Summer St Suite 200, Boston MA 02110
    """
    address_lines = [address.address_line_one, address.address_line_two]
    address_line_str = " ".join([p for p in address_lines if p])

    postal_parts = [
        str(p)
        for p in [
            address.city,
            address.geo_state.geo_state_description if address.geo_state else None,
            address.zip_code,
        ]
        if p
    ]
    postal_part_str = " ".join([p for p in postal_parts if p])

    return ", ".join([address_line_str, postal_part_str])


def experian_format_response_to_address(
    format_response: AddressFormatV1Response,
) -> Optional[Address]:
    """Create PFML Address from Experian formatted address info

    Throws Exception if the state or country codes are not in PFML DB.
    """
    if (
        format_response.result is None
        or format_response.result.address is None
        or format_response.result.components is None
    ):
        return None

    return Address(
        address_line_one=format_response.result.address.address_line_1 or None,
        address_line_two=format_response.result.address.address_line_2 or None,
        city=format_response.result.address.locality or None,
        geo_state_id=(
            GeoState.get_id(format_response.result.address.region)
            if format_response.result.address.region
            else None
        ),
        zip_code=format_response.result.address.postal_code or None,
        country_id=(
            Country.get_id(format_response.result.components.country_iso_3)
            if format_response.result.components.country_iso_3
            else None
        ),
    )
