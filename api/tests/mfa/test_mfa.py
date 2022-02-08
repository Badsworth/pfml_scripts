from datetime import datetime, timezone
from unittest import mock

import pytest

import massgov.pfml.mfa as mfa_actions
from tests.conftest import get_mock_logger


class TestHandleMfaDisabled:
    mock_logger = get_mock_logger()

    @pytest.fixture(autouse=True)
    def with_env_vars(self, monkeypatch):
        monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN", "bounce_arn")

    @pytest.fixture
    def user(self, user_with_mfa):
        user_with_mfa.email_address = "claimant@mock.nava.com"
        return user_with_mfa

    @mock.patch("massgov.pfml.mfa.send_templated_email")
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_logging(self, mock_send_email, user):
        last_enabled_at = datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mfa_actions.handle_mfa_disabled(user, last_enabled_at, "user")

        self.mock_logger.info.assert_any_call(
            "MFA disabled for user",
            extra={
                "last_enabled_at": mock.ANY,
                "time_since_enabled_in_sec": mock.ANY,
                "updated_by": "user",
            },
        )
        assert (
            self.mock_logger.info.call_args.kwargs["extra"]["last_enabled_at"].strftime("%Y-%m-%d")
            == "2022-01-02"
        )

    @mock.patch("massgov.pfml.mfa.send_templated_email")
    def test_email(self, mock_send_email, user):
        last_enabled_at = datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mfa_actions.handle_mfa_disabled(user, last_enabled_at, "user")

        mock_send_email.assert_called_once_with(
            mock.ANY,
            "MfaHasBeenDisabled",
            "PFML_DoNotReply@eol.mass.gov",
            "PFML_DoNotReply@eol.mass.gov",
            "bounce_arn",
            mock.ANY,
        )
        assert mock_send_email.call_args.args[0].to_addresses == ["claimant@mock.nava.com"]
        assert mock_send_email.call_args.args[5] == {"phone_number_last_four": "3075"}

    @mock.patch("massgov.pfml.mfa.send_templated_email")
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_with_no_last_enabled_at(self, mock_send_email, user):
        mfa_actions.handle_mfa_disabled(user, None, "user")

        self.mock_logger.error.assert_any_call(
            "MFA disabled, but no last_enabled_at timestamp was available"
        )

        self.mock_logger.info.assert_any_call(
            "MFA disabled for user", extra={"updated_by": "user",},
        )
