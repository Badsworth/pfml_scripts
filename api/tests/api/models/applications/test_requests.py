from datetime import date

from dateutil.relativedelta import relativedelta

from massgov.pfml.api.models.applications.requests import (
    max_date_of_birth_validator,
    min_date_of_birth_validator,
)


def test_max_date_of_birth_validator():
    # valid birthdate - birthdate < 150 years ago
    valid_birthdate = date(1980, 1, 1)
    field_name = "test_field"
    validator_issues = max_date_of_birth_validator(valid_birthdate, field_name)

    assert len(validator_issues) == 0

    # invalid birthdate - birthdate > 150 years ago
    invalid_birthdate = date(1800, 1, 1)
    validator_issues = max_date_of_birth_validator(invalid_birthdate, field_name)

    assert len(validator_issues) == 1
    assert validator_issues[0].message == "Date of birth must be within the past 150 years"
    assert validator_issues[0].type == "invalid_year_range"
    assert validator_issues[0].rule == "date_of_birth_within_past_150_years"
    assert validator_issues[0].field == field_name


def test_min_date_of_birth_validator():
    # valid birthdate - birthdate > 14 years ago
    valid_birthdate = date.today() - relativedelta(years=20)
    field_name = "test_field"
    validator_issues = min_date_of_birth_validator(valid_birthdate, field_name)

    assert len(validator_issues) == 0

    # invalid birthdate - birthdate < 14 years ago
    invalid_birthdate = date.today() - relativedelta(years=10)
    validator_issues = min_date_of_birth_validator(invalid_birthdate, field_name)

    assert len(validator_issues) == 1
    assert validator_issues[0].message == "The person taking leave must be at least 14 years old"
    assert validator_issues[0].type == "invalid_age"
    assert validator_issues[0].rule == "older_than_14"
    assert validator_issues[0].field == field_name
