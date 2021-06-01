import copy
import datetime

import pytest
from freezegun import freeze_time

import massgov.pfml.api.claims
import massgov.pfml.fineos.mock_client
import tests.api
from massgov.pfml.api.services.administrator_fineos_actions import DOWNLOADABLE_DOC_TYPES
from massgov.pfml.db.models.employees import UserLeaveAdministrator
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    VerificationFactory,
)
from massgov.pfml.fineos import models
from massgov.pfml.fineos.mock_client import MockFINEOSClient
from massgov.pfml.util import feature_gate
from massgov.pfml.util.pydantic.types import FEINFormattedStr
from massgov.pfml.util.strings import format_fein

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture(params=["env_var", "feature_gate", "disabled"])
def test_verification(request, monkeypatch, initialize_factories_session):
    # This checks that all tests work _both_ with
    # 1. Verification disabled and no verification record AND
    # 2. Verification enabled and verification record
    # TODO: Remove the params behavior after rollout https://lwd.atlassian.net/browse/EMPLOYER-962
    if request.param == "env_var":
        monkeypatch.setenv("ENFORCE_LEAVE_ADMIN_VERIFICATION", "1")
        return VerificationFactory.create()
    elif request.param == "feature_gate":
        monkeypatch.setenv("ENFORCE_LEAVE_ADMIN_VERIFICATION", "0")
        monkeypatch.setattr(
            feature_gate, "check_enabled", lambda feature_name, user_email: True,
        )

        return VerificationFactory.create()
    else:
        monkeypatch.setenv("ENFORCE_LEAVE_ADMIN_VERIFICATION", "0")
        return None


@pytest.fixture
def update_claim_body():
    return {
        "comment": "string",
        "employer_benefits": [
            {
                "benefit_amount_dollars": 0,
                "benefit_amount_frequency": "Per Day",
                "benefit_end_date": "1970-01-01",
                "benefit_start_date": "1970-01-01",
                "benefit_type": "Accrued paid leave",
            }
        ],
        "employer_decision": "Approve",
        "fraud": "Yes",
        "has_amendments": False,
        "hours_worked_per_week": 40,
        "previous_leaves": [
            {
                "leave_end_date": "2021-02-06",
                "leave_start_date": "2021-01-25",
                "leave_reason": "Pregnancy / Maternity",
            }
        ],
        "leave_reason": "Pregnancy/Maternity",
    }


