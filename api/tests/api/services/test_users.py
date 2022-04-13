from datetime import datetime
from unittest import mock

import boto3

from massgov.pfml.api.models.common import Phone
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.services.users import admin_disable_mfa, update_user
from tests.conftest import get_mock_logger


class TestUpdateUser:
    mock_logger = get_mock_logger()

    def test_set_consented_to_share(self, user, test_db_session, auth_token):
        update_request = UserUpdateRequest(consented_to_data_sharing=True)
        update_user(test_db_session, user, update_request, False, auth_token)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.consented_to_data_sharing is True

    def test_set_mfa_delivery_preference(self, user, test_db_session, auth_token):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request, False, auth_token)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.mfa_delivery_preference_id == 1
        assert user.mfa_delivery_preference.description == "SMS"

    def test_unset_mfa_delivery_preference(self, user_with_mfa, test_db_session, auth_token):
        update_request = UserUpdateRequest(mfa_delivery_preference=None)
        update_user(test_db_session, user_with_mfa, update_request, False, auth_token)

        test_db_session.commit()
        test_db_session.refresh(user_with_mfa)

        assert user_with_mfa.mfa_delivery_preference_id is None
        assert user_with_mfa.mfa_delivery_preference is None
        assert user_with_mfa.mfa_delivery_preference_updated_by_id == 1

    def test_set_mfa_phone_number(self, user, test_db_session, auth_token):
        mfa_phone_number = Phone(int_code="1", phone_number="510-928-3075")
        update_request = UserUpdateRequest(mfa_phone_number=mfa_phone_number)
        update_user(test_db_session, user, update_request, False, auth_token)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.mfa_phone_number == "+15109283075"

    def test_unset_mfa_phone_number(self, user_with_mfa, test_db_session, auth_token):
        update_request = UserUpdateRequest(mfa_phone_number=None)
        update_user(test_db_session, user_with_mfa, update_request, False, auth_token)

        test_db_session.commit()
        test_db_session.refresh(user_with_mfa)

        assert user_with_mfa.mfa_phone_number is None

    def test_updating_mfa_preference_updates_audit_trail(self, user, test_db_session, auth_token):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request, False, auth_token)

        test_db_session.commit()
        test_db_session.refresh(user)

        curr_date = datetime.utcnow().strftime("%Y-%m-%d")
        assert user.mfa_delivery_preference_updated_at.strftime("%Y-%m-%d") == curr_date
        assert user.mfa_delivery_preference_updated_by_id == 1
        assert (
            user.mfa_delivery_preference_updated_by.mfa_delivery_preference_updated_by_description
            == "User"
        )

    @mock.patch("massgov.pfml.api.services.users.mfa.enable_mfa")
    def test_enabling_mfa_preference_syncs_to_cognito(
        self,
        mock_enable_mfa,
        user,
        test_db_session,
        auth_token,
    ):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request, True, auth_token)

        mock_enable_mfa.assert_called_once_with(auth_token)

    @mock.patch("massgov.pfml.api.services.users.mfa.handle_mfa_disabled")
    @mock.patch("massgov.pfml.api.services.users.mfa.disable_mfa")
    def test_disabling_mfa_preference_syncs_to_cognito(
        self,
        mock_disable_mfa,
        mock_handle_mfa_disabled,
        user_with_mfa,
        test_db_session,
        auth_token,
    ):
        update_request = UserUpdateRequest(mfa_delivery_preference="Opt Out")
        update_user(test_db_session, user_with_mfa, update_request, True, auth_token)

        mock_disable_mfa.assert_called_once_with(auth_token)

    @mock.patch("massgov.pfml.api.services.users.mfa.handle_mfa_disabled")
    def test_handle_mfa_disabled_called_when_mfa_disabled(
        self, mock_handle_mfa_disabled, user_with_mfa, test_db_session, auth_token
    ):
        update_request = UserUpdateRequest(mfa_delivery_preference="Opt Out")
        update_user(test_db_session, user_with_mfa, update_request, False, auth_token)

        mock_handle_mfa_disabled.assert_called_once_with(user_with_mfa, mock.ANY)

    @mock.patch("massgov.pfml.api.services.users.mfa.handle_mfa_disabled")
    def test_handle_mfa_disabled_not_called_on_first_opt_out(
        self, mock_handle_mfa_disabled, user, test_db_session, auth_token
    ):
        update_request = UserUpdateRequest(mfa_delivery_preference="Opt Out")
        update_user(test_db_session, user, update_request, False, auth_token)

        mock_handle_mfa_disabled.assert_not_called()

    @mock.patch("massgov.pfml.api.services.users.logger", mock_logger)
    @mock.patch("massgov.pfml.api.services.users.mfa.handle_mfa_disabled")
    def test_errors_during_handle_mfa_disabled_do_not_raise(
        self, mock_handle_mfa_disabled, user_with_mfa, test_db_session, auth_token
    ):
        user_not_found_error = boto3.client(
            "cognito-idp", "us-east-1"
        ).exceptions.UserNotFoundException(
            error_response={
                "Error": {
                    "Code": "UserNotFoundException",
                    "Message": ":(",
                }
            },
            operation_name="Foo",
        )
        mock_handle_mfa_disabled.side_effect = user_not_found_error

        update_request = UserUpdateRequest(mfa_delivery_preference="Opt Out")
        update_user(test_db_session, user_with_mfa, update_request, False, auth_token)

        self.mock_logger.error.assert_any_call(
            "Error handling expected side-effects of disabling MFA. MFA is still disabled, and the API request is still successful.",
            exc_info=user_not_found_error,
        )

    @mock.patch("massgov.pfml.api.services.users._update_mfa_preference_audit_trail")
    def test_audit_trail_not_updated_if_mfa_preference_isnt_updated(
        self, mock_audit_trail, user, test_db_session, auth_token
    ):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request, False, auth_token)

        assert mock_audit_trail.call_count == 1

        update_user(test_db_session, user, update_request, False, auth_token)

        assert mock_audit_trail.call_count == 1

    @mock.patch("massgov.pfml.api.services.users.logger", mock_logger)
    def test_mfa_updated_logging(self, user, test_db_session, auth_token):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request, False, auth_token)

        self.mock_logger.info.assert_any_call(
            "MFA preference updated for user in DB",
            extra={"mfa_preference": "SMS", "save_mfa_preference_to_cognito": False},
        )


