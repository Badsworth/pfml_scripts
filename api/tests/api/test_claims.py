import massgov.pfml.fineos.mock_client
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import ClaimFactory, EmployerFactory


def test_non_employers_cannot_download_documents(client, auth_token):
    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-01/documents/1111",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


def test_non_employers_cannot_download_documents_not_attached_to_absence(
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
        "/v1/employers/claims/NTN-100-ABS-01/documents/bad_doc_id",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    assert response.status_code == 403


def test_non_employers_cannot_download_documents_of_disallowed_types(
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
        "/v1/employers/claims/NTN-100-ABS-01/documents/3011",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    assert response.status_code == 403


def test_employers_receive_200_from_document_download(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    ClaimFactory.create(
        employer_id=employer.employer_id, fineos_absence_id="leave_admin_allowable_doc_type"
    )
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/employers/claims/leave_admin_allowable_doc_type/documents/3011",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    assert response.status_code == 200


def test_non_employers_cannot_access_get_documents(client, auth_token):
    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-01/documents",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


def test_employers_receive_200_from_get_documents(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    ClaimFactory.create(employer_id=employer.employer_id, fineos_absence_id="NTN-100-ABS-01")
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-01/documents",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    assert response.status_code == 200


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
    ClaimFactory.create(employer_id=employer.employer_id, fineos_absence_id="NTN-100-ABS-01")

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
    assert response.get_json()["data"]["follow_up_date"] == "2021-02-01"


def test_employers_receive_proper_claim_using_correct_fineos_web_id(
    client, employer_user, employer_auth_token, test_db_session
):
    employer1 = EmployerFactory.create()
    employer2 = EmployerFactory.create()

    ClaimFactory.create(employer_id=employer1.employer_id, fineos_absence_id="NTN-100-ABS-01")
    ClaimFactory.create(employer_id=employer2.employer_id, fineos_absence_id="NTN-100-ABS-02")

    link1 = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer1.employer_id,
        fineos_web_id="employer1-fineos-web-id",
    )

    link2 = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer2.employer_id,
        fineos_web_id="employer2-fineos-web-id",
    )

    test_db_session.add(link1)
    test_db_session.add(link2)
    test_db_session.commit()

    massgov.pfml.fineos.mock_client.start_capture()

    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    capture = massgov.pfml.fineos.mock_client.get_capture()
    handler, fineos_web_id, params = capture[0]

    assert response.status_code == 200
    assert handler == "get_absence_period_decisions"
    assert fineos_web_id == "employer1-fineos-web-id"
    assert params == {"absence_id": "NTN-100-ABS-01"}

    massgov.pfml.fineos.mock_client.start_capture()

    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-02/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )

    capture = massgov.pfml.fineos.mock_client.get_capture()
    handler, fineos_web_id, params = capture[0]

    assert response.status_code == 200
    assert handler == "get_absence_period_decisions"
    assert fineos_web_id == "employer2-fineos-web-id"
    assert params == {"absence_id": "NTN-100-ABS-02"}


def test_non_employees_cannot_access_employer_update_claim_review(client, auth_token):
    update_request_body = {
        "comment": "string",
        "employer_benefits": [
            {
                "benefit_amount_dollars": 0,
                "benefit_amount_frequency": "Per Day",
                "benefit_end_date": "1970-01-01",
                "benefit_start_date": "1970-01-01",
                "benefit_type": "Accrued Paid Leave",
            }
        ],
        "employer_decision": "Approve",
        "fraud": "Yes",
        "hours_worked_per_week": 0,
        "previous_leaves": [
            {
                "leave_end_date": "1970-01-01",
                "leave_start_date": "1970-01-01",
                "leave_type": "Pregnancy/Maternity",
            }
        ],
    }

    response = client.patch(
        "/v1/employers/claims/3/review",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_request_body,
    )

    assert response.status_code == 403


def test_employees_receive_200_from_employer_update_claim_review(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create()
    ClaimFactory.create(employer_id=employer.employer_id, fineos_absence_id="NTN-100-ABS-01")
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    update_request_body = {
        "comment": "string",
        "employer_benefits": [
            {
                "benefit_amount_dollars": 0,
                "benefit_amount_frequency": "Per Day",
                "benefit_end_date": "1970-01-01",
                "benefit_start_date": "1970-01-01",
                "benefit_type": "Accrued Paid Leave",
            }
        ],
        "employer_decision": "Approve",
        "fraud": "Yes",
        "hours_worked_per_week": 0,
        "previous_leaves": [
            {
                "leave_end_date": "1970-01-01",
                "leave_start_date": "1970-01-01",
                "leave_type": "Pregnancy/Maternity",
            }
        ],
    }

    response = client.patch(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=update_request_body,
    )

    assert response.status_code == 200
