import csv
import os
from typing import List

import pytest

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import Address, EmployeeAddress
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    PaymentAuditData,
    bool_to_str,
    get_leave_type,
    get_payment_preference,
    write_audit_report,
)
from massgov.pfml.delegated_payments.audit.mock.delegated_payment_audit_generator import (
    AUDIT_SCENARIO_DESCRIPTORS,
    AuditScenarioData,
    AuditScenarioNameWithCount,
    generate_audit_report_dataset,
)

pytestmark = pytest.mark.integration


def test_write_audit_report(tmp_path, test_db_session, initialize_factories_session):
    test_scenarios_with_count: List[AuditScenarioNameWithCount] = [
        AuditScenarioNameWithCount(scenario_name, 1)
        for scenario_name in AUDIT_SCENARIO_DESCRIPTORS.keys()
    ]
    payment_audit_scenario_data_set: List[AuditScenarioData] = generate_audit_report_dataset(
        test_scenarios_with_count
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
        payment = payment_audit_data.payment

        employee_address: EmployeeAddress = payment.claim.employee.addresses.first()  # TODO adjust after address validation work to get the most recent valid address
        address: Address = employee_address.address

        assert row[PAYMENT_AUDIT_CSV_HEADERS.pfml_payment_id] == str(payment.payment_id)
        assert row[PAYMENT_AUDIT_CSV_HEADERS.leave_type] == get_leave_type(payment.claim)
        assert row[PAYMENT_AUDIT_CSV_HEADERS.first_name] == payment.claim.employee.first_name
        assert row[PAYMENT_AUDIT_CSV_HEADERS.last_name] == payment.claim.employee.last_name
        assert row[PAYMENT_AUDIT_CSV_HEADERS.address_line_1] == address.address_line_one
        assert row[PAYMENT_AUDIT_CSV_HEADERS.address_line_2] == ""
        assert row[PAYMENT_AUDIT_CSV_HEADERS.city] == address.city
        assert row[PAYMENT_AUDIT_CSV_HEADERS.state] == address.geo_state.geo_state_description
        assert row[PAYMENT_AUDIT_CSV_HEADERS.zip] == address.zip_code
        assert row[PAYMENT_AUDIT_CSV_HEADERS.payment_preference] == get_payment_preference(
            payment.claim.employee
        )
        assert (
            row[PAYMENT_AUDIT_CSV_HEADERS.scheduled_payment_date]
            == payment.payment_date.isoformat()
        )
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

        index += 1
