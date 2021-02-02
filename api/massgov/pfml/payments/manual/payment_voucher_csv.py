#
# Manual payment voucher tool - payment voucher CSV format.
#

import csv
import dataclasses


@dataclasses.dataclass
class PaymentVoucherCSV:
    """Manual payment voucher CSV format."""

    leave_type: str
    activity_code: str
    payment_doc_id_code: str
    payment_doc_id_dept: str
    doc_id: str
    mmars_vendor_code: str
    first_last_name: str
    payment_preference: str
    address_code: str
    address_line_1: str
    address_line_2: str
    city: str
    state: str
    zip: str
    scheduled_payment_date: str
    vendor_single_payment: str
    event_type: str
    payment_amount: str
    description: str
    vendor_invoice_number: str
    vendor_invoice_line: str
    vendor_invoice_date: str
    payment_period_start_date: str
    payment_period_end_date: str
    absence_case_number: str
    c_value: str
    i_value: str


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
)


@dataclasses.dataclass
class WritebackCSV:
    """FINEOS Writeback CSV format."""

    c_value: str
    i_value: str
    status: str
    status_effective_date: str
    status_reason: str
    transaction_status: str
    stock_no: str


WRITEBACK_CSV_HEADERS = WritebackCSV(
    c_value="pei_C_Value",
    i_value="pei_I_Value",
    status="status",
    status_effective_date="statusEffectiveDate",
    status_reason="statusReason",
    transaction_status="transactionStatus",
    stock_no="stockNo",
)


def payment_voucher_csv_writer(output_stream):
    writer = csv.DictWriter(
        output_stream,
        fieldnames=dataclasses.asdict(PAYMENT_VOUCHER_CSV_HEADERS).keys(),
        lineterminator="\n",
    )
    writer.writerow(dataclasses.asdict(PAYMENT_VOUCHER_CSV_HEADERS))
    return writer


def writeback_csv_writer(output_stream):
    writer = csv.DictWriter(
        output_stream,
        fieldnames=dataclasses.asdict(WRITEBACK_CSV_HEADERS).keys(),
        lineterminator="\n",
    )
    writer.writerow(dataclasses.asdict(WRITEBACK_CSV_HEADERS))
    return writer
