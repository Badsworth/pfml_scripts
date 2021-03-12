import csv
import os
import tempfile
from typing import List

import pytest
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    Address,
    EmployeeAddress,
    Payment,
    ReferenceFile,
    ReferenceFileType,
    State,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditData,
    bool_to_str,
    generate_audit_report,
    get_leave_type,
    get_payment_preference,
    write_audit_report,
)
from massgov.pfml.delegated_payments.audit.mock.delegated_payment_audit_generator import (
    DEFAULT_AUDIT_SCENARIO_DATA_SET,
    AuditScenarioData,
    generate_audit_report_dataset,
)

pytestmark = pytest.mark.integration


def test_write_audit_report(tmp_path, test_db_session, initialize_factories_session):
    payment_audit_scenario_data_set: List[AuditScenarioData] = generate_audit_report_dataset(
        DEFAULT_AUDIT_SCENARIO_DATA_SET
    )

    payment_audit_data_set: List[PaymentAuditData] = []
    for payment_audit_scenario_data in payment_audit_scenario_data_set:
        payment_audit_data_set.append(payment_audit_scenario_data.payment_audit_data)

    write_audit_report(payment_audit_data_set, tmp_path, test_db_session)

    # Report is created
    expected_output_folder = os.path.join(
        str(tmp_path), payments_util.get_now().strftime("%Y-%m-%d")
    )
    files = file_util.list_files(expected_output_folder)
    assert len(files) == 1

    # Correct number of rows
    csv_path = os.path.join(expected_output_folder, files[0])

    expected_count = len(payment_audit_data_set)
    file_content = file_util.read_file(csv_path)
    file_line_count = file_content.count("\n")
    expected_count = len(payment_audit_data_set)
    assert (
        file_line_count == expected_count + 1  # account for header row
    ), f"Unexpected number of lines in audit reportfound: {file_line_count}, expected: {expected_count + 1}"

    # Validate rows
    parsed_csv = csv.DictReader(open(csv_path))

    index = 0
    for row in parsed_csv:
        payment_audit_data = payment_audit_data_set[index]
        validate_payment_audit_csv_row_by_payment_audit_data(row, payment_audit_data)

        index += 1


def validate_payment_audit_csv_row_by_payment_audit_data(
    row: PaymentAuditCSV, payment_audit_data: PaymentAuditData
):
    validate_payment_audit_csv_row_by_payment(row, payment_audit_data.payment)

    assert row[PAYMENT_AUDIT_CSV_HEADERS.is_first_time_payment] == bool_to_str(
        payment_audit_data.is_first_time_payment
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.is_updated_payment] == bool_to_str(
        payment_audit_data.is_updated_payment
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.is_rejected_or_error] == bool_to_str(
        payment_audit_data.is_rejected_or_error
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.days_in_rejected_state] == str(
        payment_audit_data.days_in_rejected_state
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity] == ""
    assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_notes] == ""


def validate_payment_audit_csv_row_by_payment(row: PaymentAuditCSV, payment: Payment):
    employee_address: EmployeeAddress = payment.claim.employee.addresses.first()  # TODO adjust after address validation work to get the most recent valid address
    address: Address = employee_address.address

    assert row[PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id] == str(payment.payment_id)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_type] == get_leave_type(payment.claim)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.first_name] == payment.claim.employee.first_name
    assert row[PAYMENT_AUDIT_CSV_HEADERS.last_name] == payment.claim.employee.last_name
    assert row[PAYMENT_AUDIT_CSV_HEADERS.address_line_1] == address.address_line_one
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.address_line_2] == ""
        if address.address_line_two is None
        else address.address_line_two
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.city] == address.city
    assert row[PAYMENT_AUDIT_CSV_HEADERS.state] == address.geo_state.geo_state_description
    assert row[PAYMENT_AUDIT_CSV_HEADERS.zip] == address.zip_code
    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_preference] == get_payment_preference(
        payment.claim.employee
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.scheduled_payment_date] == payment.payment_date.isoformat()
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_start_date]
        == payment.period_start_date.isoformat()
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.payment_period_end_date]
        == payment.period_end_date.isoformat()
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_amount] == str(payment.amount)
    assert row[PAYMENT_AUDIT_CSV_HEADERS.absence_case_number] == payment.claim.fineos_absence_id
    assert row[PAYMENT_AUDIT_CSV_HEADERS.c_value] == payment.fineos_pei_c_value
    assert row[PAYMENT_AUDIT_CSV_HEADERS.i_value] == payment.fineos_pei_i_value
    assert row[PAYMENT_AUDIT_CSV_HEADERS.employer_id] == str(
        payment.claim.employer.fineos_employer_id
    )
    assert (
        row[PAYMENT_AUDIT_CSV_HEADERS.case_status]
        == payment.claim.fineos_absence_status.absence_status_description
    )
    assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_request_id] == ""
    assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_request_decision] == ""


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_generate_audit_report(test_db_session, initialize_factories_session, monkeypatch):
    # setup folder path configs
    payment_audit_report_outbound_folder_path = str(tempfile.mkdtemp())
    payment_audit_report_sent_folder_path = str(tempfile.mkdtemp())

    monkeypatch.setenv(
        "PAYMENT_AUDIT_REPORT_OUTBOUND_FOLDER_PATH", payment_audit_report_outbound_folder_path
    )
    monkeypatch.setenv(
        "PAYMENT_AUDIT_REPORT_SENT_FOLDER_PATH", payment_audit_report_sent_folder_path
    )

    date_folder = "2021-01-15"
    timestamp_file_prefix = "2021-01-15-12-00-00"

    # generate the audit report data set
    generate_audit_report_dataset(DEFAULT_AUDIT_SCENARIO_DATA_SET)

    # transition all states to pending for sampling
    payments = test_db_session.query(Payment).all()
    for payment in payments:
        state_log_util.create_finished_state_log(
            payment,
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
            state_log_util.build_outcome("test"),
            test_db_session,
        )

    # generate audit report
    generate_audit_report(test_db_session)

    # check that sampled states have transitioned
    sampled_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT,
        test_db_session,
    )
    assert len(sampled_state_logs) == len(payments)

    # check that audit report file was generated in outbound folder with correct number of rows
    expected_audit_report_outbound_folder_path = os.path.join(
        payment_audit_report_outbound_folder_path, date_folder
    )
    payment_audit_report_file_name = f"{timestamp_file_prefix}-Payment-Audit-Report.csv"
    assert_files(expected_audit_report_outbound_folder_path, [payment_audit_report_file_name])

    payment_audit_report_file_content = file_util.read_file(
        os.path.join(expected_audit_report_outbound_folder_path, payment_audit_report_file_name)
    )
    payment_audit_report_file_line_count = payment_audit_report_file_content.count("\n")
    assert (
        payment_audit_report_file_line_count
        == len(sampled_state_logs) + 1  # account for header row
    ), f"Unexpected number of lines in payment rejects report - found: {payment_audit_report_file_line_count}, expected: {len(sampled_state_logs) + 1}"

    # check that audit report file was generated in sent folder
    expected_audit_report_sent_folder_path = os.path.join(
        payment_audit_report_sent_folder_path, date_folder
    )
    assert_files(expected_audit_report_sent_folder_path, [payment_audit_report_file_name])

    # check reference file created for sent folder file
    assert (
        test_db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location
            == str(
                os.path.join(expected_audit_report_sent_folder_path, payment_audit_report_file_name)
            ),
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id,
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
