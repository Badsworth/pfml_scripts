import csv
import os
import uuid
from datetime import datetime, timedelta

import pytest

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Address,
    ClaimType,
    EmployeeAddress,
    LkClaimType,
    LkPaymentMethod,
    Payment,
    PaymentMethod,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    PaymentFactory,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_report import (
    get_leave_type,
    get_payment_preference,
    write_audit_report,
)

pytestmark = pytest.mark.integration


# TODO Scenarios (after PUB-69 is complete):
# First time payment
# Updated Payment
# Rejected Payment
# Days in Rejected State


def test_write_audit_report(tmp_path, test_db_session, initialize_factories_session):
    payment_1 = create_payment(ClaimType.MEDICAL_LEAVE, PaymentMethod.CHECK)
    payment_2 = create_payment(ClaimType.MEDICAL_LEAVE, PaymentMethod.ACH)
    payment_3 = create_payment(ClaimType.FAMILY_LEAVE, PaymentMethod.CHECK)
    payment_4 = create_payment(ClaimType.FAMILY_LEAVE, PaymentMethod.ACH)

    payments = [payment_1, payment_2, payment_3, payment_4]

    write_audit_report(payments, tmp_path, test_db_session)

    # Report is created
    expected_output_folder = os.path.join(
        str(tmp_path), payments_util.get_now().strftime("%Y-%m-%d")
    )
    files = file_util.list_files(expected_output_folder)
    assert len(files) == 1

    # Correct number of rows
    csv_path = os.path.join(expected_output_folder, files[0])

    expected_count = len(payments)
    file_content = file_util.read_file(csv_path)
    file_line_count = file_content.count("\n")
    expected_count = len(payments)
    assert (
        file_line_count == expected_count + 1  # account for header row
    ), f"Unexpected number of lines in audit reportfound: {file_line_count}, expected: {expected_count + 1}"

    # Validate rows
    parsed_csv = csv.DictReader(open(csv_path))

    index = 0
    for row in parsed_csv:
        payment = payments[index]

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
        assert row[PAYMENT_AUDIT_CSV_HEADERS.is_first_time_payment] == "N"
        assert row[PAYMENT_AUDIT_CSV_HEADERS.is_updated_payment] == "N"
        assert row[PAYMENT_AUDIT_CSV_HEADERS.is_rejected_or_error] == "N"
        assert row[PAYMENT_AUDIT_CSV_HEADERS.days_in_rejected_state] == "0"
        assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_by_program_integrity] == ""
        assert row[PAYMENT_AUDIT_CSV_HEADERS.rejected_notes] == ""

        index += 1


def create_payment(claim_type: LkClaimType, payment_method: LkPaymentMethod) -> Payment:
    c_value = str(uuid.uuid4())
    i_value = str(uuid.uuid4())

    mailing_address = AddressFactory.create(
        address_line_one="20 South Ave",
        city="Burlington",
        geo_state_id=1,
        geo_state_text="Massachusetts",
        zip_code="01803",
    )

    employer = EmployerFactory.create()

    employee = EmployeeFactory.create(payment_method_id=payment_method.payment_method_id)
    employee.addresses = [EmployeeAddress(employee=employee, address=mailing_address)]

    claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=claim_type.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
    )

    payment_date = datetime.now()
    period_start_date = payment_date - timedelta(weeks=7)
    period_end_date = payment_date - timedelta(weeks=1)

    payment = PaymentFactory.create(
        fineos_pei_c_value=c_value,
        fineos_pei_i_value=i_value,
        claim=claim,
        payment_date=payment_date,
        period_start_date=period_start_date,
        period_end_date=period_end_date,
    )

    return payment
