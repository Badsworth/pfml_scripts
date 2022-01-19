from datetime import datetime
from unittest import mock

import pytest

from massgov.pfml.api.models.common import Phone
from massgov.pfml.api.models.users.requests import UserUpdateRequest
from massgov.pfml.api.services.users import update_user


# Run `initialize_factories_session` for all tests,
# so that it doesn't need to be manually included
@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


class TestUpdateUser:
    def test_set_consented_to_share(self, user, test_db_session):
        update_request = UserUpdateRequest(consented_to_data_sharing=True)
        update_user(test_db_session, user, update_request)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.consented_to_data_sharing is True

    def test_set_mfa_delivery_preference(self, user, test_db_session):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.mfa_delivery_preference_id == 1
        assert user.mfa_delivery_preference.mfa_delivery_preference_description == "SMS"

    def test_unset_mfa_delivery_preference(self, user, test_db_session):
        # set preference to SMS
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request)

        # unset
        update_request = UserUpdateRequest(mfa_delivery_preference=None)
        update_user(test_db_session, user, update_request)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.mfa_delivery_preference_id is None
        assert user.mfa_delivery_preference is None
        assert user.mfa_delivery_preference_updated_by_id == 1

    def test_set_mfa_phone_number(self, user, test_db_session):
        mfa_phone_number = Phone(int_code="1", phone_number="510-928-3075")
        update_request = UserUpdateRequest(mfa_phone_number=mfa_phone_number)
        update_user(test_db_session, user, update_request)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.mfa_phone_number == "+15109283075"

    def test_unset_mfa_phone_number(self, user, test_db_session):
        # set mfa_phone_number
        mfa_phone_number = Phone(int_code="1", phone_number="510-928-3075")
        update_request = UserUpdateRequest(mfa_phone_number=mfa_phone_number)

        # unset mfa_phone_number
        update_request = UserUpdateRequest(mfa_phone_number=None)
        update_user(test_db_session, user, update_request)

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.mfa_phone_number is None

    def test_updating_mfa_preference_updates_audit_trail(self, user, test_db_session):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request)

        test_db_session.commit()
        test_db_session.refresh(user)

        curr_date = datetime.utcnow().strftime("%Y-%m-%d")
        assert user.mfa_delivery_preference_updated_at.strftime("%Y-%m-%d") == curr_date
        assert user.mfa_delivery_preference_updated_by_id == 1
        assert (
            user.mfa_delivery_preference_updated_by.mfa_delivery_preference_updated_by_description
            == "User"
        )

    def test_audit_trail_as_admin(self, user, test_db_session):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request, updated_by="Admin")

        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.mfa_delivery_preference_updated_by_id == 2
        assert (
            user.mfa_delivery_preference_updated_by.mfa_delivery_preference_updated_by_description
            == "Admin"
        )

    @mock.patch("massgov.pfml.api.services.users._update_mfa_preference_audit_trail")
    def test_audit_trail_not_updated_if_mfa_preference_isnt_updated(
        self, mock_audit_trail, user, test_db_session,
    ):
        update_request = UserUpdateRequest(mfa_delivery_preference="SMS")
        update_user(test_db_session, user, update_request)

        assert mock_audit_trail.call_count == 1

        update_user(test_db_session, user, update_request)

        assert mock_audit_trail.call_count == 1
