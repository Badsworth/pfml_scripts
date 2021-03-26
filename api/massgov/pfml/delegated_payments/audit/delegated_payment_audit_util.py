import pathlib
from dataclasses import dataclass
from typing import Iterable, List, Optional

from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    ClaimType,
    Employee,
    EmployeeAddress,
    Employer,
    LkClaimType,
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
    is_previously_errored_payment: bool
    is_previously_rejected_payment: bool
    number_of_times_in_rejected_or_error_state: int
    rejected_by_program_integrity: Optional[bool] = None
    rejected_notes: str = ""


def write_audit_report(
    payment_audit_data_set: Iterable[PaymentAuditData],
    output_path: str,
    db_session: db.Session,
    report_name: str,
) -> Optional[pathlib.Path]:
    payment_audit_report_rows: List[PaymentAuditCSV] = []
    for payment_audit_data in payment_audit_data_set:
        payment_audit_report_rows.append(build_audit_report_row(payment_audit_data))

    return write_audit_report_rows(payment_audit_report_rows, output_path, db_session, report_name)


def write_audit_report_rows(
    payment_audit_report_rows: Iterable[PaymentAuditCSV],
    output_path: str,
    db_session: db.Session,
    report_name: str,
) -> Optional[pathlib.Path]:
    # Setup the output file
    file_config = FileConfig(file_prefix=output_path)
    report_group = ReportGroup(file_config=file_config)

    report = Report(report_name=report_name, header_record=PAYMENT_AUDIT_CSV_HEADERS)
    report_group.add_report(report)

    for payment_audit_report_row in payment_audit_report_rows:
        report.add_record(payment_audit_report_row)

    return report_group.create_and_send_reports()


def build_audit_report_row(payment_audit_data: PaymentAuditData) -> PaymentAuditCSV:
    """Build a single row of the payment audit report file"""

    payment: Payment = payment_audit_data.payment
    claim: Claim = payment.claim
    employee: Employee = claim.employee
    employee_address: EmployeeAddress = employee.addresses.first()  # TODO adjust after address validation work to get the most recent valid address
    address: Address = employee_address.address if employee_address else None
    employer: Employer = claim.employer

    payment_audit_row = PaymentAuditCSV(
        pfml_payment_id=payment.payment_id,
        leave_type=get_leave_type(claim),
        first_name=payment.claim.employee.first_name,
        last_name=payment.claim.employee.last_name,
        address_line_1=address.address_line_one if address else None,
        address_line_2=address.address_line_two if address else None,
        city=address.city if address else None,
        state=address.geo_state.geo_state_description if address and address.geo_state else None,
        zip=address.zip_code if address else None,
        payment_preference=get_payment_preference(payment),
        scheduled_payment_date=payment.payment_date.isoformat(),
        payment_period_start_date=payment.period_start_date.isoformat(),
        payment_period_end_date=payment.period_end_date.isoformat(),
        payment_amount=payment.amount,
        absence_case_number=claim.fineos_absence_id,
        c_value=payment.fineos_pei_c_value,
        i_value=payment.fineos_pei_i_value,
        employer_id=employer.fineos_employer_id if employer else None,
        case_status=claim.fineos_absence_status.absence_status_description
        if claim.fineos_absence_status
        else None,
        is_first_time_payment=bool_to_str[payment_audit_data.is_first_time_payment],
        is_previously_errored_payment=bool_to_str[payment_audit_data.is_previously_errored_payment],
        is_previously_rejected_payment=bool_to_str[
            payment_audit_data.is_previously_rejected_payment
        ],
        number_of_times_in_rejected_or_error_state=payment_audit_data.number_of_times_in_rejected_or_error_state,
        rejected_by_program_integrity=bool_to_str[payment_audit_data.rejected_by_program_integrity],
        rejected_notes=payment_audit_data.rejected_notes,
    )

    return payment_audit_row


bool_to_str = {None: "", True: "Y", False: "N"}


def get_leave_type(claim: Claim) -> Optional[str]:
    claim_type: LkClaimType = claim.claim_type
    if not claim_type:
        return None

    if claim_type.claim_type_id == ClaimType.FAMILY_LEAVE.claim_type_id:
        return "Family"
    elif claim_type.claim_type_id == ClaimType.MEDICAL_LEAVE.claim_type_id:
        return "Medical"

    raise PaymentAuditRowError("Unexpected leave type %s" % claim_type.claim_type_description)


def get_payment_preference(payment: Payment) -> str:
    if payment.disb_method_id == PaymentMethod.ACH.payment_method_id:
        return "ACH"
    elif payment.disb_method_id == PaymentMethod.CHECK.payment_method_id:
        return "Check"

    raise PaymentAuditRowError(
        "Unexpected payment preference %s" % payment.disb_method.payment_method_description
    )
