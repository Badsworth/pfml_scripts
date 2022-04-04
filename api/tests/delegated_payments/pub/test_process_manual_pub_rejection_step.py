import os
import pathlib

import pytest
from freezegun import freeze_time

from massgov.pfml.db.models.employees import (
    PrenoteState,
    PubError,
    PubErrorType,
    ReferenceFile,
    State,
)
from massgov.pfml.db.models.factories import ReferenceFileFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.db.models.state import Flow
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.pub.manual_pub_reject_file_parser import ManualPubReject
from massgov.pfml.delegated_payments.pub.process_manual_pub_rejection_step import (
    ProcessManualPubRejectionStep,
)
from massgov.pfml.util.batch.log import LogEntry
from tests.delegated_payments.pub import (
    assert_fineos_writeback_status,
    assert_payment_state,
    assert_pub_eft_prenote_state,
    assert_pub_error,
)


@pytest.fixture
def process_manual_pub_rejection_step(initialize_factories_session, test_db_session):
    step = ProcessManualPubRejectionStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )
    # Set these so they're non-null when running specific methods
    step.log_entry = LogEntry(test_db_session, "")
    step.reference_file = ReferenceFileFactory.create(file_location="test")
    return step


def test_process_manual_pub_reject_records_eft_currently_approved(
    process_manual_pub_rejection_step, test_db_session
):
    pub_eft = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123, prenote_state=PrenoteState.APPROVED
    ).get_or_create_pub_eft()

    reject_record = ManualPubReject(1, "E123,reject notes", "E123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    assert_pub_eft_prenote_state(
        test_db_session, pub_eft.pub_eft_id, PrenoteState.REJECTED, "reject notes"
    )

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_EFT_PROCESSED,
        f'EFT manually rejected with notes "{reject_record.notes}"',
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert (
        metrics[process_manual_pub_rejection_step.Metrics.REJECTED_EFT_CURRENTLY_APPROVED_COUNT]
        == 1
    )
    assert metrics[process_manual_pub_rejection_step.Metrics.EFT_REJECTED_SUCCESSFULLY_COUNT] == 1


def test_process_manual_pub_reject_records_eft_pending_with_pub(
    process_manual_pub_rejection_step, test_db_session
):
    pub_eft = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123, prenote_state=PrenoteState.PENDING_WITH_PUB
    ).get_or_create_pub_eft()

    reject_record = ManualPubReject(1, "E123,reject notes", "E123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    assert_pub_eft_prenote_state(
        test_db_session, pub_eft.pub_eft_id, PrenoteState.REJECTED, "reject notes"
    )

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_EFT_PROCESSED,
        f'EFT manually rejected with notes "{reject_record.notes}"',
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert (
        metrics[process_manual_pub_rejection_step.Metrics.REJECTED_EFT_PENDING_WITH_PUB_COUNT] == 1
    )
    assert metrics[process_manual_pub_rejection_step.Metrics.EFT_REJECTED_SUCCESSFULLY_COUNT] == 1