@pytest.mark.integration
class TestVerificationEnforcement:
    # This class groups the tests that ensure that existing users with UserLeaveAdministrator records
    # get 403s when attempting to access claim data without a Verification

    @pytest.fixture()
    def employer(self):
        employer = EmployerFactory.create()
        return employer

    @pytest.fixture(autouse=True, params=["env_var", "feature_gate"])
    def _enforce_verifications(self, request, monkeypatch, employer_user):
        if request.param == "env_var":
            monkeypatch.setenv("ENFORCE_LEAVE_ADMIN_VERIFICATION", "1")
        else:
            monkeypatch.setenv("ENFORCE_LEAVE_ADMIN_VERIFICATION", "0")
            monkeypatch.setattr(
                feature_gate, "check_enabled", lambda feature_name, user_email: True,
            )

    @pytest.fixture
    def setup_claim(self, test_db_session, employer_user):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
        )
        test_db_session.add(link)
        test_db_session.commit()
        return claim

    def test_employers_cannot_access_claims_endpoint_without_verification(
        self, client, auth_token, employer_auth_token, setup_claim
    ):
        response = client.get(
            f"/v1/employers/claims/{setup_claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        assert response.get_json()["message"] == "User is not Verified"

    def test_employers_cannot_download_documents_without_verification(
        self, client, auth_token, employer_auth_token, setup_claim
    ):
        response = client.get(
            f"/v1/employers/claims/{setup_claim.fineos_absence_id}/documents/1111",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        assert response.get_json()["message"] == "User is not Verified"

    def test_employers_cannot_update_claim_without_verification(
        self, client, employer_auth_token, update_claim_body, setup_claim
    ):
        response = client.patch(
            f"/v1/employers/claims/{setup_claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )
        assert response.status_code == 403
        assert response.get_json()["message"] == "User is not Verified"

    def test_get_claim_user_cannot_access_without_verification(
        self, client, employer_auth_token, setup_claim
    ):
        response = client.get(
            f"/v1/claims/{setup_claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        assert response.get_json()["message"] == "User does not have access to claim."


@pytest.mark.integration
class TestNotAuthorizedForAccess:
    # This class groups the tests that ensure that users get 403s when
    # attempting to access claim data without an associated user leave administrator
    @pytest.fixture()
    def employer(self):
        employer = EmployerFactory.create()
        return employer

    @pytest.fixture
    def setup_claim(self, test_db_session, employer_user):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        test_db_session.add(employer, claim)
        test_db_session.commit()
        return claim

    def test_employers_cannot_access_claims_endpoint_without_ula(
        self, client, auth_token, employer_auth_token, setup_claim
    ):
        response = client.get(
            f"/v1/employers/claims/{setup_claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "User does not have leave administrator record for this employer"
        )
        assert (
            response.get_json()["errors"][0]["message"]
            == "User does not have leave administrator record for this employer"
        )
        assert response.get_json()["errors"][0]["type"] == "unauthorized_leave_admin"

    def test_employers_cannot_download_documents_without_ula(
        self, client, auth_token, employer_auth_token, setup_claim
    ):
        response = client.get(
            f"/v1/employers/claims/{setup_claim.fineos_absence_id}/documents/1111",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "User does not have leave administrator record for this employer"
        )
        assert (
            response.get_json()["errors"][0]["message"]
            == "User does not have leave administrator record for this employer"
        )
        assert response.get_json()["errors"][0]["type"] == "unauthorized_leave_admin"

    def test_employers_cannot_update_claim_without_ula(
        self, client, employer_auth_token, update_claim_body, setup_claim
    ):
        response = client.patch(
            f"/v1/employers/claims/{setup_claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )
        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "User does not have leave administrator record for this employer"
        )
        assert (
            response.get_json()["errors"][0]["message"]
            == "User does not have leave administrator record for this employer"
        )
        assert response.get_json()["errors"][0]["type"] == "unauthorized_leave_admin"


@pytest.mark.integration
class TestDownloadDocuments:
    @pytest.fixture
    def setup_employer(self, test_db_session, employer_user, test_verification):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()
        return claim

    def test_non_employers_cannot_download_documents(self, client, auth_token, setup_employer):
        response = client.get(
            f"/v1/employers/claims/{setup_employer.fineos_absence_id}/documents/1111",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403

    def test_non_employers_cannot_download_documents_not_attached_to_absence(
        self, client, employer_auth_token, setup_employer
    ):
        response = client.get(
            f"/v1/employers/claims/{setup_employer.fineos_absence_id}/documents/bad_doc_id",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403

    def test_non_employers_cannot_download_documents_of_disallowed_types(
        self, client, employer_auth_token, setup_employer
    ):
        response = client.get(
            f"/v1/employers/claims/{setup_employer.fineos_absence_id}/documents/3011",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403

    def test_employers_receive_200_from_document_download(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        ClaimFactory.create(
            employer_id=employer.employer_id, fineos_absence_id="leave_admin_allowable_doc_type"
        )
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.get(
            "/v1/employers/claims/leave_admin_allowable_doc_type/documents/3011",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200

    def test_non_employers_cannot_access_get_documents(self, client, auth_token, setup_employer):
        response = client.get(
            f"/v1/employers/claims/{setup_employer.fineos_absence_id}/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403

    def test_employers_receive_200_from_get_documents(
        self, client, employer_auth_token, setup_employer
    ):
        response = client.get(
            f"/v1/employers/claims/{setup_employer.fineos_absence_id}/documents",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200

    def test_employers_receive_only_downloadable_documents_from_get_documents(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        test_absence_id = "leave_admin_mixed_allowable_doc_types"
        employer = EmployerFactory.create()
        ClaimFactory.create(employer_id=employer.employer_id, fineos_absence_id=test_absence_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
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


@pytest.mark.integration
class TestGetClaimReview:
    def test_non_employers_cannot_access_get_claim_review(self, client, auth_token):
        response = client.get(
            "/v1/employers/claims/NTN-100-ABS-01/review",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403

    @freeze_time("2020-12-07")
    def test_employers_receive_200_from_get_claim_review(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create(employer_fein="999999999", employer_dba="Acme Co")
        claim = ClaimFactory.create(employer_id=employer.employer_id)

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        response_data = response.get_json()["data"]

        assert response.status_code == 200

        assert response_data["follow_up_date"] == "2021-02-01"
        # This field is set in mock_client.py::get_customer_occupations
        assert response_data["hours_worked_per_week"] == 37.5
        assert response_data["employer_dba"] == "Acme Co"
        assert response_data["employer_fein"] == "99-9999999"
        assert response_data["employer_id"] == str(employer.employer_id)
        assert response_data["is_reviewable"] is False
        # The fields below are set in mock_client.py::mock_customer_info
        assert response_data["date_of_birth"] == "****-12-25"
        assert response_data["tax_identifier"] == "***-**-1234"
        assert response_data["residential_address"]["city"] == "Atlanta"
        assert response_data["residential_address"]["line_1"] == "55 Trinity Ave."
        assert response_data["residential_address"]["line_2"] == "Suite 3450"
        assert response_data["residential_address"]["state"] == "GA"
        assert response_data["residential_address"]["zip"] == "30303"

    @freeze_time("2020-12-07")
    def test_claims_is_reviewable_managed_requirement_status(
        self,
        client,
        monkeypatch,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
    ):
        employer = EmployerFactory.create(employer_fein="999999999", employer_dba="Acme Co")
        claim = ClaimFactory.create(employer_id=employer.employer_id)

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        def patched_managed_requirements(*args, **kwargs):
            return [
                models.group_client_api.ManagedRequirementDetails.parse_obj(
                    {
                        "managedReqId": 123,
                        "category": "Fake Category",
                        "type": "Employer Confirmation of Leave Data",
                        "followUpDate": datetime.date(2021, 2, 1),
                        "documentReceived": True,
                        "creator": "Fake Creator",
                        "status": "Open",
                        "subjectPartyName": "Fake Name",
                        "sourceOfInfoPartyName": "Fake Sourcee",
                        "creationDate": datetime.date(2020, 1, 1),
                        "dateSuppressed": datetime.date(2020, 3, 1),
                    }
                ),
            ]

        monkeypatch.setattr(
            MockFINEOSClient, "get_managed_requirements", patched_managed_requirements,
        )

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        response_data = response.get_json()["data"]
        assert response.status_code == 200
        assert response_data["is_reviewable"] is True

    @freeze_time("2020-12-07")
    def test_employers_with_int_hours_worked_per_week_receive_200_from_get_claim_review(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create(employer_fein="999999999", employer_dba="Acme Co")
        ClaimFactory.create(
            employer_id=employer.employer_id, fineos_absence_id="int_fake_hours_worked_per_week",
        )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.get(
            "/v1/employers/claims/int_fake_hours_worked_per_week/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        response_data = response.get_json()["data"]

        assert response.status_code == 200

        assert response_data["follow_up_date"] == "2021-02-01"
        # This field is set in mock_client.py::get_customer_occupations
        assert response_data["hours_worked_per_week"] == 37
        assert response_data["employer_dba"] == "Acme Co"
        assert response_data["employer_fein"] == "99-9999999"
        assert response_data["is_reviewable"] is False
        # The fields below are set in mock_client.py::mock_customer_info
        assert response_data["date_of_birth"] == "****-12-25"
        assert response_data["tax_identifier"] == "***-**-1234"
        assert response_data["residential_address"]["city"] == "Atlanta"
        assert response_data["residential_address"]["line_1"] == "55 Trinity Ave."
        assert response_data["residential_address"]["line_2"] == "Suite 3450"
        assert response_data["residential_address"]["state"] == "GA"
        assert response_data["residential_address"]["zip"] == "30303"

    def test_employers_receive_proper_claim_using_correct_fineos_web_id(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer1 = EmployerFactory.create()
        employer2 = EmployerFactory.create()

        claim1 = ClaimFactory.create(employer_id=employer1.employer_id)
        claim2 = ClaimFactory.create(employer_id=employer2.employer_id)

        link1 = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer1.employer_id,
            fineos_web_id="employer1-fineos-web-id",
            verification=test_verification,
        )

        link2 = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer2.employer_id,
            fineos_web_id="employer2-fineos-web-id",
            verification=test_verification,
        )

        test_db_session.add(link1)
        test_db_session.add(link2)
        test_db_session.commit()

        massgov.pfml.fineos.mock_client.start_capture()

        response = client.get(
            f"/v1/employers/claims/{claim1.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        capture = massgov.pfml.fineos.mock_client.get_capture()
        handler, fineos_web_id, params = capture[0]

        assert response.status_code == 200
        assert handler == "get_absence_period_decisions"
        assert fineos_web_id == "employer1-fineos-web-id"
        assert params == {"absence_id": claim1.fineos_absence_id}

        massgov.pfml.fineos.mock_client.start_capture()

        response = client.get(
            f"/v1/employers/claims/{claim2.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        capture = massgov.pfml.fineos.mock_client.get_capture()
        handler, fineos_web_id, params = capture[0]

        assert response.status_code == 200
        assert handler == "get_absence_period_decisions"
        assert fineos_web_id == "employer2-fineos-web-id"
        assert params == {"absence_id": claim2.fineos_absence_id}


@pytest.mark.integration
class TestUpdateClaim:
    def test_non_employees_cannot_access_employer_update_claim_review(
        self, client, auth_token, update_claim_body
    ):

        response = client.patch(
            "/v1/employers/claims/3/review",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=update_claim_body,
        )

        assert response.status_code == 403

    def test_employers_with_decimal_hours_receive_200_from_employer_update_claim_review(
        self,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
        update_claim_body,
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )

        assert response.status_code == 200

    def test_employers_with_integer_hours_receive_200_from_employer_update_claim_review(
        self,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
        update_claim_body,
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )

        assert response.status_code == 200

    def test_employer_update_claim_review_validates_hours_worked_per_week(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        base_request = {
            "comment": "comment",
            "employer_benefits": [
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-04-10",
                    "benefit_start_date": "2021-03-16",
                    "benefit_type": "Accrued paid leave",
                }
            ],
            "employer_decision": "Approve",
            "fraud": "Yes",
            "has_amendments": False,
            # hours_worked_per_week intentionally excluded
            "previous_leaves": [
                {
                    "leave_end_date": "2021-02-06",
                    "leave_start_date": "2021-01-25",
                    "leave_reason": "Pregnancy / Maternity",
                }
            ],
        }

        request_without_hours = {**base_request, "hours_worked_per_week": None}
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_without_hours,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("message") == "hours_worked_per_week must be populated"
        assert errors[0].get("type") == "missing_expected_field"
        assert errors[0].get("field") == "hours_worked_per_week"

        request_with_zero_hours = {**base_request, "hours_worked_per_week": 0}
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_zero_hours,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("message") == "hours_worked_per_week must be greater than 0"
        assert errors[0].get("type") == "minimum"
        assert errors[0].get("field") == "hours_worked_per_week"

        request_with_negative_hours = {**base_request, "hours_worked_per_week": -1}
        response = client.patch(
            "/v1/employers/claims/NTN-100-ABS-01/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_negative_hours,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("message") == "hours_worked_per_week must be greater than 0"
        assert errors[0].get("type") == "minimum"
        assert errors[0].get("field") == "hours_worked_per_week"

        request_with_too_many_hours = {**base_request, "hours_worked_per_week": 170}
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_too_many_hours,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("message") == "hours_worked_per_week must be 168 or fewer"
        assert errors[0].get("type") == "maximum"
        assert errors[0].get("field") == "hours_worked_per_week"

    def test_employer_update_claim_review_validates_previous_leaves(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        base_request = {
            "comment": "comment",
            "employer_benefits": [
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-04-10",
                    "benefit_start_date": "2021-03-16",
                    "benefit_type": "Accrued paid leave",
                }
            ],
            "employer_decision": "Approve",
            "fraud": "Yes",
            "has_amendments": False,
            "hours_worked_per_week": 40,
            # previous_leaves intentionally excluded
        }

        request_with_start_date_before_2021 = {
            **base_request,
            "previous_leaves": [
                {
                    "leave_end_date": "2021-01-05",
                    "leave_start_date": "2020-12-06",
                    "leave_reason": "Pregnancy / Maternity",
                }
            ],
        }
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_start_date_before_2021,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("message") == "Previous leaves cannot start before 2021"
        assert errors[0].get("type") == "invalid_previous_leave_start_date"
        assert errors[0].get("field") == "previous_leaves[0].leave_start_date"

        request_with_start_after_end = {
            **base_request,
            "previous_leaves": [
                {
                    "leave_end_date": "2021-01-05",
                    "leave_start_date": "2021-02-06",
                    "leave_reason": "Pregnancy / Maternity",
                }
            ],
        }
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_start_after_end,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("message") == "leave_end_date cannot be earlier than leave_start_date"
        assert errors[0].get("type") == "minimum"
        assert errors[0].get("field") == "previous_leaves[0].leave_end_date"

    def test_employer_update_claim_review_validates_employer_benefits(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        base_request = {
            "comment": "comment",
            # employer_benefits intentionally excluded
            "employer_decision": "Approve",
            "fraud": "Yes",
            "has_amendments": False,
            "hours_worked_per_week": 40,
            "previous_leaves": [
                {
                    "leave_end_date": "2021-02-06",
                    "leave_start_date": "2021-01-25",
                    "leave_reason": "Pregnancy / Maternity",
                }
            ],
        }

        request_with_start_after_end = {
            **base_request,
            "employer_benefits": [
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                }
            ],
        }
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_start_after_end,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert (
            errors[0].get("message") == "benefit_end_date cannot be earlier than benefit_start_date"
        )
        assert errors[0].get("type") == "minimum"
        assert errors[0].get("field") == "employer_benefits[0].benefit_end_date"

    def test_employer_update_claim_review_validates_previous_leaves_length(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        base_request = {
            "comment": "comment",
            "employer_benefits": [
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-04-10",
                    "benefit_start_date": "2021-03-16",
                    "benefit_type": "Accrued paid leave",
                }
            ],
            "employer_decision": "Approve",
            "fraud": "Yes",
            "has_amendments": False,
            "hours_worked_per_week": 40,
            # previous_leaves intentionally excluded
        }

        previous_leaves = [
            {
                "leave_end_date": "2020-10-04",
                "leave_start_date": "2020-10-01",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-10-06",
                "leave_start_date": "2020-10-05",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-10-15",
                "leave_start_date": "2020-10-10",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-10-20",
                "leave_start_date": "2020-10-16",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-10-30",
                "leave_start_date": "2020-10-25",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-11-05",
                "leave_start_date": "2020-11-01",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-11-10",
                "leave_start_date": "2020-11-08",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-11-15",
                "leave_start_date": "2020-11-11",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2020-12-01",
                "leave_start_date": "2020-11-20",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-01-05",
                "leave_start_date": "2020-12-06",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-01-15",
                "leave_start_date": "2021-01-10",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-01-20",
                "leave_start_date": "2021-01-16",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-01-30",
                "leave_start_date": "2021-01-25",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-02-05",
                "leave_start_date": "2021-02-01",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-02-10",
                "leave_start_date": "2021-02-06",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-02-15",
                "leave_start_date": "2021-02-11",
                "leave_reason": "Pregnancy / Maternity",
            },
            {
                "leave_end_date": "2021-02-20",
                "leave_start_date": "2021-02-16",
                "leave_reason": "Pregnancy / Maternity",
            },
        ]

        request_with_17_previous_leaves = {**base_request, "previous_leaves": previous_leaves}

        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_17_previous_leaves,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("rule") == 16
        assert errors[0].get("type") == "maxItems"
        assert errors[0].get("field") == "previous_leaves"

    def test_employer_update_claim_review_validates_employer_benefits_length(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        base_request = {
            "comment": "comment",
            # employer_benefits intentionally excluded
            "employer_decision": "Approve",
            "fraud": "Yes",
            "has_amendments": False,
            "hours_worked_per_week": 40,
            "previous_leaves": [
                {
                    "leave_end_date": "2021-02-06",
                    "leave_start_date": "2021-01-25",
                    "leave_reason": "Pregnancy / Maternity",
                }
            ],
        }

        request_with_11_employer_benefits = {
            **base_request,
            "employer_benefits": [
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                },
            ],
        }
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_11_employer_benefits,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].get("rule") == 10
        assert errors[0].get("type") == "maxItems"
        assert errors[0].get("field") == "employer_benefits"

    def test_employer_update_claim_review_validates_multiple_fields_at_once(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        update_request_body = {
            "comment": "comment",
            "employer_benefits": [
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-03-16",
                    "benefit_start_date": "2021-04-10",
                    "benefit_type": "Accrued paid leave",
                }
            ],
            "employer_decision": "Approve",
            "fraud": "Yes",
            "has_amendments": False,
            "hours_worked_per_week": 190,
            "previous_leaves": [
                {
                    "leave_end_date": "2020-02-06",
                    "leave_start_date": "2020-01-25",
                    "leave_reason": "Pregnancy / Maternity",
                }
            ],
        }

        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_request_body,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert len(errors) == 3
        assert errors[0].get("field") == "hours_worked_per_week"
        assert errors[1].get("field") == "previous_leaves[0].leave_start_date"
        assert errors[2].get("field") == "employer_benefits[0].benefit_end_date"

    def test_employer_confirmation_sent_with_employer_update_claim_review(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        update_request_body = {
            "comment": "",
            "employer_benefits": [],
            "employer_decision": "Approve",
            "fraud": "Yes",
            "has_amendments": False,
            "hours_worked_per_week": 16,
            "previous_leaves": [],
        }

        massgov.pfml.fineos.mock_client.start_capture()

        client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_request_body,
        )

        capture = massgov.pfml.fineos.mock_client.get_capture()

        assert capture == [
            (
                "get_outstanding_information",
                "fake-fineos-web-id",
                {"case_id": claim.fineos_absence_id},
            ),
            (
                "update_outstanding_information_as_received",
                "fake-fineos-web-id",
                {
                    "outstanding_information": massgov.pfml.fineos.models.group_client_api.OutstandingInformationData(
                        informationType="Employer Confirmation of Leave Data"
                    ),
                    "case_id": claim.fineos_absence_id,
                },
            ),
        ]

    def test_create_eform_for_comment_with_employer_update_claim_review(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        update_request_body = {
            "comment": "comment",
            "employer_benefits": [],
            "employer_decision": "Approve",
            "fraud": "No",
            "has_amendments": False,
            "hours_worked_per_week": 40,
            "previous_leaves": [],
        }

        massgov.pfml.fineos.mock_client.start_capture()

        client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_request_body,
        )

        capture = massgov.pfml.fineos.mock_client.get_capture()

        assert capture[0] == (
            "get_outstanding_information",
            "fake-fineos-web-id",
            {"case_id": claim.fineos_absence_id},
        )
        assert capture[1][0] == "create_eform"
        assert capture[1][1] == "fake-fineos-web-id"
        assert capture[1][2]["absence_id"] == claim.fineos_absence_id
        eform = capture[1][2]["eform"]
        assert eform.eformType == "Employer Response to Leave Request"
        assert eform.eformAttributes == [
            {"name": "Comment", "stringValue": "comment"},
            {"name": "AverageWeeklyHoursWorked", "decimalValue": 40.0},
            {"name": "EmployerDecision", "stringValue": "Approve"},
            {"name": "Fraud1", "stringValue": "No"},
        ]

    def test_error_received_when_no_outstanding_requirements_with_employer_update_claim_review(
        self,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
        update_claim_body,
    ):
        employer = EmployerFactory.create()
        ClaimFactory.create(
            employer_id=employer.employer_id, fineos_absence_id="NTN-CASE-WITHOUT-OUTSTANDING-INFO",
        )
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.patch(
            "/v1/employers/claims/NTN-CASE-WITHOUT-OUTSTANDING-INFO/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )

        assert response.status_code == 400
        tests.api.validate_error_response(
            response, 400, message="No outstanding information request for claim"
        )

    def test_employer_confirmation_is_not_sent(
        self,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
        update_claim_body,
    ):
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # confirmation is not sent if there is not Employer confirmation outstanding info
        ClaimFactory.create(
            employer_id=employer.employer_id, fineos_absence_id="NTN-CASE-WITHOUT-OUTSTANDING-INFO",
        )

        massgov.pfml.fineos.mock_client.start_capture()

        client.patch(
            "/v1/employers/claims/NTN-CASE-WITHOUT-OUTSTANDING-INFO/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
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
        update_request_body = copy.deepcopy(update_claim_body)
        update_request_body["has_amendments"] = True

        massgov.pfml.fineos.mock_client.start_capture()

        client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_request_body,
        )

        capture = massgov.pfml.fineos.mock_client.get_capture()

        assert capture[0] == (
            "get_outstanding_information",
            "fake-fineos-web-id",
            {"case_id": claim.fineos_absence_id},
        )
        assert capture[1][0] == "create_eform"

        # confirmation is not sent if the claim is not approved
        update_request_body["has_amendments"] = False
        update_request_body["employer_decision"] = "Deny"

        massgov.pfml.fineos.mock_client.start_capture()

        client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_request_body,
        )

        capture = massgov.pfml.fineos.mock_client.get_capture()

        assert capture[0] == (
            "get_outstanding_information",
            "fake-fineos-web-id",
            {"case_id": claim.fineos_absence_id},
        )
        assert capture[1][0] == "create_eform"

    # Inner class for testing Caring Leave scenarios
    class TestCaringLeave:
        @pytest.fixture()
        def employer(self, initialize_factories_session):
            return EmployerFactory.create()

        @pytest.fixture()
        def user_leave_admin(self, employer_user, employer, test_verification):
            return UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )

        @pytest.fixture()
        def with_user_leave_admin_link(self, user_leave_admin, test_db_session):
            test_db_session.add(user_leave_admin)
            test_db_session.commit()

        @pytest.fixture()
        def with_mock_client_capture(self):
            massgov.pfml.fineos.mock_client.start_capture()

        @pytest.fixture()
        def claim(self, employer):
            return ClaimFactory.create(employer_id=employer.employer_id)

        @pytest.fixture()
        def update_caring_leave_claim_body(self, update_claim_body):
            update_claim_body["leave_reason"] = "Care for a Family Member"
            update_claim_body["believe_relationship_accurate"] = "Yes"
            update_claim_body["fraud"] = "No"
            update_claim_body["comment"] = ""

            return update_claim_body

        @pytest.fixture()
        def perform_update(self, client, claim, employer_auth_token):
            def update_claim_review(update_caring_leave_claim_body):
                return client.patch(
                    f"/v1/employers/claims/{claim.fineos_absence_id}/review",
                    headers={"Authorization": f"Bearer {employer_auth_token}"},
                    json=update_caring_leave_claim_body,
                )

            return update_claim_review

        def test_response_status(
            self,
            with_user_leave_admin_link,
            with_mock_client_capture,
            perform_update,
            update_caring_leave_claim_body,
        ):
            response = perform_update(update_caring_leave_claim_body)
            assert response.status_code == 200

        def test_employer_confirmation_sent(
            self,
            with_user_leave_admin_link,
            with_mock_client_capture,
            perform_update,
            update_caring_leave_claim_body,
            claim,
        ):
            perform_update(update_caring_leave_claim_body)

            capture = massgov.pfml.fineos.mock_client.get_capture()
            assert capture[1] == (
                "update_outstanding_information_as_received",
                "fake-fineos-web-id",
                {
                    "outstanding_information": massgov.pfml.fineos.models.group_client_api.OutstandingInformationData(
                        informationType="Employer Confirmation of Leave Data"
                    ),
                    "case_id": claim.fineos_absence_id,
                },
            )

        def test_create_eform_and_attributes_with_inaccurate_relation_and_no_comment(
            self,
            with_user_leave_admin_link,
            with_mock_client_capture,
            perform_update,
            update_caring_leave_claim_body,
        ):
            update_caring_leave_claim_body["believe_relationship_accurate"] = "No"
            update_caring_leave_claim_body["relationship_inaccurate_reason"] = "No reason, lol"
            perform_update(update_caring_leave_claim_body)

            captures = massgov.pfml.fineos.mock_client.get_capture()
            assert len(captures) >= 2

            handler, fineos_web_id, params = captures[1]
            assert handler == "create_eform"

            eform = params["eform"]
            assert eform.eformType == "Employer Response to Leave Request"

        def test_create_eform_with_comment_and_accurate_relationship(
            self,
            with_user_leave_admin_link,
            with_mock_client_capture,
            perform_update,
            update_caring_leave_claim_body,
        ):
            update_caring_leave_claim_body["comment"] = "comment"
            perform_update(update_caring_leave_claim_body)

            captures = massgov.pfml.fineos.mock_client.get_capture()
            assert len(captures) >= 2

            handler, fineos_web_id, params = captures[1]
            assert handler == "create_eform"
            assert fineos_web_id == "fake-fineos-web-id"

            eform = params["eform"]
            assert eform.eformType == "Employer Response to Leave Request"


def assert_claim_response_equal_to_claim_query(claim_response, claim_query) -> bool:
    assert claim_response["absence_period_end_date"] == claim_query.absence_period_end_date
    assert claim_response["absence_period_start_date"] == claim_query.absence_period_start_date
    assert claim_response["fineos_absence_id"] == claim_query.fineos_absence_id
    assert claim_response["fineos_notification_id"] == claim_query.fineos_notification_id
    assert claim_response["employer"]["employer_dba"] == claim_query.employer.employer_dba
    assert claim_response["employer"]["employer_fein"] == FEINFormattedStr.validate_type(
        claim_query.employer.employer_fein
    )
    assert claim_response["employer"]["employer_id"] == str(claim_query.employer.employer_id)
    assert claim_response["employee"]["first_name"] == claim_query.employee.first_name
    assert claim_response["employee"]["middle_name"] == claim_query.employee.middle_name
    assert claim_response["employee"]["last_name"] == claim_query.employee.last_name
    assert claim_response["employee"]["other_name"] == claim_query.employee.other_name
    assert (
        claim_response["fineos_absence_status"]["absence_status_description"]
        == claim_query.fineos_absence_status.absence_status_description
    )
    assert (
        claim_response["claim_status"]
        == claim_query.fineos_absence_status.absence_status_description
    )
    assert (
        claim_response["claim_type"]["claim_type_description"]
        == claim_query.claim_type.claim_type_description
    )
    assert claim_response["claim_type_description"] == claim_query.claim_type.claim_type_description


class TestGetClaimEndpoint:
    def test_get_claim_claim_does_not_exist(self, caplog, client, employer_auth_token):
        response = client.get(
            "/v1/claims/NTN-100-ABS-01", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 400
        tests.api.validate_error_response(response, 400, message="Claim not in database.")
        assert "Claim not in database." in caplog.text

    def test_get_claim_user_has_no_access(self, caplog, client, employer_auth_token):
        claim = ClaimFactory.create()

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        tests.api.validate_error_response(
            response, 403, message="User does not have access to claim."
        )
        assert "User does not have access to claim." in caplog.text

    def test_get_claim_user_has_access_as_leave_admin(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification,
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()
        claim = ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_claim_response_equal_to_claim_query(claim_data, claim)

    def test_get_claim_user_has_access_as_claimant(self, caplog, client, auth_token, user):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()
        claim = ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )
        ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_claim_response_equal_to_claim_query(claim_data, claim)


class TestGetClaimsEndpoint:
    def test_get_claims_as_leave_admin(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employerA = EmployerFactory.create()
        employee = EmployeeFactory.create()

        generated_claims = [
            ClaimFactory.create(
                employer=employerA, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
            )
            for _ in range(3)
        ]

        # Create another employer and claim that should not be returned
        employerB = EmployerFactory.create()
        ClaimFactory.create(
            employer=employerB, employee=employee, fineos_absence_status_id=1, claim_type_id=1
        )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employerA.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == len(generated_claims)
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

    def test_get_claims_paginated_as_leave_admin(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        for _ in range(30):
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)

        other_employer = EmployerFactory.create()
        other_employee = EmployeeFactory.create()
        for _ in range(5):
            ClaimFactory.create(
                employer=other_employer,
                employee=other_employee,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        test_db_session.commit()
        scenarios = [
            {
                "tag": "Request without paging parameters uses default values",
                "request": {},
                "paging": {
                    "page_size": 25,
                    "page_offset": 1,
                    "total_pages": 2,
                    "total_records": 30,
                    "order_direction": "descending",
                    "order_by": "created_at",
                },
                "real_page_size": 25,
                "status_code": 200,
            },
            {
                "tag": "Use page_size value specified in query parameter",
                "request": {"page_size": 10},
                "paging": {
                    "page_size": 10,
                    "page_offset": 1,
                    "total_pages": 3,
                    "total_records": 30,
                    "order_direction": "descending",
                    "order_by": "created_at",
                },
                "real_page_size": 10,
                "status_code": 200,
            },
            {
                "tag": "page_size must be greater than 0",
                "request": {"page_size": 0},
                "paging": {},
                "status_code": 400,
            },
            {
                "tag": "page_size value larger than total number of records succeeds",
                "request": {"page_size": 100},
                "paging": {
                    "page_size": 100,
                    "page_offset": 1,
                    "total_pages": 1,
                    "total_records": 30,
                    "order_direction": "descending",
                    "order_by": "created_at",
                },
                "real_page_size": 30,
                "status_code": 200,
            },
            {
                "tag": "order_by and order_direction params are respected",
                "request": {"order_direction": "ascending", "order_by": "claim_id"},
                "paging": {
                    "page_size": 25,
                    "page_offset": 1,
                    "total_pages": 2,
                    "total_records": 30,
                    "order_direction": "ascending",
                    "order_by": "claim_id",
                },
                "real_page_size": 25,
                "status_code": 200,
            },
            {
                "tag": "Unrecognized order_by parameter defaults to created_at",
                "request": {"order_by": "dogecoin"},
                "paging": {},
                "status_code": 400,
            },
            {
                "tag": "Unrecognized order_direction parameter returns 400",
                "request": {"order_direction": "stonks"},
                "paging": {},
                "status_code": 400,
            },
        ]

        for scenario in scenarios:
            tag = scenario["tag"]
            print(f"Running test for pagination scenario: {tag}")

            query_string = "&".join(
                [f"{key}={value}" for key, value in scenario["request"].items()]
            )
            response = client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

            assert (
                response.status_code == scenario["status_code"]
            ), f"tag:{tag}\nUnexpected response status code {response.status_code}"

            if scenario["status_code"] != 200:
                # Do not validate response structure for scenarios where an error response is expected
                continue

            response_body = response.get_json()

            actual_response_page_size = len(response_body["data"])
            expected_page_size = scenario["real_page_size"]
            assert actual_response_page_size == expected_page_size, (
                f"tag:{tag}\nUnexpected data response size {actual_response_page_size},"
                + f"should've been {expected_page_size}"
            )

            actual_page_metadata = response_body["meta"]["paging"]
            expected_page_metadata = scenario["paging"]

            for key, expected_value in expected_page_metadata.items():
                actual_value = actual_page_metadata[key]
                if actual_page_metadata[key] != expected_value:
                    raise AssertionError(
                        f"tag: {tag}\n{key} value was '{actual_value}', not expected {expected_value}"
                    )

    def test_get_claims_for_employer_id(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        for _ in range(5):
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)

        other_employer = EmployerFactory.create()
        other_link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=other_employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(other_employer)
        test_db_session.add(other_link)

        for _ in range(5):
            ClaimFactory.create(
                employer=other_employer,
                employee=employee,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        test_db_session.commit()

        response = client.get(
            f"/v1/claims?employer_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5
        for claim in response_body["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(employer.employer_fein)

    def test_get_claims_as_claimant(self, client, auth_token, user):
        employer = EmployerFactory.create()
        employeeA = EmployeeFactory.create()
        generated_claims = []

        for _ in range(3):
            new_claim = ClaimFactory.create(
                employer=employer, employee=employeeA, fineos_absence_status_id=1, claim_type_id=1,
            )
            generated_claims.append(new_claim)
            ApplicationFactory.create(user=user, claim=new_claim)

        # Create a claim that is not expected to be returned
        employeeB = EmployeeFactory.create()
        ClaimFactory.create(
            employer=employer, employee=employeeB, fineos_absence_status_id=1, claim_type_id=1
        )

        response = client.get("/v1/claims", headers={"Authorization": f"Bearer {auth_token}"},)

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

    def test_get_claims_with_blocked_fein(
        self,
        client,
        employer_auth_token,
        employer_user,
        test_db_session,
        test_verification,
        monkeypatch,
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        for _ in range(5):
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)

        other_employer = EmployerFactory.create()
        other_link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=other_employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(other_employer)
        test_db_session.add(other_link)

        for _ in range(5):
            ClaimFactory.create(
                employer=other_employer,
                employee=employee,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        test_db_session.commit()
        monkeypatch.setattr(
            massgov.pfml.api.claims,
            "CLAIMS_DASHBOARD_BLOCKED_FEINS",
            set([employer.employer_fein]),
        )
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5
        for claim in response_body["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(other_employer.employer_fein)
