import dataclasses
import re
from datetime import date, datetime, timedelta
from typing import Tuple

import faker
import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.db as db
import massgov.pfml.delegated_payments.delegated_fineos_pei_writeback as writeback
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Flow,
    LkPaymentMethod,
    LkState,
    Payment,
    PaymentCheck,
    PaymentMethod,
    PaymentReferenceFile,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import PaymentFactory
from massgov.pfml.db.models.payments import (
    ACTIVE_WRITEBACK_RECORD_STATUS,
    PENDING_ACTIVE_WRITEBACK_RECORD_STATUS,
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    LkFineosWritebackTransactionStatus,
)

# every test in here requires real resources
pytestmark = pytest.mark.integration

fake = faker.Faker()

check_number_provider = {"check_number": 1}


@pytest.fixture
def fineos_pei_writeback_step(initialize_factories_session, test_db_session, test_db_other_session):
    return writeback.FineosPeiWritebackStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@pytest.fixture
def local_fineos_pei_writeback_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return writeback.FineosPeiWritebackStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def _generate_payment(payment_method: LkPaymentMethod = PaymentMethod.ACH) -> Payment:
    payment = PaymentFactory.create(
        fineos_pei_c_value="1000",
        fineos_pei_i_value=str(fake.unique.random_int(min=1000, max=9999)),
        fineos_extraction_date=date.today() - timedelta(days=fake.random_int()),
        disb_method_id=payment_method.payment_method_id,
    )
    if payment_method == PaymentMethod.CHECK:
        check_number = check_number_provider["check_number"]
        check_number_provider["check_number"] += 1
        payment.check = PaymentCheck(check_number=check_number)

    return payment


def _generate_payment_and_state(
    test_db_session: db.Session, state: LkState, payment_method: LkPaymentMethod = PaymentMethod.ACH
) -> Payment:
    payment = _generate_payment(payment_method)
    state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=state,
        outcome=state_log_util.build_outcome("Creating for test"),
        db_session=test_db_session,
    )
    return payment


def _generate_payment_and_state_tuple(
    test_db_session: db.Session, state: State, payment_method: LkPaymentMethod = PaymentMethod.ACH
) -> Tuple[Payment, StateLog]:
    payment = _generate_payment(payment_method)
    state_log = state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=state,
        outcome=state_log_util.build_outcome("Creating for test"),
        db_session=test_db_session,
    )
    return payment, state_log


def _generate_payment_and_state_with_writeback_details(
    db_session: db.Session,
    payment_state: LkState,
    transaction_status: LkFineosWritebackTransactionStatus,
    payment_method: LkPaymentMethod = PaymentMethod.ACH,
) -> Payment:
    payment = _generate_payment_and_state(db_session, payment_state, payment_method)

    state_log_util.create_finished_state_log(
        associated_model=payment,
        end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        outcome=state_log_util.build_outcome("test"),
        db_session=db_session,
    )
    writeback_details = FineosWritebackDetails(
        payment=payment, transaction_status_id=transaction_status.transaction_status_id,
    )
    db_session.add(writeback_details)

    return payment


def _generate_zero_dollar_payment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state_with_writeback_details(
        test_db_session,
        State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT,
        FineosWritebackTransactionStatus.PROCESSED,
    )


def _generate_overpayment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state_with_writeback_details(
        test_db_session,
        State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT,
        FineosWritebackTransactionStatus.PROCESSED,
    )


def _generate_accepted_payment(
    test_db_session: db.Session, payment_method: LkPaymentMethod
) -> Payment:
    state = State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT
    if payment_method == PaymentMethod.CHECK:
        state = State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT

    return _generate_payment_and_state_with_writeback_details(
        test_db_session, state, FineosWritebackTransactionStatus.PAID, payment_method
    )


def _generate_completed_check_payment(test_db_session: db.Session) -> Payment:
    state = State.DELEGATED_PAYMENT_COMPLETE

    payment = _generate_payment_and_state_with_writeback_details(
        test_db_session, state, FineosWritebackTransactionStatus.POSTED, PaymentMethod.CHECK
    )

    payment.check.check_posted_date = payment.fineos_extraction_date + timedelta(days=10)

    return payment


