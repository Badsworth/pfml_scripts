import csv
import io
from datetime import date
from decimal import Decimal

import faker
import pytest

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.ez_check as ez_check
import massgov.pfml.util.files as file_util
from massgov.pfml.util.decimals import round_nearest_hundredth
from tests.factories import EzCheckHeaderFactory, EzCheckRecordFactory

fake = faker.Faker()


@pytest.mark.parametrize(
    "field_class, description, length, value, expected_issues",
    (
        # EzCheckIntegerField
        (
            ez_check.EzCheckIntegerField,
            "Value too long",
            2,
            123,
            [payments_util.ValidationReason.FIELD_TOO_LONG],
        ),
        (
            ez_check.EzCheckIntegerField,
            "String instead of integer type",
            5,
            "12345",
            [payments_util.ValidationReason.INVALID_TYPE],
        ),
        (
            ez_check.EzCheckIntegerField,
            "Wrong type and too long raises only invalid type issue",
            2,
            "12345",
            [payments_util.ValidationReason.INVALID_TYPE],
        ),
        # EzCheckDecimalField
        (
            ez_check.EzCheckDecimalField,
            "Float type instead of Decimal type",
            10,
            12345.00,
            [payments_util.ValidationReason.INVALID_TYPE],
        ),
        (
            ez_check.EzCheckDecimalField,
            "Number too long",
            5,
            Decimal("919.00"),
            [payments_util.ValidationReason.FIELD_TOO_LONG],
        ),
        # EzCheckDateField
        (
            ez_check.EzCheckDateField,
            "String instead of date",
            20,
            "04/19/1775",
            [payments_util.ValidationReason.INVALID_TYPE],
        ),
        # EzCheckStateAbbreviationField
        (
            ez_check.EzCheckStateAbbreviationField,
            "Input value does not match acceptable pattern",
            4,
            "MASS",
            [payments_util.ValidationReason.INVALID_VALUE],
        ),
        # EzCheckCountryAbbreviationField
        (
            ez_check.EzCheckCountryAbbreviationField,
            "Input value does not match acceptable pattern",
            3,
            "usa",
            [payments_util.ValidationReason.INVALID_VALUE],
        ),
        # EzCheckZipCodeField
        (
            ez_check.EzCheckZipCodeField,
            "Short zip code fails",
            10,
            2109,
            [payments_util.ValidationReason.INVALID_VALUE],
        ),
        (
            ez_check.EzCheckZipCodeField,
            "4-5 (instead of 5-4) zip code fails",
            10,
            "0210-91702",
            [payments_util.ValidationReason.INVALID_VALUE],
        ),
        (
            ez_check.EzCheckZipCodeField,
            "Nine digit zipcode fails without dash",
            10,
            "021091702",
            [payments_util.ValidationReason.INVALID_VALUE],
        ),
    ),
)
def test_ez_check_field_validation_issues(field_class, description, length, value, expected_issues):
    field = field_class(description, length, value)

    issue_reasons = [issue.reason for issue in field.validation_issues]
    assert sorted(issue_reasons) == sorted(expected_issues)

    # Expect to raise an exception when we attempt to stringify the field.
    with pytest.raises(payments_util.ValidationIssueException):
        str(field)


@pytest.mark.parametrize(
    "field_class, description, length, value, str_val",
    (
        # EzCheckField
        (ez_check.EzCheckField, "Long integer to string", 15, 123456789012345, "123456789012345"),
        (ez_check.EzCheckField, "String shorter than max length", 10, "abcde", "abcde"),
        # EzCheckIntegerField
        (ez_check.EzCheckIntegerField, "Long value", 15, 123456789012345, "123456789012345"),
        (ez_check.EzCheckIntegerField, "Single digit", 1, 7, "7"),
        (ez_check.EzCheckIntegerField, "Shorter than max length value", 12, 95, "95"),
        # EzCheckDecimalField
        (
            ez_check.EzCheckDecimalField,
            "Add missing zero digit after decimal point",
            10,
            Decimal(12345.1),
            "12345.10",
        ),
        (ez_check.EzCheckDecimalField, "Add all decimal digits", 8, Decimal(919), "919.00"),
        # EzCheckDateField
        (ez_check.EzCheckDateField, "Simple date field", 20, date(1775, 4, 19), "04/19/1775"),
        # EzCheckStateAbbreviationField
        (
            ez_check.EzCheckStateAbbreviationField,
            "State abbreviation uppercased properly",
            2,
            "ma",
            "MA",
        ),
        # EzCheckCountryAbbreviationField
        (ez_check.EzCheckCountryAbbreviationField, "Simple country abbreviation", 2, "US", "US"),
        # EzCheckZipCodeField
        (ez_check.EzCheckZipCodeField, "Five digit zip code integer", 10, 21091, "21091"),
        (ez_check.EzCheckZipCodeField, "Five digit zip code string", 10, "02109", "02109"),
        (ez_check.EzCheckZipCodeField, "Zip+4", 10, "02109-1702", "02109-1702"),
    ),
)
def test_ez_check_field_success(field_class, description, length, value, str_val):
    field = field_class(description, length, value)
    assert len(field.validation_issues) == 0
    assert str(field) == str_val


