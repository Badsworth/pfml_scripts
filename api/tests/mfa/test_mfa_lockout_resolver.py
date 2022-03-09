from unittest.mock import MagicMock, patch

import pytest

from massgov.pfml.mfa.mfa_lockout_resolver import MfaLockoutResolver
from tests.conftest import get_mock_logger


def create_lockout_resolver(dry_run=True):
    return MfaLockoutResolver(
        user_email="test@email.com",
        psd_number="PSD-1234",
        reason_for_disabling="lost phone",
        agent_email="edith.finch@mass.gov",
        verification_method="With Claim",
        dry_run=dry_run,
        db_session=MagicMock(),
    )


class TestMfaLockoutResolver:
    mock_logger = get_mock_logger()
    mfa_lockout_resolver = create_lockout_resolver(dry_run=False)

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.get_user_by_email")
    @patch(
        "massgov.pfml.mfa.mfa_lockout_resolver.check_phone_number_opt_out", return_value=True,
    )
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.opt_in_phone_number")
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.admin_disable_mfa")
    def test_mfa_lockout_resolution_dry_run(
        self,
        mock_disable_mfa,
        mock_opt_in_phone_number,
        mock_opt_out,
        mock_get_user,
        user_with_mfa,
    ):
        mock_get_user.return_value = user_with_mfa
        mfa_lockout_resolver = create_lockout_resolver()
        assert mfa_lockout_resolver.user_email == "test@email.com"
        log_attrs = {
            "psd_ticket_number": "PSD-1234",
            "reason_for_disabling": "lost phone",
            "contact_center_agent": "edith.finch@mass.gov",
            "identity_verification_method": "With Claim",
            "dry_run": True,
        }
        assert mfa_lockout_resolver.log_attr == log_attrs
        # dry_run is flipped when passed in
        assert mfa_lockout_resolver.should_commit_changes is False

        mfa_lockout_resolver.run()

        # check that none of the methods that make external calls are called
        mock_disable_mfa.assert_not_called()
        mock_opt_out.assert_called_once_with(user_with_mfa.mfa_phone_number)
        mock_opt_in_phone_number.assert_not_called()

        assert user_with_mfa.mfa_delivery_preference_id == 1

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    def test_mfa_lockout_resolution_init(self):
        assert self.mfa_lockout_resolver.user_email == "test@email.com"
        log_attrs = {
            "psd_ticket_number": "PSD-1234",
            "reason_for_disabling": "lost phone",
            "contact_center_agent": "edith.finch@mass.gov",
            "identity_verification_method": "With Claim",
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
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.get_user_by_email")
    def test_get_user_found(self, mock_get_user_by_email, user_with_mfa):
        mock_get_user_by_email.return_value = user_with_mfa
        self.mfa_lockout_resolver._get_user()

        mock_get_user_by_email.assert_called_once()
        self.mock_logger.info.assert_any_call(
            "Getting user from PFML API", extra=self.mfa_lockout_resolver.log_attr
        )
        # user id added to list of attrs we're logging
        assert self.mfa_lockout_resolver.log_attr["user_id"] == user_with_mfa.user_id

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
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.admin_disable_mfa")
    def test_disable_mfa(self, mock_admin_disable_mfa, user):
        self.mfa_lockout_resolver._disable_mfa(user)

        mock_admin_disable_mfa.assert_called_once()
        self.mock_logger.info.assert_any_call(
            "Disabling user MFA", extra=self.mfa_lockout_resolver.log_attr
        )

    @patch("massgov.pfml.mfa.mfa_lockout_resolver.logger", mock_logger)
    @patch("massgov.pfml.mfa.mfa_lockout_resolver.admin_disable_mfa")
    def test_disable_mfa_error(self, mock_admin_disable_mfa, user):
        mock_admin_disable_mfa.side_effect = Exception("ran into an error")

        with pytest.raises(Exception) as e:
            self.mfa_lockout_resolver._disable_mfa(user)

            self.mock_logger.info.assert_any_call(
                "Setting user opt-in in SNS", extra=self.mfa_lockout_resolver.log_attr
            )
            self.mock_logger.error.assert_any_call(
                "Error disabling user MFA in PFML db", e, extra=self.mfa_lockout_resolver.log_attr,
            )
