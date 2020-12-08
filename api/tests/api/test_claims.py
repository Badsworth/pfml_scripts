import massgov.pfml.fineos.mock_client
from massgov.pfml.api.services.administrator_fineos_actions import DOWNLOADABLE_DOC_TYPES
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


def test_employers_receive_only_downloadable_documents_from_get_documents(
    client, employer_user, employer_auth_token, test_db_session
):
    test_absence_id = "leave_admin_mixed_allowable_doc_types"
    employer = EmployerFactory.create()
    ClaimFactory.create(employer_id=employer.employer_id, fineos_absence_id=test_absence_id)
    link = UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
    )
    test_db_session.add(link)
    test_db_session.commit()

    response = client.get(
        f"/v1/employers/claims/{test_absence_id}/documents",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
    )
    response_body = response.get_json()
    document_data = response_body.get("data")

    assert response.status_code == 200
    for document in document_data:
        assert document.get("document_type") in DOWNLOADABLE_DOC_TYPES


def test_non_employers_cannot_access_get_claim_review(client, auth_token):
    response = client.get(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 403


def test_employers_receive_200_from_get_claim_review(
    client, employer_user, employer_auth_token, test_db_session
):
    employer = EmployerFactory.create(employer_fein="999999999")
    ClaimFactory.create(
        employer_id=employer.employer_id, fineos_absence_id="NTN-100-ABS-01",
    )

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
    response_data = response.get_json()["data"]

    assert response.status_code == 200

    assert response_data["follow_up_date"] == "2021-02-01"
    # This field is set in mock_client.py::get_customer_occupations
    assert response_data["hours_worked_per_week"] == 40
    assert response_data["employer_fein"] == "99-9999999"
    # The fields below are set in mock_client.py::mock_customer_info
    assert response_data["date_of_birth"] == "****-12-25"
    assert response_data["tax_identifier"] == "***-**-1234"
    assert response_data["residential_address"]["city"] == "Atlanta"
    assert response_data["residential_address"]["line_1"] == "55 Trinity Ave."
    assert response_data["residential_address"]["line_2"] == "Suite 3450"
    assert response_data["residential_address"]["state"] == "GA"
    assert response_data["residential_address"]["zip"] == "30303"


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
        "has_amendments": False,
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
        "has_amendments": False,
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


def test_employer_confirmation_sent_with_employer_update_claim_review(
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
        "has_amendments": False,
        "hours_worked_per_week": 0,
        "previous_leaves": [
            {
                "leave_end_date": "1970-01-01",
                "leave_start_date": "1970-01-01",
                "leave_type": "Pregnancy/Maternity",
            }
        ],
    }

    massgov.pfml.fineos.mock_client.start_capture()

    client.patch(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=update_request_body,
    )

    capture = massgov.pfml.fineos.mock_client.get_capture()

    assert capture == [
        ("get_outstanding_information", "fake-fineos-web-id", {"case_id": "NTN-100-ABS-01"}),
        (
            "update_outstanding_information_as_received",
            "fake-fineos-web-id",
            {
                "outstanding_information": massgov.pfml.fineos.models.group_client_api.OutstandingInformationData(
                    informationType="Employer Confirmation of Leave Data"
                ),
                "case_id": "NTN-100-ABS-01",
            },
        ),
    ]


def test_employer_confirmation_is_not_sent(
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
        "has_amendments": False,
        "hours_worked_per_week": 0,
        "previous_leaves": [
            {
                "leave_end_date": "1970-01-01",
                "leave_start_date": "1970-01-01",
                "leave_type": "Pregnancy/Maternity",
            }
        ],
    }

    # confirmation is not sent if there is not Employer confirmation outstanding info
    ClaimFactory.create(
        employer_id=employer.employer_id, fineos_absence_id="NTN-CASE-WITHOUT-OUTSTANDING-INFO"
    )

    massgov.pfml.fineos.mock_client.start_capture()

    client.patch(
        "/v1/employers/claims/NTN-CASE-WITHOUT-OUTSTANDING-INFO/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=update_request_body,
    )

    capture = massgov.pfml.fineos.mock_client.get_capture()

    assert capture == [
        (
            "get_outstanding_information",
            "fake-fineos-web-id",
            {"case_id": "NTN-CASE-WITHOUT-OUTSTANDING-INFO"},
        ),
    ]

    # confirmation is not sent if there are amendments
    update_request_body["has_amendments"] = True

    massgov.pfml.fineos.mock_client.start_capture()

    client.patch(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=update_request_body,
    )

    capture = massgov.pfml.fineos.mock_client.get_capture()

    assert capture == []

    # confirmation is not sent if the claim is not approved
    update_request_body["has_amendments"] = False
    update_request_body["employer_decision"] = "Deny"

    massgov.pfml.fineos.mock_client.start_capture()

    client.patch(
        "/v1/employers/claims/NTN-100-ABS-01/review",
        headers={"Authorization": f"Bearer {employer_auth_token}"},
        json=update_request_body,
    )

    capture = massgov.pfml.fineos.mock_client.get_capture()

    assert capture == []
