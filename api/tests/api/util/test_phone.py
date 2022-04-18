import pytest

from massgov.pfml.api.util.phone import convert_to_E164, get_area_code_and_number, parse_number


class TestConvertToE164:
    def test_us_phone_str(self):
        assert convert_to_E164("15109283075") == "+15109283075"
        assert convert_to_E164("510-928-3075") == "+15109283075"

    def test_empty_phone_str(self):
        assert convert_to_E164("") is None

    def test_int_code_used_when_provided(self):
        assert convert_to_E164("510-928-3075", "1") == "+15109283075"

    def test_int_code_ignored_if_number_includes_country_code(self):
        assert convert_to_E164("+15109283075", "30") == "+15109283075"

    def test_invalid_number_raises_exception(self):
        with pytest.raises(Exception) as exc:
            convert_to_E164("617", "1", True)

        assert str(exc.value) == "Phone number is not valid."

    def test_invalid_number_without_raise_if_invalid(self):
        assert convert_to_E164("617", "1", False) == "+1617"
        assert convert_to_E164("617", "1") == "+1617"


class TestParseNumber:
    def test_phone_parsing(self):
        phone_obj = parse_number("805-610-3889")
        assert phone_obj.national_number == 8056103889


class TestAreaCodeRetrieval:
    def test_get_area_code(self):
        assert get_area_code_and_number("805-610-3889") == ("805", "6103889")
