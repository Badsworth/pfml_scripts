import os

import pytest
from pydantic import ValidationError

from massgov.pfml.api.validation.exceptions import ValidationException


def test_send_email(mock_ses, reset_aws_env_vars):
    import massgov.pfml.util.aws.ses as ses

    recipient = ses.EmailRecipient(to_addresses=["test@example.com"])
    sender = os.getenv("PFML_EMAIL_ADDRESS")

    subject = "INF data"
    body_text = "Test Message"
    response = ses.send_email(recipient, subject, body_text, sender, sender)
    assert response is not None
    assert response["MessageId"] is not None
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_email_format():
    import massgov.pfml.util.aws.ses as ses

    # valid email addresses
    ses.EmailRecipient(to_addresses=["test@example.com"])
    ses.EmailRecipient(to_addresses=["test1@example.com", "test2@example.com"])
    ses.EmailRecipient(
        to_addresses=["test@example.com"],
        cc_addresses=["test@example.com"],
        bcc_addresses=["test@example.com"],
    )

    # invalid email addresses
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=[])
    with pytest.raises(ValidationException):
        ses.EmailRecipient(to_addresses=[""])
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
