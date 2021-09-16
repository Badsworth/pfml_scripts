import csv
import os
import tempfile
from datetime import date
from typing import List

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Payment, ReferenceFile, ReferenceFileType, State
from massgov.pfml.db.models.factories import ClaimFactory, PaymentFactory
from massgov.pfml.db.models.payments import PaymentAuditReportDetails, PaymentAuditReportType
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditReportStep,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    AUDIT_REPORT_NOTES_OVERRIDE,
    PaymentAuditData,
    bool_to_str,
    get_leave_type,
    get_payment_audit_report_details,
    get_payment_preference,
    stage_payment_audit_report_details,
    write_audit_report,
)
from massgov.pfml.delegated_payments.audit.mock.delegated_payment_audit_generator import (
    AUDIT_SCENARIO_DESCRIPTORS,
    DEFAULT_AUDIT_SCENARIO_DATA_SET,
    AuditScenarioData,
    generate_audit_report_dataset,
)
from massgov.pfml.delegated_payments.pub.pub_check import _format_check_memo
from massgov.pfml.util.datetime import get_period_in_weeks


@pytest.fixture
def payment_audit_report_step(initialize_factories_session, test_db_session, test_db_other_session):
    return PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_stage_payment_audit_report_details(test_db_session, initialize_factories_session):
    payment = PaymentFactory.create()
    stage_payment_audit_report_details(
        payment, PaymentAuditReportType.MAX_WEEKLY_BENEFITS, "Test Message", None, test_db_session
    )

    audit_report_details = test_db_session.query(PaymentAuditReportDetails).one_or_none()
    assert audit_report_details
    assert audit_report_details.payment_id == payment.payment_id
    assert (
        audit_report_details.audit_report_type_id
        == PaymentAuditReportType.MAX_WEEKLY_BENEFITS.payment_audit_report_type_id
    )
    assert audit_report_details.details
    assert audit_report_details.details["message"] == "Test Message"
    assert audit_report_details.created_at is not None
    assert audit_report_details.updated_at is not None
    assert audit_report_details.added_to_audit_report_at is None


def test_get_payment_audit_report_details(test_db_session, initialize_factories_session):
    payment = PaymentFactory.create()
    stage_payment_audit_report_details(
        payment,
        PaymentAuditReportType.MAX_WEEKLY_BENEFITS,
        "Max Weekly Benefits Test Message",
        None,
        test_db_session,
    )
    stage_payment_audit_report_details(
        payment,
        PaymentAuditReportType.DUA_DIA_REDUCTION,
        "DUA/DIA Reduction Test Message",
        None,
        test_db_session,
    )

    audit_report_time = payments_util.get_now()

    audit_report_details = get_payment_audit_report_details(
        payment, audit_report_time, test_db_session
    )

    assert audit_report_details
    assert audit_report_details.max_weekly_benefits_details == "Max Weekly Benefits Test Message"
    assert audit_report_details.dua_dia_reduction_details == "DUA/DIA Reduction Test Message"
    assert audit_report_details.rejected_by_program_integrity
    assert not audit_report_details.skipped_by_program_integrity
    assert (
        audit_report_details.rejected_notes
        == f"{AUDIT_REPORT_NOTES_OVERRIDE[PaymentAuditReportType.MAX_WEEKLY_BENEFITS.payment_audit_report_type_id]} (Rejected), {PaymentAuditReportType.DUA_DIA_REDUCTION.payment_audit_report_type_description} (Skipped)"
    )

    # test that theaudit report time was set
    audit_report_details = test_db_session.query(PaymentAuditReportDetails).all()
    assert len(audit_report_details) == 2
    for audit_report_detail in audit_report_details:
        assert audit_report_detail.added_to_audit_report_at == audit_report_time


