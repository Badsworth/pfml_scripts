import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest import mock
from unittest.mock import MagicMock

import boto3
import pytest
from pydantic import ValidationError

import massgov.pfml.util.aws.ses as ses
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
    if csv_file_path is not None:
        ses.create_email_attachments(message, csv_file_path)
    return message


def test_send_email(mock_ses):
    recipient = ses.EmailRecipient(
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
    response = ses.send_email(
        recipient, subject, body_text, sender, bounce_forwarding_email_address_arn, attachments
    )

    assert response is not None
    assert response["MessageId"] is not None
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    # Add a test to remove CC and BCC
    recipient_to_only = ses.EmailRecipient(to_addresses=["test@example.com"])
    response_to_only = ses.send_email(
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
    ses.EmailRecipient(to_addresses=["test@example.com"])
    ses.EmailRecipient(to_addresses=["test1@example.com", "test2@example.com"])
    ses.EmailRecipient(
        to_addresses=["test@example.com"],
        cc_addresses=["test@example.com"],
        bcc_addresses=["test@example.com"],
    )
    ses.EmailRecipient(to_addresses=["test+valid@example.com"])

    # invalid email addresses
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=[])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=[""])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=["nopenotvalid"])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=["nopenotvalid@@@.com"])
    with pytest.raises(ValidationError):
        ses.EmailRecipient(cc_addresses=["test@test.com"])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=["test@test.com", ""])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=[""], bcc_addresses=["test@test.com"])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=["test@test.com"], cc_addresses=[""])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=["test@test.com"], bcc_addresses=["test@test.com", ""])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(
            to_addresses=["test@test.com"], cc_addresses=[""], bcc_addresses=["test@test.com"]
        )


class TestSendTemplatedEmail:
    @pytest.fixture
    def mock_ses(self):
        mock_cognito = MagicMock()
        mock_cognito.send_templated_email = MagicMock()
        return mock_cognito

    @mock.patch("massgov.pfml.util.aws.ses.create_ses_client")
    def test_success(self, mock_client, mock_ses):
        recipient = ses.EmailRecipient(to_addresses=["test@example.com"])
        template_args = {"key": "value"}
        mock_client.return_value = mock_ses

        ses.send_templated_email(
            recipient, "template", "sender@mock.com", "sender@mock.com", "bounce_arn", template_args
        )

        mock_ses.send_templated_email.assert_called_once_with(
            Source="sender@mock.com",
            Destination=mock.ANY,
            ReturnPath="sender@mock.com",
            ReturnPathArn="bounce_arn",
            Template="template",
            TemplateData=json.dumps(template_args),
        )
        assert mock_ses.send_templated_email.call_args[1]["Destination"]["ToAddresses"] == [
            "test@example.com"
        ]

    @pytest.fixture
    def template_not_found_exception(self):
        return boto3.client("ses", "us-east-1").exceptions.TemplateDoesNotExistException(
            error_response={"Error": {"Code": "TemplateDoesNotExistException", "Message": ":("}},
            operation_name="SendTemplatedEmail",
        )

    @mock.patch("massgov.pfml.util.aws.ses.create_ses_client")
    def test_ses_throws_exception(
        self, mock_client, mock_ses, template_not_found_exception, caplog
    ):
        mock_client.return_value = mock_ses
        recipient = ses.EmailRecipient(to_addresses=["test@example.com"])
        template_args = {"key": "value"}

        mock_ses.send_templated_email.side_effect = template_not_found_exception

        with pytest.raises(Exception):
            ses.send_templated_email(
                recipient,
                "template",
                "sender@mock.com",
                "sender@mock.com",
                "bounce_arn",
                template_args,
            )

        assert "Error sending templated email in SES" in caplog.text
