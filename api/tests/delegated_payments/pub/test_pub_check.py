import logging  # noqa: B1
import re
from datetime import timedelta
from decimal import Decimal

import faker
import pytest
import sqlalchemy

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.pub.pub_check as pub_check
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    ClaimType,
    LkState,
    Payment,
    PaymentMethod,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    ExperianAddressPairFactory,
    PaymentFactory,
)
from massgov.pfml.delegated_payments.check_issue_file import CheckIssueFile
from massgov.pfml.delegated_payments.ez_check import EzCheckFile, EzCheckRecord
from tests.factories import EzCheckFileFactory, PositivePayFileFactory

fake = faker.Faker()


def _random_valid_check_payment_with_state_log(db_session: db.Session) -> Payment:
    return _random_payment_with_state_log(
        db_session, PaymentMethod.CHECK, State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK
    )


def _random_payment_with_state_log(
    db_session: db.Session, method: PaymentMethod, state: LkState
) -> Payment:
    # Create the employee and claim ourselves so the payment has an associated address.
    address_pair = ExperianAddressPairFactory(experian_address=AddressFactory())
    employee = EmployeeFactory()
    claim = ClaimFactory(employee=employee, claim_type_id=ClaimType.MEDICAL_LEAVE.claim_type_id)

    # Set the dates to some reasonably recent dates in the past.
    start_date = fake.date_between("-10w", "-2w")
    end_date = start_date + timedelta(days=6)
    payment_date = end_date + timedelta(days=1)

    payment = PaymentFactory(
        claim=claim,
        period_start_date=start_date,
        period_end_date=end_date,
        payment_date=payment_date,
        amount=Decimal(fake.random_int(min=10, max=9_999)),
        disb_method_id=method.payment_method_id,
        experian_address_pair=address_pair,
        claim_type=claim.claim_type,
        fineos_employee_first_name=employee.first_name,
        fineos_employee_last_name=employee.last_name,
    )

    state_log_util.create_finished_state_log(
        end_state=state,
        outcome=state_log_util.build_outcome("Add to PUB check file"),
        associated_model=payment,
        db_session=db_session,
    )
    db_session.commit()

    return payment


def test_create_check_file_no_eligible_payments(test_db_session):
    # Expect to return None when there are no payments to be added to a check file.
    ez_check_file, positive_pay_file = pub_check.create_check_file(test_db_session)
    assert ez_check_file is None
    assert positive_pay_file is None


def test_create_check_file_eligible_payment_error(
    initialize_factories_session, test_db_session, caplog, monkeypatch
):
    monkeypatch.setenv("PUB_PAYMENT_STARTING_CHECK_NUMBER", "0")
    # Update zip code so that it fails validation.
    payment = _random_valid_check_payment_with_state_log(test_db_session)
    payment.experian_address_pair.experian_address.zip_code = "An invalid zip code"
    test_db_session.commit()

    caplog.set_level(logging.ERROR)  # noqa: B1

    ez_check_file, positive_pay_file = pub_check.create_check_file(test_db_session)
    assert ez_check_file is None
    assert positive_pay_file is None

    assert len(caplog.records) == 1
    error_message_pattern = r"ValidationReason\.FIELD_TOO_LONG.*ValidationReason\.INVALID_VALUE"
    assert re.search(error_message_pattern, caplog.records[0].getMessage())


def test_create_check_file_success(
    local_initialize_factories_session,
    monkeypatch,
    local_test_db_session,
    local_test_db_other_session,
):
    account_number = str(fake.random_int(min=1_000_000_000_000_000, max=9_999_999_999_999_999))
    routing_number = str(fake.random_int(min=10_000_000_000, max=99_999_999_999))
    starting_check_num = str(fake.random_int(min=1_000, max=10_000))
    monkeypatch.setenv("DFML_PUB_ACCOUNT_NUMBER", account_number)
    monkeypatch.setenv("DFML_PUB_ROUTING_NUMBER", routing_number)
    monkeypatch.setenv("PUB_PAYMENT_STARTING_CHECK_NUMBER", starting_check_num)

    payments = []
    for _i in range(fake.random_int(min=3, max=8)):
        payments.append(_random_valid_check_payment_with_state_log(local_test_db_session))

    ez_check_file, positive_pay_file = pub_check.create_check_file(local_test_db_session)

    # Explicitly commit the changes to the database since we expect the calling code to do it.
    local_test_db_session.commit()

    assert isinstance(ez_check_file, EzCheckFile)
    assert isinstance(positive_pay_file, CheckIssueFile)
    assert len(ez_check_file.records) == len(payments)

    # Confirm that we updated the state log for each payment.
    for i, payment in enumerate(payments):
        assert (
            local_test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
            .filter(
                StateLog.end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id
            )
            .filter(StateLog.payment_id == payment.payment_id)
            .scalar()
            == 1
        )

        assert payment.check.check_number == (i + int(starting_check_num) + 1)


def test_send_check_file(mock_s3_bucket):
    ez_check_file = EzCheckFileFactory()
    archive_folder_path = f"s3://{mock_s3_bucket}/pub/archive"
    outbound_folder_path = f"s3://{mock_s3_bucket}/pub/outbound"

    ref_file = pub_check.send_check_file(ez_check_file, archive_folder_path, outbound_folder_path)

    filename_pattern = (
        r"\d{4}-\d{2}-\d{2}\/\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-EOLWD-DFML-EZ-CHECK.csv"
    )
    assert re.search(filename_pattern, ref_file.file_location)

    # Confirm output file has 2 rows for each record and 1 for the header.
    file_stream = file_util.open_stream(ref_file.file_location)
    assert len([line for line in file_stream]) == 1 + 2 * len(ez_check_file.records)

    # The outbound file should have been identically built
    file_stream = file_util.open_stream(f"{outbound_folder_path}/EOLWD-DFML-EZ-CHECK.csv")
    assert len([line for line in file_stream]) == 1 + 2 * len(ez_check_file.records)


