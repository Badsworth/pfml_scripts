import os
import tempfile
from typing import List, Optional

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    ClaimType,
    Flow,
    Payment,
    PaymentMethod,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import ClaimFactory, PaymentFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    PaymentAuditData,
    build_audit_report_row,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_rejects import (
    ACCEPTED_OUTCOME,
    ACCEPTED_STATE,
    AUDIT_REJECT_NOTE_TO_WRITEBACK_STATUS,
    AUDIT_SKIPPED_NOTE_TO_WRITEBACK_STATUS,
    NOT_SAMPLED_PAYMENT_NEXT_STATE_BY_CURRENT_STATE,
    NOT_SAMPLED_PAYMENT_OUTCOME_BY_CURRENT_STATE,
    NOT_SAMPLED_STATE_TRANSITIONS,
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
        str(tmp_path),
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
        payments_util.get_now().strftime("%Y-%m-%d"),
    )

    file_path = os.path.join(
        expected_rejects_folder, "2021-01-15-12-00-00-Payment-Audit-Report-Response.csv"
    )
    payment_rejects_rows: List[PaymentAuditCSV] = payment_rejects_step.parse_payment_rejects_file(
        file_path
    )

    assert len(payment_rejects_rows) == len(DEFAULT_AUDIT_SCENARIO_DATA_SET)

    payments = test_db_session.query(Payment).all()
    payments_by_id = {str(p.payment_id): p for p in payments}

    rejects_count = 0
    for payment_rejects_row in payment_rejects_rows:
        payment = payments_by_id[payment_rejects_row.pfml_payment_id]
        assert payment is not None

        if payment_rejects_row.rejected_by_program_integrity == "Y":
            rejects_count += 1

    assert rejects_count > 0


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_parse_payment_rejects_file_missing_columns(
    tmp_path, test_db_session, payment_rejects_step
):
    # Test that if columns are missing during parsing,
    # it won't throw any errors. Required columns
    # are validated later in processing (See: test_rejects_column_validation)
    # This avoids issues if we create a new column and
    # the deployment happens between the file generation
    # in ECS task #1, and the parsing in ECS task #2
    expected_rejects_folder = os.path.join(
        str(tmp_path),
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
        payments_util.get_now().strftime("%Y-%m-%d"),
    )

    file_path = os.path.join(
        expected_rejects_folder, "2021-01-15-12-00-00-Payment-Audit-Report-Response.csv"
    )
    # Create a partial output, only putting two real column and a fake (which gets ignored)
    with file_util.write_file(file_path) as output_file:
        output_file.write(
            f"{PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id},{PAYMENT_AUDIT_CSV_HEADERS.leave_type},FAKE_COLUMN_HEADER\n"
        )
        output_file.write("1,1,1\n")
        output_file.write("2,2,2\n")
        output_file.write("3,3,3")

    payment_rejects_rows: List[PaymentAuditCSV] = payment_rejects_step.parse_payment_rejects_file(
        file_path
    )
    assert len(payment_rejects_rows) == 3
    for row in payment_rejects_rows:
        assert row.pfml_payment_id is not None
        assert row.pfml_payment_id == row.leave_type

        # Just verify a few others aren't set
        assert row.rejected_by_program_integrity is None
        assert row.skipped_by_program_integrity is None
        assert row.max_weekly_benefits_details is None
        assert row.dua_dia_reduction_details is None
        assert row.dor_fineos_name_mismatch_details is None


