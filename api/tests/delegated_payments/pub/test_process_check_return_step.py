#
# Tests for class ProcessCheckReturnFileStep.
#

import datetime
import decimal
import pathlib

import freezegun
import pytest

import massgov.pfml.api.util.state_log_util
import massgov.pfml.util.batch.log
from massgov.pfml.db.models import factories
from massgov.pfml.db.models.employees import (
    Flow,
    Payment,
    PaymentCheck,
    PaymentCheckStatus,
    PaymentMethod,
    PaymentTransactionType,
    PubError,
    PubErrorType,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.pub import check_return, process_check_return_step
from massgov.pfml.delegated_payments.pub.check_return import PaidStatus


def check_payment_factory(
    status: PaidStatus, check_number: str = "501"
) -> check_return.CheckPayment:
    return check_return.CheckPayment(
        line_number=20,
        raw_line="abcd",
        check_number=check_number,
        payee_name="Test Aaa",
        status=status,
        paid_date=datetime.date(2021, 3, 22),
        amount=decimal.Decimal("101.75"),
    )


@pytest.fixture
def step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session,
):
    step = process_check_return_step.ProcessCheckReturnFileStep(
        local_test_db_session, local_test_db_other_session
    )
    step.log_entry = massgov.pfml.util.batch.log.LogEntry(local_test_db_other_session, "")
    step.reference_file = factories.ReferenceFileFactory.create(file_location="test")
    return step


@pytest.fixture
def payment(local_test_db_session, local_initialize_factories_session):
    return payment_by_check_sent_to_pub_factory(1, local_test_db_session)


@pytest.fixture
def payment_complete(local_test_db_session, local_initialize_factories_session):
    return payment_by_check_sent_to_pub_factory(
        1, local_test_db_session, State.DELEGATED_PAYMENT_COMPLETE
    )


@pytest.fixture
def payment_in_bad_state(local_test_db_session, local_initialize_factories_session):
    return payment_by_check_sent_to_pub_factory(
        1, local_test_db_session, State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT
    )


@pytest.fixture
def payment_without_state(local_test_db_session, local_initialize_factories_session):
    return payment_by_check_sent_to_pub_factory(1, local_test_db_session, None)


@pytest.fixture
def payment_state(payment, local_test_db_session):
    def get_state():
        return massgov.pfml.api.util.state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_session
        )

    return get_state


def assert_writeback_state_and_details(
    test_db_session, payment, writeback_expected, expected_transaction_status=None
):
    writeback_state = massgov.pfml.api.util.state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, test_db_session
    )

    writeback_details = (
        test_db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .one_or_none()
    )

    if not writeback_expected:
        assert writeback_state is None
        assert writeback_details is None
        return

    assert writeback_state
    assert writeback_state.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id
    assert writeback_state.outcome == {
        "message": expected_transaction_status.transaction_status_description
    }

    assert writeback_details
    assert (
        writeback_details.transaction_status_id == expected_transaction_status.transaction_status_id
    )


def test_process_single_check_payment_paid(step, payment, payment_state, local_test_db_session):
    step.process_single_check_payment(check_payment_factory(PaidStatus.PAID))

    assert payment.check.payment_check_status_id == PaymentCheckStatus.PAID.payment_check_status_id
    assert payment.check.check_posted_date == datetime.date(2021, 3, 22)
    assert payment_state().end_state_id == State.DELEGATED_PAYMENT_COMPLETE.state_id
    assert payment_state().outcome == {
        "check_line_number": "20",
        "check_paid_date": "2021-03-22",
        "message": "Payment complete by paid check",
    }
    step.log_entry.metrics["payment_complete_by_paid_check"] == 1

    assert_writeback_state_and_details(
        local_test_db_session, payment, True, FineosWritebackTransactionStatus.POSTED
    )


def test_process_single_check_payment_previously_paid(step, payment_complete):
    step.process_single_check_payment(check_payment_factory(PaidStatus.PAID))

    assert (
        payment_complete.check.payment_check_status_id
        == PaymentCheckStatus.PAID.payment_check_status_id
    )
    assert payment_complete.check.check_posted_date == datetime.date(2021, 3, 22)
    step.log_entry.metrics["payment_complete_by_paid_check"] == 1


@pytest.mark.parametrize("check_status", (PaidStatus.OUTSTANDING, PaidStatus.FUTURE))
def test_process_single_check_payment_outstanding(
    step, payment, payment_state, local_test_db_session, check_status
):
    step.process_single_check_payment(check_payment_factory(check_status))

    assert payment.check.payment_check_status_id is None
    assert payment.check.check_posted_date is None
    assert (
        payment_state().end_state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id
    )
    assert_writeback_state_and_details(local_test_db_session, payment, False)

    step.log_entry.metrics["payment_still_outstanding"] == 1