def test_is_first_time_payment(
    initialize_factories_session, test_db_session, test_db_other_session
):
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    claim = ClaimFactory.create()
    payment = PaymentFactory.create(claim=claim)
    state_log_util.create_finished_state_log(
        payment,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        state_log_util.build_outcome("test"),
        test_db_session,
    )
    assert payment_audit_report_step.previously_audit_sent_count(payment) == 0

    previous_error_payment = PaymentFactory.create(claim=claim)
    state_log_util.create_finished_state_log(
        previous_error_payment,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )
    assert payment_audit_report_step.previously_audit_sent_count(payment) == 0

    previous_rejected_payment = PaymentFactory.create(claim=claim)
    state_log_util.create_finished_state_log(
        previous_rejected_payment,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )
    state_log_util.create_finished_state_log(
        previous_rejected_payment,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )
    assert payment_audit_report_step.previously_audit_sent_count(payment) == 1

    previous_bank_error_payment = PaymentFactory.create(claim=claim)
    state_log_util.create_finished_state_log(
        previous_bank_error_payment,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        state_log_util.build_outcome("test"),
        test_db_session,
    )
    state_log_util.create_finished_state_log(
        previous_bank_error_payment,
        State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
        state_log_util.build_outcome("test"),
        test_db_session,
    )
    assert payment_audit_report_step.previously_audit_sent_count(payment) == 2


