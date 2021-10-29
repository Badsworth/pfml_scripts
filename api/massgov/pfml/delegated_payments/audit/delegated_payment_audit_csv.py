from dataclasses import dataclass
from typing import Optional

from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.delegated_payments.reporting.delegated_abstract_reporting import AbstractRecord


@dataclass
class PaymentAuditCSV(AbstractRecord):
    """Payment Audit Report CSV format"""

    pfml_payment_id: Optional[str]
    leave_type: Optional[str]
    fineos_customer_number: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    dor_first_name: Optional[str]
    dor_last_name: Optional[str]
    dor_fineos_name_mismatch_details: Optional[str]
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    is_address_verified: Optional[str]
    payment_preference: Optional[str]
    scheduled_payment_date: Optional[str]
    payment_period_start_date: Optional[str]
    payment_period_end_date: Optional[str]
    payment_period_weeks: Optional[str]
    payment_amount: Optional[str]
    absence_case_number: Optional[str]
    c_value: Optional[str]
    i_value: Optional[str]
    employer_id: Optional[str]
    absence_case_creation_date: Optional[str]
    absence_start_date: Optional[str]
    absence_end_date: Optional[str]
    case_status: Optional[str]
    leave_request_decision: Optional[str]
    check_description: Optional[str]
    is_first_time_payment: Optional[str]
    previously_errored_payment_count: Optional[str]
    previously_rejected_payment_count: Optional[str]
    previously_skipped_payment_count: Optional[str]

    max_weekly_benefits_details: Optional[str] = None
    dua_dia_reduction_details: Optional[str] = None
    rejected_by_program_integrity: Optional[str] = None
    skipped_by_program_integrity: Optional[str] = None
    rejected_notes: Optional[str] = None


@dataclass
class PaymentAuditDetails:
    """Subset of payment audit report relevant to system generated details"""

    max_weekly_benefits_details: Optional[str] = None
    dua_dia_reduction_details: Optional[str] = None
    dor_fineos_name_mismatch_details: Optional[str] = None
    rejected_by_program_integrity: bool = False
    skipped_by_program_integrity: bool = False
    rejected_notes: Optional[str] = None


PAYMENT_AUDIT_CSV_HEADERS = PaymentAuditCSV(
    pfml_payment_id="PFML Payment Id",
    leave_type="Leave type",
    fineos_customer_number="Customer Number",
    first_name="First Name",
    last_name="Last Name",
    dor_first_name="DOR First Name",
    dor_last_name="DOR Last Name",
    dor_fineos_name_mismatch_details=PaymentAuditReportType.DOR_FINEOS_NAME_MISMATCH.payment_audit_report_type_description,
    address_line_1="Address Line 1",
    address_line_2="Address Line 2",
    city="City",
    state="State",
    zip="Zip",
    is_address_verified="Address Verified",
    payment_preference="Payment Preference",
    scheduled_payment_date="Scheduled Payment Date",
    payment_period_start_date="Payment Period Start",
    payment_period_end_date="Payment Period End",
    payment_period_weeks="Payment Period Weeks",
    payment_amount="Payment Amount",
    absence_case_number="Absence Case Number",
    c_value="C Value",
    i_value="I Value",
    employer_id="Employer ID",
    absence_case_creation_date="Absence Case Creation Date",
    absence_start_date="Absence Case Start Date",
    absence_end_date="Absence Case End Date",
    case_status="Case Status",
    leave_request_decision="Leave Request Decision",
    check_description="Check Memo",
    is_first_time_payment="First Time Payment",
    previously_errored_payment_count="Previously Errored Payment Count",
    previously_rejected_payment_count="Previously Rejected Payment Count",
    previously_skipped_payment_count="Previously Skipped Payment Count",
    max_weekly_benefits_details=PaymentAuditReportType.MAX_WEEKLY_BENEFITS.payment_audit_report_type_description,
    dua_dia_reduction_details=PaymentAuditReportType.DUA_DIA_REDUCTION.payment_audit_report_type_description,
    rejected_by_program_integrity="Reject",
    skipped_by_program_integrity="Skip",
    rejected_notes="Reject Notes",
)
