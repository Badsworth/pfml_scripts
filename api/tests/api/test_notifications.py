import copy
import json

import tests.api
from massgov.pfml.db.models.applications import Notification

leave_admin_body = {
    "absence_case_id": "NTN-111-ABS-01",
    "document_type": "Approval Notice",
    "fein": "00-0000000",
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
    "fein": "00-0000000",
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


def test_notifications_post_leave_admin(client, test_db_session, fineos_user_token):
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=leave_admin_body,
    )
    assert response.status_code == 201

    notification = test_db_session.query(Notification).first()

    assert notification.created_at
    assert notification.updated_at
    request_json = json.loads(notification.request_json)
    assert request_json == leave_admin_body


def test_notifications_post_leave_admin_no_document_type(
    client, test_db_session, fineos_user_token
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
    request_json = json.loads(notification.request_json)
    assert request_json == leave_admin_body_no_document_type


def test_notifications_post_leave_admin_empty_str_document_type(
    client, test_db_session, fineos_user_token
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
    request_json = json.loads(notification.request_json)
    assert request_json == leave_admin_body_empty_str_document_type


def test_notifications_post_claimant(client, test_db_session, fineos_user_token):
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=claimant_body,
    )
    assert response.status_code == 201

    notification = test_db_session.query(Notification).first()

    assert notification.created_at
    assert notification.updated_at
    request_json = json.loads(notification.request_json)
    assert request_json == claimant_body


def test_notification_post_multiple_notifications(client, test_db_session, fineos_user_token):
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


def test_notification_post_missing_leave_admin_param(client, test_db_session, fineos_user_token):
    bad_body = leave_admin_body.copy()
    bad_body["recipients"] = [{"email_address": "fake@website.com"}]
    response = client.post(
        "/v1/notifications", headers={"Authorization": f"Bearer {fineos_user_token}"}, json=bad_body
    )
    assert response.status_code == 400

    tests.api.validate_error_response(response, 400, message="Validation error")
    assert len(response.get_json()["errors"]) == 2


def test_notification_post_missing_claimant_param(client, test_db_session, fineos_user_token):
    bad_body = claimant_body.copy()
    bad_body["recipients"] = [{"email_address": "fake@website.com"}]
    response = client.post(
        "/v1/notifications", headers={"Authorization": f"Bearer {fineos_user_token}"}, json=bad_body
    )
    assert response.status_code == 400

    tests.api.validate_error_response(response, 400, message="Validation error")
    assert len(response.get_json()["errors"]) == 2


def test_notification_post_unauthorized(client, test_db_session, auth_token):
    response = client.post(
        "/v1/notifications",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=leave_admin_body,
    )
    tests.api.validate_error_response(response, 403)
    notifications = test_db_session.query(Notification).all()
    assert len(notifications) == 0
