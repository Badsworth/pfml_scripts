from typing import Optional

import massgov.pfml.experian.address_validate_soap.models as sm
from massgov.pfml.db.models.employees import Address, GeoState
from massgov.pfml.experian.address_validate_soap.layouts import Layout
from massgov.pfml.experian.experian_util import address_to_experian_search_text


class Constants:
    STATE_MA_LINE_1 = "Address Line 1"
    STATE_MA_LINE_2 = "Address Line 2"
    STATE_MA_CITY = "City"
    STATE_MA_STATE = "State"
    STATE_MA_ZIP = "Zip+4"


def address_to_experian_verification_search(address: Address) -> sm.SearchRequest:
    return sm.SearchRequest(
        engine=sm.EngineEnum.VERIFICATION,
        search=address_to_experian_search_text(address),
        layout=Layout.StateMA,
    )


def experian_verification_response_to_address(
    response: Optional[sm.SearchResponse],
) -> Optional[Address]:
    """
    Create PFML Address from Experian SOAP formatted address info

    Throws Exception if the state or country codes are not in PFML DB.
    """
    if not response or not response.address:
        return None

    search_address = response.address

    address = Address()
    for address_line in search_address.address_lines:
        label = address_line.label
        line_value = address_line.line

        if label == Constants.STATE_MA_LINE_1:
            address.address_line_one = line_value
        elif label == Constants.STATE_MA_LINE_2:
            address.address_line_two = line_value
        elif label == Constants.STATE_MA_CITY:
            address.city = line_value
        elif label == Constants.STATE_MA_STATE:
            address.geo_state_id = GeoState.get_id(line_value) if line_value else None
        elif label == Constants.STATE_MA_ZIP:
            address.zip_code = line_value

    return address
