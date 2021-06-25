import copy
import json

import pytest

import tests.api
from massgov.pfml.db.models.applications import Notification
from massgov.pfml.db.models.employees import Claim
from massgov.pfml.db.models.factories import EmployeeWithFineosNumberFactory, EmployerFactory

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
    request_json = json.loads(notification.request_json)
    assert request_json == leave_admin_body

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
    request_json = json.loads(notification.request_json)
    assert request_json == leave_admin_body_no_document_type


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
    request_json = json.loads(notification.request_json)
    assert request_json == leave_admin_body_empty_str_document_type


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
    request_json = json.loads(notification.request_json)
    assert request_json == claimant_body


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
