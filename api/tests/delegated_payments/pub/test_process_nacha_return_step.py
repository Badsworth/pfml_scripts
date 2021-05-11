#
# Tests for class ProcessReturnFileStep.
#

import datetime
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
from massgov.pfml.db.models.factories import PaymentFactory, PubEftFactory
from massgov.pfml.delegated_payments.pub import process_nacha_return_step
from massgov.pfml.util.batch.log import LogEntry


@pytest.fixture
def process_nacha_file_step(test_db_session, initialize_factories_session, test_db_other_session):
    return process_nacha_return_step.ProcessNachaReturnFileStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


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
        if pub_eft.pub_individual_id in {1, 26, 18, 27}:
            assert pub_eft.prenote_state_id == PrenoteState.REJECTED.prenote_state_id
        else:
            assert pub_eft.prenote_state_id == PrenoteState.PENDING_WITH_PUB.prenote_state_id

    # Test updates to reference_file table.
    reference_file = local_test_db_session.query(ReferenceFile).one()
    assert (
        reference_file.reference_file_type_id
        == ReferenceFileType.PUB_ACH_RETURN.reference_file_type_id
    )

    assert reference_file.file_location == str(
        tmp_path / payments_util.get_date_folder() / "processed" / "ach_return_small.ach"
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
        46: (State.ADD_TO_ERRORED_PEI_WRITEBACK, "R05", 7, None),
        61: (State.DELEGATED_PAYMENT_COMPLETE, "C01", 9, "4000401234"),
        68: (State.DELEGATED_PAYMENT_COMPLETE, "C02", 11, "100234567"),
        75: (State.DELEGATED_PAYMENT_COMPLETE, "C05", 13, "22"),
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
        else:
            # Not in test file - state unchanged.
            assert state_id == State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT.state_id
            assert payment.reference_files == []

    # Metrics collected.
    expected_metrics = {
        "ach_return_count": 8,
        "change_notification_count": 6,
        "eft_prenote_count": 7,
        "eft_prenote_already_approved_count": 1,
        "eft_prenote_id_not_found_count": 2,
        "eft_prenote_rejected_count": 4,
        "payment_count": 7,
        "payment_complete_with_change_count": 3,
        "payment_id_not_found_count": 3,
        "payment_rejected_count": 1,
    }
    assert expected_metrics.items() <= process_nacha_file_step.log_entry.metrics.items()

    pub_errors = local_test_db_session.query(PubError).all()
    pub_error_count = Counter(p.pub_error_type_id for p in pub_errors)

    # TODO test for metrics and PubError entry (account for in PUB-127):
    # warning_count
    # unknown_id_format_count
    # eft_prenote_unexpected_state_count
    # payment_unexpected_state_count
    # payment_notification_unexpected_state_count

    assert (
        pub_error_count.get(PubErrorType.ACH_WARNING.pub_error_type_id) is None
    )  # TODO expected_metrics["warning_count"]

    assert pub_error_count[PubErrorType.ACH_PRENOTE.pub_error_type_id] == (
        expected_metrics["eft_prenote_id_not_found_count"]
        + expected_metrics["eft_prenote_already_approved_count"]
        # expected_metrics["eft_prenote_unexpected_state_count"] # TODO
    )

    assert pub_error_count[PubErrorType.ACH_RETURN.pub_error_type_id] == (
        expected_metrics["payment_id_not_found_count"]
        + expected_metrics["payment_rejected_count"]
        # expected_metrics["unknown_id_format_count"] # TODO
        # expected_metrics["payment_unexpected_state_count"] # TODO
    )

    assert (
        pub_error_count.get(PubErrorType.ACH_NOTIFICATION.pub_error_type_id) is None
    )  # TODO expected_metrics["payment_notification_unexpected_state_count"]

    assert pub_error_count[PubErrorType.ACH_SUCCESS_WITH_NOTIFICATION.pub_error_type_id] == (
        expected_metrics["payment_complete_with_change_count"]
    )


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


def pub_eft_pending_with_pub_factory(pub_individual_id, test_db_session):
    employee = factories.EmployeeFactory.create()
    pub_eft = PubEft(
        routing_nbr="%09d" % (444000000 + pub_individual_id),
        account_nbr="%011d" % (3030000000 + pub_individual_id),
        bank_account_type_id=BankAccountType.CHECKING.bank_account_type_id,
        prenote_state_id=PrenoteState.PENDING_WITH_PUB.prenote_state_id,
        pub_individual_id=pub_individual_id,
    )
    test_db_session.add(pub_eft)
    employee.pub_efts.append(EmployeePubEftPair(pub_eft=pub_eft))

    test_db_session.commit()

    massgov.pfml.api.util.state_log_util.create_finished_state_log(
        end_state=State.DELEGATED_EFT_PRENOTE_SENT,
        associated_model=employee,
        db_session=test_db_session,
        outcome=massgov.pfml.api.util.state_log_util.build_outcome(
            "Generated state EFT_PRENOTE_SENT"
        ),
    )

    return pub_eft


def payment_sent_to_pub_factory(pub_individual_id, test_db_session):
    employee = factories.EmployeeFactory.create()
    employer = factories.EmployerFactory.create()
    factories.WagesAndContributionsFactory.create(employer=employer, employee=employee)

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
        end_state=State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT,
        associated_model=payment,
        db_session=test_db_session,
        outcome=massgov.pfml.api.util.state_log_util.build_outcome(
            "Generated state DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT"
        ),
    )

    return payment
