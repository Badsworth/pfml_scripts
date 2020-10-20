from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import EmployerFactory


def test_non_employers_cannot_access_get_claim_review(client, auth_token):
    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


def test_employers_receive_200_from_get_claim_review(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    assert response.status_code == 200


def test_non_employees_cannot_access_employer_update_claim_review(client, auth_token):
    update_request_body = {
        "comment": "string",
        "employer_benefits": [
            {
                "benefit_amount_dollars": 0,
                "benefit_amount_frequency": "string",
                "benefit_end_date": "1970-01-01",
                "benefit_start_date": "1970-01-01",
                "benefit_type": "string",
            }
        ],
        "employer_notification_date": "1970-01-01",
        "hours_worked_per_week": 0,
        "previous_leaves": [{"leave_end_date": "1970-01-01", "leave_start_date": "1970-01-01"}],
    }

    response = client.patch(
        "/v1/employers/claims/3/review",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_request_body,
    )

    assert response.status_code == 403


def test_employees_receive_200_from_employer_update_claim_review(client, employer_auth_token):
    update_request_body = {
        "comment": "string",
        "employer_benefits": [
            {
                "benefit_amount_dollars": 0,
                "benefit_amount_frequency": "string",
                "benefit_end_date": "1970-01-01",
                "benefit_start_date": "1970-01-01",
                "benefit_type": "string",
            }
        ],
        "employer_notification_date": "1970-01-01",
        "hours_worked_per_week": 0,
        "previous_leaves": [{"leave_end_date": "1970-01-01", "leave_start_date": "1970-01-01"}],
    }

    response = client.patch(
        "/v1/employers/claims/3/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=update_request_body,
    )

    assert response.status_code == 200
