#
# Manual payment voucher tool - payment voucher CSV format.
#

import csv
import dataclasses
from typing import Optional


@dataclasses.dataclass
class PaymentVoucherCSV:
    """Manual payment voucher CSV format."""

    leave_type: str
    activity_code: str
    payment_doc_id_code: str
    payment_doc_id_dept: str
    doc_id: str
    mmars_vendor_code: str
    first_last_name: Optional[str]
    payment_preference: Optional[str]
    address_code: str
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    scheduled_payment_date: str
    vendor_single_payment: str
    event_type: str
    payment_amount: Optional[str]
    description: str
    vendor_invoice_number: str
    vendor_invoice_line: str
    vendor_invoice_date: str
    payment_period_start_date: str
    payment_period_end_date: str
    absence_case_number: str
    c_value: str
    i_value: str
    fineos_customer_number_employee: Optional[str]
    case_status: str
    employer_id: str
    leave_request_id: Optional[str]
    leave_request_decision: Optional[str]
    payment_event_type: Optional[str]
    vcm_flag: str
    absence_case_creation_date: Optional[str]

    # fields mostly to be populated manually by team using the voucher file for
    # actually processing the payments
    good_to_pay_from_prior_batch: str
    had_a_payment_in_a_prior_batch_by_vc_code: str
    inv: str  # exists on the VALID payments sent to EOLFIN/ MMARS nnnnn
    payments_offset_to_zero: str
    claimants_that_have_zero_or_credit_value: str  # fill this column in with "1" if the payment amount is <= $0
    is_exempt: str
    leave_decision_not_approved: str
    has_a_check_preference_with_an_adl2_issue: str
    adl2_corrected: str
    removed_or_added_after_audit_of_info: str
    to_be_removed_from_file: str
    notes: str


PAYMENT_VOUCHER_CSV_HEADERS = PaymentVoucherCSV(
    leave_type="Leave type",
    activity_code="Activity code",
    payment_doc_id_code="Payment doc ID CODE",
    payment_doc_id_dept="Payment doc ID DEPT",
    doc_id="DOC ID",
    mmars_vendor_code="MMARS vendor code",
    first_last_name="First last name",
    payment_preference="Payment preference",
    address_code="Address code",
    address_line_1="Address line 1",
    address_line_2="Address line 2",
    city="City",
    state="State",
    zip="Zip",
    scheduled_payment_date="Scheduled payment date",
    vendor_single_payment="Vendor single payment",
    event_type="Event type",
    payment_amount="Payment amount",
    description="Check description",
    vendor_invoice_number="Vendor invoice number",
    vendor_invoice_line="Vendor invoice line",
    vendor_invoice_date="Vendor invoice date",
    payment_period_start_date="Payment period start date",
    payment_period_end_date="Payment period end date",
    absence_case_number="Absence case number",
    c_value="C value",
    i_value="I value",
    fineos_customer_number_employee="FINEOS customer number (Employee)",
    case_status="Case Status",
    employer_id="Employer ID",
    leave_request_id="Leave request ID",
    leave_request_decision="Leave request decision",
    payment_event_type="FINEOS PEI event type",
    vcm_flag="Has Pending VCM",
    absence_case_creation_date="Absence case creation date",
    good_to_pay_from_prior_batch="Good to pay from prior batch",
    had_a_payment_in_a_prior_batch_by_vc_code="Had a payment in a prior batch (by VC Code)",
    inv="Inv # Exists on the VALID payments sent to EOLFIN/ MMARS nnnnn",
    payments_offset_to_zero="Payments offset to 0",
    claimants_that_have_zero_or_credit_value="Claimants that have $0 or credit value",
    is_exempt="Is Exempt",
    leave_decision_not_approved="LEAVE DECISION NOT APPROVED",
    has_a_check_preference_with_an_adl2_issue="Has a Check Preference with an ADL2 Issue",
    adl2_corrected="ADL2 Corrected? (-1)",
    removed_or_added_after_audit_of_info="REMOVED or ADDED after audit of info",
    to_be_removed_from_file="TO BE REMOVED FROM FILE",
    notes="NOTES:",
)


@dataclasses.dataclass
class WritebackCSV:
    """FINEOS Writeback CSV format."""

    c_value: str
    i_value: str
    status: str
    transaction_status: str
    trans_status_date: str
    stock_no: str


WRITEBACK_CSV_HEADERS = WritebackCSV(
    c_value="pei_C_Value",
    i_value="pei_I_Value",
    status="status",
    transaction_status="transactionStatus",
    trans_status_date="transStatusDate",
    stock_no="transactionNo",
)


def payment_voucher_csv_writer(output_stream):
    writer = csv.DictWriter(
        output_stream,
        fieldnames=dataclasses.asdict(PAYMENT_VOUCHER_CSV_HEADERS).keys(),
        lineterminator="\n",
        quoting=csv.QUOTE_ALL,
    )
    writer.writerow(dataclasses.asdict(PAYMENT_VOUCHER_CSV_HEADERS))
    return writer


def writeback_csv_writer(output_stream):
    writer = csv.DictWriter(
        output_stream,
        fieldnames=dataclasses.asdict(WRITEBACK_CSV_HEADERS).keys(),
        lineterminator="\n",
        quoting=csv.QUOTE_ALL,
    )
    writer.writerow(dataclasses.asdict(WRITEBACK_CSV_HEADERS))
    return writer
