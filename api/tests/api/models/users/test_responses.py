from massgov.pfml.db.models.employees import MFADeliveryPreference
from massgov.pfml.db.models.factories import ApplicationFactory


class TestUserResponse:
    def test_creates_response_dictionary(self, app, client, user, auth_token):
        application = ApplicationFactory.create(user=user)
        response = client.get(
            "/v1/users/current", headers={"Authorization": f"Bearer {auth_token}"}
        )
        response_body = response.get_json().get("data")

        assert response_body["user_id"] == str(user.user_id)
        assert response_body["email_address"] == user.email_address
        assert response_body["mfa_delivery_preference"] is None
        assert response_body["mfa_phone_number"] is None
        assert response_body["consented_to_data_sharing"] is False
        assert response_body["roles"] == []
        assert response_body["user_leave_administrators"] == []
        assert len(response_body["application_names"]) == 1
        application_name = response_body["application_names"][0]
        assert application_name.get("first_name") == application.first_name
        assert application_name.get("middle_name") == application.middle_name
        assert application_name.get("last_name") == application.last_name

    def test_flattens_mfa_delivery_preference(self, app, client, user, test_db_session, auth_token):
        sms_preference = MFADeliveryPreference.get_instance(test_db_session, description="SMS")
        user.mfa_delivery_preference = sms_preference
        response = client.get(
            "/v1/users/current", headers={"Authorization": f"Bearer {auth_token}"}
        )

        response_body = response.get_json().get("data")

        assert response_body["mfa_delivery_preference"] == "SMS"

    def test_returns_masked_phone(self, app, client, user, auth_token):
        user.mfa_phone_number = "+15109283075"

        response = client.get(
            "/v1/users/current", headers={"Authorization": f"Bearer {auth_token}"}
        )

        response_body = response.get_json().get("data")

        assert response_body["mfa_phone_number"]["phone_number"] == "***-***-3075"
