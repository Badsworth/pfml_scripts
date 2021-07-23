import copy
from datetime import date, timedelta
from unittest import mock

import pytest

import tests.api
from massgov.pfml.db.models.applications import Notification
from massgov.pfml.db.models.employees import (
    Claim,
    ManagedRequirement,
    ManagedRequirementCategory,
    ManagedRequirementStatus,
    ManagedRequirementType,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeWithFineosNumberFactory,
    EmployerFactory,
)
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
)
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails

# every test in here requires real resources
pytestmark = pytest.mark.integration


leave_admin_body = {
    "absence_case_id": "NTN-111-ABS-01",
    "document_type": "Approval Notice",
    "fein": "71-6779225",
    "organization_name": "Wayne Enterprises",
    "trigger": "claim.approved",
    "source": "Self-Service",
    "recipient_type": "Leave Administrator",
    "recipients": [
        {"full_name": "john smith", "email_address": "example@gmail.com", "contact_id": "11"}
    ],
    "claimant_info": {
        "first_name": "jane",
        "last_name": "doe",
        "date_of_birth": "1970-01-01",
        "customer_id": "1234",
    },
}

claimant_body = {
    "absence_case_id": "NTN-111-ABS-01",
    "document_type": "Legal Notice",
    "fein": "71-6779225",
    "organization_name": "Wayne Enterprises",
    "trigger": "claim.approved",
    "source": "Self-Service",
    "recipient_type": "Claimant",
    "recipients": [
        {"first_name": "john", "last_name": "smith", "email_address": "example@gmail.com"}
    ],
    "claimant_info": {
        "first_name": "jane",
        "last_name": "doe",
        "date_of_birth": "1970-01-01",
        "customer_id": "1234",
    },
}

invalid_fein_body = {
    "absence_case_id": "NTN-111-ABS-01",
    "document_type": "Legal Notice",
    "fein": "invalid-fein",
    "organization_name": "Wayne Enterprises",
    "trigger": "claim.approved",
    "source": "Self-Service",
    "recipient_type": "Claimant",
    "recipients": [
        {"first_name": "john", "last_name": "smith", "email_address": "example@gmail.com"}
    ],
    "claimant_info": {
        "first_name": "jane",
        "last_name": "doe",
        "date_of_birth": "1970-01-01",
        "customer_id": "1234",
    },
}


@pytest.fixture
def employer():
    return EmployerFactory.create(employer_fein="716779225")


def test_notifications_post_leave_admin(client, test_db_session, fineos_user_token, employer):
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=leave_admin_body,
    )
    assert response.status_code == 201

    notification = test_db_session.query(Notification).first()

    assert notification.created_at
    assert notification.updated_at
    assert notification.fineos_absence_id == leave_admin_body["absence_case_id"]
    assert notification.request_json == leave_admin_body

    associated_claim = (
        test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == leave_admin_body["absence_case_id"])
        .one_or_none()
    )

    assert associated_claim is not None
    assert associated_claim.employer_id is not None
    assert associated_claim.fineos_absence_id == "NTN-111-ABS-01"
    assert associated_claim.employee_id is None


def test_notifications_update_claims(client, test_db_session, fineos_user_token, employer):
    existing_claim = Claim(fineos_absence_id=leave_admin_body["absence_case_id"])
    test_db_session.add(existing_claim)
    test_db_session.commit()
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=leave_admin_body,
    )
    assert response.status_code == 201
    claim_record = (
        test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == leave_admin_body["absence_case_id"])
        .one_or_none()
    )
    assert claim_record
    assert claim_record.employer_id == employer.employer_id
    assert claim_record.employee_id is None


def test_notifications_post_leave_admin_no_document_type(
    client, test_db_session, fineos_user_token, employer
):
    leave_admin_body_no_document_type = copy.deepcopy(leave_admin_body)
    del leave_admin_body_no_document_type["document_type"]
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=leave_admin_body_no_document_type,
    )
    assert response.status_code == 201

    notification = test_db_session.query(Notification).first()

    assert notification.created_at
    assert notification.updated_at
    assert notification.fineos_absence_id == leave_admin_body["absence_case_id"]
    assert notification.request_json == leave_admin_body_no_document_type


