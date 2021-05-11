from dataclasses import dataclass
from typing import Optional

from massgov.pfml.delegated_payments.reporting.delegated_abstract_reporting import AbstractRecord


@dataclass
class PaymentAuditCSV(AbstractRecord):
    """Payment Audit Report CSV format"""

    pfml_payment_id: Optional[str]
    leave_type: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
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
    payment_amount: Optional[str]
    absence_case_number: Optional[str]
    c_value: Optional[str]
    i_value: Optional[str]
    fineos_customer_number: Optional[str]
    employer_id: Optional[str]
    case_status: Optional[str]
    leave_request_decision: Optional[str]
    check_description: Optional[str]
    is_first_time_payment: Optional[str]
    is_previously_errored_payment: Optional[str]
    is_previously_rejected_payment: Optional[str]
    number_of_times_in_rejected_or_error_state: Optional[str]
    rejected_by_program_integrity: Optional[str]
    rejected_notes: Optional[str]


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
    is_address_verified="Address Verified",
    payment_preference="Payment Preference",
    scheduled_payment_date="Scheduled Payment Date",
    payment_period_start_date="Payment Period Start",
    payment_period_end_date="Payment Period End",
    payment_amount="Payment Amount",
    absence_case_number="Absence Case Number",
    c_value="C Value",
    i_value="I Value",
    fineos_customer_number="Customer Number",
    employer_id="Employer ID",
    case_status="Case Status",
    leave_request_decision="Leave Request Decision",
    check_description="Check Memo",
    is_first_time_payment="First Time Payment",
    is_previously_errored_payment="Previously Errored Payment",
    is_previously_rejected_payment="Previously Rejected Payment",
    number_of_times_in_rejected_or_error_state="Number of times in Error or Rejected State",
    rejected_by_program_integrity="Reject",
    rejected_notes="Reject Notes",
)
