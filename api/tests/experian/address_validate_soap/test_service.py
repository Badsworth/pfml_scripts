import massgov.pfml.experian.address_validate_soap.models as sm
from massgov.pfml.db.models.employees import Address, Country, GeoState
from massgov.pfml.experian.address_validate_soap.service import (
    Constants,
    address_to_experian_verification_search,
    experian_verification_response_to_address,
)


def test_address_to_experian_verification_search():
    address = Address(
        address_line_one="1234 main st",
        address_line_two="#827 unit",
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
        country=Country.USA,
        geo_state_id=GeoState.MA.geo_state_id,
        geo_state=GeoState.MA,
    )

    request = address_to_experian_verification_search(address)
    assert request.engine == sm.EngineEnum.VERIFICATION
    assert (
        request.search
        == f"{address.address_line_one},{address.address_line_two},{address.city},{address.geo_state.geo_state_description},{address.zip_code}"
    )
    assert request.layout == sm.Layout.StateMA


def test_address_to_experian_verification_search_no_line_two():
    address = Address(
        address_line_one="1234 main st",
        address_line_two=None,
        city="boston",
        zip_code="02110",
        country_id=Country.USA.country_id,
        country=Country.USA,
        geo_state_id=GeoState.MA.geo_state_id,
        geo_state=GeoState.MA,
    )

    request = address_to_experian_verification_search(address)
    assert request.engine == sm.EngineEnum.VERIFICATION
    assert (
        request.search
        == f"{address.address_line_one},{address.city},{address.geo_state.geo_state_description},{address.zip_code}"
    )
    assert request.layout == sm.Layout.StateMA


def test_experian_verification_response_to_address():
    address_lines = [
        sm.SearchAddressLine(
            label=Constants.STATE_MA_LINE_1,
            line="1234 main st",
            line_content=sm.SearchAddressLineContentType.NONE,
        ),
        sm.SearchAddressLine(
            label=Constants.STATE_MA_LINE_2,
            line="#827 unit",
            line_content=sm.SearchAddressLineContentType.NONE,
        ),
        sm.SearchAddressLine(
            label=Constants.STATE_MA_CITY,
            line="boston",
            line_content=sm.SearchAddressLineContentType.ADDRESS,
        ),
        sm.SearchAddressLine(
            label=Constants.STATE_MA_STATE,
            line="MA",
            line_content=sm.SearchAddressLineContentType.ADDRESS,
        ),
        sm.SearchAddressLine(
            label=Constants.STATE_MA_ZIP,
            line="02110",
            line_content=sm.SearchAddressLineContentType.ADDRESS,
        ),
    ]
    search_address = sm.SearchAddress(
        address_lines=address_lines, dpv_status=sm.DPVStatus.CONFIRMED
    )
    search_response = sm.SearchResponse(
        address=search_address, verify_level=sm.VerifyLevel.VERIFIED
    )
    address = experian_verification_response_to_address(search_response)

    assert address.address_line_one == "1234 main st"
    assert address.address_line_two == "#827 unit"
    assert address.city == "boston"
    assert address.geo_state_id == GeoState.MA.geo_state_id
    assert address.zip_code == "02110"


def test_experian_verification_response_to_address_other_labels():
    address_lines = [
        sm.SearchAddressLine(
            label=Constants.STATE_MA_LINE_1,
            line="1234 main st",
            line_content=sm.SearchAddressLineContentType.NONE,
        ),
        sm.SearchAddressLine(
            label="Something else",
            line="#827 unit",
            line_content=sm.SearchAddressLineContentType.NONE,
        ),
        sm.SearchAddressLine(
            label="Another field",
            line="boston",
            line_content=sm.SearchAddressLineContentType.ADDRESS,
        ),
        sm.SearchAddressLine(
            label="Example", line="MA", line_content=sm.SearchAddressLineContentType.ADDRESS
        ),
        sm.SearchAddressLine(
            label="Text", line="02110", line_content=sm.SearchAddressLineContentType.ADDRESS
        ),
    ]

    search_address = sm.SearchAddress(
        address_lines=address_lines, dpv_status=sm.DPVStatus.CONFIRMED
    )
    search_response = sm.SearchResponse(
        address=search_address, verify_level=sm.VerifyLevel.VERIFIED
    )
    address = experian_verification_response_to_address(search_response)

    # Only line one gets set
    assert address.address_line_one == "1234 main st"
    assert address.address_line_two is None
    assert address.city is None
    assert address.geo_state_id is None
    assert address.zip_code is None


def test_experian_verification_response_to_address_none_values():
    # A null response returns None
    assert experian_verification_response_to_address(None) is None

    # If the address is None, return None
    no_address_response = sm.SearchResponse(address=None, verify_level=sm.VerifyLevel.VERIFIED)
    assert experian_verification_response_to_address(no_address_response) is None