def test_notifications_invalid_fein_error(client, test_db_session, fineos_user_token, employer):
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=invalid_fein_body,
    )
    assert response.status_code == 400
    tests.api.validate_error_response(
        response,
        400,
        message="Failed to lookup the specified FEIN to add Claim record on Notification POST request",
    )


def test_notification_post_employee(client, test_db_session, fineos_user_token, employer):
    employee = EmployeeWithFineosNumberFactory.create()
    body = copy.deepcopy(leave_admin_body)
    body["claimant_info"]["customer_id"] = employee.fineos_customer_number
    response = client.post(
        "/v1/notifications", headers={"Authorization": f"Bearer {fineos_user_token}"}, json=body,
    )
    assert response.status_code == 201
    claim_record = (
        test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == body["absence_case_id"])
        .one_or_none()
    )
    assert claim_record
    assert claim_record.employee_id is not None
    assert claim_record.employer_id == employer.employer_id
    assert claim_record.employee_id == employee.employee_id


def test_notifications_update_claims_employee(client, test_db_session, fineos_user_token, employer):
    employee = EmployeeWithFineosNumberFactory.create()
    body = copy.deepcopy(leave_admin_body)
    body["claimant_info"]["customer_id"] = employee.fineos_customer_number
    existing_claim = Claim(fineos_absence_id=leave_admin_body["absence_case_id"])
    test_db_session.add(existing_claim)
    test_db_session.commit()
    response = client.post(
        "/v1/notifications", headers={"Authorization": f"Bearer {fineos_user_token}"}, json=body,
    )
    assert response.status_code == 201
    claim_record = (
        test_db_session.query(Claim)
        .filter(Claim.fineos_absence_id == body["absence_case_id"])
        .one_or_none()
    )
    assert claim_record
    assert claim_record.employer_id == employer.employer_id
    assert claim_record.employee_id == employee.employee_id


def test_notifications_post_leave_admin_empty_str_document_type(
    client, test_db_session, fineos_user_token, employer
):
    leave_admin_body_empty_str_document_type = copy.deepcopy(leave_admin_body)
    leave_admin_body_empty_str_document_type["document_type"] = ""
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=leave_admin_body_empty_str_document_type,
    )
    assert response.status_code == 201

    notification = test_db_session.query(Notification).first()

    assert notification.created_at
    assert notification.updated_at
    assert notification.fineos_absence_id == leave_admin_body["absence_case_id"]
    assert notification.request_json == leave_admin_body_empty_str_document_type


def test_notifications_post_claimant(client, test_db_session, fineos_user_token, employer):
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=claimant_body,
    )
    assert response.status_code == 201

    notification = test_db_session.query(Notification).first()

    assert notification.created_at
    assert notification.updated_at
    assert notification.fineos_absence_id == leave_admin_body["absence_case_id"]
    assert notification.request_json == claimant_body


def test_notification_post_multiple_notifications(
    client, test_db_session, fineos_user_token, employer
):
    # Send the same notification twice, we don't do any sort of de-dupe
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=leave_admin_body,
    )
    assert response.status_code == 201
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=leave_admin_body,
    )
    assert response.status_code == 201

    notifications = test_db_session.query(Notification).all()
    assert len(notifications) == 2


def test_notification_post_missing_leave_admin_param(
    client, test_db_session, fineos_user_token, employer
):
    bad_body = leave_admin_body.copy()
    bad_body["recipients"] = [{"email_address": "fake@website.com"}]
    response = client.post(
        "/v1/notifications", headers={"Authorization": f"Bearer {fineos_user_token}"}, json=bad_body
    )
    assert response.status_code == 400

    tests.api.validate_error_response(response, 400, message="Validation error")
    assert len(response.get_json()["errors"]) == 2


