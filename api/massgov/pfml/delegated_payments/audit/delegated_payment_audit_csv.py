from dataclasses import dataclass, field
from typing import List, Optional

from massgov.pfml.db.models.payments import PaymentAuditReportDetails, PaymentAuditReportType
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
<<<<<<< HEAD
    employer_name: Optional[str]
=======
    employer_id: Optional[str]
    employer_payee_name: Optional[str]
    employer_address_line_1: Optional[str]
    employer_address_line_2: Optional[str]
    employer_city: Optional[str]
    employer_state: Optional[str]
    employer_zip: Optional[str]
    employer_is_address_verified: Optional[str]
>>>>>>> origin
    payment_preference: Optional[str]
    scheduled_payment_date: Optional[str]
    payment_period_start_date: Optional[str]
    payment_period_end_date: Optional[str]
    payment_period_weeks: Optional[str]
    gross_payment_amount: Optional[str]
    payment_amount: Optional[str]
    federal_withholding_amount: Optional[str]
    state_withholding_amount: Optional[str]
    employer_reimbursement_amount: Optional[str]
    child_support_amount: Optional[str]
    absence_case_number: Optional[str]
    c_value: Optional[str]
    i_value: Optional[str]
    federal_withholding_i_value: Optional[str]
    state_withholding_i_value: Optional[str]
    employer_reimbursement_i_value: Optional[str]
    child_support_i_value: Optional[str]
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
    dua_additional_income_details: Optional[str] = None
    dia_additional_income_details: Optional[str] = None
    rejected_by_program_integrity: Optional[str] = None
    skipped_by_program_integrity: Optional[str] = None
    rejected_notes: Optional[str] = None
    previously_paid_payment_count: str = "0"
    previously_paid_payments: Optional[str] = None
    exceeds_26_weeks_total_leave_details: Optional[str] = None
    payment_date_mismatch_details: Optional[str] = None
    is_preapproved: Optional[str] = None
    preapproval_issues: Optional[str] = None


@dataclass
class PaymentAuditDetails:
    """Subset of payment audit report relevant to system generated details"""

    dua_additional_income_details: Optional[str] = None
    dia_additional_income_details: Optional[str] = None
    dor_fineos_name_mismatch_details: Optional[str] = None
    rejected_by_program_integrity: bool = False
    skipped_by_program_integrity: bool = False
    rejected_notes: Optional[str] = None
    exceeds_26_weeks_total_leave_details: Optional[str] = None
    payment_date_mismatch_details: Optional[str] = None
    audit_report_details_list: List[PaymentAuditReportDetails] = field(default_factory=list)


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
<<<<<<< HEAD
    employer_name="Employer Name",
=======
    employer_id="Employer ID",
    employer_payee_name="Employer Payee Name",
    employer_address_line_1="Employer Address Line 1",
    employer_address_line_2="Employer Address Line 2",
    employer_city="Employer City",
    employer_state="Employer State",
    employer_zip="Employer Zip",
    employer_is_address_verified="Employer Address Verified",
>>>>>>> origin
    payment_preference="Payment Preference",
    scheduled_payment_date="Scheduled Payment Date",
    payment_period_start_date="Payment Period Start",
    payment_period_end_date="Payment Period End",
    payment_period_weeks="Payment Period Weeks",
    gross_payment_amount="Gross Payment Amount",
    payment_amount="Payment Amount",
    federal_withholding_amount="Federal Withholding Amount",
    state_withholding_amount="State Withholding Amount",
    employer_reimbursement_amount="Employer Reimbursement Amount",
    child_support_amount="Child Support Amount",
    absence_case_number="Absence Case Number",
    c_value="C Value",
    i_value="I Value",
    federal_withholding_i_value="Federal Withholding I Value",
    state_withholding_i_value="State Withholding I Value",
    employer_reimbursement_i_value="Employer Reimbursement I Value",
    child_support_i_value="Child Support I Value",
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
    dua_additional_income_details=PaymentAuditReportType.DUA_ADDITIONAL_INCOME.payment_audit_report_type_description,
    dia_additional_income_details=PaymentAuditReportType.DIA_ADDITIONAL_INCOME.payment_audit_report_type_description,
    rejected_by_program_integrity="Reject",
    skipped_by_program_integrity="Skip",
    rejected_notes="Reject Notes",
    previously_paid_payment_count="Previously Paid Payment Count",
    previously_paid_payments="List of Previously Paid Payments",
    exceeds_26_weeks_total_leave_details=">26 weeks",
    payment_date_mismatch_details=PaymentAuditReportType.PAYMENT_DATE_MISMATCH.payment_audit_report_type_description,
    is_preapproved="Is Pre-approved",
    preapproval_issues="Pre-approval Issues",
)
