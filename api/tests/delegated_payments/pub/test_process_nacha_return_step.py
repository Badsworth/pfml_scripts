#
# Tests for class ProcessReturnFileStep.
#

import datetime
import io
import pathlib
import uuid
from collections import Counter

import pytest

import massgov.pfml.api.util.state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models import factories
from massgov.pfml.db.models.employees import (
    BankAccountType,
    Claim,
    ClaimType,
    EmployeePubEftPair,
    Flow,
    ImportLog,
    Payment,
    PaymentMethod,
    PaymentTransactionType,
    PrenoteState,
    PubEft,
    PubError,
    PubErrorType,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.db.models.factories import PaymentFactory, PubEftFactory, ReferenceFileFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.pub import process_nacha_return_step
from massgov.pfml.delegated_payments.util.ach.reader import (
    ACHChangeNotification,
    ACHReader,
    ACHReturn,
    RawRecord,
    TypeCode,
)
from massgov.pfml.util.batch.log import LogEntry

# == Utils ==


@pytest.fixture
def mock_ach_reader():
    ach_reader = ACHReader(io.StringIO(""), parse=False)
    return ach_reader


@pytest.fixture
def process_return_step(
    local_test_db_session, local_test_db_other_session, local_initialize_factories_session
):
    process_return_step = process_nacha_return_step.ProcessNachaReturnFileStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )
    process_return_step.log_entry = LogEntry(local_test_db_other_session, "Test")
    process_return_step.reference_file = ReferenceFileFactory.create(
        reference_file_type_id=ReferenceFileType.PUB_ACH_RETURN.reference_file_type_id
    )
    return process_return_step


def create_ach_return(id_number, type_code, reason_code, line_number=1, data="Test Data"):
    raw_record = RawRecord(type_code=type_code, line_number=line_number, data=data)
    ach_return = ACHReturn(
        id_number=id_number,
        return_reason_code=reason_code,
        original_dfi_id="444000000",
        dfi_account_number="3030000000",
        amount="0.00",
        name="Jane Smith",
        line_number=line_number,
        raw_record=raw_record,
    )
    return ach_return


def create_ach_change_notification(
    id_number,
    type_code,
    reason_code,
    line_number=1,
    data="Test Data",
    addenda_information="Test Addenda",
):
    raw_record = RawRecord(type_code=type_code, line_number=line_number, data=data)
    ach_change_notification = ACHChangeNotification(
        id_number=id_number,
        return_reason_code=reason_code,
        original_dfi_id="444000000",
        dfi_account_number="3030000000",
        amount="0.00",
        name="Jane Smith",
        line_number=line_number,
        raw_record=raw_record,
        addenda_information=addenda_information,
    )
    return ach_change_notification


def pub_eft_with_state_factory(
    pub_individual_id, prenote_state, employee_end_state, test_db_session
):
    employee = factories.EmployeeFactory.create()
    pub_eft = PubEft(
        routing_nbr="%09d" % (444000000 + pub_individual_id),
        account_nbr="%011d" % (3030000000 + pub_individual_id),
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        prenote_state_id=prenote_state.prenote_state_id,
        pub_individual_id=pub_individual_id,
    )
    test_db_session.add(pub_eft)
    employee.pub_efts.append(EmployeePubEftPair(pub_eft=pub_eft))

    test_db_session.commit()

    massgov.pfml.api.util.state_log_util.create_finished_state_log(
        end_state=employee_end_state,
        associated_model=employee,
        db_session=test_db_session,
        outcome=massgov.pfml.api.util.state_log_util.build_outcome(
            f"Generated state {prenote_state.prenote_state_description}"
        ),
    )

    test_db_session.refresh(pub_eft)

    return pub_eft


def pub_eft_pending_with_pub_factory(pub_individual_id, test_db_session):
    return pub_eft_with_state_factory(
        pub_individual_id,
        PrenoteState.PENDING_WITH_PUB,
        State.DELEGATED_EFT_PRENOTE_SENT,
        test_db_session,
    )