def test_notification_post_missing_claimant_param(
    client, test_db_session, fineos_user_token, employer
):
    bad_body = claimant_body.copy()
    bad_body["recipients"] = [{"email_address": "fake@website.com"}]
    response = client.post(
        "/v1/notifications", headers={"Authorization": f"Bearer {fineos_user_token}"}, json=bad_body
    )
    assert response.status_code == 400

    tests.api.validate_error_response(response, 400, message="Validation error")
    assert len(response.get_json()["errors"]) == 2


def test_notification_post_unauthorized(client, test_db_session, auth_token, employer):
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=leave_admin_body,
    )
    tests.api.validate_error_response(response, 403)
    notifications = test_db_session.query(Notification).all()
    assert len(notifications) == 0


class TestNotificationManagedRequirement:
    @classmethod
    def managed_requirement(cls):
        return {
            "managedReqId": 100,
            "status": ManagedRequirementStatus.get_description(1),
            "category": ManagedRequirementCategory.get_description(1),
            "type": ManagedRequirementType.get_description(1),
            "followUpDate": (date.today() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "documentReceived": False,
            "creator": "unknown",
            "subjectPartyName": "unknown",
            "sourceOfInfoPartyName": "unknown",
            "creationDate": None,
            "dateSuppressed": None,
        }

    @classmethod
    def leave_admin_body_create(cls):
        rv = leave_admin_body.copy()
        rv["trigger"] = "Employer Confirmation of Leave Data"
        return rv

    @classmethod
    def leave_admin_body_update(cls):
        rv = leave_admin_body.copy()
        rv["trigger"] = "Designation Notice"
        return rv

    @pytest.fixture()
    def claim(self, employer):
        return ClaimFactory.create(
            employer_id=employer.employer_id,
            fineos_absence_id=self.leave_admin_body_update()["absence_case_id"],
        )

    @pytest.fixture()
    def fineos_managed_requirement(self, claim):
        return ManagedRequirementDetails.parse_obj(self.managed_requirement())

    def _api_call_create(self, client, token):
        return client.post(
            "/v1/notifications",
            headers={"Authorization": f"Bearer {token}"},
            json=self.leave_admin_body_create(),
        )

    def _api_call_update(self, client, token):
        return client.post(
            "/v1/notifications",
            headers={"Authorization": f"Bearer {token}"},
            json=self.leave_admin_body_update(),
        )

    def _assert_managed_requirement_data(
        self,
        claim: Claim,
        managed_requirement: ManagedRequirement,
        fineos_managed_requirement: ManagedRequirementDetails,
    ):
        assert managed_requirement is not None
        assert str(managed_requirement.claim_id) == str(claim.claim_id)
        assert managed_requirement.fineos_managed_requirement_id == str(
            fineos_managed_requirement.managedReqId
        )
        assert managed_requirement.follow_up_date == fineos_managed_requirement.followUpDate
        status = (
            managed_requirement.managed_requirement_status.managed_requirement_status_description
        )
        assert status == fineos_managed_requirement.status

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_notification_managed_requirement_create_success(
        self,
        mock_get_req,
        client,
        test_db_session,
        fineos_user_token,
        fineos_managed_requirement,
        claim,
    ):
        mock_get_req.return_value = [fineos_managed_requirement]

        response = self._api_call_create(client, fineos_user_token)

        assert response.status_code == 201
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )
        self._assert_managed_requirement_data(
            claim, managed_requirement, fineos_managed_requirement
        )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_notification_managed_requirement_update_success(
        self,
        mock_get_req,
        client,
        test_db_session,
        claim,
        fineos_user_token,
        fineos_managed_requirement,
    ):
        mock_get_req.return_value = [fineos_managed_requirement]
        # create existing managed requirement in db not in sync with fineos managed requirement
        create_managed_requirement_from_fineos(
            test_db_session, claim.claim_id, fineos_managed_requirement, {}
        )
        fineos_managed_requirement.followUpDate = date.today() + timedelta(days=20)
        fineos_managed_requirement.status = ManagedRequirementStatus.get_description(2)

        response = self._api_call_update(client, fineos_user_token)

        assert response.status_code == 201
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )
        self._assert_managed_requirement_data(
            claim, managed_requirement, fineos_managed_requirement
        )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_notification_managed_requirement_create_failure(
        self, mock_get_req, client, test_db_session, fineos_user_token, fineos_managed_requirement,
    ):
        fineos_managed_requirement.status = "Bad Status"
        mock_get_req.return_value = [fineos_managed_requirement]

        response = self._api_call_create(client, fineos_user_token)

        assert response.status_code == 201
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )
        assert managed_requirement is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_notification_managed_requirement_update_failure_status(
        self, mock_get_req, client, test_db_session, fineos_user_token, fineos_managed_requirement,
    ):
        fineos_managed_requirement.status = "Bad Status"
        mock_get_req.return_value = [fineos_managed_requirement]

        response = self._api_call_update(client, fineos_user_token)

        assert response.status_code == 201
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )

        assert managed_requirement is None

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_notification_managed_requirement_update_failure_no_contact_id(
        self,
        mock_get_req,
        client,
        claim,
        test_db_session,
        fineos_user_token,
        fineos_managed_requirement,
    ):
        mock_get_req.return_value = [fineos_managed_requirement]
        body = self.leave_admin_body_update().copy()
        body["recipients"] = []
        create_managed_requirement_from_fineos(
            test_db_session, claim.claim_id, fineos_managed_requirement, {}
        )
        fineos_managed_requirement.followUpDate = date.today() + timedelta(days=20)
        fineos_managed_requirement.status = ManagedRequirementStatus.get_description(2)

        response = client.post(
            "/v1/notifications",
            headers={"Authorization": f"Bearer {fineos_user_token}"},
            json=body,
        )
        assert response.status_code == 201
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )

        assert managed_requirement is not None
        assert str(managed_requirement.claim_id) == str(claim.claim_id)
        assert managed_requirement.fineos_managed_requirement_id == str(
            fineos_managed_requirement.managedReqId
        )
        # assert no update
        assert managed_requirement.follow_up_date != fineos_managed_requirement.followUpDate
        assert (
            managed_requirement.managed_requirement_status.managed_requirement_status_description
            != fineos_managed_requirement.status
        )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_notification_managed_requirement_update_success_new_man_req(
        self,
        mock_get_req,
        client,
        test_db_session,
        claim,
        fineos_user_token,
        fineos_managed_requirement,
    ):
        mock_get_req.return_value = [fineos_managed_requirement]

        response = self._api_call_create(client, fineos_user_token)

        assert response.status_code == 201
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )

        self._assert_managed_requirement_data(
            claim, managed_requirement, fineos_managed_requirement
        )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_notification_managed_requirement_update_success_multiple_man_req(
        self,
        mock_get_req,
        client,
        test_db_session,
        claim,
        fineos_user_token,
        fineos_managed_requirement,
    ):
        second_requirement = self.managed_requirement()
        second_requirement["managedReqId"] = fineos_managed_requirement.managedReqId + 1
        fineos_second_managed_requirement = ManagedRequirementDetails.parse_obj(second_requirement)
        managed_requirements = [
            {
                "fineos_obj": fineos_managed_requirement,
                "new_follow_up_date": date.today() + timedelta(days=20),
                "description_id": 2,
            },
            {
                "fineos_obj": fineos_second_managed_requirement,
                "new_follow_up_date": date.today() + timedelta(days=2),
                "description_id": 3,
            },
        ]
        mock_get_req.return_value = [man_req["fineos_obj"] for man_req in managed_requirements]

        # create existing managed requirements in db not in sync with fineos managed requirements
        for man_req in managed_requirements:
            create_managed_requirement_from_fineos(
                test_db_session, claim.claim_id, man_req["fineos_obj"], {}
            )
            man_req["fineos_obj"].followUpDate = man_req["new_follow_up_date"]
            man_req["fineos_obj"].status = ManagedRequirementStatus.get_description(
                man_req["description_id"]
            )

        response = self._api_call_update(client, fineos_user_token)

        assert response.status_code == 201

        for man_req in managed_requirements:
            managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
                man_req["fineos_obj"].managedReqId, test_db_session
            )

            self._assert_managed_requirement_data(claim, managed_requirement, man_req["fineos_obj"])
