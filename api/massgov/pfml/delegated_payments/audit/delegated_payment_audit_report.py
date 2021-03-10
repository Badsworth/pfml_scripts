from dataclasses import dataclass
from typing import Iterable, Optional

from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    ClaimType,
    Employee,
    EmployeeAddress,
    Employer,
    LkClaimType,
    LkPaymentMethod,
    Payment,
    PaymentMethod,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
)
from massgov.pfml.delegated_payments.reporting.delegated_abstract_reporting import (
    FileConfig,
    Report,
    ReportGroup,
)


class PaymentAuditRowError(Exception):
    """An error in a row that prevents processing of the payment."""


@dataclass
class PaymentAuditData:
    """Wrapper class to create payment audit report"""

    payment: Payment
    is_first_time_payment: bool
    is_updated_payment: bool
    is_rejected_or_error: bool
    days_in_rejected_state: int
    rejected_by_program_integrity: Optional[bool] = None
    rejected_notes: str = ""


def write_audit_report(payments: Iterable[Payment], output_path: str, db_session: db.Session):
    # Setup the output file
    file_config = FileConfig(file_prefix=output_path)
    report_group = ReportGroup(file_config=file_config)

    report = Report(report_name="Payment-Audit-Report", header_record=PAYMENT_AUDIT_CSV_HEADERS)
    report_group.add_report(report)

    write_audit_report_rows(report, payments)

    report_group.create_and_send_reports()


def write_audit_report_rows(report: Report, payments: Iterable[Payment]):
    for payment in payments:

        # TODO query payments and state logs to populate the following (after PUB-69 is complete)
        is_first_time_payment = False
        is_updated_payment = False
        is_rejected_or_error = False
        days_in_rejected_state = 0

        payment_audit_data = PaymentAuditData(
            payment=payment,
            is_first_time_payment=is_first_time_payment,
            is_updated_payment=is_updated_payment,
            is_rejected_or_error=is_rejected_or_error,
            days_in_rejected_state=days_in_rejected_state,
        )

        payment_audit_report_row = build_audit_report_row(payment_audit_data)
        report.add_record(payment_audit_report_row)


def build_audit_report_row(payment_audit_data: PaymentAuditData) -> PaymentAuditCSV:
    """Build a single row of the payment audit report file"""

    payment: Payment = payment_audit_data.payment
    claim: Claim = payment.claim
    employee: Employee = claim.employee
    employee_address: EmployeeAddress = employee.addresses.first()  # TODO adjust after address validation work to get the most recent valid address
    address: Address = employee_address.address
    employer: Employer = claim.employer

    payment_audit_row = PaymentAuditCSV(
        pfml_payment_id=payment.payment_id,
        leave_type=get_leave_type(claim),
        first_name=payment.claim.employee.first_name,
        last_name=payment.claim.employee.last_name,
        address_line_1=address.address_line_one,
        address_line_2=address.address_line_two,
        city=address.city,
        state=address.geo_state.geo_state_description,
        zip=address.zip_code,
        payment_preference=get_payment_preference(employee),
        scheduled_payment_date=payment.payment_date.isoformat(),
        payment_period_start_date=payment.period_start_date.isoformat(),
        payment_period_end_date=payment.period_end_date.isoformat(),
        payment_amount=payment.amount,
        absence_case_number=claim.fineos_absence_id,
        c_value=payment.fineos_pei_c_value,
        i_value=payment.fineos_pei_i_value,
        employer_id=employer.fineos_employer_id,
        case_status=claim.fineos_absence_status.absence_status_description,
        leave_request_id="",  # TODO these are not currently persisted - persist somewhere and fetch or take out of audit
        leave_request_decision="",  # TODO these are not currently persisted - persist somewhere and fetch or take out of audit
        is_first_time_payment=bool_to_str(payment_audit_data.is_first_time_payment),
        is_updated_payment=bool_to_str(payment_audit_data.is_updated_payment),
        is_rejected_or_error=bool_to_str(payment_audit_data.is_rejected_or_error),
        days_in_rejected_state=payment_audit_data.days_in_rejected_state,
        rejected_by_program_integrity=bool_to_str(payment_audit_data.rejected_by_program_integrity),
        rejected_notes=payment_audit_data.rejected_notes,
    )

    return payment_audit_row


def bool_to_str(flag: Optional[bool]) -> str:
    if flag is None:
        return ""

    if flag:
        return "Y"
    else:
        return "N"


def get_leave_type(claim: Claim) -> str:
    claim_type: LkClaimType = claim.claim_type
    if claim_type.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id:
        return "Family"
    elif claim_type.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id:
        return "Medical"

    raise PaymentAuditRowError("Unexpected leave type %s" % claim_type.claim_type_description)


def get_payment_preference(employee: Employee) -> str:
    payment_preference: LkPaymentMethod = employee.payment_method
    if payment_preference.payment_method_id == PaymentMethod.ACH.payment_method_id:
        return "ACH"
    elif payment_preference.payment_method_id == PaymentMethod.CHECK.payment_method_id:
        return "Check"

    raise PaymentAuditRowError(
        "Unexpected payment preference %s" % payment_preference.payment_method_description
    )
