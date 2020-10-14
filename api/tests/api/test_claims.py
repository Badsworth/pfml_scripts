def test_non_employees_cannot_access_employer_update_claim(client, auth_token):
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
        "/v1/employers/claim/review/3",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_request_body,
    )

    assert response.status_code == 403


def test_employees_receive_200_from_employer_update_claim(client, employer_auth_token):
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
        "/v1/employers/claim/review/3",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=update_request_body,
    )

    assert response.status_code == 200