def _generate_completed_eft_payment_with_change_notification(
    test_db_session: db.Session,
) -> Payment:
    state = State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION

    return _generate_payment_and_state_with_writeback_details(
        test_db_session, state, FineosWritebackTransactionStatus.POSTED, PaymentMethod.ACH
    )


def _generate_cancelled_payment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state_with_writeback_details(
        test_db_session,
        State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION,
        FineosWritebackTransactionStatus.PROCESSED,
    )


def _generate_errored_payment(test_db_session: db.Session) -> Payment:
    return _generate_payment_and_state_with_writeback_details(
        test_db_session,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR,
    )


def validate_writeback_sent_state(db_session: db.Session, payment: Payment):
    writeback_state_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, db_session
    )
    assert writeback_state_log.end_state_id == State.DELEGATED_FINEOS_WRITEBACK_SENT.state_id


@pytest.mark.parametrize(
    "zero_dollar_payment_count, overpayment_count, accepted_payment_count, cancelled_payment_count, errored_payment_count",
    (
        # Some payments in each state.
        (
            fake.random_int(min=1, max=4),
            fake.random_int(min=2, max=8),
            fake.random_int(min=2, max=6),
            fake.random_int(min=4, max=7),
            fake.random_int(min=1, max=3),
        ),
    ),
    ids=["state_payments"],
)
@freeze_time("2021-01-01 12:00:00")
def test_process_payments_for_writeback(
    local_fineos_pei_writeback_step,
    local_test_db_session,
    local_test_db_other_session,
    mock_s3_bucket,
    monkeypatch,
    zero_dollar_payment_count,
    overpayment_count,
    accepted_payment_count,
    cancelled_payment_count,
    errored_payment_count,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket

    fineos_data_import_path = s3_bucket_uri + "/TEST/peiupdate/"
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", fineos_data_import_path)

    pfml_fineos_outbound_path = s3_bucket_uri + "/cps/outbound/"
    monkeypatch.setenv("PFML_FINEOS_WRITEBACK_ARCHIVE_PATH", pfml_fineos_outbound_path)

    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    for _i in range(fake.random_int(min=2, max=7)):
        _generate_payment_and_state(
            local_test_db_session, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT
        )

    zero_dollar_payments = []
    for _i in range(zero_dollar_payment_count):
        zero_dollar_payments.append(_generate_zero_dollar_payment(local_test_db_session))

    overpayments = []
    for _i in range(overpayment_count):
        overpayments.append(_generate_overpayment(local_test_db_session))

    accepted_check_payments = []
    for _i in range(accepted_payment_count):
        accepted_check_payments.append(
            _generate_accepted_payment(local_test_db_session, PaymentMethod.CHECK)
        )

    accepted_eft_payments = []
    for _i in range(accepted_payment_count):
        accepted_eft_payments.append(
            _generate_accepted_payment(local_test_db_session, PaymentMethod.ACH)
        )

    cancelled_payments = []
    for _i in range(cancelled_payment_count):
        cancelled_payments.append(_generate_cancelled_payment(local_test_db_session))

    completed_check_payments = []
    for _i in range(accepted_payment_count):
        completed_check_payments.append(_generate_completed_check_payment(local_test_db_session))

    completed_eft_payments_with_change_notification = []
    for _i in range(accepted_payment_count):
        completed_eft_payments_with_change_notification.append(
            _generate_completed_eft_payment_with_change_notification(local_test_db_session)
        )

    errored_payments = []
    for _i in range(errored_payment_count):
        errored_payments.append(_generate_errored_payment(local_test_db_session))

    all_payments = (
        zero_dollar_payments
        + overpayments
        + accepted_check_payments
        + accepted_eft_payments
        + cancelled_payments
        + completed_check_payments
        + completed_eft_payments_with_change_notification
        + errored_payments
    )

    local_fineos_pei_writeback_step.process_payments_for_writeback()

    reference_files = (
        local_test_db_other_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PEI_WRITEBACK.reference_file_type_id
        )
        .all()
    )

    # Expect to have created a single ReferenceFile for our single writeback file.
    assert len(reference_files) == 1

    ref_file = reference_files[0]
    assert ref_file.file_location.endswith(writeback.WRITEBACK_FILE_SUFFIX)
    assert (
        ref_file
        == local_test_db_other_session.query(StateLog)
        .filter(StateLog.end_state_id == State.PEI_WRITEBACK_SENT.state_id)
        .one_or_none()
        .reference_file
    )

    # Expect there to be a single PaymentReferenceFile linking the payment and the reference file.
    for payment in all_payments:
        payment_reference_files = (
            local_test_db_other_session.query(PaymentReferenceFile)
            .filter(PaymentReferenceFile.reference_file_id == ref_file.reference_file_id)
            .filter(PaymentReferenceFile.payment_id == payment.payment_id)
            .all()
        )
        assert len(payment_reference_files) == 1

    # Each payment transitioned to the correct state.
    for payment in zero_dollar_payments:
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT.state_id
        validate_writeback_sent_state(local_test_db_other_session, payment)

    for payment in overpayments:
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT.state_id
        validate_writeback_sent_state(local_test_db_other_session, payment)

    for payment in cancelled_payments:
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_PROCESSED_CANCELLATION.state_id
        validate_writeback_sent_state(local_test_db_other_session, payment)

    accepted_check_payments_i_values = []
    for payment in accepted_check_payments:
        accepted_check_payments_i_values.append(payment.fineos_pei_i_value)
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id
        validate_writeback_sent_state(local_test_db_other_session, payment)

    accepted_eft_payments_i_values = []
    for payment in accepted_eft_payments:
        accepted_eft_payments_i_values.append(payment.fineos_pei_i_value)
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_id
        validate_writeback_sent_state(local_test_db_other_session, payment)

    completed_check_payment_i_values = []
    for payment in completed_check_payments:
        completed_check_payment_i_values.append(payment.fineos_pei_i_value)
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_COMPLETE.state_id
        validate_writeback_sent_state(local_test_db_other_session, payment)

    completed_eft_payment_i_values = []
    for payment in completed_eft_payments_with_change_notification:
        completed_eft_payment_i_values.append(payment.fineos_pei_i_value)
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert (
            state_log.end_state_id
            == State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION.state_id
        )
        validate_writeback_sent_state(local_test_db_other_session, payment)

    errored_payments_i_values = []
    for payment in errored_payments:
        errored_payments_i_values.append(payment.fineos_pei_i_value)
        state_log = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        assert state_log.end_state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id

    # Assert that the contents of the writeback file match our expectations.
    writeback_file_lines = list(file_util.read_file_lines(ref_file.file_location))
    header_row = writeback_file_lines.pop(0)
    assert header_row == ",".join(
        [f.name for f in dataclasses.fields(writeback.PeiWritebackRecord)]
    )

    expected_line_pattern = "{},({}),({}|{}),({}),({}),({}|{}|{}|{}),({})".format(
        r"\d\d\d\d",  # C value
        r"\d\d\d\d",  # I value
        ACTIVE_WRITEBACK_RECORD_STATUS,
        PENDING_ACTIVE_WRITEBACK_RECORD_STATUS,
        r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d",  # Extraction date
        r"\d*",  # Check number
        # Expect both transaction statuses in the writeback file.
        FineosWritebackTransactionStatus.PAID.transaction_status_description,
        FineosWritebackTransactionStatus.PROCESSED.transaction_status_description,
        FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR.transaction_status_description,
        FineosWritebackTransactionStatus.POSTED.transaction_status_description,
        r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d",  # Transaction date
    )
    prog = re.compile(expected_line_pattern)
    assert len(all_payments) == len(writeback_file_lines)
    now = payments_util.get_now().date()

    for line in writeback_file_lines:
        # Expect that each line will match our pattern.
        result = prog.match(line)
        assert result

        # Expect that payment types will set the appropriate transaction status.
        i_value = result.group(1)
        record_status = result.group(2)
        extraction_date = datetime.strptime(result.group(3), "%Y-%m-%d %H:%M:%S")
        transaction_number = result.group(4)
        transaction_status = result.group(5)
        transaction_date = datetime.strptime(result.group(6), "%Y-%m-%d %H:%M:%S")

        if i_value in accepted_check_payments_i_values:
            assert (
                transaction_status
                == FineosWritebackTransactionStatus.PAID.transaction_status_description
            )
            assert record_status == FineosWritebackTransactionStatus.PAID.writeback_record_status
            assert transaction_number != ""
            assert transaction_date.date() == now
        elif i_value in accepted_eft_payments_i_values:
            assert (
                transaction_status
                == FineosWritebackTransactionStatus.PAID.transaction_status_description
            )
            assert record_status == FineosWritebackTransactionStatus.PAID.writeback_record_status
            assert transaction_date.date() == now
        elif i_value in errored_payments_i_values:
            assert (
                transaction_status
                == FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR.transaction_status_description
            )
            assert (
                record_status
                == FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR.writeback_record_status
            )
            assert transaction_date.date() == now
        elif i_value in completed_check_payment_i_values:
            assert (
                transaction_status
                == FineosWritebackTransactionStatus.POSTED.transaction_status_description
            )
            assert record_status == FineosWritebackTransactionStatus.POSTED.writeback_record_status
            # We set the check posted date to 10 days past the extraction date
            assert transaction_date == extraction_date + timedelta(days=10)
        elif i_value in completed_eft_payment_i_values:
            assert (
                transaction_status
                == FineosWritebackTransactionStatus.POSTED.transaction_status_description
            )
            assert record_status == FineosWritebackTransactionStatus.POSTED.writeback_record_status
            assert transaction_date.date() == now
        else:
            assert (
                transaction_status
                == FineosWritebackTransactionStatus.PROCESSED.transaction_status_description
            )
            assert (
                record_status == FineosWritebackTransactionStatus.PROCESSED.writeback_record_status
            )
            assert transaction_date.date() == now


