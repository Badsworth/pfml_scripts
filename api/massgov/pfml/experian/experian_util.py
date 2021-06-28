from typing import Optional, cast

from massgov.pfml.db.models.employees import Address, GeoState, LkGeoState

# Shared utility methods for both the REST and SOAP Experian clients


class MockExperianException(Exception):
    pass


def get_geo_state(state: str) -> Optional[LkGeoState]:
    # In any context where the DB exists and is initialized
    # we can just reverse lookup the description
    if hasattr(GeoState, "description_to_db_instance"):
        # Cast as the description_to_db_instance just looks like Optional[type]
        # to mypys type checker.
        return cast(Optional[LkGeoState], GeoState.description_to_db_instance.get(state))

    # If a scenario doesn't have the DB initialized, that
    # dict won't be populated, so let's do it a bit differently.
    # Iterate over the attributes and find the one that matches
    for attr in GeoState.__dict__.values():
        if type(attr) is LkGeoState:
            if attr.geo_state_description == state:
                return attr

    return None


def experian_search_request_to_address(experian_address: str) -> Address:
    """
    This method is the reverse of address_to_experian_search_request
    """
    experian_address_parts = experian_address.split(",")
    parts_count = len(experian_address_parts)
    # We expect an address to be 3-5 pieces
    # line one, city, and zip code are always expected
    # line two, and state are both potentially there
    if parts_count < 3 or parts_count > 5:
        raise MockExperianException(
            "Unable to parse address for mocking purposes: [%s]" % experian_address
        )

    address = Address()
    # The address is ordered in the string like:
    # address_line_one
    # address_line_two - optionally present
    # city
    # state - optionally present
    # zip_code

    # As we always assume address_line_one & zip code are present, can grab them
    address.address_line_one = experian_address_parts[0]
    address.zip_code = experian_address_parts[-1]

    # If there are three, we assume the remaining record is the city
    if parts_count == 3:
        address.city = experian_address_parts[1]

    # Need to figure out whether it's address line two or the state
    if parts_count == 4:
        # State is always 2 characters, if the next to last item
        # is exactly two, assume its a state. Unless address 2 is set AND
        # the cities name is exactly 2 chars, this should be a reasonable
        # assumption to make as far as mocking goes.
        if len(experian_address_parts[2]) == 2:
            address.geo_state = get_geo_state(experian_address_parts[2])  # type: ignore
            address.city = experian_address_parts[1]
        # We assume address line two is set otherwise
        else:
            address.address_line_two = experian_address_parts[1]
            address.city = experian_address_parts[2]

    # All 5 present, can set all fields
    if parts_count == 5:
        address.address_line_two = experian_address_parts[1]
        address.city = experian_address_parts[2]
        address.geo_state = get_geo_state(experian_address_parts[3])  # type: ignore

    return address


def address_to_experian_search_text(address: Address) -> str:
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
    return ",".join(address_parts)
