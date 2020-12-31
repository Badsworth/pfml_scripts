import os
import re
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, validator

import massgov.pfml.util.logging as logging
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.util.files import read_file

logger = logging.get_logger(__name__)

# The character encoding for the email.
CHARSET = "UTF-8"


class EmailRecipient(BaseModel):
    to_addresses: List[str]
    cc_addresses: Optional[List[str]] = []
    bcc_addresses: Optional[List[str]] = []

    @validator("to_addresses")
    def check_to_addresses_format(cls, emails):  # noqa: B902
        if len(emails) == 0:
            validation_error = ValidationErrorDetail(
                message="Have to provide at least one valid email address",
                type="missing_email_format",
            )
            raise ValidationException(
                errors=[validation_error], message="Email validation error", data={}
            )
        for email in emails:
            cls.check_email_format(email)

        return emails

    @validator("cc_addresses", "bcc_addresses", each_item=True)
    def check_cc_and_bcc_format(cls, email):  # noqa: B902
        cls.check_email_format(email)
        return email

    @classmethod
    def check_email_format(cls, email):
        regex = "^[a-z0-9]+[\\._]?[a-z0-9]+[@]\\w+[.]\\w{2,3}$"
        if not re.match(regex, email):
            validation_error = ValidationErrorDetail(
                message=f"Email format has to match {regex}", type="incorrect_email_format",
            )
            raise ValidationException(
                errors=[validation_error], message="Email validation error", data={}
            )


def send_email(
    recipient: EmailRecipient,
    subject: str,
    body_text: str,
    sender: str,
    bounce_forwarding_email: str,
) -> Dict:
    aws_ses = boto3.client("ses")

    try:
        response = aws_ses.send_email(
            Destination={
                "BccAddresses": recipient.bcc_addresses,
                "CcAddresses": recipient.cc_addresses,
                "ToAddresses": recipient.to_addresses,
            },
            Message={
                "Body": {"Text": {"Charset": CHARSET, "Data": body_text,},},
                "Subject": {"Charset": CHARSET, "Data": subject,},
            },
            Source=sender,
            ReturnPath=bounce_forwarding_email,
        )
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
        return response
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.exception("Error sending email: %s", error_message)
        raise RuntimeError("Error sending email: %s", error_message)


def send_email_with_attachment(
    recipient: EmailRecipient, subject: str, body_text: str, sender: str, attachments: List[str]
) -> Dict:
    """
    attachments is a list containing the full-paths to the file that will be attached to the email.
     Eg ["/tmp/tmp8pjy66hd/fineos-vendor_customer_numbers.csv", ...]
    """
    aws_ses = boto3.client("ses")

    msg = MIMEMultipart("mixed")

    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(
        recipient.to_addresses + (recipient.cc_addresses if recipient.cc_addresses else [])
    )
    if recipient.bcc_addresses:
        msg["Bcc"] = ", ".join(recipient.bcc_addresses if recipient.bcc_addresses else [])

    msg_body = MIMEMultipart("alternative")
    msg_text = MIMEText(str(body_text.encode(CHARSET)), "plain", CHARSET)
    msg_body.attach(msg_text)

    msg.attach(msg_body)

    # Add the attachment to the parent container.
    create_email_attachments(msg, attachments)

    try:
        response = aws_ses.send_raw_email(
            Source=msg["From"], Destinations=[msg["To"]], RawMessage={"Data": msg.as_string(),},
        )

        logger.info(f"Email sent! Message ID: {response['MessageId']}")
        return response
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.exception("Error sending email: %s", error_message)
        raise RuntimeError("Error sending email: %s", error_message)


def create_email_attachments(msg_container: MIMEMultipart, attachments: List[str]) -> None:
    for attachment in attachments:
        att = MIMEApplication(read_file(attachment, mode="rb"))
        att.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment))
        msg_container.attach(att)
