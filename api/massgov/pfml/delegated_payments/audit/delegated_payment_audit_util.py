import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, cast

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    ClaimType,
    Employee,
    Employer,
    ExperianAddressPair,
    LkClaimType,
    Payment,
    PaymentMethod,
)
from massgov.pfml.db.models.payments import (
    AuditReportAction,
    LkPaymentAuditReportType,
    PaymentAuditReportDetails,
    PaymentAuditReportType,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
    PaymentAuditDetails,
)
from massgov.pfml.delegated_payments.pub.pub_check import _format_check_memo
from massgov.pfml.delegated_payments.reporting.delegated_abstract_reporting import (
    FileConfig,
    Report,
    ReportGroup,
)
from massgov.pfml.util.datetime import get_period_in_weeks

# Specify an override for the notes to put if the
# description on the audit report type doesn't match the message
AUDIT_REPORT_NOTES_OVERRIDE = {
    PaymentAuditReportType.MAX_WEEKLY_BENEFITS.payment_audit_report_type_id: "Weekly benefit amount exceeds $850"
}


class PaymentAuditRowError(Exception):
    """An error in a row that prevents processing of the payment."""


@dataclass
class PaymentAuditData:
    """Wrapper class to create payment audit report"""

    payment: Payment
    is_first_time_payment: bool
    previously_errored_payment_count: int
    previously_rejected_payment_count: int
    previously_skipped_payment_count: int


def write_audit_report(
    payment_audit_data_set: Iterable[PaymentAuditData],
    output_path: str,
    db_session: db.Session,
    report_name: str,
) -> Optional[str]:
    payment_audit_report_rows: List[PaymentAuditCSV] = []
    for payment_audit_data in payment_audit_data_set:
        payment_audit_report_rows.append(
            build_audit_report_row(payment_audit_data, payments_util.get_now(), db_session)
        )

    return write_audit_report_rows(payment_audit_report_rows, output_path, db_session, report_name)


def write_audit_report_rows(
    payment_audit_report_rows: Iterable[PaymentAuditCSV],
    output_path: str,
    db_session: db.Session,
    report_name: str,
) -> Optional[str]:
    # Setup the output file
    file_prefix = os.path.join(output_path, payments_util.Constants.S3_OUTBOUND_SENT_DIR)
    file_config = FileConfig(file_prefix=file_prefix)
    report_group = ReportGroup(file_config=file_config)

    report = Report(report_name=report_name, header_record=PAYMENT_AUDIT_CSV_HEADERS)
    report_group.add_report(report)

    for payment_audit_report_row in payment_audit_report_rows:
        report.add_record(payment_audit_report_row)

    reports = report_group.create_and_send_reports()
    if not reports:
        return None  # This will error further up.
    elif len(reports) != 1:
        raise Exception("Audit report generation created %i reports: %s" % (len(reports), reports))

    return reports[0]


def build_audit_report_row(
    payment_audit_data: PaymentAuditData, audit_report_time: datetime, db_session: db.Session
) -> PaymentAuditCSV:
    """Build a single row of the payment audit report file"""

    payment: Payment = payment_audit_data.payment
    claim: Claim = payment.claim
    employee: Employee = claim.employee

    address: Optional[Address] = None
    experian_address_pair: Optional[ExperianAddressPair] = payment.experian_address_pair
    experian_address: Optional[Address] = None
    is_address_verified = "N"

    if experian_address_pair:
        experian_address = experian_address_pair.experian_address
        address = (
            experian_address
            if experian_address is not None
            else experian_address_pair.fineos_address
        )
        is_address_verified = "Y" if experian_address is not None else "N"

    employer: Employer = claim.employer

    check_description = _format_check_memo(payment)

    payment_period_start_date = (
        payment.period_start_date.isoformat() if payment.period_start_date else None
    )
    payment_period_end_date = (
        payment.period_end_date.isoformat() if payment.period_end_date else None
    )

    payment_period_weeks = None
    if payment.period_start_date and payment.period_end_date:
        payment_period_weeks = get_period_in_weeks(
            payment.period_start_date, payment.period_end_date
        )

    audit_report_details = get_payment_audit_report_details(payment, audit_report_time, db_session)

    payment_audit_row = PaymentAuditCSV(
        pfml_payment_id=str(payment.payment_id),
        leave_type=get_leave_type(payment),
        fineos_customer_number=employee.fineos_customer_number
        if employee.fineos_customer_number
        else None,
        first_name=payment.fineos_employee_first_name,
        last_name=payment.fineos_employee_last_name,
        address_line_1=address.address_line_one if address else None,
        address_line_2=address.address_line_two if address else None,
        city=address.city if address else None,
        state=address.geo_state.geo_state_description if address and address.geo_state else None,
        zip=address.zip_code if address else None,
        is_address_verified=is_address_verified,
        payment_preference=get_payment_preference(payment),
        scheduled_payment_date=payment.payment_date.isoformat() if payment.payment_date else None,
        payment_period_start_date=payment_period_start_date,
        payment_period_end_date=payment_period_end_date,
        payment_period_weeks=str(payment_period_weeks),
        payment_amount=str(payment.amount),
        absence_case_number=claim.fineos_absence_id,
        c_value=payment.fineos_pei_c_value,
        i_value=payment.fineos_pei_i_value,
        employer_id=str(employer.fineos_employer_id) if employer else None,
        absence_case_creation_date=payment.absence_case_creation_date.isoformat()
        if payment.absence_case_creation_date
        else None,
        case_status=claim.fineos_absence_status.absence_status_description
        if claim.fineos_absence_status
        else None,
        leave_request_decision=payment.leave_request_decision
        if payment.leave_request_decision
        else None,
        check_description=check_description,
        is_first_time_payment=bool_to_str[payment_audit_data.is_first_time_payment],
        previously_errored_payment_count=str(payment_audit_data.previously_errored_payment_count),
        previously_rejected_payment_count=str(payment_audit_data.previously_rejected_payment_count),
        previously_skipped_payment_count=str(payment_audit_data.previously_skipped_payment_count),
        max_weekly_benefits_details=audit_report_details.max_weekly_benefits_details,
        dua_dia_reduction_details=audit_report_details.dua_dia_reduction_details,
        rejected_by_program_integrity=bool_to_str[
            audit_report_details.rejected_by_program_integrity
        ],
        skipped_by_program_integrity=bool_to_str[audit_report_details.skipped_by_program_integrity],
        rejected_notes=audit_report_details.rejected_notes,
    )

    return payment_audit_row


