from dataclasses import dataclass
from typing import Optional

from massgov.pfml.delegated_payments.reporting.delegated_abstract_reporting import AbstractRecord


@dataclass
class PaymentAuditCSV(AbstractRecord):
    """Payment Audit Report CSV format"""

    pfml_payment_id: str
    leave_type: str
    first_name: str
    last_name: str
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state: str
    zip: str
    payment_preference: str
    scheduled_payment_date: str
    payment_period_start_date: str
    payment_period_end_date: str
    payment_amount: str
    absence_case_number: str
    c_value: str
    i_value: str
    employer_id: Optional[str]
    case_status: Optional[str]
    leave_request_id: Optional[str]
    leave_request_decision: Optional[str]
    is_first_time_payment: str
    is_updated_payment: str
    is_rejected_or_error: str
    days_in_rejected_state: str
    rejected_by_program_integrity: str
    rejected_notes: str


PAYMENT_AUDIT_CSV_HEADERS = PaymentAuditCSV(
    pfml_payment_id="PFML Payment Id",
    leave_type="Leave type",
    first_name="First Name",
    last_name="Last Name",
    address_line_1="Address Line 1",
    address_line_2="Address Line 2",
    city="City",
    state="State",
    zip="Zip",
    payment_preference="Payment Preference",
    scheduled_payment_date="Scheduled Payment Date",
    payment_period_start_date="Payment Period Start",
    payment_period_end_date="Payment Period End",
    payment_amount="Payment Amount",
    absence_case_number="Absence Case Number",
    c_value="C Value",
    i_value="I Value",
    employer_id="Employer ID",
    case_status="Case Status",
    leave_request_id="Leave Request ID",
    leave_request_decision="Leave Request Decision",
    is_first_time_payment="First Time Payment",
    is_updated_payment="Updated Payment",
    is_rejected_or_error="Currently Rejected",
    days_in_rejected_state="Days in Rejected State",
    rejected_by_program_integrity="Reject",
    rejected_notes="Reject Notes",
)
