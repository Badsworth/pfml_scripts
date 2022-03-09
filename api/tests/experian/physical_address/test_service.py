import massgov.pfml.experian.physical_address.service as experian_address_service
from massgov.pfml.db.models.employees import Address
from massgov.pfml.db.models.geo import Country, GeoState
from massgov.pfml.experian.physical_address.client.models import (
    AddressFormatV1Address,
    AddressFormatV1Components,
    AddressFormatV1Response,
    AddressFormatV1Result,
)


def test_address_to_experian_search_request():
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

    experian_search_request = experian_address_service.address_to_experian_search_request(address)

    assert experian_search_request.country_iso == address.country.country_description
    assert experian_search_request.components.unspecified == [
        f"{address.address_line_one},{address.address_line_two},{address.city},{address.geo_state.geo_state_description},{address.zip_code}"
    ]


def test_address_to_experian_search_request_no_line_two():
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

    experian_search_request = experian_address_service.address_to_experian_search_request(address)

    assert experian_search_request.country_iso == address.country.country_description
    assert experian_search_request.components.unspecified == [
        f"{address.address_line_one},{address.city},{address.geo_state.geo_state_description},{address.zip_code}"
    ]


def test_address_to_experian_search_request_no_country_defaults_to_usa():
    address = Address(
        address_line_one="1234 main st",
        address_line_two=None,
        city="boston",
        zip_code="02110",
        country_id=None,
        country=None,
        geo_state_id=GeoState.MA.geo_state_id,
        geo_state=GeoState.MA,
    )

    experian_search_request = experian_address_service.address_to_experian_search_request(address)

    assert experian_search_request.country_iso == "USA"
    assert experian_search_request.components.unspecified == [
        f"{address.address_line_one},{address.city},{address.geo_state.geo_state_description},{address.zip_code}"
    ]


def test_address_to_experian_search_request_no_info():
    address = Address()

    experian_search_request = experian_address_service.address_to_experian_search_request(address)

    assert experian_search_request.country_iso == "USA"
    assert experian_search_request.components.unspecified == [""]


def test_experian_format_response_to_address_no_info():
    experian_address_format_response = AddressFormatV1Response()

    address = experian_address_service.experian_format_response_to_address(
        experian_address_format_response
    )

    assert address is None


def test_experian_format_response_to_address_full_info(mocker):
    experian_address_format_response = AddressFormatV1Response(
        result=AddressFormatV1Result(
            global_address_key="foo",
            address=AddressFormatV1Address(
                address_line_1="100 Cambridge St",
                address_line_2="Ste 101",
                address_line_3="",
                locality="Boston",
                region="MA",
                postal_code="02114-2579",
                country="UNITED STATES OF AMERICA",
            ),
            components=AddressFormatV1Components(country_iso_3="USA"),
        )
    )

    address = experian_address_service.experian_format_response_to_address(
        experian_address_format_response
    )

    assert address.address_id is None
    assert address.address_type_id is None
    assert (
        address.address_line_one == experian_address_format_response.result.address.address_line_1
    )
    assert (
        address.address_line_two == experian_address_format_response.result.address.address_line_2
    )
    assert address.city == experian_address_format_response.result.address.locality
    assert address.geo_state_id == GeoState.MA.geo_state_id
    assert address.zip_code == experian_address_format_response.result.address.postal_code
    assert address.country_id == Country.USA.country_id


def test_experian_format_response_to_address_partial_info(mocker):
    experian_address_format_response = AddressFormatV1Response(
        result=AddressFormatV1Result(
            global_address_key="foo",
            address=AddressFormatV1Address(
                address_line_1="100 Cambridge St",
                address_line_2="",
                locality="Boston",
                postal_code="02114-2579",
            ),
            components=AddressFormatV1Components(),
        )
    )

    address = experian_address_service.experian_format_response_to_address(
        experian_address_format_response
    )

    assert address.address_id is None
    assert address.address_type_id is None
    assert (
        address.address_line_one == experian_address_format_response.result.address.address_line_1
    )
    assert address.address_line_two is None
    assert address.city == experian_address_format_response.result.address.locality
    assert address.geo_state_id is None
    assert address.zip_code == experian_address_format_response.result.address.postal_code
    assert address.country_id is None


def test_experian_format_response_to_address_partial_empty_info(mocker):
    experian_address_format_response = AddressFormatV1Response(
        result=AddressFormatV1Result(
            global_address_key="foo",
            address=AddressFormatV1Address(address_line_1="", locality="", postal_code=""),
            components=AddressFormatV1Components(country_iso_3=""),
        )
    )

    address = experian_address_service.experian_format_response_to_address(
        experian_address_format_response
    )

    assert address.address_id is None
    assert address.address_type_id is None
    assert address.address_line_one is None
    assert address.address_line_two is None
    assert address.city is None
    assert address.geo_state_id is None
    assert address.zip_code is None
    assert address.country_id is None