def test_send_positive_pay_file(mock_s3_bucket):
    positive_pay_file = PositivePayFileFactory()
    archive_folder_path = f"s3://{mock_s3_bucket}/pub/archive"
    outbound_folder_path = f"s3://{mock_s3_bucket}/pub/outbound"

    ref_file = pub_check.send_positive_pay_file(
        positive_pay_file, archive_folder_path, outbound_folder_path
    )

    filename_pattern = (
        r"\d{4}-\d{2}-\d{2}\/\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-EOLWD-DFML-POSITIVE-PAY.txt"
    )
    assert re.search(filename_pattern, ref_file.file_location)

    # Confirm output file has a row for each record
    file_stream = file_util.open_stream(ref_file.file_location)
    assert len([line for line in file_stream]) == len(positive_pay_file.entries)

    # The outbound file should have been identically built
    file_stream = file_util.open_stream(f"{outbound_folder_path}/EOLWD-DFML-POSITIVE-PAY.txt")
    assert len([line for line in file_stream]) == len(positive_pay_file.entries)


@pytest.mark.parametrize(
    "_description, ach_payment_count, wrong_state_count, eligible_payment_count",
    (
        (
            "A few number of eligible payments, no ineligible payments",
            0,
            0,
            fake.random_int(min=2, max=8),
        ),
        ("No payments", 0, 0, 0),
    ),
    ids=["some_payments", "no_payments"],
)
def test_get_eligible_check_payments_success(
    initialize_factories_session,
    test_db_session,
    _description,
    ach_payment_count,
    wrong_state_count,
    eligible_payment_count,
):
    # ACH payment type instead of Check.
    for _i in range(ach_payment_count):
        _random_payment_with_state_log(
            test_db_session, PaymentMethod.ACH, State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK
        )

    # Check payment in state after being included in PUB check file.
    for _i in range(wrong_state_count):
        _random_payment_with_state_log(
            test_db_session, PaymentMethod.CHECK, State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
        )

    for _i in range(eligible_payment_count):
        _random_valid_check_payment_with_state_log(test_db_session)

    eligible_payments = pub_check._get_eligible_check_payments(test_db_session)

    assert len(eligible_payments) == eligible_payment_count


def test_get_eligible_check_payments_error(test_db_session, initialize_factories_session):
    for _ in range(5):
        _random_payment_with_state_log(
            test_db_session,
            PaymentMethod.CHECK,
            State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK,
        )

    # include ACH payment instead of check
    _random_payment_with_state_log(
        test_db_session, PaymentMethod.ACH, State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK
    )

    with pytest.raises(
        Exception, match=r"Non-Check payment method detected in state log: .+",
    ):
        pub_check._get_eligible_check_payments(test_db_session)


def test_convert_payment_to_ez_check_record_success(initialize_factories_session, test_db_session):
    payment = _random_valid_check_payment_with_state_log(test_db_session)
    ez_check_record = pub_check._convert_payment_to_ez_check_record(payment, 0)

    assert isinstance(ez_check_record, EzCheckRecord)


def test_convert_payment_to_ez_check_record_failure(initialize_factories_session, test_db_session):
    payment_without_address = PaymentFactory()
    with pytest.raises(AttributeError):
        pub_check._convert_payment_to_ez_check_record(payment_without_address, 0)


def test_convert_payment_to_ez_check_record_unsupported_claimtype(
    initialize_factories_session, test_db_session
):
    claim = ClaimFactory(claim_type_id=ClaimType.MILITARY_LEAVE.claim_type_id)
    payment_without_address = PaymentFactory(claim=claim, claim_type=claim.claim_type)
    with pytest.raises(pub_check.UnSupportedClaimTypeException):
        pub_check._convert_payment_to_ez_check_record(payment_without_address, 0)


def test_format_check_memo_success(initialize_factories_session, test_db_session):
    payment = _random_valid_check_payment_with_state_log(test_db_session)
    memo = pub_check._format_check_memo(payment)
    claim_type = payment.claim_type.claim_type_description

    pattern = "PFML {} Payment {}".format(claim_type, payment.claim.fineos_absence_id)
    assert re.search(pattern, memo)


def test_format_check_memo_failure(initialize_factories_session, test_db_session):
    payment_without_dates = PaymentFactory(
        period_start_date=None, period_end_date=None, payment_date=None
    )

    with pytest.raises(AttributeError):
        pub_check._format_check_memo(payment_without_dates)


@pytest.mark.parametrize(
    "_description, first_name, last_name, expected_result",
    (
        ("Short name", "David", "Ortiz", "David Ortiz"),
        (
            "80 letter last name includes 4 letters from first name",
            "Clara",
            ("1234567890" * 9)[:80],
            "Clar " + ("1234567890" * 9)[:80],
        ),
        ("84 letter last name", "Amelia", ("1234567890" * 9)[:84], ("1234567890" * 9)[:84]),
        ("85 letter last name", "Kevin", ("1234567890" * 9)[:85], ("1234567890" * 9)[:85]),
        (
            "100 letter last name trimmed to 85 characters",
            "Susan",
            ("1234567890" * 10),
            ("1234567890" * 9)[:85],
        ),
    ),
)
def test_format_employee_name_for_ez_check_success(
    initialize_factories_session,
    test_db_session,
    _description,
    first_name,
    last_name,
    expected_result,
):
    payment = PaymentFactory(
        fineos_employee_first_name=first_name, fineos_employee_last_name=last_name
    )
    assert pub_check._format_employee_name_for_ez_check(payment) == expected_result
