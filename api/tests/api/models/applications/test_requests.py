from datetime import date

from dateutil.relativedelta import relativedelta

from massgov.pfml.api.models.applications.requests import (
    future_date_of_birth_validator,
    max_date_of_birth_validator,
    min_date_of_birth_validator,
)

TEST_FIELD_NAME = "test_field"


class TestDateOfBirthValidators:
    def test_max_date_of_birth_validator_with_valid_date(self):
        # valid birthdate - birthdate < 150 years ago
        valid_birthdate = date(1980, 1, 1)
        validator_issues = max_date_of_birth_validator(valid_birthdate, TEST_FIELD_NAME)

        assert len(validator_issues) == 0

    def test_max_date_of_birth_validator_with_invalid_date(self):
        # invalid birthdate - birthdate > 150 years ago
        invalid_birthdate = date(1800, 1, 1)
        validator_issues = max_date_of_birth_validator(invalid_birthdate, TEST_FIELD_NAME)

        assert len(validator_issues) == 1
        assert validator_issues[0].message == "Date of birth must be within the past 150 years"
        assert validator_issues[0].type == "invalid_year_range"
        assert validator_issues[0].rule == "date_of_birth_within_past_150_years"
        assert validator_issues[0].field == TEST_FIELD_NAME

    def test_min_date_of_birth_validator_with_valid_date(self):
        # valid birthdate - birthdate > 14 years ago
        valid_birthdate = date.today() - relativedelta(years=20)
        validator_issues = min_date_of_birth_validator(valid_birthdate, TEST_FIELD_NAME)

        assert len(validator_issues) == 0

    def test_min_date_of_birth_validator_with_invalid_date(self):
        # invalid birthdate - birthdate < 14 years ago
        invalid_birthdate = date.today() - relativedelta(years=10)
        validator_issues = min_date_of_birth_validator(invalid_birthdate, TEST_FIELD_NAME)

        assert len(validator_issues) == 1
        assert (
            validator_issues[0].message == "The person taking leave must be at least 14 years old"
        )
        assert validator_issues[0].type == "invalid_age"
        assert validator_issues[0].rule == "older_than_14"
        assert validator_issues[0].field == TEST_FIELD_NAME

    def test_future_date_of_birth_validator_with_valid_date(self):
        # valid birthdate - birthdate < 7 months in the future
        valid_birthdate = date.today() + relativedelta(months=6)
        validator_issues = future_date_of_birth_validator(valid_birthdate, TEST_FIELD_NAME)

        assert len(validator_issues) == 0

    def test_future_date_of_birth_validator_with_invalid_date(self):
        # invalid birthdate - birthdate > 7 months in the future
        invalid_birthdate = date.today() + relativedelta(months=7, days=1)
        validator_issues = future_date_of_birth_validator(invalid_birthdate, TEST_FIELD_NAME)

        assert len(validator_issues) == 1
        assert (
            validator_issues[0].message
            == "Family member's date of birth must be less than 7 months from now"
        )
        assert validator_issues[0].type == "future_birth_date"
        assert validator_issues[0].rule == "max_7_months_in_future"
        assert validator_issues[0].field == TEST_FIELD_NAME
