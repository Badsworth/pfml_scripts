from massgov.pfml.api.models.users.responses import user_response
from massgov.pfml.db.models.employees import MFADeliveryPreference


class TestUserResponse:
    def test_creates_response_dictionary(self, user, test_db_session):
        response = user_response(user, test_db_session)

        assert response["user_id"] == user.user_id
        assert response["email_address"] == user.email_address
        assert response["mfa_delivery_preference"] is None
        assert response["mfa_phone_number"] is None
        assert response["consented_to_data_sharing"] is False
        assert response["roles"] == []
        assert response["user_leave_administrators"] == []

    def test_flattens_mfa_delivery_preference(self, user, test_db_session):
        sms_preference = MFADeliveryPreference.get_instance(test_db_session, description="SMS")
        user.mfa_delivery_preference = sms_preference

        response = user_response(user, test_db_session)

        assert response["mfa_delivery_preference"] == "SMS"
