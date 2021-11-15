import pytest

from massgov.pfml.experian.experian_util import (
    MockExperianException,
    experian_search_request_to_address,
)


def test_experian_search_request_to_address(local_initialize_factories_session):
    # If the address contains all 5 parts
    full_address = experian_search_request_to_address("line_one,line_two,city,MA,zip")
    assert full_address.address_line_one == "line_one"
    assert full_address.address_line_two == "line_two"
    assert full_address.city == "city"
    assert full_address.geo_state.geo_state_description == "MA"
    assert full_address.zip_code == "zip"

    # Address is missing
    minimum_address = experian_search_request_to_address("line_one,city,zip")
    assert minimum_address.address_line_one == "line_one"
    assert minimum_address.address_line_two is None
    assert minimum_address.city == "city"
    assert minimum_address.geo_state is None
    assert minimum_address.zip_code == "zip"

    partial_address_no_state = experian_search_request_to_address("line_one,line_two,city,zip")
    assert partial_address_no_state.address_line_one == "line_one"
    assert partial_address_no_state.address_line_two == "line_two"
    assert partial_address_no_state.city == "city"
    assert partial_address_no_state.geo_state is None
    assert partial_address_no_state.zip_code == "zip"

    partial_address_no_line_two = experian_search_request_to_address("line_one,city,MA,zip")
    assert partial_address_no_line_two.address_line_one == "line_one"
    assert partial_address_no_line_two.address_line_two is None
    assert partial_address_no_line_two.city == "city"
    assert partial_address_no_line_two.geo_state.geo_state_description == "MA"
    assert partial_address_no_line_two.zip_code == "zip"


def test_experian_search_request_to_address_invalid():
    with pytest.raises(
        MockExperianException,
        match="Unable to parse address for mocking purposes: \\[line_one,line_two\\]",
    ):
        experian_search_request_to_address("line_one,line_two")

    with pytest.raises(
        MockExperianException,
        match="Unable to parse address for mocking purposes: \\[a,b,c,d,e,f\\]",
    ):
        experian_search_request_to_address("a,b,c,d,e,f")