def test_process_payments_for_writeback_no_payments_ready_for_writeback(
    fineos_pei_writeback_step, test_db_session,
):
    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    for _i in range(fake.random_int(min=2, max=7)):
        _generate_payment_and_state(
            test_db_session, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT
        )

    fineos_pei_writeback_step.process_payments_for_writeback()

    # Did not create any ReferenceFile objects since we did not create any writeback files.
    reference_files = (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.PEI_WRITEBACK.reference_file_type_id
        )
        .all()
    )

    assert len(reference_files) == 0


@pytest.mark.parametrize(
    "zero_dollar_payment_count, overpayment_count, accepted_payment_count, cancelled_payment_count, errored_payment_count, add_check_payment_count",
    (
        # No payments in any of the states we want to pick up for the writeback.
        (0, 0, 0, 0, 0, 0),
        # Some payments in each state.
        (
            fake.random_int(min=3, max=5),
            fake.random_int(min=1, max=8),
            fake.random_int(min=2, max=6),
            fake.random_int(min=4, max=7),
            fake.random_int(min=2, max=6),
            fake.random_int(min=3, max=5),
        ),
    ),
    ids=["writeback", "payments"],
)
def test_get_writeback_items_for_state(
    fineos_pei_writeback_step,
    test_db_session,
    zero_dollar_payment_count,
    overpayment_count,
    accepted_payment_count,
    cancelled_payment_count,
    errored_payment_count,
    add_check_payment_count,
    caplog,
):
    # Create some small amount of Payments that are in a state other than the one we pick up
    # for the writeback.
    for _i in range(fake.random_int(min=2, max=7)):
        _generate_payment_and_state(
            test_db_session, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT
        )

    for _i in range(zero_dollar_payment_count):
        _generate_zero_dollar_payment(test_db_session)

    for _i in range(overpayment_count):
        _generate_overpayment(test_db_session)

    for _i in range(accepted_payment_count):
        _generate_accepted_payment(test_db_session, PaymentMethod.ACH)

    for _i in range(accepted_payment_count):
        _generate_accepted_payment(test_db_session, PaymentMethod.CHECK)

    for _i in range(cancelled_payment_count):
        _generate_cancelled_payment(test_db_session)

    for _i in range(errored_payment_count):
        _generate_errored_payment(test_db_session)

    for _i in range(add_check_payment_count):
        _generate_completed_check_payment(test_db_session)

    for _i in range(add_check_payment_count):
        _generate_completed_eft_payment_with_change_notification(test_db_session)

    payments_ready_for_writeback_count = (
        zero_dollar_payment_count
        + overpayment_count
        + (accepted_payment_count * 2)
        + cancelled_payment_count
        + errored_payment_count
        + (add_check_payment_count * 2)
    )
    writeback_records = fineos_pei_writeback_step.get_records_to_writeback()
    assert len(writeback_records) == payments_ready_for_writeback_count
