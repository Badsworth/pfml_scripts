import os
from dataclasses import dataclass
from datetime import datetime, timedelta
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
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_csv import (
    PAYMENT_AUDIT_CSV_HEADERS,
    PaymentAuditCSV,
    PaymentAuditDetails,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_preapproval_util import (
    get_payment_preapproval_status,
)
from massgov.pfml.delegated_payments.pub.pub_check import _format_check_memo
from massgov.pfml.delegated_payments.reporting.delegated_abstract_reporting import (
    FileConfig,
    Report,
    ReportGroup,
)
from massgov.pfml.util.datetime import get_now_us_eastern, get_period_in_weeks


class PaymentAuditRowError(Exception):
    """An error in a row that prevents processing of the payment."""


@dataclass
class PaymentAuditData:
    """Wrapper class to create payment audit report"""

    payment: Payment
    employer_reimbursement_payment: Optional[Payment]
    is_first_time_payment: bool
    previously_errored_payment_count: int
    previously_rejected_payment_count: int
    previously_skipped_payment_count: int
    previously_paid_payment_count: int
    previously_paid_payments_string: Optional[str]
    gross_payment_amount: str
    net_payment_amount: str
    federal_withholding_amount: str
    state_withholding_amount: str
    employer_reimbursement_amount: str
    federal_withholding_i_value: str
    state_withholding_i_value: str
    employer_reimbursement_i_value: str


def write_audit_report(
    payment_audit_data_set: Iterable[PaymentAuditData],
    output_path: str,
    db_session: db.Session,
    report_name: str,
) -> Optional[str]:
    payment_audit_report_rows: List[PaymentAuditCSV] = []
    for payment_audit_data in payment_audit_data_set:
        payment_audit_report_rows.append(
            build_audit_report_row(payment_audit_data, get_now_us_eastern(), db_session)
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
    employer_reimbursement: Optional[Payment] = payment_audit_data.employer_reimbursement_payment

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

    employer_address: Optional[Address] = None
    employer_experian_address_pair: Optional[ExperianAddressPair] = (
        employer_reimbursement.experian_address_pair if employer_reimbursement else None
    )
    employer_experian_address: Optional[Address] = None
    employer_is_address_verified = "N"

    if employer_reimbursement:
        if employer_experian_address_pair:
            employer_experian_address = employer_experian_address_pair.experian_address
            employer_address = (
                employer_experian_address
                if employer_experian_address is not None
                else employer_experian_address_pair.fineos_address
            )
            employer_is_address_verified = "Y" if employer_experian_address is not None else "N"

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
    preapproval_status = get_payment_preapproval_status(
        payment, audit_report_details.audit_report_details_list, db_session
    )
    waiting_week_status = get_payment_in_waiting_week_status(payment, db_session)

    payment_audit_row = PaymentAuditCSV(
        pfml_payment_id=str(payment.payment_id),
        leave_type=get_leave_type(payment),
        fineos_customer_number=employee.fineos_customer_number if employee else None,
        first_name=payment.fineos_employee_first_name,
        last_name=payment.fineos_employee_last_name,
        dor_first_name=employee.first_name if employee else None,
        dor_last_name=employee.last_name if employee else None,
        address_line_1=address.address_line_one if address else None,
        address_line_2=address.address_line_two if address else None,
        city=address.city if address else None,
        state=address.geo_state.geo_state_description if address and address.geo_state else None,
        zip=address.zip_code if address else None,
        is_address_verified=is_address_verified,
        employer_id=str(employer.fineos_employer_id) if employer else None,
        employer_payee_name=employer_reimbursement.payee_name if employer_reimbursement else None,
        employer_address_line_1=employer_address.address_line_one if employer_address else None,
        employer_address_line_2=employer_address.address_line_two if employer_address else None,
        employer_city=employer_address.city if employer_address else None,
        employer_state=employer_address.geo_state.geo_state_description
        if employer_address and employer_address.geo_state
        else None,
        employer_zip=employer_address.zip_code if employer_address else None,
        employer_is_address_verified=employer_is_address_verified,
        payment_preference=get_payment_preference(payment),
        scheduled_payment_date=payment.payment_date.isoformat() if payment.payment_date else None,
        payment_period_start_date=payment_period_start_date,
        payment_period_end_date=payment_period_end_date,
        payment_period_weeks=str(payment_period_weeks),
        gross_payment_amount=str(payment_audit_data.gross_payment_amount),
        payment_amount=str(payment_audit_data.net_payment_amount),
        federal_withholding_amount=str(payment_audit_data.federal_withholding_amount),
        state_withholding_amount=str(payment_audit_data.state_withholding_amount),
        employer_reimbursement_amount=str(payment_audit_data.employer_reimbursement_amount),
        child_support_amount=None,
        absence_case_number=claim.fineos_absence_id,
        c_value=payment.fineos_pei_c_value,
        i_value=payment.fineos_pei_i_value,
        federal_withholding_i_value=str(payment_audit_data.federal_withholding_i_value),
        state_withholding_i_value=str(payment_audit_data.state_withholding_i_value),
        employer_reimbursement_i_value=str(payment_audit_data.employer_reimbursement_i_value),
        child_support_i_value=None,
        absence_case_creation_date=payment.absence_case_creation_date.isoformat()
        if payment.absence_case_creation_date
        else None,
        absence_start_date=claim.absence_period_start_date.isoformat()
        if claim.absence_period_start_date
        else None,
        absence_end_date=claim.absence_period_end_date.isoformat()
        if claim.absence_period_end_date
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
        dua_additional_income_details=audit_report_details.dua_additional_income_details,
        dia_additional_income_details=audit_report_details.dia_additional_income_details,
        dor_fineos_name_mismatch_details=audit_report_details.dor_fineos_name_mismatch_details,
        rejected_by_program_integrity=bool_to_str[
            audit_report_details.rejected_by_program_integrity
        ],
        skipped_by_program_integrity=bool_to_str[audit_report_details.skipped_by_program_integrity],
        rejected_notes=audit_report_details.rejected_notes,
        previously_paid_payment_count=str(payment_audit_data.previously_paid_payment_count),
        previously_paid_payments=payment_audit_data.previously_paid_payments_string,
        exceeds_26_weeks_total_leave_details=audit_report_details.exceeds_26_weeks_total_leave_details,
        payment_date_mismatch_details=audit_report_details.payment_date_mismatch_details,
        is_preapproved=bool_to_str[preapproval_status.is_preapproved()],
        preapproval_issues=preapproval_status.get_preapproval_issue_description(),
        waiting_week=waiting_week_status,
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
    else:
        return ""

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

        audit_report_column = (
            staged_audit_report_detail.audit_report_type.payment_audit_report_column
        )

        audit_report_action = (
            staged_audit_report_detail.audit_report_type.payment_audit_report_action
        )

        # Set the message in the correct column if the audit report action
        # dictates that we should populate a column
        if audit_report_column:
            details_dict = cast(Dict[str, Any], staged_audit_report_detail.details)
            audit_report_details[audit_report_column] = details_dict["message"]

        # The notes we add are based on the audit report description
        # unless an override is specified above for that particular type
        notes_to_add = audit_report_type
        if audit_report_action == AuditReportAction.REJECTED:
            rejected = True
            program_integrity_notes.append(f"{notes_to_add} (Rejected)")
        elif audit_report_action == AuditReportAction.SKIPPED:
            skipped = True
            program_integrity_notes.append(f"{notes_to_add} (Skipped)")
        elif audit_report_action == AuditReportAction.INFORMATIONAL:
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
        audit_report_details_list=staged_audit_report_details_list,
        **audit_report_details,
    )


def get_payment_in_waiting_week_status(payment: Payment, db_session: db.Session) -> str:

    claim: Claim = payment.claim

    if not claim or not claim.absence_period_start_date or not payment.period_start_date:
        return ""

    assert payment.period_start_date
    assert claim.absence_period_start_date
    waiting_week_end_date = claim.absence_period_start_date + timedelta(days=6)
    if claim.absence_period_start_date <= payment.period_start_date <= waiting_week_end_date:
        waiting_week_status = "1"
        possible_extension_claim = (
            db_session.query(Claim)
            .join(Employer)
            .filter(
                Claim.employee_id == payment.claim.employee_id,
                Employer.employer_fein == payment.claim.employer_fein,
                Claim.absence_period_end_date
                == (payment.claim.absence_period_start_date - timedelta(days=1)),  # type: ignore
            )
            .one_or_none()
        )

        if possible_extension_claim is not None:
            waiting_week_status = "Potential Extension"

        return waiting_week_status
    else:
        return ""