@pytest.mark.parametrize(
    "check_status, expected_payment_check_status",
    (
        (PaidStatus.STALE, PaymentCheckStatus.STALE),
        (PaidStatus.STOP, PaymentCheckStatus.STOP),
        (PaidStatus.VOID, PaymentCheckStatus.VOID),
    ),
)
def test_process_single_check_payment_failed(
    payment,
    payment_state,
    check_status,
    expected_payment_check_status,
    local_test_db_session,
    local_test_db_other_session,
    step,
):
    step.process_single_check_payment(check_payment_factory(check_status))

    assert (
        payment.check.payment_check_status_id
        == expected_payment_check_status.payment_check_status_id
    )
    assert payment.check.check_posted_date is None
    assert payment_state().end_state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id
    assert payment_state().outcome == {
        "check_line_number": "20",
        "check_status": check_status.name,
        "message": "Payment failed by check status " + check_status.name,
    }
    assert_writeback_state_and_details(
        local_test_db_session, payment, True, FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR
    )

    pub_error = local_test_db_session.query(PubError).one_or_none()
    assert pub_error.pub_error_type_id == PubErrorType.CHECK_PAYMENT_FAILED.pub_error_type_id
    assert pub_error.message == "payment failed by check: " + check_status.name
    assert pub_error.line_number == 20
    assert pub_error.raw_data == "abcd"
    assert pub_error.details == {"check_number": "501", "status": check_status.name}
    assert pub_error.payment_id == payment.payment_id


def test_process_single_check_payment_not_found(step, payment, local_test_db_session):
    step.process_single_check_payment(check_payment_factory(PaidStatus.PAID, "999"))

    step.log_entry.metrics["check_number_not_found_count"] == 1

    pub_error = local_test_db_session.query(PubError).one_or_none()
    assert pub_error.pub_error_type_id == PubErrorType.CHECK_PAYMENT_ERROR.pub_error_type_id
    assert pub_error.message == "check number not in payment table"
    assert pub_error.line_number == 20
    assert pub_error.raw_data == "abcd"
    assert pub_error.details == {"check_number": "999"}
    assert pub_error.payment_id is None


def test_process_single_check_payment_in_wrong_state(
    step, payment_in_bad_state, local_test_db_session
):
    step.process_single_check_payment(check_payment_factory(PaidStatus.PAID))

    step.log_entry.metrics["payment_unexpected_state_count"] == 1

    pub_error = local_test_db_session.query(PubError).one_or_none()
    assert pub_error.pub_error_type_id == PubErrorType.CHECK_PAYMENT_ERROR.pub_error_type_id
    assert pub_error.message == "unexpected state for payment: Add to Payment Audit Report (129)"
    assert pub_error.line_number == 20
    assert pub_error.raw_data == "abcd"
    assert pub_error.details == {"check_number": "501"}
    assert pub_error.payment_id == payment_in_bad_state.payment_id


def test_process_single_check_payment_without_state(
    step, payment_without_state, local_test_db_session
):
    step.process_single_check_payment(check_payment_factory(PaidStatus.PAID))

    step.log_entry.metrics["payment_unexpected_state_count"] == 1

    pub_error = local_test_db_session.query(PubError).one_or_none()
    assert pub_error.pub_error_type_id == PubErrorType.CHECK_PAYMENT_ERROR.pub_error_type_id
    assert pub_error.message == "unexpected state for payment: NONE (None)"
    assert pub_error.line_number == 20
    assert pub_error.raw_data == "abcd"
    assert pub_error.details == {"check_number": "501"}
    assert pub_error.payment_id == payment_without_state.payment_id