def test_rejects_column_validation(test_db_session, payment_rejects_step):
    claim = ClaimFactory.create(claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id)
    payment = PaymentFactory.create(
        disb_method_id=PaymentMethod.ACH.payment_method_id, claim=claim,
    )
    state_log_util.create_finished_state_log(
        payment,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    payment_audit_data = PaymentAuditData(
        payment=payment,
        is_first_time_payment=True,
        previously_rejected_payment_count=1,
        previously_errored_payment_count=1,
        previously_skipped_payment_count=0,
    )
    payment_rejects_row = build_audit_report_row(
        payment_audit_data, payments_util.get_now(), test_db_session
    )

    payment_rejects_row.pfml_payment_id = None
    payment_rejects_row.rejected_by_program_integrity = "Y"

    with pytest.raises(
        PaymentRejectsException, match="Missing payment id column in rejects file.",
    ):
        payment_rejects_step.transition_audit_pending_payment_states([payment_rejects_row])

    payment_rejects_row.pfml_payment_id = payment.payment_id
    payment_rejects_row.rejected_by_program_integrity = None

    with pytest.raises(
        PaymentRejectsException, match="Missing rejection column in rejects file.",
    ):
        payment_rejects_step.transition_audit_pending_payment_states([payment_rejects_row])

    payment_rejects_row.rejected_by_program_integrity = "Y"
    payment_rejects_row.skipped_by_program_integrity = None

    with pytest.raises(
        PaymentRejectsException, match="Missing skip column in rejects file.",
    ):
        payment_rejects_step.transition_audit_pending_payment_states([payment_rejects_row])

    payment_rejects_row.rejected_by_program_integrity = "Y"
    payment_rejects_row.skipped_by_program_integrity = "Y"

    with pytest.raises(
        PaymentRejectsException, match="Unexpected state - rejects row both rejected and skipped.",
    ):
        payment_rejects_step.transition_audit_pending_payment_states([payment_rejects_row])


@pytest.mark.parametrize(
    "rejected_by_program_integrity, skipped_by_program_integrity",
    [("", ""), ("N", "N"), ("Foo", "Foo"), ("Y", ""), ("", "Y"),],
)
def test_valid_combination_of_reject_and_skip(
    test_db_session,
    payment_rejects_step,
    rejected_by_program_integrity,
    skipped_by_program_integrity,
):
    claim = ClaimFactory.create(claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id)
    payment = PaymentFactory.create(
        disb_method_id=PaymentMethod.ACH.payment_method_id, claim=claim,
    )
    state_log_util.create_finished_state_log(
        payment,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    payment_audit_data = PaymentAuditData(
        payment=payment,
        is_first_time_payment=True,
        previously_rejected_payment_count=1,
        previously_errored_payment_count=1,
        previously_skipped_payment_count=0,
    )

    payment_rejects_row = build_audit_report_row(
        payment_audit_data, payments_util.get_now(), test_db_session
    )
    payment_rejects_row.rejected_by_program_integrity = rejected_by_program_integrity
    payment_rejects_row.skipped_by_program_integrity = skipped_by_program_integrity

    payment_rejects_step.transition_audit_pending_payment_states([payment_rejects_row])

    end_state = ACCEPTED_STATE
    if rejected_by_program_integrity == "Y":
        end_state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT

    if skipped_by_program_integrity == "Y":
        end_state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE

    payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )

    assert payment_state_log is not None
    assert payment_state_log.end_state_id == end_state.state_id


def test_transition_audit_pending_payment_state(test_db_session, payment_rejects_step):
    # test rejection
    payment_1 = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        payment_1,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    payment_rejects_step.transition_audit_pending_payment_state(
        payment_1, True, False, "Example notes"
    )

    payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
        payment_1, Flow.DELEGATED_PAYMENT, test_db_session
    )

    assert payment_state_log is not None
    assert (
        payment_state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT.state_id
    )
    assert payment_state_log.outcome["message"] == "Payment rejected with notes: Example notes"

    expected_writeback_transaction_status = (
        FineosWritebackTransactionStatus.FAILED_MANUAL_VALIDATION
    )
    writeback_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
        payment_1, Flow.DELEGATED_PEI_WRITEBACK, test_db_session
    )
    assert writeback_state_log is not None
    assert writeback_state_log.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id
    assert (
        writeback_state_log.outcome["message"]
        == expected_writeback_transaction_status.transaction_status_description
    )

    writeback_details = (
        test_db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment_1.payment_id)
        .one_or_none()
    )
    assert writeback_details is not None
    assert (
        writeback_details.transaction_status_id
        == expected_writeback_transaction_status.transaction_status_id
    )

    # test acceptance
    payment_2 = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        payment_2,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    payment_rejects_step.transition_audit_pending_payment_state(payment_2, False, False)

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
        payment_rejects_step.transition_audit_pending_payment_state(payment_3, True, False)

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
        payment_rejects_step.transition_audit_pending_payment_state(payment_4, True, False)

    # test skip
    payment_5 = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        payment_5,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    payment_rejects_step.transition_audit_pending_payment_state(payment_5, False, True)

    payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
        payment_5, Flow.DELEGATED_PAYMENT, test_db_session
    )

    assert payment_state_log is not None
    assert (
        payment_state_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE.state_id
    )
    assert payment_state_log.outcome["message"] == "Payment skipped"

    expected_writeback_transaction_status = FineosWritebackTransactionStatus.PENDING_PAYMENT_AUDIT
    writeback_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
        payment_5, Flow.DELEGATED_PEI_WRITEBACK, test_db_session
    )
    assert writeback_state_log is not None
    assert writeback_state_log.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id
    assert (
        writeback_state_log.outcome["message"]
        == expected_writeback_transaction_status.transaction_status_description
    )

    writeback_details = (
        test_db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment_5.payment_id)
        .one_or_none()
    )
    assert writeback_details is not None
    assert (
        writeback_details.transaction_status_id
        == expected_writeback_transaction_status.transaction_status_id
    )


