from datetime import datetime, timezone
from unittest import mock

import pytest

import massgov.pfml.mfa as mfa_actions
from massgov.pfml.mfa import MFAUpdatedBy
from tests.conftest import get_mock_logger


@pytest.fixture
def last_enabled_at():
    return datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)


class TestHandleMfaDisabled:
    mock_logger = get_mock_logger()

    @pytest.fixture(autouse=True)
    def with_env_vars(self, monkeypatch):
        monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN", "bounce_arn")
        monkeypatch.setenv("DISABLE_SENDING_EMAILS", None)

    @pytest.fixture
    def user(self, user_with_mfa):
        user_with_mfa.email_address = "claimant@mock.nava.com"
        return user_with_mfa

    @mock.patch("massgov.pfml.mfa.send_templated_email")
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_logging(self, mock_send_email, user):
        last_enabled_at = datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mfa_actions.handle_mfa_disabled(user, last_enabled_at, MFAUpdatedBy.USER)

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
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_with_no_last_enabled_at(self, mock_send_email, user):
        mfa_actions.handle_mfa_disabled(user, None, MFAUpdatedBy.USER)

        self.mock_logger.error.assert_any_call(
            "MFA disabled, but no last_enabled_at timestamp was available"
        )

        self.mock_logger.info.assert_any_call("MFA disabled for user", extra={"updated_by": "user"})

    @mock.patch("massgov.pfml.mfa.send_templated_email")
    def test_email(self, mock_send_email, user):
        last_enabled_at = datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mfa_actions.handle_mfa_disabled(user, last_enabled_at, MFAUpdatedBy.USER)

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
    def test_does_not_send_email_when_sending_emails_is_disabled(
        self, mock_send_email, user, monkeypatch
    ):
        monkeypatch.setenv("DISABLE_SENDING_EMAILS", "1")
        last_enabled_at = datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mfa_actions.handle_mfa_disabled(user, last_enabled_at, MFAUpdatedBy.USER)

        mock_send_email.assert_not_called()
        self.mock_logger.info.assert_any_call(
            "Skipping sending an MFA disabled notification email",
            extra={
                "last_enabled_at": mock.ANY,
                "time_since_enabled_in_sec": mock.ANY,
                "updated_by": MFAUpdatedBy.USER,
            },
        )

    @mock.patch("massgov.pfml.mfa.send_templated_email")
    def test_sends_email_when_email_sending_is_enabled(self, mock_send_email, user, monkeypatch):
        monkeypatch.setenv("DISABLE_SENDING_EMAILS", "0")
        last_enabled_at = datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mfa_actions.handle_mfa_disabled(user, last_enabled_at, MFAUpdatedBy.USER)

        mock_send_email.assert_called()

    @mock.patch("massgov.pfml.mfa.send_templated_email")
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_sends_email_when_environment_is_not_local(self, mock_send_email, user, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "prod")
        monkeypatch.setenv("DISABLE_SENDING_EMAILS", "1")
        last_enabled_at = datetime(2022, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mfa_actions.handle_mfa_disabled(user, last_enabled_at, MFAUpdatedBy.USER)

        mock_send_email.assert_called()


class TestHandleMfaDisabledByAdmin:
    mock_logger = get_mock_logger()

    @pytest.fixture(autouse=True)
    def with_env_vars(self, monkeypatch):
        monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL_ADDRESS_ARN", "bounce_arn")
        monkeypatch.setenv("DISABLE_SENDING_EMAILS", None)

    @pytest.fixture
    def user(self, user_with_mfa):
        user_with_mfa.email_address = "claimant@mock.nava.com"
        return user_with_mfa

    @mock.patch("massgov.pfml.mfa.admin_disable_user_mfa")
    @mock.patch("massgov.pfml.mfa.send_templated_email")
    def test_success(self, mock_send_email, mock_disable_mfa, user, last_enabled_at, auth_token):
        mfa_actions.handle_mfa_disabled_by_admin(user, last_enabled_at)

        mock_disable_mfa.assert_called_once_with(user.email_address)

    @mock.patch("massgov.pfml.mfa.admin_disable_user_mfa")
    @mock.patch("massgov.pfml.mfa.send_templated_email")
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_logging(self, mock_send_email, mock_disable_mfa, user, last_enabled_at):
        mfa_actions.handle_mfa_disabled_by_admin(user, last_enabled_at)

        self.mock_logger.info.assert_any_call(
            "MFA disabled for user",
            extra={
                "last_enabled_at": mock.ANY,
                "time_since_enabled_in_sec": mock.ANY,
                "updated_by": "admin",
            },
        )
        assert (
            self.mock_logger.info.call_args.kwargs["extra"]["last_enabled_at"].strftime("%Y-%m-%d")
            == "2022-01-02"
        )

    @mock.patch("massgov.pfml.mfa.admin_disable_user_mfa")
    @mock.patch("massgov.pfml.mfa.send_templated_email")
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_with_no_last_enabled_at(self, mock_send_email, mock_disable_mfa, user):
        mfa_actions.handle_mfa_disabled_by_admin(user, None)

        self.mock_logger.error.assert_any_call(
            "MFA disabled, but no last_enabled_at timestamp was available"
        )

        self.mock_logger.info.assert_any_call(
            "MFA disabled for user", extra={"updated_by": "admin"}
        )

    @mock.patch("massgov.pfml.mfa.admin_disable_user_mfa")
    @mock.patch("massgov.pfml.mfa.send_templated_email")
    @mock.patch("massgov.pfml.mfa.logger", mock_logger)
    def test_does_not_send_email_or_sync_to_cognito_when_aws_integration_is_disabled(
        self, mock_send_email, mock_disable_mfa, user, last_enabled_at, monkeypatch
    ):
        monkeypatch.setenv("DISABLE_SENDING_EMAILS", "1")

        mfa_actions.handle_mfa_disabled_by_admin(user, last_enabled_at)

        mock_send_email.assert_not_called()
        mock_disable_mfa.assert_not_called()
        self.mock_logger.info.assert_any_call(
            "Skipping updating Cognito or sending an MFA disabled notification email",
            extra={
                "last_enabled_at": mock.ANY,
                "time_since_enabled_in_sec": mock.ANY,
                "updated_by": "admin",
            },
        )

    @mock.patch("massgov.pfml.mfa.admin_disable_user_mfa")
    @mock.patch("massgov.pfml.mfa.send_templated_email")
    def test_sends_email_and_syncs_to_cognito_when_environment_is_not_local(
        self, mock_send_email, mock_disable_mfa, user, last_enabled_at, monkeypatch
    ):
        monkeypatch.setenv("ENVIRONMENT", "prod")
        monkeypatch.setenv("DISABLE_SENDING_EMAILS", "1")

        mfa_actions.handle_mfa_disabled_by_admin(user, last_enabled_at)

        mock_send_email.assert_called_once_with(
            mock.ANY,
            "MfaHasBeenDisabled",
            "PFML_DoNotReply@eol.mass.gov",
            "PFML_DoNotReply@eol.mass.gov",
            "bounce_arn",
            mock.ANY,
        )
        mock_disable_mfa.assert_called_once_with(user.email_address)