@pytest.mark.parametrize(
    "_description, args, expected_issues",
    (
        (
            "All errors for single invalid field raised",
            {"state": "MASS"},
            [
                payments_util.ValidationReason.INVALID_VALUE,
                payments_util.ValidationReason.FIELD_TOO_LONG,
            ],
        ),
        (
            "Errors for all invalid fields are raised",
            {"check_date": 1999, "zip_code": 1999},
            [
                payments_util.ValidationReason.INVALID_TYPE,
                payments_util.ValidationReason.INVALID_VALUE,
            ],
        ),
    ),
)
def test_ez_check_record_failure(_description, args, expected_issues):
    # Expect to raise an exception when we initialize the object.
    try:
        EzCheckRecordFactory(**args)
    except payments_util.ValidationIssueException as e:
        record_issues = [issue.reason for issue in e.issues]
        assert sorted(record_issues) == sorted(expected_issues)


def test_ez_check_record_success():
    args = {
        "check_number": fake.random_int(min=1_000_000_000, max=9_999_999_999),
        "check_date": fake.date_between("-3w", "today"),
        "amount": Decimal(fake.random_int(min=10, max=9_999)),
        "memo": fake.sentence()[:99],
        "payee_name": fake.name(),
        "address_line_1": fake.street_address(),
        "address_line_2": "",
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip_code": fake.postcode(),
        "country": fake.country_code(),
    }

    record = ez_check.EzCheckRecord(**args)

    s = io.StringIO()
    w = csv.writer(s)
    w.writerow(
        [
            2,
            args["check_number"],
            args["check_date"].strftime(ez_check.DATE_FORMAT),
            round_nearest_hundredth(args["amount"]),
            args["memo"],
        ]
    )
    w.writerow(
        [
            3,
            args["payee_name"],
            "",
            args["address_line_1"],
            args["address_line_2"],
            args["city"],
            args["state"],
            args["zip_code"],
            args["country"],
        ]
    )

    assert str(record) == s.getvalue()


@pytest.mark.parametrize(
    "_description, args, expected_issues",
    (
        (
            "Routing number too long",
            {"routing_number": 123_456_789_012_345},
            [payments_util.ValidationReason.FIELD_TOO_LONG],
        ),
        (
            "Errors for all invalid fields are raised",
            {"account_number": "99", "zip_code": "2021"},
            [
                payments_util.ValidationReason.INVALID_TYPE,
                payments_util.ValidationReason.INVALID_VALUE,
            ],
        ),
    ),
)
def test_ez_check_header_failure(_description, args, expected_issues):
    # Expect to raise an exception when we initialize the object.
    try:
        EzCheckHeaderFactory(**args)
    except payments_util.ValidationIssueException as e:
        record_issues = [issue.reason for issue in e.issues]
        assert sorted(record_issues) == sorted(expected_issues)


def test_ez_check_header_success():
    args = {
        "name_line_1": fake.name(),
        "name_line_2": fake.company(),
        "address_line_1": fake.street_address(),
        "address_line_2": "Bldg. " + fake.building_number(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip_code": fake.postcode(),
        "country": fake.country_code(),
        "account_number": fake.random_int(min=1_000_000_000_000_000, max=9_999_999_999_999_999),
        "routing_number": fake.random_int(min=10_000_000_000, max=99_999_999_999),
    }

    header = ez_check.EzCheckHeader(**args)

    s = io.StringIO()
    w = csv.writer(s)
    w.writerow(
        [
            1,
            args["name_line_1"],
            args["name_line_2"],
            args["address_line_1"],
            args["address_line_2"],
            args["city"],
            args["state"],
            args["zip_code"],
            args["country"],
            args["account_number"],
            args["routing_number"],
        ]
    )

    assert str(header) == s.getvalue()


@pytest.mark.parametrize("args, exception_type", (({}, TypeError), ({"header": None}, TypeError)))
def test_ez_check_file_initialization_failure(args, exception_type):
    with pytest.raises(exception_type):
        ez_check.EzCheckFile(**args)


def test_ez_check_file_success(mock_s3_bucket):
    ez_check_file = ez_check.EzCheckFile(EzCheckHeaderFactory())

    # Create some small number of records to add to the file.
    record_count = fake.random_int(min=1, max=15)
    for _i in range(record_count):
        ez_check_file.add_record(EzCheckRecordFactory())

    # Write the EzCheck file to S3.
    # s3 = boto3.client("s3")
    s3_path = "s3://{}/{}".format(mock_s3_bucket, "path/to/ez_check_file.csv")
    with file_util.write_file(s3_path) as fh:
        ez_check_file.write_to(fh)

    # Re-open the file for reading so we can assert we wrote each record to the file with the
    # expected line numbers.
    file_stream = file_util.open_stream(s3_path)

    line_count = 0
    for line in file_stream:
        line_count += 1
        if line_count == 1:
            assert line.startswith("1,")
            continue

        if line_count % 2 == 0:
            assert line.startswith("2,")
        else:
            assert line.startswith("3,")

    # Header line + 2 lines for each record in the file.
    assert line_count == 1 + 2 * record_count