def test_convert_reject_notes_to_writeback_status_rejected_scenarios(
    test_db_session, payment_rejects_step
):
    test_cases = []

    for (reject_note, expected_status) in AUDIT_REJECT_NOTE_TO_WRITEBACK_STATUS.items():
        test_cases.append(
            {"reject_notes": reject_note, "expected_status": expected_status,}
        )

    # Close matches
    test_cases.append(
        {
            "reject_notes": "Dua Additional Income",
            "expected_status": FineosWritebackTransactionStatus.DUA_ADDITIONAL_INCOME,
        }
    )

    test_cases.append(
        {
            "reject_notes": "DUA Additional Income.",
            "expected_status": FineosWritebackTransactionStatus.DUA_ADDITIONAL_INCOME,
        }
    )

    # No matches
    test_cases.append(
        {
            "reject_notes": None,
            "expected_status": FineosWritebackTransactionStatus.FAILED_MANUAL_VALIDATION,
        }
    )
    test_cases.append(
        {
            "reject_notes": "",
            "expected_status": FineosWritebackTransactionStatus.FAILED_MANUAL_VALIDATION,
        }
    )
    test_cases.append(
        {
            "reject_notes": "Unknown reject status note",
            "expected_status": FineosWritebackTransactionStatus.FAILED_MANUAL_VALIDATION,
        }
    )
    for test_case in test_cases:
        payment_1 = PaymentFactory.create()

        writeback_status = payment_rejects_step.convert_reject_notes_to_writeback_status(
            payment_1, True, test_case["reject_notes"]
        )

        assert (
            writeback_status.transaction_status_id
            == test_case["expected_status"].transaction_status_id
        )


def test_convert_reject_notes_to_writeback_status_skipped_scenarios(
    test_db_session, payment_rejects_step
):
    test_cases = []

    for (reject_note, expected_status) in AUDIT_SKIPPED_NOTE_TO_WRITEBACK_STATUS.items():
        test_cases.append(
            {"reject_notes": reject_note, "expected_status": expected_status,}
        )

    # Close matches
    test_cases.append(
        {
            "reject_notes": "Leave Plan In Review (Skipped)",
            "expected_status": FineosWritebackTransactionStatus.LEAVE_IN_REVIEW,
        }
    )

    test_cases.append(
        {
            "reject_notes": "~!~LeAvE PlAn IN review~!~",
            "expected_status": FineosWritebackTransactionStatus.LEAVE_IN_REVIEW,
        }
    )

    # Unknown test cases
    test_cases.append(
        {
            "reject_notes": "Unknown reject status note",
            "expected_status": FineosWritebackTransactionStatus.PENDING_PAYMENT_AUDIT,
        }
    )

    for test_case in test_cases:
        payment_1 = PaymentFactory.create()

        writeback_status = payment_rejects_step.convert_reject_notes_to_writeback_status(
            payment_1, False, test_case["reject_notes"]
        )

        assert (
            writeback_status.transaction_status_id
            == test_case["expected_status"].transaction_status_id
        )


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


