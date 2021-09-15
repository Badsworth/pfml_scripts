import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest
from pydantic import ValidationError

import massgov.pfml.util.aws.ses as conn
from massgov.pfml.api.validation.exceptions import ValidationException
from massgov.pfml.util.files import create_csv_from_list


def get_raw_email_msg_object():
    message = MIMEMultipart("mixed")
    message["Subject"] = "Test"
    message["To"] = "to@example.com"
    message["CC"] = "cc@example.com"
    message["Bcc"] = "bcc@example.com"

    # Message body
    msg_body = MIMEMultipart("alternative")
    msg_txt = MIMEText("test file attached")
    msg_body.attach(msg_txt)
    message.attach(msg_body)

    # Attachment
    file_name = "test_file"
    csv_file_path = [create_csv_from_list([{"name": "test"}], ["name"], file_name)]
    conn.create_email_attachments(message, csv_file_path)
    return message


def test_send_email(mock_ses):
    recipient = conn.EmailRecipient(
        to_addresses=["test@example.com"],
        cc_addresses=["test@example.com"],
        bcc_addresses=["test@example.com"],
    )
    sender = os.getenv("PFML_EMAIL_ADDRESS")
    subject = "INF data"
    body_text = "Test Message"

    bounce_forwarding_email_address_arn = os.getenv("BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN", "")
    fieldnames = ["fineos_customer_number", "ctr_vendor_customer_code"]
    file_name = "test_file"
    fineos_vendor_customer_numbers = [
        {"fineos_customer_number": 1, "ctr_vendor_customer_code": 1},
        {"fineos_customer_number": 2, "ctr_vendor_customer_code": 2},
    ]
    attachments = [create_csv_from_list(fineos_vendor_customer_numbers, fieldnames, file_name)]
    response = conn.send_email(
        recipient, subject, body_text, sender, bounce_forwarding_email_address_arn, attachments
    )

    assert response is not None
    assert response["MessageId"] is not None
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    # Add a test to remove CC and BCC
    recipient_to_only = conn.EmailRecipient(to_addresses=["test@example.com"])
    response_to_only = conn.send_email(
        recipient_to_only,
        subject,
        body_text,
        sender,
        bounce_forwarding_email_address_arn,
        attachments,
    )

    assert response_to_only is not None
    assert response_to_only["MessageId"] is not None
    assert response_to_only["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_send_email_attachments(mock_ses):
    message = get_raw_email_msg_object()
    sender = os.getenv("PFML_EMAIL_ADDRESS")
    kwargs = dict(Source=sender, RawMessage={"Data": message.as_string()})

    mock_ses.send_raw_email(**kwargs)

    send_quota = mock_ses.get_send_quota()
    sent_count = int(send_quota["SentLast24Hours"])
    assert sent_count == len(message["To"].split(",")) + len(message["CC"].split(",")) + len(
        message["Bcc"].split(",")
    )
    assert mock_ses.list_identities()["Identities"] == [sender]


def test_email_format():

    # valid email addresses
    conn.EmailRecipient(to_addresses=["test@example.com"])
    conn.EmailRecipient(to_addresses=["test1@example.com", "test2@example.com"])
    conn.EmailRecipient(
        to_addresses=["test@example.com"],
        cc_addresses=["test@example.com"],
        bcc_addresses=["test@example.com"],
    )

    # invalid email addresses
    with pytest.raises(ValidationException):
        conn.EmailRecipient(to_addresses=[])
    with pytest.raises(ValidationException):
        conn.EmailRecipient(to_addresses=[""])
    with pytest.raises(ValidationError):
        conn.EmailRecipient(cc_addresses=["test@test.com"])
    with pytest.raises(ValidationException):
        conn.EmailRecipient(to_addresses=["test@test.com", ""])
    with pytest.raises(ValidationException):
        conn.EmailRecipient(to_addresses=[""], bcc_addresses=["test@test.com"])
    with pytest.raises(ValidationException):
        conn.EmailRecipient(to_addresses=["test@test.com"], cc_addresses=[""])
    with pytest.raises(ValidationException):
        conn.EmailRecipient(to_addresses=["test@test.com"], bcc_addresses=["test@test.com", ""])
    with pytest.raises(ValidationException):
        conn.EmailRecipient(
            to_addresses=["test@test.com"], cc_addresses=[""], bcc_addresses=["test@test.com"]
        )