def payment_with_state_factory(pub_individual_id, payment_end_state, test_db_session):
    employee = factories.EmployeeFactory.create()
    employer = factories.EmployerFactory.create()

    pub_eft = PubEft(
        routing_nbr="%09d" % (444000000 + pub_individual_id),
        account_nbr="%011d" % (3030000000 + pub_individual_id),
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        prenote_state_id=PrenoteState.APPROVED.prenote_state_id,
        pub_individual_id=pub_individual_id,
    )
    test_db_session.add(pub_eft)
    employee.pub_efts.append(EmployeePubEftPair(pub_eft=pub_eft))

    claim = Claim(
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        employer=employer,
        employee=employee,
        fineos_absence_id="NTN-9900%s-ABS-1" % pub_individual_id,
    )
    test_db_session.add(claim)

    payment = Payment(
        payment_transaction_type_id=PaymentTransactionType.STANDARD.payment_transaction_type_id,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.75 + pub_individual_id,
        fineos_pei_c_value=42424,
        fineos_pei_i_value=10000 + pub_individual_id,
        fineos_extraction_date=datetime.date(2021, 3, 24),
        disb_method_id=PaymentMethod.ACH.payment_method_id,
        pub_eft=pub_eft,
        claim=claim,
        pub_individual_id=pub_individual_id,
    )
    test_db_session.add(payment)

    test_db_session.commit()

    massgov.pfml.api.util.state_log_util.create_finished_state_log(
        end_state=payment_end_state,
        associated_model=payment,
        db_session=test_db_session,
        outcome=massgov.pfml.api.util.state_log_util.build_outcome(
            "Generated state DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT"
        ),
    )

    return payment


def payment_sent_to_pub_factory(pub_individual_id, test_db_session):
    return payment_with_state_factory(
        pub_individual_id, State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT, test_db_session
    )


# == Tests ==


def test_add_pub_error(
    test_db_session, monkeypatch, tmp_path, initialize_factories_session, test_db_other_session
):
    monkeypatch.setenv("PFML_PUB_ACH_ARCHIVE_PATH", str(tmp_path))

    step = process_nacha_return_step.ProcessNachaReturnFileStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    # error if log entry has not been set (i.e. process has not been run)
    with pytest.raises(
        Exception, match="object has no log entry set",
    ):
        step.add_pub_error(PubErrorType.ACH_RETURN, "test", 2, "", 6)

    step.log_entry = LogEntry(test_db_session, "Test")

    # error if reference file has not been set (i.e. process has not been run)
    with pytest.raises(
        AttributeError,
        match="'ProcessNachaReturnFileStep' object has no attribute 'reference_file",
    ):
        step.add_pub_error(PubErrorType.ACH_RETURN, "test", 2, "", 6)

    # add reference file and log entry
    reference_file = ReferenceFile(
        file_location=str(tmp_path),
        reference_file_type_id=ReferenceFileType.PUB_ACH_RETURN.reference_file_type_id,
        reference_file_id=uuid.uuid4(),
    )
    step.reference_file = reference_file
    test_db_session.add(reference_file)

    test_db_session.commit()

    details = {"foo": "bar"}
    raw_data = "62244400000303030000003      0000010375P3             Stephens John           1221172180000002"

    # no payment or pub_eft
    pub_error = step.add_pub_error(PubErrorType.ACH_RETURN, "test", 2, raw_data, 6, details=details)

    assert pub_error.pub_error_type_id == PubErrorType.ACH_RETURN.pub_error_type_id
    assert pub_error.message == "test"
    assert pub_error.line_number == 2
    assert pub_error.type_code == 6
    assert pub_error.raw_data == raw_data
    assert pub_error.details == details
    assert pub_error.import_log_id == test_db_session.query(ImportLog).one_or_none().import_log_id
    assert pub_error.reference_file_id == step.reference_file.reference_file_id
    assert pub_error.created_at is not None
    assert pub_error.payment_id is None
    assert pub_error.pub_eft is None

    # no details
    pub_error = step.add_pub_error(PubErrorType.ACH_RETURN, "test", 2, raw_data, 6)
    assert pub_error.details == {}

    # with payment
    payment = PaymentFactory.create()
    pub_error = step.add_pub_error(
        PubErrorType.ACH_RETURN, "test", 2, raw_data, 6, details=details, payment=payment
    )
    assert pub_error.payment_id == payment.payment_id

    # with pub_eft
    pub_eft = PubEftFactory.create()
    pub_error = step.add_pub_error(
        PubErrorType.ACH_RETURN, "test", 2, raw_data, 6, details=details, pub_eft=pub_eft
    )
    assert pub_error.pub_eft_id == pub_eft.pub_eft_id


