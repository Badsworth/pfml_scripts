import re
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, validator

import massgov.pfml.util.logging as logging
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException

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