def test_process_manual_pub_reject_records_eft_already_rejected(
    process_manual_pub_rejection_step, test_db_session
):
    pub_eft = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123, prenote_state=PrenoteState.REJECTED
    ).get_or_create_pub_eft()

    reject_record = ManualPubReject(1, "E123,reject notes", "E123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    # Note this was already rejected, and not re-updated
    assert_pub_eft_prenote_state(test_db_session, pub_eft.pub_eft_id, PrenoteState.REJECTED)

    # No pub error
    assert len(test_db_session.query(PubError).all()) == 0

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert (
        metrics[process_manual_pub_rejection_step.Metrics.REJECTED_EFT_ALREADY_REJECTED_COUNT] == 1
    )


def test_process_manual_pub_reject_records_eft_pending_pre_pub(
    process_manual_pub_rejection_step, test_db_session
):
    pub_eft = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123, prenote_state=PrenoteState.PENDING_PRE_PUB
    ).get_or_create_pub_eft()

    reject_record = ManualPubReject(1, "E123,reject notes", "E123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    # State not changed.
    assert_pub_eft_prenote_state(test_db_session, pub_eft.pub_eft_id, PrenoteState.PENDING_PRE_PUB)

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_ERROR,
        "Unexpected existing prenote state - EFT has not been sent to PUB yet",
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert (
        metrics[process_manual_pub_rejection_step.Metrics.EFT_UNEXPECTED_PRENOTE_STATE_COUNT] == 1
    )


def test_process_manual_pub_reject_records_eft_not_found(
    process_manual_pub_rejection_step, test_db_session
):
    reject_record = ManualPubReject(1, "E123,reject notes", "E123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_ERROR,
        "PUB EFT individual ID not found in DB",
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert metrics[process_manual_pub_rejection_step.Metrics.EFT_ID_NOT_FOUND_COUNT] == 1


def test_process_manual_pub_reject_records_payment_eft_sent_state(
    process_manual_pub_rejection_step, test_db_session
):
    payment = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT)

    reject_notes = (
        FineosWritebackTransactionStatus.INVALID_ROUTING_NUMBER.transaction_status_description
    )
    reject_record = ManualPubReject(1, f"P123,{reject_notes}", "P123", reject_notes)
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    assert_fineos_writeback_status(
        payment, FineosWritebackTransactionStatus.INVALID_ROUTING_NUMBER, test_db_session
    )

    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        test_db_session,
    )

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_PAYMENT_PROCESSED,
        f'Payment manually rejected with notes "{reject_record.notes}"',
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert (
        metrics[process_manual_pub_rejection_step.Metrics.PAYMENT_REJECTED_SUCCESSFULLY_COUNT] == 1
    )


def test_process_manual_pub_reject_records_payment_change_notification_state(
    process_manual_pub_rejection_step, test_db_session
):
    payment = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION)

    reject_notes = (
        FineosWritebackTransactionStatus.INVALID_ROUTING_NUMBER.transaction_status_description
    )
    reject_record = ManualPubReject(1, f"P123,{reject_notes}", "P123", reject_notes)
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    assert_fineos_writeback_status(
        payment, FineosWritebackTransactionStatus.INVALID_ROUTING_NUMBER, test_db_session
    )

    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        test_db_session,
    )

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_PAYMENT_PROCESSED,
        f'Payment manually rejected with notes "{reject_record.notes}"',
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert (
        metrics[process_manual_pub_rejection_step.Metrics.PAYMENT_REJECTED_SUCCESSFULLY_COUNT] == 1
    )
    assert (
        metrics[
            process_manual_pub_rejection_step.Metrics.PAYMENT_SWITCHING_CHANGE_NOTIFICATION_TO_ERROR_COUNT
        ]
        == 1
    )


def test_process_manual_pub_reject_records_payment_already_errored_state(
    process_manual_pub_rejection_step, test_db_session
):
    payment = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ERROR_FROM_BANK)

    reject_record = ManualPubReject(1, "P123,reject notes", "P123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    # No writeback
    assert len(test_db_session.query(FineosWritebackDetails).all()) == 0

    # No state change
    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        test_db_session,
    )

    # No pub error
    assert len(test_db_session.query(PubError).all()) == 0

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert metrics[process_manual_pub_rejection_step.Metrics.PAYMENT_ALREADY_ERRORED_COUNT] == 1