@freezegun.freeze_time("2021-04-12 08:00:00", tz_offset=0)
def test_process_check_return_step_full(
    local_test_db_session,
    local_test_db_other_session,
    local_initialize_factories_session,
    mock_s3_bucket_resource,
):
    # Note: see check_outstanding_small.csv and check_paid_small.csv to understand this test.

    # Copy test files to mock S3 bucket.
    test_files = pathlib.Path(__file__).parent / "test_files"
    for name in ("check_outstanding_small.csv", "check_paid_small.csv"):
        mock_s3_bucket_resource.upload_file(str(test_files / name), "received/" + name)

    # Add payments 1 to 9 to the database. These correspond to check numbers 501 to 509 in return
    # files.
    payments = [
        payment_by_check_sent_to_pub_factory(i, local_test_db_other_session) for i in range(1, 10)
    ]

    # Run step.
    process_return_file_step = process_check_return_step.ProcessCheckReturnFileStep(
        local_test_db_session,
        local_test_db_other_session,
        "s3://%s/" % mock_s3_bucket_resource.name,
    )
    assert process_return_file_step.have_more_files_to_process() is True
    process_return_file_step.run()
    assert process_return_file_step.have_more_files_to_process() is True
    process_return_file_step.run()
    assert process_return_file_step.have_more_files_to_process() is False

    # Test updates to reference_file table.
    reference_files = (
        local_test_db_other_session.query(ReferenceFile).order_by(ReferenceFile.created_at).all()
    )
    assert len(reference_files) == 2
    for reference_file in reference_files:
        assert (
            reference_file.reference_file_type_id
            == ReferenceFileType.PUB_CHECK_RETURN.reference_file_type_id
        )
    processed_dir = "s3://%s/processed/2021-04-12" % mock_s3_bucket_resource.name
    assert reference_files[0].file_location == processed_dir + "/check_outstanding_small.csv"
    assert reference_files[1].file_location == processed_dir + "/check_paid_small.csv"

    # Payment states.
    expected_states = {
        501: (
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            None,
            None,
            reference_files[0],
            2,
        ),
        502: (
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            None,
            None,
            reference_files[0],
            3,
        ),
        503: (
            State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            "STALE",
            reference_files[0],
            4,
        ),
        504: (
            State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            "STOP",
            reference_files[0],
            5,
        ),
        505: (
            State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            "VOID",
            reference_files[0],
            6,
        ),
        506: (
            State.DELEGATED_PAYMENT_COMPLETE,
            State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            None,
            reference_files[1],
            3,
        ),
        507: (
            State.DELEGATED_PAYMENT_COMPLETE,
            State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            None,
            reference_files[1],
            4,
        ),
    }
    for payment in payments:
        local_test_db_other_session.refresh(payment)
        payment_state_log = massgov.pfml.api.util.state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_other_session
        )
        state_id = payment_state_log.end_state.state_id

        writeback_state_log = massgov.pfml.api.util.state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PEI_WRITEBACK, local_test_db_other_session
        )
        writeback_state_id = writeback_state_log.end_state.state_id if writeback_state_log else None
        if payment.check.check_number in expected_states:
            (
                expected_state,
                expected_writeback_state,
                expected_status,
                expected_reference_file,
                expected_line_num,
            ) = expected_states[payment.check.check_number]
            assert state_id == expected_state.state_id
            if expected_writeback_state:
                assert writeback_state_id == expected_writeback_state.state_id
            else:
                assert writeback_state_id is None

            if expected_status:
                assert payment_state_log.outcome["check_status"] == expected_status
                assert payment_state_log.outcome["check_line_number"] == str(expected_line_num)
            assert len(payment.reference_files) == 1
            assert payment.reference_files[0].reference_file == expected_reference_file

            if expected_writeback_state:
                writeback_details = (
                    local_test_db_session.query(FineosWritebackDetails)
                    .filter(FineosWritebackDetails.payment_id == payment.payment_id)
                    .one_or_none()
                )
                assert writeback_details

                transaction_status_id = writeback_details.transaction_status_id
                if expected_state.state_id == State.DELEGATED_PAYMENT_ERROR_FROM_BANK.state_id:
                    assert (
                        transaction_status_id
                        == FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR.transaction_status_id
                    )
                else:
                    assert (
                        transaction_status_id
                        == FineosWritebackTransactionStatus.POSTED.transaction_status_id
                    )

        else:
            # Not in test files - state unchanged.
            assert state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT.state_id
            assert payment.reference_files == []

    errors = local_test_db_other_session.query(PubError).all()
    assert len(errors) == 6
    assert errors[0].reference_file == reference_files[0]
    assert errors[0].line_number == 4
    assert errors[0].message == "payment failed by check: STALE"
    assert errors[0].details == {"check_number": "503", "status": "STALE"}
    assert errors[1].reference_file == reference_files[0]
    assert errors[1].line_number == 5
    assert errors[1].message == "payment failed by check: STOP"
    assert errors[1].details == {"check_number": "504", "status": "STOP"}
    assert errors[2].reference_file == reference_files[0]
    assert errors[2].line_number == 6
    assert errors[2].message == "payment failed by check: VOID"
    assert errors[2].details == {"check_number": "505", "status": "VOID"}
    assert errors[3].reference_file == reference_files[0]
    assert errors[3].line_number == 7
    assert errors[3].message == "check number not in payment table"
    assert errors[3].details == {"check_number": "999"}
    assert errors[4].reference_file == reference_files[1]
    assert errors[4].line_number == 4
    assert errors[4].message == "invalid date"
    assert errors[4].details == {}
    assert errors[5].reference_file == reference_files[1]
    assert errors[5].line_number == 2
    assert errors[5].message == "unexpected state for payment: Payment Errored from Bank (182)"
    assert errors[5].details == {"check_number": "505"}


def payment_by_check_sent_to_pub_factory(
    pub_individual_id,
    local_test_db_session,
    end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
) -> Payment:
    employee = factories.EmployeeFactory.create()
    employer = factories.EmployerFactory.create()
    factories.WagesAndContributionsFactory.create(employer=employer, employee=employee)

    payment = Payment(
        payment_transaction_type_id=PaymentTransactionType.STANDARD.payment_transaction_type_id,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.75 + pub_individual_id,
        fineos_pei_c_value=42424,
        fineos_pei_i_value=10000 + pub_individual_id,
        fineos_extraction_date=datetime.date(2021, 3, 24),
        disb_method_id=PaymentMethod.CHECK.payment_method_id,
        pub_individual_id=pub_individual_id,
        check=PaymentCheck(check_number=500 + pub_individual_id),
    )
    local_test_db_session.add(payment)

    local_test_db_session.commit()

    if end_state is not None:
        massgov.pfml.api.util.state_log_util.create_finished_state_log(
            end_state=end_state,
            associated_model=payment,
            db_session=local_test_db_session,
            outcome=massgov.pfml.api.util.state_log_util.build_outcome("Generated state"),
        )

    return payment
