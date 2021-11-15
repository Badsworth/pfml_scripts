import pytest

from massgov.pfml.db.models.employees import GeoState
from massgov.pfml.db.models.factories import AddressFactory
from massgov.pfml.experian.experian_util import MockExperianException
from massgov.pfml.experian.physical_address.client.mock import MockClient
from massgov.pfml.experian.physical_address.client.models import Confidence
from massgov.pfml.experian.physical_address.service import address_to_experian_search_request


def validate_address(address, response):
    experian_address = response.result.address
    assert address.address_line_one == experian_address.address_line_1
    assert address.city == experian_address.locality
    assert address.zip_code[:5] == experian_address.postal_code[:5]

    if address.address_line_two:
        assert address.address_line_two == experian_address.address_line_2
    if address.geo_state:
        assert address.geo_state.geo_state_description == experian_address.region


def test_search_and_format_fallback_verified_match():
    client = MockClient(fallback_confidence=Confidence.VERIFIED_MATCH)
    assert len(client.search_responses) == 0
    assert len(client.format_responses) == 0

    address = AddressFactory.build()

    # This will create mock responses when it's unable to find existing ones
    search_response1 = client.search(address_to_experian_search_request(address))
    assert search_response1.result.confidence == Confidence.VERIFIED_MATCH
    assert len(search_response1.result.suggestions) == 1

    format_key = search_response1.result.suggestions[0].global_address_key
    format_response = client.format(format_key)
    validate_address(address, format_response)

    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 1

    # If we call with the same address, the same responses are used
    search_response2 = client.search(address_to_experian_search_request(address))
    assert search_response2.result.suggestions[0].global_address_key == format_key
    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 1


def test_search_and_format_fallback_multiple_matches(local_initialize_factories_session):
    client = MockClient(fallback_confidence=Confidence.MULTIPLE_MATCHES, multiple_count=5)
    assert len(client.search_responses) == 0
    assert len(client.format_responses) == 0

    address = AddressFactory.build(geo_state=GeoState.MA)

    # This will create mock responses when it's unable to find existing ones
    search_response = client.search(address_to_experian_search_request(address))
    assert search_response.result.confidence == Confidence.MULTIPLE_MATCHES
    assert len(search_response.result.suggestions) == 5

    # Each suggestion should be found when calling format
    for suggestion in search_response.result.suggestions:
        format_response = client.format(suggestion.global_address_key)
        validate_address(address, format_response)

    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 5

    # If we call with the same address, the same responses are used
    # and additional ones are not created
    client.search(address_to_experian_search_request(address))
    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 5


def test_search_and_format_fallback_no_matches():
    client = MockClient(fallback_confidence=Confidence.NO_MATCHES)
    assert len(client.search_responses) == 0
    assert len(client.format_responses) == 0

    address = AddressFactory.build()
    # We expect the response to come back without any matches
    search_response = client.search(address_to_experian_search_request(address))
    assert search_response.result.confidence == Confidence.NO_MATCHES
    assert len(search_response.result.suggestions) == 0

    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 0

    # Any subsequent queries will reuse the search response created.
    client.search(address_to_experian_search_request(address))
    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 0


def test_search_and_format_fallback_insufficient_search_terms():
    client = MockClient(fallback_confidence=Confidence.INSUFFICIENT_SEARCH_TERMS)
    assert len(client.search_responses) == 0
    assert len(client.format_responses) == 0

    address = AddressFactory.build()
    # We expect the response to come back without any matches
    search_response = client.search(address_to_experian_search_request(address))
    assert search_response.result.confidence == Confidence.INSUFFICIENT_SEARCH_TERMS
    assert len(search_response.result.suggestions) == 0

    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 0

    # Any subsequent queries will reuse the search response created.
    client.search(address_to_experian_search_request(address))
    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 0


def test_format_not_initialized_for_response():
    client = MockClient()
    with pytest.raises(
        MockExperianException, match="No mock scenario setup for global_address_key=fake_key"
    ):
        client.format("fake_key")


def test_add_mock_address_response_verified_address():
    # This test shows that you can "override" and specify your
    # own mock address responses without solely relying on the fallback
    client = MockClient(fallback_confidence=Confidence.NO_MATCHES)
    assert len(client.search_responses) == 0
    assert len(client.format_responses) == 0

    address = AddressFactory.build()

    # Create a verified match response
    client.add_mock_address_response(address, Confidence.VERIFIED_MATCH)
    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 1

    # Searching for and formatting the reponse should not create a new record
    search_response = client.search(address_to_experian_search_request(address))
    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 1

    assert len(search_response.result.suggestions) == 1

    format_key = search_response.result.suggestions[0].global_address_key
    format_response = client.format(format_key)
    validate_address(address, format_response)


def test_add_mock_address_response_multiple_addresses():
    # This test shows that you can "override" and specify your
    # own mock address responses without solely relying on the fallback
    client = MockClient(fallback_confidence=Confidence.NO_MATCHES, multiple_count=4)
    assert len(client.search_responses) == 0
    assert len(client.format_responses) == 0

    address = AddressFactory.build()

    # Create a verified match response
    client.add_mock_address_response(address, Confidence.MULTIPLE_MATCHES)
    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 4

    # Searching for and formatting the reponse should not create a new record
    search_response = client.search(address_to_experian_search_request(address))
    assert search_response.result.confidence == Confidence.MULTIPLE_MATCHES
    assert len(search_response.result.suggestions) == 4

    # Each suggestion should be found when calling format
    for suggestion in search_response.result.suggestions:
        format_response = client.format(suggestion.global_address_key)
        validate_address(address, format_response)

    assert len(client.search_responses) == 1
    assert len(client.format_responses) == 4