def test_process_manual_pub_reject_records_payment_not_found(
    process_manual_pub_rejection_step, test_db_session
):
    reject_record = ManualPubReject(1, "P123,reject notes", "P123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_ERROR,
        "Payment individual ID not found in DB",
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert metrics[process_manual_pub_rejection_step.Metrics.PAYMENT_NOT_FOUND_COUNT] == 1


def test_process_manual_pub_reject_records_payment_not_in_expected_state(
    process_manual_pub_rejection_step, test_db_session
):
    # Payment state isn't an expected one
    payment = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_COMPLETE)
    reject_record = ManualPubReject(1, "P123,reject notes", "P123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    # No writeback
    assert len(test_db_session.query(FineosWritebackDetails).all()) == 0

    # No state change
    assert_payment_state(
        payment, Flow.DELEGATED_PAYMENT, State.DELEGATED_PAYMENT_COMPLETE, test_db_session
    )

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_ERROR,
        "Unexpected state for payment in manual invalidation file",
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert metrics[process_manual_pub_rejection_step.Metrics.UNEXPECTED_PAYMENT_STATE_COUNT] == 1


def test_process_manual_pub_reject_records_missing_reject_notes(
    process_manual_pub_rejection_step, test_db_session
):
    DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION)

    reject_record = ManualPubReject(1, "P123,", "P123", "")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    # No writeback
    writeback_details = test_db_session.query(FineosWritebackDetails).all()
    assert len(writeback_details) == 0

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_ERROR,
        "Empty reject note for payment",
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert metrics[process_manual_pub_rejection_step.Metrics.MISSING_REJECT_NOTES] == 1


