from unittest.mock import MagicMock, patch

import pytest

from massgov.pfml.mfa.mfa_lockout_resolver import MfaLockoutResolver
from tests.conftest import get_mock_logger


def create_lockout_resolver(dry_run=True):
    return MfaLockoutResolver(
        user_email="test@email.com",
        psd_number="PSD-1234",
        reason_for_disabling="lost phone",
        employee_name="call center",
        verification_method="seemed truthful",
        dry_run=dry_run,
        db_session=MagicMock(),
    )


class TestMFALockoutResolverWithDryRunEnabled:
    mock_logger = get_mock_logger()
    mfa_lockout_resolver = create_lockout_resolver()

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    def test_mfa_lockout_resolution_init(self):
        assert self.mfa_lockout_resolver.user_email == "test@email.com"
        log_attrs = {
            "psd_ticket_number": "PSD-1234",
            "reason_for_disabling": "lost phone",
            "contact_center_employee_name": "call center",
            "identity_verification_method": "seemed truthful",
            "dry_run": True,
        }
        assert self.mfa_lockout_resolver.log_attr == log_attrs
        # dry_run is flipped when passed in
        assert self.mfa_lockout_resolver.should_commit_changes is False

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.disable_user_mfa")
    def test_disable_mfa_cognito(self, mock_disable_user_mfa):
        self.mfa_lockout_resolver._disable_mfa_cognito()

        mock_disable_user_mfa.assert_not_called()
        self.mock_logger.info.assert_any_call(
            "Disabling user MFA in Cognito", extra=self.mfa_lockout_resolver.log_attr
        )
        self.mock_logger.info.assert_any_call(
            "(DRY RUN: Skipping API call to disable user MFA)",
            extra=self.mfa_lockout_resolver.log_attr,
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch(
        "massgov.pfml.mfa.mfa_lockout_resolver.check_phone_number_opt_out", return_value=True,
    )
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.opt_in_phone_number")
    def test_sns_opt_out_phone_opted_out(self, mock_opt_in, mock_phone_opt_out, user_with_mfa):
        self.mfa_lockout_resolver._set_sns_opt_in(user_with_mfa)

        mock_phone_opt_out.assert_called_once_with(user_with_mfa.mfa_phone_number)
        mock_opt_in.assert_not_called()
        self.mock_logger.info.assert_any_call(
            "Setting user opt-in in SNS", extra=self.mfa_lockout_resolver.log_attr
        )
        self.mock_logger.info.assert_any_call(
            "(DRY RUN: Skipping API call to opt user into SNS)",
            extra=self.mfa_lockout_resolver.log_attr,
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.update_user")
    def test_disable_mfa_pfml_dry_run(self, mock_update_user, user):
        self.mfa_lockout_resolver._disable_mfa_pfml(user)

        mock_update_user.assert_not_called()
        self.mock_logger.info.assert_any_call(
            "Disabling user MFA in PFML db", extra=self.mfa_lockout_resolver.log_attr
        )
        self.mock_logger.info.assert_any_call(
            "(DRY RUN: Skipping API call to disable MFA in PFML DB)",
            extra=self.mfa_lockout_resolver.log_attr,
        )


class TestMFALockoutResolverWithDryRunDisabled:
    mock_logger = get_mock_logger()
    mfa_lockout_resolver = create_lockout_resolver(dry_run=False)

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    def test_mfa_lockout_resolution_init(self):
        assert self.mfa_lockout_resolver.user_email == "test@email.com"
        log_attrs = {
            "psd_ticket_number": "PSD-1234",
            "reason_for_disabling": "lost phone",
            "contact_center_employee_name": "call center",
            "identity_verification_method": "seemed truthful",
            "dry_run": False,
        }
        assert self.mfa_lockout_resolver.log_attr == log_attrs
        # dry_run is flipped when passed in
        assert self.mfa_lockout_resolver.should_commit_changes is True

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.MfaLockoutResolver._resolve_lockout")
    def test_logs_on_run(self, mock_resolve_lockout):

        self.mfa_lockout_resolver.run()

        self.mfa_lockout_resolver._resolve_lockout.assert_called_once()
        self.mock_logger.info.assert_any_call(
            "Starting MFA lockout resolution", extra=self.mfa_lockout_resolver.log_attr
        )
        self.mock_logger.info.assert_any_call(
            "Completed MFA lockout resolution!", extra=self.mfa_lockout_resolver.log_attr
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch(
        "massgov.pfml.mfa.mfa_lockout_resolver.get_user_by_email", return_value="user",
    )
    def test_get_user_found(self, mock_get_user_by_email):
        self.mfa_lockout_resolver._get_user()

        mock_get_user_by_email.assert_called_once()
        self.mock_logger.info.assert_any_call(
            "Getting user from PFML API", extra=self.mfa_lockout_resolver.log_attr
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch(
        "massgov.pfml.mfa.mfa_lockout_resolver.get_user_by_email", return_value=None,
    )
    def test_get_user_not_found(self, mock_get_user_by_email):
        with pytest.raises(Exception) as e:
            self.mfa_lockout_resolver._get_user()

            assert str(e.value) == "Unable to find user with the given email"
            mock_get_user_by_email.assert_called_once()
            self.mock_logger.info.assert_any_call(
                "Getting user from PFML API", extra=self.mfa_lockout_resolver.log_attr
            )
            self.mock_logger.error.assert_any_call(
                "Error finding user in PFML database", e, extra=self.mfa_lockout_resolver.log_attr,
            )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.disable_user_mfa")
    def test_disable_mfa_cognito(self, mock_disable_user_mfa):
        self.mfa_lockout_resolver._disable_mfa_cognito()
        mock_disable_user_mfa.assert_called_once_with(self.mfa_lockout_resolver.user_email)
        self.mock_logger.info.assert_any_call(
            "Disabling user MFA in Cognito", extra=self.mfa_lockout_resolver.log_attr
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.disable_user_mfa")
    def test_disable_mfa_cognito_error(self, mock_disable_user_mfa):
        mock_disable_user_mfa.side_effect = Exception("ran into an error")
        mfa_lockout_resolver = create_lockout_resolver(dry_run=False)
        with pytest.raises(Exception) as e:
            mfa_lockout_resolver._disable_mfa_cognito()
            mock_disable_user_mfa.assert_called_once_with(mfa_lockout_resolver.user_email)
            self.mock_logger.info.assert_any_call(
                "Disabling user MFA in Cognito", extra=self.mfa_lockout_resolver.log_attr
            )
            self.mock_logger.error.assert_any_call(
                "Error disabling user MFA in Cognito", e, extra=self.mfa_lockout_resolver.log_attr,
            )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch(
        "massgov.pfml.mfa.mfa_lockout_resolver.check_phone_number_opt_out", return_value=True,
    )
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.opt_in_phone_number")
    def test_sns_opt_out_phone_opted_out(self, mock_phone_opt_out, mock_opt_in, user_with_mfa):
        self.mfa_lockout_resolver._set_sns_opt_in(user_with_mfa)

        mock_phone_opt_out.assert_called_once_with(user_with_mfa.mfa_phone_number)
        mock_opt_in.assert_called_once_with(user_with_mfa.mfa_phone_number)
        self.mock_logger.info.assert_any_call(
            "Setting user opt-in in SNS", extra=self.mfa_lockout_resolver.log_attr
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch(
        "massgov.pfml.mfa.mfa_lockout_resolver.check_phone_number_opt_out", return_value=False,
    )
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.opt_in_phone_number")
    def test_sns_opt_out_phone_opted_in(self, mock_opt_in, mock_phone_opt_out, user_with_mfa):
        self.mfa_lockout_resolver._set_sns_opt_in(user_with_mfa)

        mock_phone_opt_out.assert_called_once_with(user_with_mfa.mfa_phone_number)
        mock_opt_in.assert_not_called()
        self.mock_logger.info.assert_any_call(
            "Setting user opt-in in SNS", extra=self.mfa_lockout_resolver.log_attr
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.check_phone_number_opt_out")
    def test_sns_opt_out_check_opt_out_error(self, mock_phone_opt_out, user_with_mfa):
        mock_phone_opt_out.side_effect = Exception("ran into an error")

        with pytest.raises(Exception) as e:
            self.mfa_lockout_resolver._set_sns_opt_in(user_with_mfa)

            self.mock_logger.info.assert_any_call(
                "Setting user opt-in in SNS", extra=self.mfa_lockout_resolver.log_attr
            )
            self.mock_logger.error.assert_any_call(
                "Error pulling opt-in status from SNS", e, extra=self.mfa_lockout_resolver.log_attr,
            )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch(
        "massgov.pfml.mfa.mfa_lockout_resolver.check_phone_number_opt_out", return_value=True,
    )
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.opt_in_phone_number")
    def test_sns_opt_out_opt_in_error(self, mock_opt_in, mock_phone_opt_out, user_with_mfa):
        mock_phone_opt_out.side_effect = Exception("ran into an error")

        with pytest.raises(Exception) as e:
            self.mfa_lockout_resolver._set_sns_opt_in(user_with_mfa)

            mock_phone_opt_out.assert_called_once_with(user_with_mfa.mfa_phone_number)
            self.mock_logger.info.assert_any_call(
                "Setting user opt-in in SNS", extra=self.mfa_lockout_resolver.log_attr
            )
            self.mock_logger.error.assert_any_call(
                "Error setting user opt-in in SNS", e, extra=self.mfa_lockout_resolver.log_attr
            )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.update_user")
    def test_disable_mfa_pfml(self, mock_update_user, user):
        self.mfa_lockout_resolver._disable_mfa_pfml(user)

        mock_update_user.assert_called_once()
        self.mock_logger.info.assert_any_call(
            "Disabling user MFA in PFML db", extra=self.mfa_lockout_resolver.log_attr
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.update_user")
    def test_disable_mfa_pfml_error(self, mock_update_user, user):
        mock_update_user.side_effect = Exception("ran into an error")

        with pytest.raises(Exception) as e:
            self.mfa_lockout_resolver._disable_mfa_pfml(user)

            self.mock_logger.info.assert_any_call(
                "Setting user opt-in in SNS", extra=self.mfa_lockout_resolver.log_attr
            )
            self.mock_logger.error.assert_any_call(
                "Error disabling user MFA in PFML db", e, extra=self.mfa_lockout_resolver.log_attr,
            )