def _generate_rejects_file(payment_rejects_received_folder_path, file_name, db_session):
    # generate the rejects file
    audit_scenario_data = generate_payment_audit_data_set_and_rejects_file(
        DEFAULT_AUDIT_SCENARIO_DATA_SET,
        payment_rejects_received_folder_path,
        db_session,
        1,
        file_name,
    )
    # The above method creates the audit report in a dated folder
    # as it uses the audit report generation logic. Move it out of that folder
    # as we don't expect it to be there when we are processing reject files.
    dated_input_folder = os.path.join(
        payment_rejects_received_folder_path,
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
        payments_util.get_now().strftime("%Y-%m-%d"),
    )
    files = file_util.list_files(dated_input_folder)
    assert len(files) == 1
    file_util.rename_file(
        os.path.join(dated_input_folder, files[0]),
        os.path.join(payment_rejects_received_folder_path, files[0]),
    )

    return audit_scenario_data


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_rejects(
    test_db_session, test_db_other_session, initialize_factories_session, monkeypatch
):
    # setup folder path configs
    payment_rejects_archive_folder_path = str(tempfile.mkdtemp())
    payment_rejects_received_folder_path = os.path.join(
        payment_rejects_archive_folder_path, "received"
    )
    payment_rejects_processed_folder_path = os.path.join(
        payment_rejects_archive_folder_path, "processed"
    )

    monkeypatch.setenv("PFML_PAYMENT_REJECTS_ARCHIVE_PATH", payment_rejects_archive_folder_path)

    date_folder = payments_util.get_now().strftime("%Y-%m-%d")
    timestamp_file_prefix = "2021-01-15-12-00-00"

    # generate the rejects file
    audit_scenario_data = _generate_rejects_file(
        payment_rejects_received_folder_path, "Payment-Audit-Report-Response", test_db_session
    )

    # Create a few more payments in pending state (not sampled)
    not_sampled = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        not_sampled,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED,
        state_log_util.build_outcome("test"),
        test_db_session,
    )

    # process rejects
    payment_rejects_step = PaymentRejectsStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )
    payment_rejects_step.process_rejects()

    # check some are rejected
    # TODO adjust scenario config to specify desired rejection state instead of random sampling
    rejected_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
        test_db_session,
    )
    assert len(rejected_state_logs) > len(
        audit_scenario_data
    )  # there are previously rejected statements in scenario

    # check all non sampled pending states have transitioned
    payment_state_log = state_log_util.get_latest_state_log_in_flow(
        not_sampled, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert payment_state_log.end_state_id == State.DELEGATED_PAYMENT_VALIDATED.state_id

    # check rejects file was moved to processed folder
    expected_processed_folder_path = os.path.join(
        payment_rejects_processed_folder_path, date_folder
    )
    rejects_file_name = f"{timestamp_file_prefix}-Payment-Audit-Report-Response.csv"
    assert_files(expected_processed_folder_path, [rejects_file_name])

    # check reference files created for proccessed reject file
    assert_reference_file(expected_processed_folder_path, [rejects_file_name], test_db_session)


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_process_rejects_error(
    test_db_session, test_db_other_session, initialize_factories_session, monkeypatch
):
    # setup folder path configs
    payment_rejects_archive_folder_path = str(tempfile.mkdtemp())
    payment_rejects_received_folder_path = os.path.join(
        payment_rejects_archive_folder_path, "received"
    )
    payment_rejects_errored_folder_path = os.path.join(payment_rejects_archive_folder_path, "error")

    monkeypatch.setenv("PFML_PAYMENT_REJECTS_ARCHIVE_PATH", payment_rejects_archive_folder_path)

    # generate two rejects files to trigger a processing error
    _generate_rejects_file(
        payment_rejects_received_folder_path, "Payment-Audit-Report-Response-1", test_db_session
    )
    _generate_rejects_file(
        payment_rejects_received_folder_path, "Payment-Audit-Report-Response-2", test_db_session
    )

    current_timestamp = payments_util.get_now().strftime("%Y-%m-%d-%H-%M-%S")
    rejects_file_name_1 = f"{current_timestamp}-Payment-Audit-Report-Response-1.csv"
    rejects_file_name_2 = f"{current_timestamp}-Payment-Audit-Report-Response-2.csv"

    payment_rejects_step = PaymentRejectsStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )
    with pytest.raises(
        PaymentRejectsException,
        match=f"Too many Payment Rejects files found: {rejects_file_name_1}, {rejects_file_name_2}",
    ):
        payment_rejects_step.process_rejects()

    # check rejects file was moved to processed folder
    expected_errored_folder_path = os.path.join(
        payment_rejects_errored_folder_path, payments_util.get_now().strftime("%Y-%m-%d")
    )
    assert_files(expected_errored_folder_path, [rejects_file_name_1, rejects_file_name_2])


# Assertion helpers
def assert_files(folder_path, expected_files):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert expected_file in files_in_folder


def assert_reference_file(folder_path, expected_files, db_session):
    for expected_file in expected_files:
        assert (
            db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.file_location == str(os.path.join(folder_path, expected_file)),
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.DELEGATED_PAYMENT_REJECTS.reference_file_type_id,
            )
            .one_or_none()
            is not None
        )
