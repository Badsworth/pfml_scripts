import io
from datetime import date
from typing import Dict
from unittest import mock

import pytest
from freezegun import freeze_time

import massgov.pfml.util.datetime as datetime_util
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail
from massgov.pfml.db.models.employees import ChangeRequest
from massgov.pfml.db.models.factories import ChangeRequestFactory


# Run `initialize_factories_session` for all tests,
# so that it doesn't need to be manually included
@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


class TestPostChangeRequest:
    @pytest.fixture
    def request_body(self) -> Dict[str, str]:
        return {
            "change_request_type": "Modification",
            "start_date": "2022-01-01",
            "end_date": "2022-02-01",
        }

    @freeze_time("2022-02-22")
    @mock.patch("massgov.pfml.api.services.change_requests.add_change_request_to_db")
    @mock.patch(
        "massgov.pfml.api.change_requests.claim_rules.get_change_request_issues", return_value=[]
    )
    @mock.patch("massgov.pfml.api.services.claims.get_claim_from_db")
    def test_successful_call(
        self,
        mock_get_claim,
        mock_change_request_issues,
        mock_add_change,
        auth_token,
        claim,
        client,
        request_body,
    ):
        submitted_time = datetime_util.utcnow()
        mock_add_change.return_value = submitted_time
        mock_get_claim.return_value = claim
        response = client.post(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_body,
        )
        response_body = response.get_json().get("data")
        assert response.status_code == 201
        assert response_body.get("change_request_type") == request_body["change_request_type"]
        assert response_body.get("fineos_absence_id") == claim.fineos_absence_id
        assert response_body.get("start_date") == request_body["start_date"]
        assert response_body.get("end_date") == request_body["end_date"]

    @mock.patch(
        "massgov.pfml.api.change_requests.claim_rules.get_change_request_issues", return_value=[]
    )
    @mock.patch("massgov.pfml.api.change_requests.get_claim_from_db", return_value=None)
    def test_missing_claim(
        self, mock_get_claim, mock_change_request_issues, auth_token, claim, client, request_body
    ):
        response = client.post(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_body,
        )
        assert response.status_code == 404
        assert response.get_json()["message"] == "Claim does not exist for given absence ID"