def test_previously_errored_payment_count(
    initialize_factories_session, test_db_session, test_db_other_session
):
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    outcome = state_log_util.build_outcome("test")

    period_start_date = date(2021, 1, 16)
    period_end_date = date(2021, 1, 28)

    other_period_start_date = date(2021, 1, 1)
    other_period_end_date = date(2021, 1, 15)

    # state the payment for audit
    claim = ClaimFactory.create()
    payment = PaymentFactory.create(
        claim=claim, period_start_date=period_start_date, period_end_date=period_end_date
    )
    state_log_util.create_finished_state_log(
        payment,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_errored_payment_count(payment) == 0

    # confirm that errors for payments in other periods for the same claim are not counted
    other_period_erroed_payment = PaymentFactory.create(
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    )
    state_log_util.create_finished_state_log(
        other_period_erroed_payment,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        outcome,
        test_db_session,
    )

    other_period_erroed_payment_restarted = PaymentFactory.create(
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    )
    state_log_util.create_finished_state_log(
        other_period_erroed_payment_restarted,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
        outcome,
        test_db_session,
    )

    assert payment_audit_report_step.previously_errored_payment_count(payment) == 0

    # check errored payments in the same payment period are counted

    same_period_address_error = PaymentFactory.create(
        claim=claim, period_start_date=period_start_date, period_end_date=period_end_date
    )
    state_log_util.create_finished_state_log(
        same_period_address_error,
        State.PAYMENT_FAILED_ADDRESS_VALIDATION,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_errored_payment_count(payment) == 1

    same_period_erroed_payment = PaymentFactory.create(
        claim=claim, period_start_date=period_start_date, period_end_date=period_end_date
    )
    state_log_util.create_finished_state_log(
        same_period_erroed_payment,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_errored_payment_count(payment) == 2

    same_period_erroed_payment_restarted = PaymentFactory.create(
        claim=claim, period_start_date=period_start_date, period_end_date=period_end_date
    )
    state_log_util.create_finished_state_log(
        same_period_erroed_payment_restarted,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_errored_payment_count(payment) == 3

    # each restart will be counted
    same_period_erroed_payment_restarted_2 = PaymentFactory.create(
        claim=claim,
        fineos_pei_c_value=same_period_erroed_payment_restarted.fineos_pei_c_value,
        fineos_pei_i_value=same_period_erroed_payment_restarted.fineos_pei_c_value,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )
    state_log_util.create_finished_state_log(
        same_period_erroed_payment_restarted_2,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_errored_payment_count(payment) == 4


def test_previously_rejected_payment_count(
    initialize_factories_session, test_db_session, test_db_other_session
):
    payment_audit_report_step = PaymentAuditReportStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )

    outcome = state_log_util.build_outcome("test")

    period_start_date = date(2021, 1, 16)
    period_end_date = date(2021, 1, 28)

    other_period_start_date = date(2021, 1, 1)
    other_period_end_date = date(2021, 1, 15)

    # state the payment for audit
    claim = ClaimFactory.create()
    payment = PaymentFactory.create(
        claim=claim, period_start_date=period_start_date, period_end_date=period_end_date
    )
    state_log_util.create_finished_state_log(
        payment,
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 0

    # confirm that rejects for payments in other periods for the same claim are not counted
    other_period_rejected_payment = PaymentFactory.create(
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    )
    state_log_util.create_finished_state_log(
        other_period_rejected_payment,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
        outcome,
        test_db_session,
    )

    other_period_rejected_payment_restarted = PaymentFactory.create(
        claim=claim,
        period_start_date=other_period_start_date,
        period_end_date=other_period_end_date,
    )
    state_log_util.create_finished_state_log(
        other_period_rejected_payment_restarted,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
        outcome,
        test_db_session,
    )

    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 0

    # check errored payments in the same payment period are counted
    same_period_rejected_payment = PaymentFactory.create(
        claim=claim, period_start_date=period_start_date, period_end_date=period_end_date
    )
    state_log_util.create_finished_state_log(
        same_period_rejected_payment,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 1

    # skips are counted separately
    same_period_rejected_payment_restarted = PaymentFactory.create(
        claim=claim, period_start_date=period_start_date, period_end_date=period_end_date
    )
    state_log_util.create_finished_state_log(
        same_period_rejected_payment_restarted,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_rejected_payment_count(payment) == 1
    assert payment_audit_report_step.previously_skipped_payment_count(payment) == 1

    # each restart will be counted
    same_period_rejected_payment_restarted_2 = PaymentFactory.create(
        claim=claim,
        fineos_pei_c_value=same_period_rejected_payment_restarted.fineos_pei_c_value,
        fineos_pei_i_value=same_period_rejected_payment_restarted.fineos_pei_c_value,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )
    state_log_util.create_finished_state_log(
        same_period_rejected_payment_restarted_2,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
        outcome,
        test_db_session,
    )
    assert payment_audit_report_step.previously_skipped_payment_count(payment) == 2


def test_write_audit_report(tmp_path, test_db_session, initialize_factories_session):
    payment_audit_scenario_data_set: List[AuditScenarioData] = generate_audit_report_dataset(
        DEFAULT_AUDIT_SCENARIO_DATA_SET, test_db_session
    )

    payment_audit_data_set: List[PaymentAuditData] = []
    for payment_audit_scenario_data in payment_audit_scenario_data_set:
        payment_audit_data_set.append(payment_audit_scenario_data.payment_audit_data)

    write_audit_report(payment_audit_data_set, tmp_path, test_db_session, "Payment-Audit-Report")

    # Report is created
    expected_output_folder = os.path.join(
        str(tmp_path),
        payments_util.Constants.S3_OUTBOUND_SENT_DIR,
        payments_util.get_now().strftime("%Y-%m-%d"),
    )
    files = file_util.list_files(expected_output_folder)
    assert len(files) == 1

    # Correct number of rows
    csv_path = os.path.join(expected_output_folder, files[0])

    # Validate rows
    parsed_csv = csv.DictReader(open(csv_path))

    index = 0
    for row in parsed_csv:
        audit_scenario_data = payment_audit_scenario_data_set[index]
        validate_payment_audit_csv_row_by_payment_audit_data(row, audit_scenario_data)

        index += 1

    expected_count = len(payment_audit_data_set)
    assert (
        index == expected_count  # account for header row
    ), f"Unexpected number of lines in audit report found: {index}, expected: {expected_count}"


def validate_payment_audit_csv_row_by_payment_audit_data(
    row: PaymentAuditCSV, audit_scenario_data: AuditScenarioData
):
    payment_audit_data: PaymentAuditData = audit_scenario_data.payment_audit_data
    scenario_descriptor = AUDIT_SCENARIO_DESCRIPTORS[audit_scenario_data.scenario_name]
    previous_rejection_count = len(
        list(
            filter(
                lambda s: s == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT,
                scenario_descriptor.previous_rejection_states,
            )
        )
    )
    previously_skipped_payment_count = len(
        list(
            filter(
                lambda s: s == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE,
                scenario_descriptor.previous_rejection_states,
            )
        )
    )

    error_msg = f"Error validaing payment audit scenario data - scenario name: {audit_scenario_data.scenario_name}"

    validate_payment_audit_csv_row_by_payment(row, payment_audit_data.payment)

    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.is_first_time_payment]
        == bool_to_str[scenario_descriptor.is_first_time_payment]
    ), error_msg
    assert row[PAYMENT_AUDIT_CSV_HEADERS.previously_errored_payment_count] == str(
        len(scenario_descriptor.previous_error_states)
    ), error_msg
    assert row[PAYMENT_AUDIT_CSV_HEADERS.previously_rejected_payment_count] == str(
        previous_rejection_count
    ), error_msg
    assert row[PAYMENT_AUDIT_CSV_HEADERS.previously_skipped_payment_count] == str(
        previously_skipped_payment_count
    )

    if scenario_descriptor.audit_report_detail_rejected:
        assert row[PAYMENT_AUDIT_CSV_HEADERS.max_weekly_benefits_details]
        assert row[PAYMENT_AUDIT_CSV_HEADERS.max_weekly_benefits_details] != ""

    if scenario_descriptor.audit_report_detail_skipped:
        assert row[PAYMENT_AUDIT_CSV_HEADERS.dua_dia_reduction_details]
        assert row[PAYMENT_AUDIT_CSV_HEADERS.dua_dia_reduction_details] != ""

    assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity] == (
        "Y" if scenario_descriptor.audit_report_detail_rejected else ""
    ), error_msg

    assert row[PAYMENT_AUDIT_CSV_HEADERS.skipped_by_program_integrity] == (
        "Y"
        if not scenario_descriptor.audit_report_detail_rejected
        and scenario_descriptor.audit_report_detail_skipped
        else ""
    ), error_msg

    if (
        scenario_descriptor.audit_report_detail_rejected
        or scenario_descriptor.audit_report_detail_skipped
    ):
        assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_notes]
        assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_notes] != ""


def validate_payment_audit_csv_row_by_payment(row: PaymentAuditCSV, payment: Payment):
    assert row[PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id] == str(payment.payment_id)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_type] == get_leave_type(payment)
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.fineos_customer_number]
        == payment.claim.employee.fineos_customer_number
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.first_name] == payment.fineos_employee_first_name
    assert row[PAYMENT_AUDIT_CSV_HEADERS.last_name] == payment.fineos_employee_last_name

    validate_address_columns(row, payment)

    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_preference] == get_payment_preference(payment)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.scheduled_payment_date] == payment.payment_date.isoformat()
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_start_date]
        == payment.period_start_date.isoformat()
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_end_date]
        == payment.period_end_date.isoformat()
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_weeks] == str(
        get_period_in_weeks(payment.period_start_date, payment.period_end_date)
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_amount] == str(payment.amount)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.absence_case_number] == payment.claim.fineos_absence_id
    assert row[PAYMENT_AUDIT_CSV_HEADERS.c_value] == payment.fineos_pei_c_value
    assert row[PAYMENT_AUDIT_CSV_HEADERS.i_value] == payment.fineos_pei_i_value

    assert row[PAYMENT_AUDIT_CSV_HEADERS.employer_id] == str(
        payment.claim.employer.fineos_employer_id
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.absence_case_creation_date]
        == payment.absence_case_creation_date.isoformat()
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.case_status]
        == payment.claim.fineos_absence_status.absence_status_description
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_request_decision] == payment.leave_request_decision
    assert row[PAYMENT_AUDIT_CSV_HEADERS.check_description] == _format_check_memo(payment)