class TestAdminDisableMfa:
    @mock.patch("massgov.pfml.api.services.users.mfa.handle_mfa_disabled_by_admin")
    def test_admin_disable_mfa_sets_mfa_preference(
        self, mock_handle_mfa_disabled_by_admin, user_with_mfa, test_db_session, auth_token
    ):
        admin_disable_mfa(test_db_session, user_with_mfa)

        test_db_session.commit()
        test_db_session.refresh(user_with_mfa)

        assert user_with_mfa.mfa_delivery_preference_id == 2
        assert user_with_mfa.mfa_delivery_preference.description == "Opt Out"

    @mock.patch("massgov.pfml.api.services.users.mfa.handle_mfa_disabled_by_admin")
    def test_admin_disable_mfa_syncs_to_cognito(
        self, mock_handle_mfa_disabled_by_admin, user_with_mfa, test_db_session, auth_token
    ):
        admin_disable_mfa(test_db_session, user_with_mfa)

        mock_handle_mfa_disabled_by_admin.assert_called_once_with(user_with_mfa, mock.ANY)

    @mock.patch("massgov.pfml.api.services.users.mfa.handle_mfa_disabled_by_admin")
    def test_admin_disable_mfa_audit_trail(
        self, mock_handle_mfa_disabled_by_admin, user_with_mfa, test_db_session, auth_token
    ):
        admin_disable_mfa(test_db_session, user_with_mfa)

        test_db_session.commit()
        test_db_session.refresh(user_with_mfa)

        assert user_with_mfa.mfa_delivery_preference_updated_by_id == 2
        assert (
            user_with_mfa.mfa_delivery_preference_updated_by.mfa_delivery_preference_updated_by_description
            == "Admin"
        )
