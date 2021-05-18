from massgov.pfml.util.routing_number_validation import validate_routing_number


def test_routing_number_validation():
    # Invalid routing number
    assert not validate_routing_number("123456789")

    # Valid routing number
    assert validate_routing_number("221172610")