class TestGetChangeRequests:
    @mock.patch("massgov.pfml.api.services.change_requests.get_change_requests_from_db")
    def test_successful_get_request(
        self, mock_get_change_requests_from_db, claim, change_request, client, auth_token, user
    ):
        mock_get_change_requests_from_db.return_value = [change_request]

        response = client.get(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        assert len(response_body["data"]["change_requests"]) == 1
        assert response_body["data"]["change_requests"][0]["change_request_type"] == "Modification"
        assert response_body["message"] == "Successfully retrieved change requests"

    @mock.patch("massgov.pfml.api.services.change_requests.get_change_requests_from_db")
    def test_successful_get_request_no_change_requests(
        self, mock_get_change_requests_from_db, claim, client, auth_token, user
    ):
        mock_get_change_requests_from_db.return_value = []

        response = client.get(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        assert len(response_body["data"]["change_requests"]) == 0

    def test_no_existing_claim(self, client, auth_token, user):
        response = client.get(
            "/v1/change-request?fineos_absence_id={}".format("fake_absence_id"),
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        response_body = response.get_json()
        assert response_body["message"] == "Claim does not exist for given absence ID"

    def test_unauthorized_user_unsuccessful(self, claim, client, user):
        response = client.get(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": "Bearer fake_auth_token"},
        )

        assert response.status_code == 401


class TestSubmitChangeRequest:
    @mock.patch("massgov.pfml.api.change_requests.get_or_404")
    @mock.patch(
        "massgov.pfml.api.change_requests.claim_rules.get_change_request_issues", return_value=[]
    )
    @mock.patch("massgov.pfml.api.change_requests.fineos_submit_change_request")
    def test_successful_call(
        self, mock_submit, mock_get_issues, mock_get_or_404, auth_token, change_request, client
    ):
        mock_get_or_404.return_value = change_request
        response = client.post(
            "/v1/change-request/5f91c12b-4d49-4eb0-b5d9-7fa0ce13eb32/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert change_request.submitted_time is not None
        assert response.status_code == 200
        mock_submit.assert_called_once()

    @mock.patch("massgov.pfml.api.change_requests.get_or_404")
    @mock.patch("massgov.pfml.api.change_requests.claim_rules.get_change_request_issues")
    @mock.patch("massgov.pfml.api.change_requests.fineos_submit_change_request")
    def test_validation_issues(
        self, mock_submit, mock_get_issues, mock_get_or_404, auth_token, change_request, client
    ):
        mock_get_or_404.return_value = change_request
        mock_get_issues.return_value = [
            ValidationErrorDetail(
                message="start_date required",
                type="required",
                field="start_date",
            )
        ]
        response = client.post(
            "/v1/change-request/5f91c12b-4d49-4eb0-b5d9-7fa0ce13eb32/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 400
        assert response.get_json()["message"] == "Invalid change request"
        mock_submit.assert_not_called()

    def test_missing_claim(self, auth_token, claim, client):
        response = client.post(
            "/v1/change-request/5f91c12b-4d49-4eb0-b5d9-7fa0ce13eb32/submit",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
        assert (
            response.get_json()["message"]
            == "Could not find ChangeRequest with ID 5f91c12b-4d49-4eb0-b5d9-7fa0ce13eb32"
        )


class TestDeleteChangeRequest:
    def test_success(self, client, auth_token, test_db_session):
        change_request = ChangeRequestFactory.create()
        response = client.delete(
            f"/v1/change-request/{change_request.change_request_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        response_body = response.get_json()
        assert response_body["message"] == "Successfully deleted change request"

        db_entry = (
            test_db_session.query(ChangeRequest)
            .filter(ChangeRequest.change_request_id == change_request.change_request_id)
            .one_or_none()
        )
        assert db_entry is None

    def test_missing_change_request(self, client, auth_token):
        response = client.delete(
            "/v1/change-request/009fa369-291b-403f-a85a-15e938c26f2f",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
        response_body = response.get_json()
        assert (
            response_body["message"]
            == "Could not find ChangeRequest with ID 009fa369-291b-403f-a85a-15e938c26f2f"
        )

    def test_error_on_submitted_change_request(self, client, auth_token):
        change_request = ChangeRequestFactory.create(submitted_time=datetime_util.utcnow())
        response = client.delete(
            f"/v1/change-request/{change_request.change_request_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 400
        response_body = response.get_json()
        assert response_body["message"] == "Cannot delete a submitted request"


class TestUpdateChangeRequest:
    @pytest.fixture
    def request_body(self) -> Dict[str, str]:
        return {
            "change_request_type": "Medical To Bonding Transition",
            "start_date": "2022-05-01",
            "end_date": "2022-06-01",
        }

    @mock.patch(
        "massgov.pfml.api.change_requests.claim_rules.get_change_request_issues", return_value=[]
    )
    def test_success(self, mock_issues, client, auth_token, change_request, request_body):
        response = client.patch(
            f"/v1/change-request/{change_request.change_request_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_body,
        )
        assert response.status_code == 200
        response_body = response.get_json()
        assert response_body["message"] == "Successfully updated change request"

        assert change_request.start_date == date(2022, 5, 1)
        assert change_request.end_date == date(2022, 6, 1)
        assert change_request.type == "Medical To Bonding Transition"

    def test_missing_change_request(self, client, auth_token, request_body):
        response = client.patch(
            "/v1/change-request/009fa369-291b-403f-a85a-15e938c26f2f",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_body,
        )
        assert response.status_code == 404
        response_body = response.get_json()
        assert (
            response_body["message"]
            == "Could not find ChangeRequest with ID 009fa369-291b-403f-a85a-15e938c26f2f"
        )


class TestUploadDocument:
    def test_success(
        self, application, change_request, client, consented_user, consented_user_token
    ):

        form_data = {"document_type": "Passport", "name": "passport.png", "description": "Passport"}
        form_data["file"] = (io.BytesIO(b"abcdef"), "test.png")

        application.user = consented_user

        response = client.post(
            "/v1/change-request/{}/documents".format(change_request.change_request_id),
            headers={"Authorization": f"Bearer {consented_user_token}"},
            content_type="multipart/form-data",
            data=form_data,
        )

        response_json = response.get_json()

        assert response_json["status_code"] == 200

        response_data = response_json["data"]
        assert response_data["content_type"] == "image/png"
        assert response_data["description"] == "Passport"
        assert response_data["document_type"] == "Passport"
        assert (
            response_data["fineos_document_id"] == "3011"
        )  # See massgov/pfml/fineos/mock_client.py
        assert response_data["name"] == "passport.png"
        assert response_data["user_id"] == str(consented_user.user_id)
        assert response_data["created_at"] is not None
