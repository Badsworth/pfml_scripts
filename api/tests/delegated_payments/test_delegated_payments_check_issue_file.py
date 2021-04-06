import os
from datetime import datetime

import pytest
from freezegun import freeze_time

from massgov.pfml.delegated_payments.check_issue_file import CheckIssueEntry, CheckIssueFile
from massgov.pfml.delegated_payments.delegated_payments_util import ValidationIssueException


def test_positive_pay_field_validation_issues():
    today = datetime.today()

    file = CheckIssueFile()

    # Bad account number
    with pytest.raises(ValueError):
        file.add_entry(
            CheckIssueEntry(
                status_code="V",
                check_number="123",
                amount=123.00,
                issue_date=today,
                payee_id="12243",
                payee_name="Smith John",
                account_number="invalid_account",
            )
        )

    # invalid length for alphanumeric code (status_code)
    with pytest.raises(ValidationIssueException):
        file.add_entry(
            CheckIssueEntry(
                status_code="too_long",
                check_number="123",
                amount=123.00,
                issue_date=today,
                payee_id="12243",
                payee_name="Smith John",
                account_number="invalid_account",
            )
        )

    # invalid length for generic field (issue date)
    with pytest.raises(AttributeError):
        file.add_entry(
            CheckIssueEntry(
                status_code="too_long",
                check_number="123",
                amount=123.00,
                issue_date="this date is invalid and too long",
                payee_id="12243",
                payee_name="Smith John",
                account_number="invalid_account",
            )
        )


@freeze_time("2021-03-17 21:58:00")
def test_generate_positive_pay_file(monkeypatch, test_db_session):
    today = datetime.today()

    file = CheckIssueFile()

    entry = CheckIssueEntry(
        status_code="V",
        check_number="123",
        amount=123.00,
        issue_date=today,
        payee_id="12243",
        payee_name="Smith John",
        account_number=123456789,
    )

    entry2 = CheckIssueEntry(
        status_code="I",
        check_number="1234",
        amount=129.00,
        issue_date=today,
        payee_id="12243",
        payee_name="Smith John",
        account_number=123456789,
    )

    file.add_entry(entry)
    file.add_entry(entry2)

    positive_pay_output = file.to_bytes()

    expected_output = open(
        os.path.join(os.path.dirname(__file__), "test_files", "expected_positive_pay_file.txt"),
        "rb",
    ).read()

    assert positive_pay_output == expected_output