def validate_address_columns(row: PaymentAuditCSV, payment: Payment):
    def validate_address_columns_helper(
        address_line_one, address_line_two, city, state, zip_code, is_address_verified,
    ):
        assert row[PAYMENT_AUDIT_CSV_HEADERS.address_line_1] == address_line_one
        assert row[PAYMENT_AUDIT_CSV_HEADERS.address_line_2] == address_line_two
        assert row[PAYMENT_AUDIT_CSV_HEADERS.city] == city
        assert row[PAYMENT_AUDIT_CSV_HEADERS.state] == state
        assert row[PAYMENT_AUDIT_CSV_HEADERS.zip] == zip_code
        assert row[PAYMENT_AUDIT_CSV_HEADERS.is_address_verified] == is_address_verified

    address_pair = payment.experian_address_pair

    if address_pair is None:
        validate_address_columns_helper(
            address_line_one="",
            address_line_two="",
            city="",
            state="",
            zip_code="",
            is_address_verified="N",
        )
    else:
        address = (
            address_pair.experian_address
            if address_pair.experian_address is not None
            else address_pair.fineos_address
        )
        is_address_verified = "Y" if address_pair.experian_address is not None else "N"

        validate_address_columns_helper(
            address_line_one=address.address_line_one,
            address_line_two="" if address.address_line_two is None else address.address_line_two,
            city=address.city,
            state=address.geo_state.geo_state_description,
            zip_code=address.zip_code,
            is_address_verified=is_address_verified,
        )


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_generate_audit_report(test_db_session, payment_audit_report_step, monkeypatch):
    # setup folder path configs
    archive_folder_path = str(tempfile.mkdtemp())
    outgoing_folder_path = str(tempfile.mkdtemp())

    monkeypatch.setenv("PFML_ERROR_REPORTS_ARCHIVE_PATH", archive_folder_path)
    monkeypatch.setenv("DFML_REPORT_OUTBOUND_PATH", outgoing_folder_path)

    date_folder = "2021-01-15"
    timestamp_file_prefix = "2021-01-15-12-00-00"

    # generate the audit report data set
    payment_audit_scenario_data_set = generate_audit_report_dataset(
        DEFAULT_AUDIT_SCENARIO_DATA_SET, test_db_session
    )
    payment_audit_scenario_data_set_by_payment_id = {
        str(audit_scenario_data.payment_audit_data.payment.payment_id): audit_scenario_data
        for audit_scenario_data in payment_audit_scenario_data_set
    }

    # generate audit report
    payment_audit_report_step.run()

    # check that sampled states have transitioned
    sampled_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        test_db_session,
    )
    assert len(sampled_state_logs) == len(DEFAULT_AUDIT_SCENARIO_DATA_SET)

    # check that audit report file was generated in outbound folder with correct number of rows
    expected_audit_report_archive_folder_path = os.path.join(
        archive_folder_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR, date_folder
    )
    payment_audit_report_file_name = f"{timestamp_file_prefix}-Payment-Audit-Report.csv"
    assert_files(expected_audit_report_archive_folder_path, [payment_audit_report_file_name])

    audit_report_file_path = os.path.join(
        expected_audit_report_archive_folder_path, payment_audit_report_file_name
    )

    # Validate column values
    parsed_csv = csv.DictReader(open(audit_report_file_path))
    parsed_csv_by_payment_id = {
        row[PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id]: row for row in parsed_csv
    }

    assert len(parsed_csv_by_payment_id) == len(
        sampled_state_logs
    ), f"Unexpected number of lines in payment rejects report - found: {parsed_csv}, expected: {len(sampled_state_logs)}"

    for payment_id, row in parsed_csv_by_payment_id.items():
        audit_scenario_data = payment_audit_scenario_data_set_by_payment_id.get(payment_id, None)
        assert audit_scenario_data is not None

        validate_payment_audit_csv_row_by_payment_audit_data(row, audit_scenario_data)

    # check reference file created for archive folder file
    assert (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == str(
                os.path.join(
                    expected_audit_report_archive_folder_path, payment_audit_report_file_name
                )
            ),
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id,
        )
        .one_or_none()
        is not None
    )

    # check that audit report file was generated in outgoing folder without any timestamps in path/name
    assert_files(outgoing_folder_path, ["Payment-Audit-Report.csv"])


# Assertion helpers
def assert_files(folder_path, expected_files):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert expected_file in files_in_folder


# TODO test all exception scenarios