bool_to_str = {None: "", True: "Y", False: ""}


def get_leave_type(payment: Payment) -> Optional[str]:
    claim_type: LkClaimType = payment.claim_type
    if not claim_type:
        return ""

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


def stage_payment_audit_report_details(
    payment: Payment,
    audit_report_type: LkPaymentAuditReportType,
    message: str,
    import_log_id: Optional[int],
    db_session: db.Session,
) -> None:
    details: Dict[str, Any] = {}
    details["message"] = message

    audit_report_details = PaymentAuditReportDetails(
        payment_id=payment.payment_id,
        audit_report_type_id=audit_report_type.payment_audit_report_type_id,
        details=details,
        import_log_id=import_log_id,
    )
    db_session.add(audit_report_details)


def get_payment_audit_report_details(
    payment: Payment, added_to_audit_report_at: datetime, db_session: db.Session
) -> PaymentAuditDetails:
    """Returns an partial object of the payment audit report row relevant to details"""
    staged_audit_report_details_list: List[PaymentAuditReportDetails] = (
        db_session.query(PaymentAuditReportDetails)
        .filter(PaymentAuditReportDetails.payment_id == payment.payment_id)
        .order_by(PaymentAuditReportDetails.created_at.asc())
        .all()
    )

    if len(staged_audit_report_details_list) == 0:
        return PaymentAuditDetails()

    audit_report_details = {}
    rejected = False
    skipped = False
    program_integrity_notes = []

    for staged_audit_report_detail in staged_audit_report_details_list:
        audit_report_type = (
            staged_audit_report_detail.audit_report_type.payment_audit_report_type_description
        )

        audit_report_action = (
            staged_audit_report_detail.audit_report_type.payment_audit_report_action
        )

        # Set the message in the correct column if the audit report action
        # dictates that we should populate a column
        if AuditReportAction.should_populate_column(audit_report_action):
            key = f"{audit_report_type.lower()}_details".replace(" ", "_")
            details_dict = cast(Dict[str, Any], staged_audit_report_detail.details)
            audit_report_details[key] = details_dict["message"]

        # The notes we add are based on the audit report description
        # unless an override is specified above for that particular type
        notes_to_add = AUDIT_REPORT_NOTES_OVERRIDE.get(
            staged_audit_report_detail.audit_report_type_id, audit_report_type
        )
        if AuditReportAction.is_rejected(audit_report_action):
            rejected = True
            program_integrity_notes.append(f"{notes_to_add} (Rejected)")
        elif AuditReportAction.is_skipped(audit_report_action):
            skipped = True
            program_integrity_notes.append(f"{notes_to_add} (Skipped)")
        elif AuditReportAction.is_informational(audit_report_action):
            program_integrity_notes.append(f"{notes_to_add}")

        # Mark the details row as processed
        staged_audit_report_detail.added_to_audit_report_at = added_to_audit_report_at

    # set aggregated notes
    rejected_notes = None
    if len(program_integrity_notes) > 0:
        rejected_notes = ", ".join(program_integrity_notes)

    return PaymentAuditDetails(
        rejected_by_program_integrity=rejected,
        skipped_by_program_integrity=(not rejected and skipped),
        rejected_notes=rejected_notes,
        **audit_report_details,
    )
