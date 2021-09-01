from datetime import date

from massgov.pfml.api.rmv_check import is_test_record
from massgov.pfml.api.services.rmv_check import RMVCheckRequest


def test_is_test_record():
    test_records = {
        ("Steve", "Tester"),
        ("Charles", "Presley"),
        ("Willis", "Sierra"),
        ("Lilibeth", "Perozo"),
        ("Roseangela", "Leite Da Silva"),
        ("Vida", "King"),
        ("John", "Pinkham"),
        ("Jonathan", "Day"),
        ("Linda", "Bellabe"),
    }

    for f_name, l_name in test_records:
        rmv_check_request = RMVCheckRequest(
            first_name=f_name,
            last_name=l_name,
            date_of_birth=date(1970, 1, 1),
            ssn_last_4="1234",
            mass_id_number="S12345678",
            residential_address_line_1="123 Main St.",
            residential_address_line_2="Apt. 123",
            residential_address_city="Boston",
            residential_address_zip_code="12345",
            absence_case_id="foo",
        )

        assert is_test_record(rmv_check_request) is True