def test_process_manual_pub_reject_records_missing_reject_notes_mapping(
    process_manual_pub_rejection_step, test_db_session
):
    DelegatedPaymentFactory(
        test_db_session, pub_individual_id=123
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION)

    reject_record = ManualPubReject(1, "P123,reject notes", "P123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    # No writeback
    writeback_details = test_db_session.query(FineosWritebackDetails).all()
    assert len(writeback_details) == 0

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_ERROR,
        "Missing reject note writeback status mapping for payment in manual invalidation file",
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert metrics[process_manual_pub_rejection_step.Metrics.MISSING_REJECT_NOTES_MAPPING] == 1


def test_process_manual_pub_reject_records_invalid_id(
    process_manual_pub_rejection_step, test_db_session
):
    # EFT records start with an E, payments with a P. B is unknown
    reject_record = ManualPubReject(1, "B123,reject notes", "B123", "reject notes")
    process_manual_pub_rejection_step.process_manual_pub_reject_records([reject_record])

    assert_pub_error(
        test_db_session,
        PubErrorType.MANUAL_PUB_REJECT_ERROR,
        "Could not determine what type of record to reject for manual PUB reject record",
    )

    metrics = process_manual_pub_rejection_step.log_entry.metrics
    assert metrics[process_manual_pub_rejection_step.Metrics.UNKNOWN_RECORD_COUNT] == 1


@freeze_time("2022-02-15 12:00:00", tz_offset=0)
def test_process_manual_pub_reject_step_full(
    initialize_factories_session,
    test_db_session,
    mock_s3_bucket_resource,
    monkeypatch,
):
    s3_base_path = f"s3://{mock_s3_bucket_resource.name}/pub/reject-files/"
    file_name = "manual_reject_file.csv"
    monkeypatch.setenv("PFML_MANUAL_PUB_REJECT_ARCHIVE_PATH", s3_base_path)

    test_files = pathlib.Path(__file__).parent / "test_files"
    mock_s3_bucket_resource.upload_file(
        str(test_files / file_name), "pub/reject-files/received/" + file_name
    )

    # Create a payment and EFT record that will be in the file in valid states
    payment = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=1
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT)

    pub_eft = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=2, prenote_state=PrenoteState.PENDING_WITH_PUB
    ).get_or_create_pub_eft()

    process_manual_pub_rejection_step = ProcessManualPubRejectionStep(
        test_db_session, test_db_session
    )

    assert process_manual_pub_rejection_step.have_more_files_to_process() is True
    process_manual_pub_rejection_step.run()
    assert process_manual_pub_rejection_step.have_more_files_to_process() is False

    # Make sure the reference file was created properly
    reference_files = test_db_session.query(ReferenceFile).order_by(ReferenceFile.created_at).all()
    assert len(reference_files) == 1
    assert reference_files[0].file_location == os.path.join(
        s3_base_path, "processed/2022-02-15", file_name
    )
    reference_file_id = reference_files[0].reference_file_id

    # Validate the payment state was updated
    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        test_db_session,
    )

    assert_fineos_writeback_status(
        payment, FineosWritebackTransactionStatus.INVALID_ROUTING_NUMBER, test_db_session
    )

    # Validate the PUB EFT state
    assert_pub_eft_prenote_state(
        test_db_session, pub_eft.pub_eft_id, PrenoteState.REJECTED, "invalid routing number"
    )

    errors = test_db_session.query(PubError).all()
    assert len(errors) == 5
    for error in errors:
        assert error.reference_file_id == reference_file_id

    # The payment above
    assert errors[0].line_number == 2
    assert errors[0].payment_id == payment.payment_id
    assert errors[0].pub_eft_id is None
    assert errors[0].message == 'Payment manually rejected with notes "Invalid Routing Number"'
    assert (
        errors[0].pub_error_type_id
        == PubErrorType.MANUAL_PUB_REJECT_PAYMENT_PROCESSED.pub_error_type_id
    )

    # The PUB EFT above
    assert errors[1].line_number == 3
    assert errors[1].payment_id is None
    assert errors[1].pub_eft_id == pub_eft.pub_eft_id
    assert errors[1].message == 'EFT manually rejected with notes "invalid routing number"'
    assert (
        errors[1].pub_error_type_id
        == PubErrorType.MANUAL_PUB_REJECT_EFT_PROCESSED.pub_error_type_id
    )

    # Invalid code X3 doesn't correspond to payment or EFT
    assert errors[2].line_number == 4
    assert errors[2].payment_id is None
    assert errors[2].pub_eft_id is None
    assert (
        errors[2].message
        == "Could not determine what type of record to reject for manual PUB reject record"
    )
    assert errors[2].pub_error_type_id == PubErrorType.MANUAL_PUB_REJECT_ERROR.pub_error_type_id

    # Payment ID format, but payment doesn't exist
    assert errors[3].line_number == 5
    assert errors[3].payment_id is None
    assert errors[3].pub_eft_id is None
    assert errors[3].message == "Payment individual ID not found in DB"
    assert errors[3].pub_error_type_id == PubErrorType.MANUAL_PUB_REJECT_ERROR.pub_error_type_id

    # EFT ID format, but EFT doesn't exist
    assert errors[4].line_number == 6
    assert errors[4].payment_id is None
    assert errors[4].pub_eft_id is None
    assert errors[4].message == "PUB EFT individual ID not found in DB"
    assert errors[4].pub_error_type_id == PubErrorType.MANUAL_PUB_REJECT_ERROR.pub_error_type_id


@freeze_time("2022-02-15 12:00:00", tz_offset=0)
def test_process_manual_pub_reject_step_full_with_odd_encoding(
    initialize_factories_session,
    test_db_session,
    mock_s3_bucket_resource,
    monkeypatch,
):
    # The file we are parsing has a <U+FEFF> character at the start
    s3_base_path = f"s3://{mock_s3_bucket_resource.name}/pub/reject-files/"
    file_name = "odd_encoding_manual_reject_file.csv"
    monkeypatch.setenv("PFML_MANUAL_PUB_REJECT_ARCHIVE_PATH", s3_base_path)

    test_files = pathlib.Path(__file__).parent / "test_files"
    mock_s3_bucket_resource.upload_file(
        str(test_files / file_name), "pub/reject-files/received/" + file_name
    )

    payment = DelegatedPaymentFactory(
        test_db_session, pub_individual_id=1
    ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT)

    process_manual_pub_rejection_step = ProcessManualPubRejectionStep(
        test_db_session, test_db_session
    )
    process_manual_pub_rejection_step.run()

    # Validate the payment state was updated
    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        test_db_session,
    )

    assert_fineos_writeback_status(
        payment, FineosWritebackTransactionStatus.PUB_PAYMENT_RETURNED, test_db_session
    )
