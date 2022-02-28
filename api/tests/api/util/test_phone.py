from massgov.pfml.api.util.phone import convert_to_E164


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
