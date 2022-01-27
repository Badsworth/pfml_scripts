import pytest

from massgov.pfml.util.converters.str_to_numeric import str_to_int


def test_str_to_int__value_is_none():
    value = None
    parsed = str_to_int(value)
    assert parsed is None


@pytest.mark.parametrize("value", ["NaN", "0.001"])
def test_str_to_int__value_is_non_numeric(value: str):
    parsed = str_to_int(value)
    assert parsed is None


@pytest.mark.parametrize(
    "value", ["0", "1", "2", "3", "1000", "10000", "9223372036854775807", "-9223372036854775807"]
)
def test_str_to_int__value_is_valid(value: str):
    parsed = str_to_int(value)
    assert parsed == int(value)
