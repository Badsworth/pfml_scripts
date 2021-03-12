import os
import tempfile
from typing import List, Optional

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Flow,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import PaymentFactory
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import PaymentAuditCSV
from massgov.pfml.delegated_payments.audit.delegated_payment_rejects import (
    ACCEPTED_OUTCOME,
    ACCEPTED_STATE,
    NOT_SAMPLED_PAYMENT_NEXT_STATE_BY_CURRENT_STATE,
    NOT_SAMPLED_PAYMENT_OUTCOME_BY_CURRENT_STATE,
    NOT_SAMPLED_STATE_TRANSITIONS,
    REJECTED_OUTCOME,
    REJECTED_STATE,
    PaymentRejectsException,
    PaymentRejectsStep,
)
from massgov.pfml.delegated_payments.audit.mock.delegated_payment_audit_generator import (
    DEFAULT_AUDIT_SCENARIO_DATA_SET,
    generate_payment_audit_data_set_and_rejects_file,
)


@pytest.fixture
def payment_rejects_step(initialize_factories_session, test_db_session, test_db_other_session):
    return PaymentRejectsStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_parse_payment_rejects_file(tmp_path, test_db_session, payment_rejects_step):
    generate_payment_audit_data_set_and_rejects_file(
        DEFAULT_AUDIT_SCENARIO_DATA_SET, tmp_path, test_db_session, 1
    )

    expected_rejects_folder = os.path.join(
        str(tmp_path), payments_util.get_now().strftime("%Y-%m-%d")
    )

    file_path = os.path.join(expected_rejects_folder, "2021-01-15-12-00-00-Payment-Rejects.csv")
    payment_rejects_rows: List[PaymentAuditCSV] = payment_rejects_step.parse_payment_rejects_file(
        file_path
    )

    assert len(payment_rejects_rows) == len(DEFAULT_AUDIT_SCENARIO_DATA_SET)

    payments = test_db_session.query(Payment).all()
    payments_by_id = {str(p.payment_id): p for p in payments}

    assert len(payment_rejects_rows) == len(payments)

    rejects_count = 0
    for payment_rejects_row in payment_rejects_rows:
        payment = payments_by_id[payment_rejects_row.pfml_payment_id]
        assert payment is not None

        if payment_rejects_row.rejected_by_program_integrity == "Y":
            rejects_count += 1

    assert rejects_count > 0


def test_transition_audit_pending_payment_state(test_db_session, payment_rejects_step):
    # test rejection
    payment_1 = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        payment_1,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    payment_rejects_step.transition_audit_pending_payment_state(payment_1, True)

    payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
        payment_1, Flow.DELEGATED_PAYMENT, test_db_session
    )

    assert payment_state_log is not None
    assert payment_state_log.end_state_id == REJECTED_STATE.state_id
    assert payment_state_log.outcome["message"] == REJECTED_OUTCOME["message"]

    # test acceptance
    payment_2 = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        payment_2,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    payment_rejects_step.transition_audit_pending_payment_state(payment_2, False)

    payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
        payment_2, Flow.DELEGATED_PAYMENT, test_db_session
    )

    assert payment_state_log is not None
    assert payment_state_log.end_state_id == ACCEPTED_STATE.state_id
    assert payment_state_log.outcome["message"] == ACCEPTED_OUTCOME["message"]

    # test no state found exception
    payment_3 = PaymentFactory.create()

    with pytest.raises(
        PaymentRejectsException,
        match=f"No state log found for payment found in audit reject file: {payment_3.payment_id}",
    ):
        payment_rejects_step.transition_audit_pending_payment_state(payment_3, True)

    # test not a payment pending state exception
    payment_4 = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        payment_4,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    with pytest.raises(
        PaymentRejectsException,
        match=f"Found payment state log not in audit response pending state: {State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED.state_description}, payment_id: {payment_4.payment_id}",
    ):
        payment_rejects_step.transition_audit_pending_payment_state(payment_4, True)


