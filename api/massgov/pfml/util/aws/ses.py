from __future__ import annotations

import json
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence

import boto3
from botocore.exceptions import ClientError
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, validator

import massgov.pfml.util.logging as logging
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.util.files import read_file

if TYPE_CHECKING:
    from _typeshed import AnyPath

logger = logging.get_logger(__name__)

# The character encoding for the email.
CHARSET = "UTF-8"


def create_ses_client():
    return boto3.client("ses")


class EmailRecipient(BaseModel):
    to_addresses: List[str]
    cc_addresses: Optional[List[str]] = []
    bcc_addresses: Optional[List[str]] = []

    @validator("to_addresses")
    def check_to_addresses_format(cls, emails):  # noqa: B902
        if len(emails) == 0:
            validation_error = ValidationErrorDetail(
                message="Have to provide at least one valid email address", type=IssueType.required
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
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            validation_error = ValidationErrorDetail(message=f"{e}", type=IssueType.pattern)
            raise ValidationException(
                errors=[validation_error], message="Email validation error", data={}
            )


def send_email(
    recipient: EmailRecipient,
    subject: str,
    body_text: str,
    sender: str,
    bounce_forwarding_email_address_arn: str,
    attachments: Optional[Sequence[AnyPath]] = None,
) -> Dict:
    """
    attachments is a list containing the full-paths to the file that will be attached to the email.
     Eg ["/tmp/tmp8pjy66hd/fineos-vendor_customer_numbers.csv", ...]
    """
    aws_ses = create_ses_client()

    msg = MIMEMultipart("mixed")

    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipient.to_addresses)
    msg["CC"] = ", ".join(recipient.cc_addresses if recipient.cc_addresses else [])
    msg["Bcc"] = ", ".join(recipient.bcc_addresses if recipient.bcc_addresses else [])

    # Ensure no empty destinations are included.
    destinations: List[str] = list(filter(None, [msg["To"], msg["CC"], msg["Bcc"]]))

    msg_body = MIMEMultipart("alternative")
    msg_text = MIMEText(body_text, "plain", CHARSET)
    msg_body.attach(msg_text)

    msg.attach(msg_body)

    # Add the attachment to the parent container.
    if attachments is not None:
        create_email_attachments(msg, attachments)

    try:
        response = aws_ses.send_raw_email(
            Source=msg["From"],
            Destinations=destinations,
            RawMessage={"Data": msg.as_string()},
            ReturnPathArn=bounce_forwarding_email_address_arn,
        )

        logger.info(
            "Email sent successfully.",
            extra={"message_id": response["MessageId"], "subject": subject},
        )
        return response
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.exception(f"Error sending email from {msg['From']}, to {msg['To']}: {error_message}")
        raise RuntimeError(f"Error sending email: {error_message}")


def send_templated_email(
    recipient: EmailRecipient,
    template: str,
    sender: str,
    bounce_forwarding_email_address: str,
    bounce_forwarding_email_address_arn: str,
    template_data: Optional[Dict[str, str]],
) -> None:
    """Send an email from an SES template. The template must already exist in SES. Template parameters
    in the SES template can be populated by passing values in the template_data parameter.

    Read more about SES email templates:
        https://docs.aws.amazon.com/ses/latest/dg/send-personalized-email-api.html#send-personalized-email-create-template

    Args:
        recipient:
            the email address to send to
        template:
            the name of the SES template to send. This template must already exist in SES
        sender:
            the email address to send from
        bounce_forwarding_email_address:
            the email which will receive bounce/failure messages (eg if the email cannot be delivered). Must be an email address verified in SES
        bounce_forwarding_email_address_arn:
            arn for the bounce forwarding email
        template_data:
            optional dictionary of template "tag" values populate in the email template. See the link above for more info
    """
    aws_ses = create_ses_client()
    if template_data is None:
        template_data = {}

    # Ensure no empty destinations are included.
    destinations: Dict[str, List[str]] = {"ToAddresses": list(filter(None, recipient.to_addresses))}

    try:
        response = aws_ses.send_templated_email(
            Source=sender,
            Destination=destinations,
            ReturnPath=bounce_forwarding_email_address,
            ReturnPathArn=bounce_forwarding_email_address_arn,
            Template=template,
            TemplateData=json.dumps(template_data),
        )
    except Exception as error:
        if isinstance(error, ClientError) and "TemplateDoesNotExistException" in str(
            error.__class__
        ):
            logger.error(
                "Error sending templated email in SES - Template does not exist", exc_info=error
            )
        elif isinstance(error, ClientError) and "MessageRejected" in str(error.__class__):
            logger.error("Error sending templated email in SES - Message rejected", exc_info=error)
        else:
            logger.error("Error sending templated email in SES", exc_info=error)

        raise error

    logger.info(
        "Templated email sent successfully.",
        extra={"message_id": response["MessageId"], "template": template},
    )


def create_email_attachments(msg_container: MIMEMultipart, attachments: Sequence[AnyPath]) -> None:
    for attachment in attachments:
        att = MIMEApplication(read_file(attachment, mode="rb"))
        att.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment))  # type: ignore
        msg_container.attach(att)
