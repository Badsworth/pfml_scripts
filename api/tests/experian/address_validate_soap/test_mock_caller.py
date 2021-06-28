import pytest

import massgov.pfml.experian.address_validate_soap.models as sm
from massgov.pfml.db.models.employees import GeoState
from massgov.pfml.db.models.factories import AddressFactory
from massgov.pfml.experian.address_validate_soap.client import Client
from massgov.pfml.experian.address_validate_soap.mock_caller import MockVerificationZeepCaller
from massgov.pfml.experian.address_validate_soap.service import (
    address_to_experian_verification_search,
    experian_verification_response_to_address,
)


def validate_address(address, response):
    assert response.address
    assert len(response.address.address_lines) == 5

    experian_address = experian_verification_response_to_address(response)

    assert address.address_line_one == experian_address.address_line_one
    assert address.address_line_two == experian_address.address_line_two
    assert address.city == experian_address.city
    assert address.zip_code == experian_address.zip_code[:5]  # Mock adds -1234
    assert address.geo_state_id == experian_address.geo_state_id


@pytest.mark.parametrize(
    "verify_level", [(sm.VerifyLevel.VERIFIED), (sm.VerifyLevel.INTERACTION_REQUIRED)],
)
def test_search_fallback_with_address(verify_level):
    # These verify levels return an address in the response
    mock_caller = MockVerificationZeepCaller(fallback_verify_level=verify_level)
    assert len(mock_caller.search_responses) == 0
    client = Client(mock_caller)

    address = AddressFactory.build(geo_state=GeoState.MA)

    search_response1 = client.search(address_to_experian_verification_search(address))
    assert search_response1.verify_level == verify_level
    validate_address(address, search_response1)
    assert len(mock_caller.search_responses) == 1

    # If we call with the same address, the same responses are used
    search_response = client.search(address_to_experian_verification_search(address))
    assert search_response.verify_level == verify_level
    validate_address(address, search_response)
    assert len(mock_caller.search_responses) == 1

    # Adding a different address will return a different result
    address2 = AddressFactory.build(geo_state=GeoState.MA)

    search_response2 = client.search(address_to_experian_verification_search(address2))
    assert search_response2.verify_level == verify_level
    validate_address(address2, search_response2)
    assert len(mock_caller.search_responses) == 2


@pytest.mark.parametrize(
    "verify_level",
    [(sm.VerifyLevel.NONE), (sm.VerifyLevel.PREMISES_PARTIAL), (sm.VerifyLevel.STREET_PARTIAL)],
)
def test_search_fallback_no_address_expected(verify_level):
    # These verify levels do not return an address in the response
    mock_caller = MockVerificationZeepCaller(fallback_verify_level=verify_level)
    assert len(mock_caller.search_responses) == 0
    client = Client(mock_caller)

    address = AddressFactory.build(geo_state=GeoState.MA)

    search_response1 = client.search(address_to_experian_verification_search(address))
    assert search_response1.verify_level == verify_level
    assert search_response1.address is None
    assert len(mock_caller.search_responses) == 1

    # If we call with the same address, the same responses are used
    search_response = client.search(address_to_experian_verification_search(address))
    assert search_response.verify_level == verify_level
    assert search_response.address is None
    assert len(mock_caller.search_responses) == 1

    # Adding a different address will return a different result
    address2 = AddressFactory.build(geo_state=GeoState.MA)

    search_response2 = client.search(address_to_experian_verification_search(address2))
    assert search_response2.verify_level == verify_level
    assert search_response2.address is None
    assert len(mock_caller.search_responses) == 2


@pytest.mark.parametrize(
    "verify_level", [(sm.VerifyLevel.VERIFIED), (sm.VerifyLevel.INTERACTION_REQUIRED)],
)
def test_add_mock_search_response_with_address(verify_level):
    mock_caller = MockVerificationZeepCaller(fallback_verify_level=verify_level)
    assert len(mock_caller.search_responses) == 0

    address = AddressFactory.build(geo_state=GeoState.MA)

    mocked_response = mock_caller.add_mock_search_response(address, verify_level)
    assert mocked_response.verify_level == verify_level
    validate_address(address, mocked_response)
    assert len(mock_caller.search_responses) == 1

    # Repeated calls give the same result
    mock_caller.add_mock_search_response(address, verify_level)
    assert len(mock_caller.search_responses) == 1

    # Adding a different address will return a different result
    address2 = AddressFactory.build(geo_state=GeoState.MA)
    mocked_response2 = mock_caller.add_mock_search_response(address2, verify_level)
    validate_address(address2, mocked_response2)
    assert len(mock_caller.search_responses) == 2


@pytest.mark.parametrize(
    "verify_level",
    [(sm.VerifyLevel.NONE), (sm.VerifyLevel.PREMISES_PARTIAL), (sm.VerifyLevel.STREET_PARTIAL)],
)
def test_add_mock_search_response_without_address(verify_level):
    mock_caller = MockVerificationZeepCaller(fallback_verify_level=verify_level)
    assert len(mock_caller.search_responses) == 0

    address = AddressFactory.build(geo_state=GeoState.MA)

    mocked_response = mock_caller.add_mock_search_response(address, verify_level)
    assert mocked_response.verify_level == verify_level
    assert mocked_response.address is None
    assert len(mock_caller.search_responses) == 1

    # Repeated calls give the same result
    mock_caller.add_mock_search_response(address, verify_level)
    assert len(mock_caller.search_responses) == 1

    # Adding a different address will return a different result
    address2 = AddressFactory.build(geo_state=GeoState.MA)
    mocked_response2 = mock_caller.add_mock_search_response(address2, verify_level)
    assert mocked_response2.address is None
    assert len(mock_caller.search_responses) == 2
