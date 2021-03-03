from dataclasses import dataclass
from typing import List, Optional

import massgov.pfml.payments.config as payments_config
import massgov.pfml.payments.payments_util as payments_util
from massgov.pfml.payments.reporting.abstract_reporting import (
    AbstractRecord,
    EmailConfig,
    FileConfig,
    Report,
    ReportGroup,
)
from massgov.pfml.util.aws.ses import EmailRecipient

# The column headers in the CSV
DESCRIPTION_COLUMN = "Description of Issue"
FINEOS_CUSTOMER_NUM_COLUMN = "FINEOS Customer Number"
FINEOS_ABSENCE_ID_COLUMN = "FINEOS Absence Case ID"
MMARS_VENDOR_CUST_NUM_COLUMN = "MMARS Vendor Customer Number"
MMARS_DOCUMENT_ID_COLUMN = "MMARS Document ID"
PAYMENT_DATE_COLUMN = "Payment Date"

CSV_HEADER: List[str] = [
    DESCRIPTION_COLUMN,
    FINEOS_CUSTOMER_NUM_COLUMN,
    FINEOS_ABSENCE_ID_COLUMN,
    MMARS_VENDOR_CUST_NUM_COLUMN,
    MMARS_DOCUMENT_ID_COLUMN,
    PAYMENT_DATE_COLUMN,
]


FINEOS_PAYMENTS_EMAIL_SUBJECT = "DFML CPS Reports for {0}"
FINEOS_PAYMENTS_EMAIL_BODY = "This is the daily error report for {0}. Attached are errors resulting from the {1}. Note that the error report might be an empty file. If this happens it means there are no outstanding errors in that category for the day."
CTR_PAYMENTS_EMAIL_SUBJECT = "DFML CTR Reports for {0}"
CTR_PAYMENTS_EMAIL_BODY = "This is the daily error report for {0}. Attached are errors resulting from the {1}. Note that the error report might be an empty file. If this happens it means there are no outstanding errors in that category for the day."


@dataclass
class ErrorRecord(AbstractRecord):
    description: Optional[str] = None
    fineos_customer_number: Optional[str] = None
    fineos_absence_id: Optional[str] = None
    ctr_vendor_customer_code: Optional[str] = None
    mmars_document_id: Optional[str] = None
    payment_date: Optional[str] = None


#######################
## Factory functions ##
#######################


def initialize_fineos_payments_error_report_group() -> ReportGroup:
    return ReportGroup(
        email_config=_get_fineos_payments_error_report_email_config(),
        file_config=_get_error_report_s3_config(),
    )


def initialize_ctr_payments_error_report_group() -> ReportGroup:
    return ReportGroup(
        email_config=_get_ctr_payments_error_report_email_config(),
        file_config=_get_error_report_s3_config(),
    )


def initialize_error_report(report_name: str) -> Report:
    return Report(report_name=report_name, header_record=_get_header_record())


#######################
## Utility functions ##
#######################


def _get_header_record() -> ErrorRecord:
    return ErrorRecord(
        description=DESCRIPTION_COLUMN,
        fineos_customer_number=FINEOS_CUSTOMER_NUM_COLUMN,
        fineos_absence_id=FINEOS_ABSENCE_ID_COLUMN,
        ctr_vendor_customer_code=MMARS_VENDOR_CUST_NUM_COLUMN,
        mmars_document_id=MMARS_DOCUMENT_ID_COLUMN,
        payment_date=PAYMENT_DATE_COLUMN,
    )


def _get_fineos_payments_error_report_email_config() -> EmailConfig:
    payments_email_config = payments_config.get_email_config()
    now = payments_util.get_now()
    return EmailConfig(
        sender=payments_email_config.pfml_email_address,
        recipient=EmailRecipient(
            to_addresses=[payments_email_config.dfml_business_operations_email_address]
        ),
        subject=FINEOS_PAYMENTS_EMAIL_SUBJECT.format(now.strftime("%m/%d/%Y")),
        body_text=FINEOS_PAYMENTS_EMAIL_BODY.format(now.strftime("%m/%d/%Y"), "FINEOS processing"),
        bounce_forwarding_email_address_arn=payments_email_config.bounce_forwarding_email_address_arn,
    )


def _get_ctr_payments_error_report_email_config() -> EmailConfig:
    payments_email_config = payments_config.get_email_config()
    now = payments_util.get_now()
    return EmailConfig(
        sender=payments_email_config.pfml_email_address,
        recipient=EmailRecipient(
            to_addresses=[payments_email_config.dfml_business_operations_email_address]
        ),
        subject=CTR_PAYMENTS_EMAIL_SUBJECT.format(now.strftime("%m/%d/%Y")),
        body_text=CTR_PAYMENTS_EMAIL_BODY.format(now.strftime("%m/%d/%Y"), "CTR processing"),
        bounce_forwarding_email_address_arn=payments_email_config.bounce_forwarding_email_address_arn,
    )


def _get_error_report_s3_config() -> FileConfig:
    return FileConfig(file_prefix=payments_config.get_s3_config().pfml_error_reports_path)