def test_transition_not_sampled_payment_audit_pending_states(test_db_session, payment_rejects_step):
    # create payments with pending states
    payment_to_pending_state = {}
    for state_transition in NOT_SAMPLED_STATE_TRANSITIONS:
        payment = PaymentFactory.create()
        state_log_util.create_finished_state_log(
            payment,
            state_transition.from_state,
            state_log_util.build_outcome("test"),
            test_db_session,
        )

        payment_to_pending_state[payment.payment_id] = state_transition.from_state

    # transition the states
    payment_rejects_step.transition_not_sampled_payment_audit_pending_states()

    # confirm states was transitioned correctly
    payments = test_db_session.query(Payment).all()
    for payment in payments:
        payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
            payment, Flow.DELEGATED_PAYMENT, test_db_session
        )

        end_state = NOT_SAMPLED_PAYMENT_NEXT_STATE_BY_CURRENT_STATE[
            payment_to_pending_state[payment.payment_id].state_id
        ]
        outcome = NOT_SAMPLED_PAYMENT_OUTCOME_BY_CURRENT_STATE[
            payment_to_pending_state[payment.payment_id].state_id
        ]

        assert payment_state_log is not None
        assert payment_state_log.end_state_id == end_state.state_id
        assert payment_state_log.outcome["message"] == outcome["message"]


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_rejects(test_db_session, payment_rejects_step, monkeypatch):
    # setup folder path configs
    payment_rejects_received_folder_path = str(tempfile.mkdtemp())
    payment_rejects_processed_folder_path = str(tempfile.mkdtemp())
    payment_rejects_report_outbound_folder = str(tempfile.mkdtemp())
    payment_rejects_report_sent_folder_path = str(tempfile.mkdtemp())

    monkeypatch.setenv("PAYMENT_REJECTS_RECEIVED_FOLDER_PATH", payment_rejects_received_folder_path)
    monkeypatch.setenv(
        "PAYMENT_REJECTS_PROCESSED_FOLDER_PATH", payment_rejects_processed_folder_path
    )
    monkeypatch.setenv(
        "PAYMENT_REJECTS_REPORT_OUTBOUND_FOLDER", payment_rejects_report_outbound_folder
    )
    monkeypatch.setenv(
        "PAYMENT_REJECTS_REPORT_SENT_FOLDER_PATH", payment_rejects_report_sent_folder_path
    )

    date_folder = "2021-01-15"
    timestamp_file_prefix = "2021-01-15-12-00-00"

    # generate the rejects file
    generate_payment_audit_data_set_and_rejects_file(
        DEFAULT_AUDIT_SCENARIO_DATA_SET, payment_rejects_received_folder_path, test_db_session, 1
    )

    # transition all states to the correct state to simulate audit report sampling
    payments = test_db_session.query(Payment).all()
    for payment in payments:
        state_log_util.create_finished_state_log(
            payment,
            State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
            state_log_util.build_outcome("test"),
            test_db_session,
        )

    # Create a few more payments in pending state (not sampled)
    cancelled_payment = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        cancelled_payment,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    zero_payment = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        zero_payment,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    overpayment = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        overpayment,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    not_sampled = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        not_sampled,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    # process rejects
    payment_rejects_step.process_rejects()

    # check some are rejected
    # TODO adjust scenario config to specify desired rejection state instead of random sampling
    rejected_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT, REJECTED_STATE, test_db_session
    )
    assert len(rejected_state_logs) == len(DEFAULT_AUDIT_SCENARIO_DATA_SET)

    # check all non sampled pending states have transitioned
    payment_state_log = state_log_util.get_latest_state_log_in_flow(
        cancelled_payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK.state_id
    )

    payment_state_log = state_log_util.get_latest_state_log_in_flow(
        zero_payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK.state_id
    )

    payment_state_log = state_log_util.get_latest_state_log_in_flow(
        overpayment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK.state_id
    )

    payment_state_log = state_log_util.get_latest_state_log_in_flow(
        not_sampled, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert (
        payment_state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK.state_id
    )

    # check rejects file was moved to proccessed folder
    expected_processed_folder_path = os.path.join(
        payment_rejects_processed_folder_path, date_folder
    )
    rejects_file_name = f"{timestamp_file_prefix}-Payment-Rejects.csv"
    assert_files(expected_processed_folder_path, [rejects_file_name])

    # check reference files created for proccessed reject file
    assert (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == str(os.path.join(expected_processed_folder_path, rejects_file_name)),
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DELEGATED_PAYMENT_REJECTS.reference_file_type_id,
        )
        .one_or_none()
        is not None
    )

    # check rejects report sent to program integrity and archive folder
    expected_rejects_report_outbound_folder_path = os.path.join(
        payment_rejects_report_outbound_folder, date_folder
    )
    payment_rejects_file_name = f"{timestamp_file_prefix}-Payment-Rejects-Report.csv"
    assert_files(expected_rejects_report_outbound_folder_path, [payment_rejects_file_name])

    payment_rejects_file_content = file_util.read_file(
        os.path.join(expected_rejects_report_outbound_folder_path, payment_rejects_file_name)
    )
    payment_rejects_file_line_count = payment_rejects_file_content.count("\n")
    assert (
        payment_rejects_file_line_count == len(rejected_state_logs) + 1  # account for header row
    ), f"Unexpected number of lines in payment rejects report - found: {payment_rejects_file_line_count}, expected: {len(rejected_state_logs) + 1}"

    expected_rejects_report_sent_folder_path = os.path.join(
        payment_rejects_report_sent_folder_path, date_folder
    )
    assert_files(expected_rejects_report_sent_folder_path, [payment_rejects_file_name])

    # check reference files created - sent
    assert (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == str(
                os.path.join(expected_rejects_report_sent_folder_path, payment_rejects_file_name)
            ),
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DELEGATED_PAYMENT_REJECTS_REPORT.reference_file_type_id,
        )
        .one_or_none()
        is not None
    )


# Assertion helpers
def assert_files(folder_path, expected_files):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert expected_file in files_in_folder


# TODO test all exception scenarios
