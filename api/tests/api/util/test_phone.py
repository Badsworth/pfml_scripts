from massgov.pfml.api.models.common import Phone
from massgov.pfml.api.util.phone import convert_to_E164


class TestConvertToE164:
    def test_us_phone(self):
        assert convert_to_E164(Phone(int_code="1", phone_number="510-928-3075")) == "+15109283075"

    def test_empty_phone(self):
        assert convert_to_E164(Phone()) is None