def test_ach_warnings(local_test_db_session, process_return_step, mock_ach_reader):
    raw_record_1 = RawRecord(type_code=TypeCode.ENTRY_DETAIL, line_number=1, data="Test Data")
    mock_ach_reader.add_warning(raw_record_1, "Test Warning")

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_error(local_test_db_session, PubErrorType.ACH_WARNING, "Test Warning")

    metrics = process_return_step.log_entry.metrics
    assert metrics["warning_count"] == 1


def test_unknown_return_id_format(local_test_db_session, process_return_step, mock_ach_reader):
    # Unknown return id format
    ach_return = create_ach_return("X123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_error(
        local_test_db_session, PubErrorType.ACH_RETURN, "id number not in known PFML formats"
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["unknown_id_format_count"] == 1


def test_prenote_eft_not_found(local_test_db_session, process_return_step, mock_ach_reader):
    ach_return = create_ach_return("E123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_error(
        local_test_db_session, PubErrorType.ACH_PRENOTE, "id number not in pub_eft table"
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["eft_prenote_id_not_found_count"] == 1


def test_prenote_pending_pre_pub(local_test_db_session, process_return_step, mock_ach_reader):
    pub_eft_with_state_factory(
        123, PrenoteState.PENDING_PRE_PUB, State.DELEGATED_EFT_SEND_PRENOTE, local_test_db_session
    )

    ach_return = create_ach_return("E123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_error(
        local_test_db_session,
        PubErrorType.ACH_PRENOTE,
        f"Unexpected existing prenote state: {PrenoteState.PENDING_PRE_PUB.prenote_state_description}",
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["eft_prenote_unexpected_state_count"] == 1


def test_prenote_rejected(local_test_db_session, process_return_step, mock_ach_reader):
    pub_eft_with_state_factory(
        123, PrenoteState.REJECTED, State.DELEGATED_EFT_PRENOTE_SENT, local_test_db_session
    )

    ach_return = create_ach_return("E123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_error(
        local_test_db_session,
        PubErrorType.ACH_PRENOTE,
        f"Unexpected existing prenote state: {PrenoteState.REJECTED.prenote_state_description}",
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["eft_prenote_already_rejected_count"] == 1


def test_prenote_return_pending_with_pub(
    local_test_db_session, process_return_step, mock_ach_reader
):
    pub_eft = pub_eft_with_state_factory(
        123, PrenoteState.PENDING_WITH_PUB, State.DELEGATED_EFT_PRENOTE_SENT, local_test_db_session
    )

    ach_return = create_ach_return("E123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_eft_prenote_state(local_test_db_session, pub_eft.pub_eft_id, PrenoteState.REJECTED)

    assert_pub_error(
        local_test_db_session,
        PubErrorType.ACH_PRENOTE,
        f"Rejected from existing state: {PrenoteState.PENDING_WITH_PUB.prenote_state_description}.",
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["eft_prenote_rejected_count"] == 1


def test_prenote_return_approved(local_test_db_session, process_return_step, mock_ach_reader):
    pub_eft = pub_eft_with_state_factory(
        123, PrenoteState.APPROVED, State.DELEGATED_EFT_PRENOTE_SENT, local_test_db_session
    )

    ach_return = create_ach_return("E123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_eft_prenote_state(local_test_db_session, pub_eft.pub_eft_id, PrenoteState.REJECTED)

    assert_pub_error(
        local_test_db_session,
        PubErrorType.ACH_PRENOTE,
        f"Rejected from existing state: {PrenoteState.APPROVED.prenote_state_description}.",
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["eft_prenote_rejected_count"] == 1


def test_prenote_change_notification_pending_with_pub(
    local_test_db_session, process_return_step, mock_ach_reader
):
    pub_eft = pub_eft_with_state_factory(
        123, PrenoteState.PENDING_WITH_PUB, State.DELEGATED_EFT_PRENOTE_SENT, local_test_db_session
    )

    ach_change_notification = create_ach_change_notification("E123", TypeCode.ENTRY_DETAIL, "C01")
    mock_ach_reader.change_notifications.append(ach_change_notification)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_eft_prenote_state(local_test_db_session, pub_eft.pub_eft_id, PrenoteState.APPROVED)

    assert_pub_error(
        local_test_db_session,
        PubErrorType.ACH_PRENOTE,
        f"Approved with change notification from existing state: {PrenoteState.PENDING_WITH_PUB.prenote_state_description}. {ach_change_notification.addenda_information}",
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["change_notification_count"] == 1
    assert metrics["eft_prenote_change_notification_count"] == 1


def test_prenote_change_notification_already_approved(
    local_test_db_session, process_return_step, mock_ach_reader
):
    pub_eft = pub_eft_with_state_factory(
        123, PrenoteState.APPROVED, State.DELEGATED_EFT_PRENOTE_SENT, local_test_db_session
    )

    ach_change_notification = create_ach_change_notification("E123", TypeCode.ENTRY_DETAIL, "C01")
    mock_ach_reader.change_notifications.append(ach_change_notification)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_eft_prenote_state(local_test_db_session, pub_eft.pub_eft_id, PrenoteState.APPROVED)

    assert_pub_error(
        local_test_db_session,
        PubErrorType.ACH_PRENOTE,
        f"Approved with change notification from existing state: {PrenoteState.APPROVED.prenote_state_description}. {ach_change_notification.addenda_information}",
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["change_notification_count"] == 1
    assert metrics["eft_prenote_change_notification_count"] == 1


def test_payment_not_found(local_test_db_session, process_return_step, mock_ach_reader):
    ach_return = create_ach_return("P123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_pub_error(
        local_test_db_session, PubErrorType.ACH_RETURN, "id number not in payment table"
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["payment_id_not_found_count"] == 1


def test_payment_change_notification_pub_transaction_sent(
    local_test_db_session, process_return_step, mock_ach_reader
):
    payment = payment_with_state_factory(
        123, State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT, local_test_db_session
    )

    ach_change_notification = create_ach_change_notification("P123", TypeCode.ENTRY_DETAIL, "C01")
    mock_ach_reader.change_notifications.append(ach_change_notification)

    process_return_step.process_parsed(mock_ach_reader)

    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
        local_test_db_session,
    )
    assert_payment_state(
        payment,
        Flow.DELEGATED_PEI_WRITEBACK,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        local_test_db_session,
    )

    assert_fineos_writeback_status(
        payment, FineosWritebackTransactionStatus.POSTED, local_test_db_session
    )

    assert_pub_error(
        local_test_db_session,
        PubErrorType.ACH_SUCCESS_WITH_NOTIFICATION,
        "Payment complete with change notification",
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["change_notification_count"] == 1
    assert metrics["payment_complete_with_change_count"] == 1


def test_payment_change_notification_already_complete_with_change_notification(
    local_test_db_session, process_return_step, mock_ach_reader
):
    payment = payment_with_state_factory(
        123, State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION, local_test_db_session
    )

    ach_change_notification = create_ach_change_notification("P123", TypeCode.ENTRY_DETAIL, "C01")
    mock_ach_reader.change_notifications.append(ach_change_notification)

    process_return_step.process_parsed(mock_ach_reader)

    # No state change
    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
        local_test_db_session,
    )

    # No writeback
    assert len(local_test_db_session.query(FineosWritebackDetails).all()) == 0

    # No pub error
    assert len(local_test_db_session.query(PubError).all()) == 0

    metrics = process_return_step.log_entry.metrics
    assert metrics["change_notification_count"] == 1
    assert metrics["payment_already_complete_count"] == 1


def test_payment_change_notification_current_payment_end_state_invalid(
    local_test_db_session, process_return_step, mock_ach_reader
):
    payment = payment_with_state_factory(
        123, State.DELEGATED_PAYMENT_COMPLETE, local_test_db_session
    )

    ach_change_notification = create_ach_change_notification("P123", TypeCode.ENTRY_DETAIL, "C01")
    mock_ach_reader.change_notifications.append(ach_change_notification)

    process_return_step.process_parsed(mock_ach_reader)

    assert_payment_state(
        payment, Flow.DELEGATED_PAYMENT, State.DELEGATED_PAYMENT_COMPLETE, local_test_db_session
    )

    assert_pub_error(
        local_test_db_session, PubErrorType.ACH_NOTIFICATION, "unexpected state for payment"
    )

    metrics = process_return_step.log_entry.metrics
    assert metrics["change_notification_count"] == 1
    assert metrics["payment_notification_unexpected_state_count"] == 1


def test_payment_return_pub_transaction_sent(
    local_test_db_session, process_return_step, mock_ach_reader
):
    payment = payment_with_state_factory(
        123, State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT, local_test_db_session
    )

    ach_return = create_ach_return("P123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        local_test_db_session,
    )
    assert_payment_state(
        payment,
        Flow.DELEGATED_PEI_WRITEBACK,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        local_test_db_session,
    )

    assert_fineos_writeback_status(
        payment, FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR, local_test_db_session
    )

    assert_pub_error(local_test_db_session, PubErrorType.ACH_RETURN, "Payment rejected by PUB")

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["payment_rejected_count"] == 1


def test_payment_return_already_errored(
    local_test_db_session, process_return_step, mock_ach_reader
):
    payment = payment_with_state_factory(
        123, State.DELEGATED_PAYMENT_ERROR_FROM_BANK, local_test_db_session
    )

    ach_return = create_ach_return("P123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    # No state change
    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        local_test_db_session,
    )

    # No writeback
    assert len(local_test_db_session.query(FineosWritebackDetails).all()) == 0

    # No pub error
    assert len(local_test_db_session.query(PubError).all()) == 0

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["payment_already_rejected_count"] == 1


def test_payment_return_invalid_current_state(
    local_test_db_session, process_return_step, mock_ach_reader
):
    payment = payment_with_state_factory(
        123, State.DELEGATED_PAYMENT_COMPLETE, local_test_db_session
    )

    ach_return = create_ach_return("P123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    # No state change
    assert_payment_state(
        payment, Flow.DELEGATED_PAYMENT, State.DELEGATED_PAYMENT_COMPLETE, local_test_db_session
    )

    assert_pub_error(local_test_db_session, PubErrorType.ACH_RETURN, "unexpected state for payment")

    metrics = process_return_step.log_entry.metrics
    assert metrics["ach_return_count"] == 1
    assert metrics["payment_unexpected_state_count"] == 1


def test_payment_return_pub_transaction_sent_duplicate_record(
    local_test_db_session, process_return_step, mock_ach_reader
):
    payment = payment_with_state_factory(
        123, State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT, local_test_db_session
    )

    # Verify that if we receive duplicate records, the process behaves fine
    ach_return = create_ach_return("P123", TypeCode.ENTRY_DETAIL, "R01")
    mock_ach_reader.ach_returns.append(ach_return)
    mock_ach_reader.ach_returns.append(ach_return)
    mock_ach_reader.ach_returns.append(ach_return)

    process_return_step.process_parsed(mock_ach_reader)

    assert_payment_state(
        payment,
        Flow.DELEGATED_PAYMENT,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        local_test_db_session,
    )
    assert_payment_state(
        payment,
        Flow.DELEGATED_PEI_WRITEBACK,
        State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
        local_test_db_session,
    )

    assert_fineos_writeback_status(
        payment, FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR, local_test_db_session
    )

    assert_pub_error(local_test_db_session, PubErrorType.ACH_RETURN, "Payment rejected by PUB")


def test_process_nacha_return_file_step_full(
    local_test_db_session,
    monkeypatch,
    tmp_path,
    local_initialize_factories_session,
    local_test_db_other_session,
):
    # Note: see ach_return_small.ach to understand this test. That file contains a mix of prenote
    # and payment returns, with some being ACH Returns (errors) and some Change Notifications.
    #
    # This test case creates matching pub_eft rows (prenotes) and payments for a subset of the
    # items in ach_return_small.ach. Some are intentionally excluded to test error paths.

    # Build directory structure with test file.
    monkeypatch.setenv("PFML_PUB_ACH_ARCHIVE_PATH", str(tmp_path))
    test_files = pathlib.Path(__file__).parent / "test_files"

    source_file_path = str(test_files / "ach_return_small.ach")
    destination_file_path = str(tmp_path / "received" / "ach_return_small.ach")
    file_util.copy_file(source_file_path, destination_file_path)

    # Add prenotes 0 to 39 to database. These correspond to E0 to E39 ids in return file.
    pub_efts = [pub_eft_pending_with_pub_factory(i, local_test_db_session) for i in range(40)]

    # Add payments 40 to 79 to the database. These correspond to P40 to P79 ids in return file.
    payments = [payment_sent_to_pub_factory(i, local_test_db_session) for i in range(40, 80)]

    # Run step.
    process_nacha_file_step = process_nacha_return_step.ProcessNachaReturnFileStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )
    assert process_nacha_file_step.have_more_files_to_process() is True
    process_nacha_file_step.run()
    assert process_nacha_file_step.have_more_files_to_process() is False

    # Test updates to pub_eft table.
    assert pub_efts[1].prenote_response_reason_code == "R01"
    assert pub_efts[26].prenote_response_reason_code == "C01"
    assert pub_efts[18].prenote_response_reason_code == "C02"
    for pub_eft in pub_efts:
        if pub_eft.pub_individual_id in {1, 27}:
            assert pub_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id
        elif (
            pub_eft.prenote_response_reason_code
            and pub_eft.prenote_response_reason_code.startswith("C")
        ):
            assert pub_eft.prenote_state_id == PrenoteState.APPROVED.prenote_state_id
            assert pub_eft.prenote_approved_at is not None
        else:
            assert pub_eft.prenote_state_id == PrenoteState.PENDING_WITH_PUB.prenote_state_id

    # Test updates to reference_file table.
    reference_file = local_test_db_session.query(ReferenceFile).one()
    assert (
        reference_file.reference_file_type_id
        == ReferenceFileType.PUB_ACH_RETURN.reference_file_type_id
    )

    assert reference_file.file_location == str(
        tmp_path / "processed" / payments_util.get_date_folder() / "ach_return_small.ach"
    )

    # There should be no change to employee states in this process (returns are tracked in the
    # pub_eft table). All should remain in the DELEGATED_EFT_PRENOTE_SENT state.
    prenote_sent = massgov.pfml.api.util.state_log_util.get_all_latest_state_logs_in_end_state(
        massgov.pfml.api.util.state_log_util.AssociatedClass.EMPLOYEE,
        State.DELEGATED_EFT_PRENOTE_SENT,
        local_test_db_session,
    )
    assert len(prenote_sent) == 40

    # Payment states.
    expected_states = {
        46: (State.DELEGATED_PAYMENT_ERROR_FROM_BANK, "R05", 7, None),
        61: (State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION, "C01", 9, "4000401234"),
        68: (State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION, "C02", 11, "100234567"),
        75: (State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION, "C05", 13, "22"),
    }
    for payment in payments:
        local_test_db_session.refresh(payment)
        payment_state_log = massgov.pfml.api.util.state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, local_test_db_session
        )
        state_id = payment_state_log.end_state.state_id
        if payment.pub_individual_id in expected_states:
            # Present in test file as an ACH Return (Rnn) or Change Notification (Cnn).
            (
                expected_state,
                expected_reason_code,
                expected_line_num,
                expected_change,
            ) = expected_states[payment.pub_individual_id]
            assert state_id == expected_state.state_id
            assert payment_state_log.outcome["ach_return_reason_code"] == expected_reason_code
            assert payment_state_log.outcome["ach_return_line_number"] == str(expected_line_num)
            if expected_change:
                assert payment_state_log.outcome["ach_return_change_information"] == expected_change
            assert len(payment.reference_files) == 1
            assert payment.reference_files[0].reference_file == reference_file

            writeback_state_log = massgov.pfml.api.util.state_log_util.get_latest_state_log_in_flow(
                payment, Flow.DELEGATED_PEI_WRITEBACK, local_test_db_session
            )
            assert (
                writeback_state_log.end_state.state_id
                == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id
            )

            writeback_details = (
                local_test_db_session.query(FineosWritebackDetails)
                .filter(FineosWritebackDetails.payment_id == payment.payment_id)
                .one_or_none()
            )
            assert writeback_details
            transaction_status_id = writeback_details.transaction_status_id
            if expected_state == State.DELEGATED_PAYMENT_ERROR_FROM_BANK:
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
            # Not in test file - state unchanged.
            assert state_id == State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT.state_id
            assert payment.reference_files == []

    # Metrics collected.
    expected_metrics = {
        "ach_return_count": 8,
        "change_notification_count": 6,
        "eft_prenote_count": 7,
        "eft_prenote_unexpected_state_count": 0,
        "eft_prenote_already_rejected_count": 0,
        "eft_prenote_id_not_found_count": 2,
        "eft_prenote_change_notification_count": 2,
        "eft_prenote_rejected_count": 3,
        "payment_count": 7,
        "payment_complete_with_change_count": 3,
        "payment_id_not_found_count": 3,
        "payment_rejected_count": 1,
    }
    assert expected_metrics.items() <= process_nacha_file_step.log_entry.metrics.items()

    pub_errors = local_test_db_session.query(PubError).all()
    pub_error_count = Counter(p.pub_error_type_id for p in pub_errors)

    assert pub_error_count.get(PubErrorType.ACH_WARNING.pub_error_type_id) is None

    assert pub_error_count[PubErrorType.ACH_PRENOTE.pub_error_type_id] == (
        expected_metrics["eft_prenote_id_not_found_count"]
        + expected_metrics["eft_prenote_unexpected_state_count"]
        + expected_metrics["eft_prenote_already_rejected_count"]
        + expected_metrics["eft_prenote_change_notification_count"]
        + expected_metrics["eft_prenote_rejected_count"]
    )

    assert pub_error_count[PubErrorType.ACH_RETURN.pub_error_type_id] == (
        expected_metrics["payment_id_not_found_count"] + expected_metrics["payment_rejected_count"]
    )

    assert pub_error_count.get(PubErrorType.ACH_NOTIFICATION.pub_error_type_id) is None

    assert pub_error_count[PubErrorType.ACH_SUCCESS_WITH_NOTIFICATION.pub_error_type_id] == (
        expected_metrics["payment_complete_with_change_count"]
    )


# == Assertion Helpers ==


def assert_pub_error(db_session, pub_error_type, message):
    pub_errors = db_session.query(PubError).all()
    assert len(pub_errors) == 1

    pub_error = pub_errors[0]
    assert pub_error.pub_error_type_id == pub_error_type.pub_error_type_id
    assert pub_error.message == message


def assert_pub_eft_prenote_state(db_session, pub_eft_id, prenote_state):
    assert (
        db_session.query(PubEft)
        .filter(
            PubEft.pub_eft_id == pub_eft_id,
            PubEft.prenote_state_id == prenote_state.prenote_state_id,
        )
        .one_or_none()
    )


def assert_payment_state(payment, flow, end_state, db_session):
    state_log = massgov.pfml.api.util.state_log_util.get_latest_state_log_in_flow(
        payment, flow, db_session
    )

    assert state_log
    assert state_log.end_state_id == end_state.state_id


def assert_fineos_writeback_status(payment, transaction_status, db_session):
    assert (
        db_session.query(FineosWritebackDetails)
        .filter(
            FineosWritebackDetails.payment_id == payment.payment_id,
            FineosWritebackDetails.transaction_status_id
            == transaction_status.transaction_status_id,
        )
        .one_or_none()
    )
