import copy
from datetime import date, datetime, timedelta
from unittest import mock

import factory  # this is from the factory_boy package
import pytest
from freezegun import freeze_time
from jose import jwt
from jose.constants import ALGORITHMS

import massgov.pfml.api.claims
import massgov.pfml.fineos.mock_client
import massgov.pfml.util.datetime as datetime_util
import tests.api
from massgov.pfml.api.models.claims.responses import DocumentResponse
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    ManagedRequirementStatus,
    ManagedRequirementType,
    Role,
    UserLeaveAdministrator,
)
from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    ManagedRequirementFactory,
    UserFactory,
    VerificationFactory,
)
from massgov.pfml.db.queries.get_claims_query import ActionRequiredStatusFilter
from massgov.pfml.fineos import models
from massgov.pfml.fineos.mock_client import MockFINEOSClient
from massgov.pfml.util.pydantic.types import FEINFormattedStr
from massgov.pfml.util.strings import format_fein

# every test in here requires real resources
pytestmark = pytest.mark.integration


# Run `initialize_factories_session` for all tests,
# so that it doesn't need to be manually included
@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


@pytest.fixture
def test_verification():
    return VerificationFactory.create()


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
                "leave_reason": "Pregnancy",
            }
        ],
        "leave_reason": "Pregnancy/Maternity",
    }


@pytest.fixture
def employer():
    return EmployerFactory.create()


@pytest.fixture
def claim(employer):
    return ClaimFactory.create(employer_id=employer.employer_id)


@pytest.fixture
def user_leave_admin(employer_user, employer, test_verification):
    return UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
        verification=test_verification,
    )


@pytest.mark.integration
class TestVerificationEnforcement:
    # This class groups the tests that ensure that existing users with UserLeaveAdministrator records
    # get 403s when attempting to access claim data without a Verification

    @pytest.fixture()
    def employer(self):
        employer = EmployerFactory.create()
        return employer

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


# testing class for employer_get_claim_documents
@pytest.mark.integration
class TestEmployerGetClaimDocuments:
    @pytest.fixture(autouse=True)
    def setup_db(self, claim, employer, user_leave_admin, test_db_session):
        test_db_session.add(user_leave_admin)
        test_db_session.commit()

    @pytest.fixture
    def request_params(self, claim, employer_auth_token):
        class GetClaimDocumentsRequestParams(object):
            __slots__ = ["absence_id", "auth_token"]

            def __init__(self, absence_id, auth_token):
                self.absence_id = absence_id
                self.auth_token = auth_token

        return GetClaimDocumentsRequestParams(claim.fineos_absence_id, employer_auth_token)

    def get_documents(self, client, params):
        return client.get(
            f"/v1/employers/claims/{params.absence_id}/documents",
            headers={"Authorization": f"Bearer {params.auth_token}"},
        )

    def test_non_employers_cannot_access(self, client, request_params, auth_token):
        request_params.auth_token = auth_token

        response = self.get_documents(client, request_params)
        assert response.status_code == 403

    def test_employers_receive_200(self, client, request_params):
        response = self.get_documents(client, request_params)
        assert response.status_code == 200


# testing class for employer_document_download
class TestEmployerDocumentDownload:
    @pytest.fixture(autouse=True)
    def setup_db(self, claim, employer, user_leave_admin, test_db_session):
        test_db_session.add(user_leave_admin)
        test_db_session.commit()

    @pytest.fixture
    def document_id(self):
        return "123"

    @pytest.fixture
    def document(self, document_id):
        return DocumentResponse(
            created_at=None,
            document_type="state managed paid leave confirmation",
            content_type="application/pdf",
            fineos_document_id=document_id,
            name="test.pdf",
            description="Mock File",
        )

    @pytest.fixture
    def request_params(self, claim, document_id, employer_auth_token):
        class EmployerDocumentDownloadRequestParams(object):
            __slots__ = ["absence_id", "document_id", "auth_token"]

            def __init__(self, absence_id, document_id, auth_token):
                self.absence_id = absence_id
                self.document_id = document_id
                self.auth_token = auth_token

        return EmployerDocumentDownloadRequestParams(
            claim.fineos_absence_id, document_id, employer_auth_token
        )

    def download_document(self, client, params):
        return client.get(
            f"/v1/employers/claims/{params.absence_id}/documents/{params.document_id}",
            headers={"Authorization": f"Bearer {params.auth_token}"},
        )

    def test_non_employers_receive_403(self, client, request_params, auth_token):
        request_params.auth_token = auth_token

        response = self.download_document(client, request_params)
        assert response.status_code == 403

        response_json = response.get_json()
        message = response_json["message"]
        assert "does not have read access" in message

    @mock.patch("massgov.pfml.api.claims.get_documents_as_leave_admin")
    def test_employers_receive_200(self, mock_get_docs, document, client, request_params):
        mock_get_docs.return_value = [document]

        response = self.download_document(client, request_params)
        assert response.status_code == 200

    @mock.patch("massgov.pfml.api.claims.get_documents_as_leave_admin")
    def test_cannot_download_documents_not_attached_to_absence(
        self, mock_get_docs, document, client, request_params, caplog
    ):
        document.fineos_document_id = "bad_doc_id"
        mock_get_docs.return_value = [document]

        response = self.download_document(client, request_params)

        tests.api.validate_error_response(
            response, 403, message="User does not have access to this document"
        )
        assert "document not found" in caplog.text


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
            headers={
                "Authorization": f"Bearer {employer_auth_token}",
                "X-FF-Default-To-V2": "value_does_not_matter",
            },
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
        assert response_data["uses_second_eform_version"] is True

    @freeze_time("2020-12-07")
    def test_second_eform_version_defaults_to_true_when_ff_is_set(
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
            headers={
                "Authorization": f"Bearer {employer_auth_token}",
                "X-FF-Default-To-V2": "value_does_not_matter",
            },
        )
        response_data = response.get_json()["data"]

        assert response.status_code == 200
        assert response_data["uses_second_eform_version"] is True

    @freeze_time("2020-12-07")
    def test_second_eform_version_defaults_to_false_when_ff_is_not_set(
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
        assert response_data["uses_second_eform_version"] is False

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
                        "followUpDate": date(2021, 2, 1),
                        "documentReceived": True,
                        "creator": "Fake Creator",
                        "status": "Open",
                        "subjectPartyName": "Fake Name",
                        "sourceOfInfoPartyName": "Fake Sourcee",
                        "creationDate": date(2020, 1, 1),
                        "dateSuppressed": date(2020, 3, 1),
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
                    "leave_reason": "Pregnancy",
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
                    "leave_reason": "Pregnancy",
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
                    "leave_reason": "Pregnancy",
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
                    "leave_reason": "Pregnancy",
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
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-10-06",
                "leave_start_date": "2020-10-05",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-10-15",
                "leave_start_date": "2020-10-10",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-10-20",
                "leave_start_date": "2020-10-16",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-10-30",
                "leave_start_date": "2020-10-25",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-11-05",
                "leave_start_date": "2020-11-01",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-11-10",
                "leave_start_date": "2020-11-08",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-11-15",
                "leave_start_date": "2020-11-11",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2020-12-01",
                "leave_start_date": "2020-11-20",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-01-05",
                "leave_start_date": "2020-12-06",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-01-15",
                "leave_start_date": "2021-01-10",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-01-20",
                "leave_start_date": "2021-01-16",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-01-30",
                "leave_start_date": "2021-01-25",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-02-05",
                "leave_start_date": "2021-02-01",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-02-10",
                "leave_start_date": "2021-02-06",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-02-15",
                "leave_start_date": "2021-02-11",
                "leave_reason": "Pregnancy",
            },
            {
                "leave_end_date": "2021-02-20",
                "leave_start_date": "2021-02-16",
                "leave_reason": "Pregnancy",
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
                    "leave_reason": "Pregnancy",
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

    def test_employer_update_claim_review_validates_v1_employer_benefits_length(
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
                    "leave_reason": "Pregnancy",
                }
            ],
            "uses_second_eform_version": False,
        }

        request_with_5_employer_benefits = {
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
            ],
        }
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_with_5_employer_benefits,
        )

        errors = response.get_json().get("errors")
        assert response.status_code == 400
        assert errors[0].get("message") == "Employer benefits cannot exceed limit of 4"
        assert errors[0].get("type") == "maximum"

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
                    "leave_reason": "Pregnancy",
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

    def test_long_comment_is_valid(
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

        update_claim_body["comment"] = "a" * 9999

        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )

        assert response.status_code == 200

    def test_too_long_comment_is_invalid(
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

        update_claim_body["comment"] = "a" * 10000

        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )

        assert response.status_code == 400
        assert response.get_json().get("message") == "Request Validation Error"

        errors = response.get_json().get("errors")
        error = next(
            (e for e in errors if e.get("field") == "comment" and e.get("type") == "maxLength"),
            None,
        )
        assert error is not None

    # Inner class for testing Caring Leave scenarios
    # TODO: add tests for the logging data: https://lwd.atlassian.net/browse/EMPLOYER-1389
    class TestCaringLeave:
        @pytest.fixture(autouse=True)
        def with_mock_client_capture(self):
            massgov.pfml.fineos.mock_client.start_capture()

        @pytest.fixture(autouse=True)
        def with_user_leave_admin(self, user_leave_admin, test_db_session):
            # persist a ULA associated with this employer
            test_db_session.add(user_leave_admin)
            test_db_session.commit()

        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def user_leave_admin(self, employer_user, employer, test_verification):
            return UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )

        @pytest.fixture
        def claim(self, employer):
            return ClaimFactory.create(employer_id=employer.employer_id)

        @pytest.fixture
        def claim_review_body(self, update_claim_body):
            update_claim_body["leave_reason"] = "Care for a Family Member"
            update_claim_body["believe_relationship_accurate"] = "Yes"
            update_claim_body["fraud"] = "No"
            del update_claim_body["comment"]

            return update_claim_body

        # Collects the params necessary for making a request with an approved claim review
        # to the mock API client
        @pytest.fixture
        def approval_request_params(self, client, claim, employer_auth_token, claim_review_body):
            class SubmitClaimReviewRequestParams(object):
                __slots__ = ["client", "absence_id", "auth_token", "body"]

                def __init__(self, client, absence_id, auth_token, body):
                    self.client = client
                    self.absence_id = absence_id
                    self.auth_token = auth_token
                    self.body = body

            return SubmitClaimReviewRequestParams(
                client, claim.fineos_absence_id, employer_auth_token, claim_review_body
            )

        # Submits a claim_review request with the given params
        def perform_update(self, request_params):
            client = request_params.client

            return client.patch(
                f"/v1/employers/claims/{request_params.absence_id}/review",
                headers={"Authorization": f"Bearer {request_params.auth_token}"},
                json=request_params.body,
            )

        def test_with_approval_and_no_issues_response_status_is_200(self, approval_request_params):
            response = self.perform_update(approval_request_params)
            assert response.status_code == 200

        def test_with_approval_and_no_issues_employer_confirmation_sent(
            self, approval_request_params, claim
        ):
            self.perform_update(approval_request_params)

            captures = massgov.pfml.fineos.mock_client.get_capture()
            update_outstanding_info_capture = next(
                (c for c in captures if c[0] == "update_outstanding_information_as_received"), None
            )

            assert update_outstanding_info_capture == (
                "update_outstanding_information_as_received",
                "fake-fineos-web-id",
                {
                    "outstanding_information": massgov.pfml.fineos.models.group_client_api.OutstandingInformationData(
                        informationType="Employer Confirmation of Leave Data"
                    ),
                    "case_id": claim.fineos_absence_id,
                },
            )

        def test_with_inaccurate_relationship_response_status_is_200(self, approval_request_params):
            claim_review_body = approval_request_params.body
            claim_review_body["believe_relationship_accurate"] = "No"
            claim_review_body["relationship_inaccurate_reason"] = "A good reason"

            response = self.perform_update(approval_request_params)

            assert response.status_code == 200

        def test_with_inaccurate_relationship_it_creates_eform_with_attributes(
            self, approval_request_params
        ):
            claim_review_body = approval_request_params.body
            claim_review_body["believe_relationship_accurate"] = "No"
            claim_review_body["relationship_inaccurate_reason"] = "A good reason"

            self.perform_update(approval_request_params)

            captures = massgov.pfml.fineos.mock_client.get_capture()

            create_eform_capture = next((c for c in captures if c[0] == "create_eform"), None)
            assert create_eform_capture is not None

            eform = create_eform_capture[2]["eform"]
            assert eform.eformType == "Employer Response to Leave Request"

            assert eform.get_attribute("NatureOfLeave") is not None
            assert eform.get_attribute("BelieveAccurate") is not None
            assert eform.get_attribute("WhyInaccurate") is not None

        def test_with_inaccurate_relationship_and_no_comment_it_creates_eform(
            self, approval_request_params
        ):
            claim_review_body = approval_request_params.body
            claim_review_body["believe_relationship_accurate"] = "No"
            claim_review_body["relationship_inaccurate_reason"] = "A good reason"
            self.perform_update(approval_request_params)

            captures = massgov.pfml.fineos.mock_client.get_capture()
            assert len(captures) >= 2

            create_eform_capture = next((c for c in captures if c[0] == "create_eform"), None)
            assert create_eform_capture is not None

            eform = create_eform_capture[2]["eform"]
            assert eform.eformType == "Employer Response to Leave Request"

        def test_with_accurate_relationship_and_comment_it_creates_eform(
            self, approval_request_params
        ):
            claim_review_body = approval_request_params.body
            claim_review_body["comment"] = "comment"

            self.perform_update(approval_request_params)

            captures = massgov.pfml.fineos.mock_client.get_capture()

            create_eform_capture = next((c for c in captures if c[0] == "create_eform"), None)
            assert create_eform_capture is not None

            eform = create_eform_capture[2]["eform"]
            assert eform.eformType == "Employer Response to Leave Request"

        def test_long_relationship_inaccurate_reason_is_valid(self, approval_request_params):
            claim_review_body = approval_request_params.body
            claim_review_body["relationship_inaccurate_reason"] = "a" * 9999

            response = self.perform_update(approval_request_params)
            assert response.status_code == 200

        def test_too_long_relationship_inaccurate_reason_is_invalid(self, approval_request_params):
            claim_review_body = approval_request_params.body
            claim_review_body["relationship_inaccurate_reason"] = "a" * 10000

            response = self.perform_update(approval_request_params)
            assert response.status_code == 400
            assert response.get_json().get("message") == "Request Validation Error"

            errors = response.get_json().get("errors")
            error = next(
                (
                    e
                    for e in errors
                    if e.get("field") == "relationship_inaccurate_reason"
                    and e.get("type") == "maxLength"
                ),
                None,
            )
            assert error is not None


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
        claim_response["claim_status"]
        == claim_query.fineos_absence_status.absence_status_description
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

    # Inner class for testing Claims With Status Filtering
    class TestClaimsOrder:
        @pytest.fixture(autouse=True)
        def load_test_db(self, employer_user, test_verification, test_db_session):
            employer = EmployerFactory.create()
            employee = EmployeeFactory.create()

            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)

            other_employer = EmployerFactory.create()
            other_employee = EmployeeFactory.create()

            other_link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=other_employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(other_link)

            for _ in range(5):
                ClaimFactory.create(
                    employer=employer,
                    employee=employee,
                    fineos_absence_status_id=1,
                    claim_type_id=1,
                )
                ClaimFactory.create(
                    employer=other_employer,
                    employee=other_employee,
                    fineos_absence_status_id=2,
                    claim_type_id=1,
                    created_at=factory.Faker(
                        "date_between_dates",
                        date_start=date(2021, 1, 1),
                        date_end=date(2021, 1, 15),
                    ),
                )
                ClaimFactory.create(
                    employer=other_employer,
                    employee=other_employee,
                    fineos_absence_status_id=7,
                    claim_type_id=1,
                    created_at=factory.Faker(
                        "date_between_dates",
                        date_start=date(2021, 1, 1),
                        date_end=date(2021, 1, 15),
                    ),
                )
                claim = Claim(employer=employer, fineos_absence_status_id=6, claim_type_id=1,)
                test_db_session.add(claim)
            self.claims_count = 20
            test_db_session.commit()

        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        def _assert_data_order(self, data, desc=True):
            if desc:
                for i in range(0, len(data) - 1):
                    assert data[i] >= data[i + 1]
            else:
                for i in range(0, len(data) - 1):
                    assert data[i] <= data[i + 1]

        def test_get_claims_with_order_default(self, client, employer_auth_token):
            request = {}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = [d["created_at"] for d in response_body.get("data", [])]
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=True)

        def test_get_claims_with_order_default_asc(self, client, employer_auth_token):
            request = {"order_direction": "ascending"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = [d["created_at"] for d in response_body.get("data", [])]
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=False)

        def test_get_claims_with_order_unsupported_key(self, client, employer_auth_token):
            request = {"order_by": "unsupported"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 400

        def _extract_employee_name(self, response_body):
            data = []
            for d in response_body.get("data", []):
                employee = d["employee"] or {}
                name = (
                    employee.get("last_name", " ")
                    + employee.get("first_name", " ")
                    + employee.get("middle_name", " ")
                )
                data.append(name)
            return data

        def test_get_claims_with_order_employee_asc(self, client, employer_auth_token):
            request = {"order_direction": "ascending", "order_by": "employee"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = self._extract_employee_name(response_body)
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=False)

        def test_get_claims_with_order_employee_desc(self, client, employer_auth_token):
            request = {"order_direction": "descending", "order_by": "employee"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = self._extract_employee_name(response_body)
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=True)

        def test_get_claims_with_order_fineos_absence_status_asc(
            self, client, employer_auth_token, test_db_session
        ):
            request = {"order_direction": "ascending", "order_by": "fineos_absence_status"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            claims = response_body.get("data", [])

            absence_status_orders = [
                AbsenceStatus.get_instance(
                    test_db_session, description=claim["claim_status"]
                ).sort_order
                if claim["claim_status"]
                else 0
                for claim in claims
            ]

            assert len(claims) == self.claims_count
            self._assert_data_order(absence_status_orders, desc=False)

        def test_get_claims_with_order_fineos_absence_status_desc(
            self, client, employer_auth_token, test_db_session
        ):
            request = {"order_direction": "descending", "order_by": "fineos_absence_status"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            claims = response_body.get("data", [])

            absence_status_orders = [
                AbsenceStatus.get_instance(
                    test_db_session, description=claim["claim_status"]
                ).sort_order
                if claim["claim_status"]
                else 0
                for claim in claims
            ]

            assert len(claims) == self.claims_count
            self._assert_data_order(absence_status_orders, desc=True)

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

    # Inner class for testing Claims With Status Filtering
    class TestClaimsWithStatus:
        NUM_CLAIM_PER_STATUS = 2

        @pytest.fixture(autouse=True)
        def load_test_db(self, employer_user, test_verification, test_db_session):
            employer = EmployerFactory.create()
            employee = EmployeeFactory.create()
            for i in range(1, 9):
                for _ in range(0, self.NUM_CLAIM_PER_STATUS):
                    if i == 8:  # absence_status_id => NULL
                        ClaimFactory.create(
                            employer=employer, employee=employee, claim_type_id=1,
                        )
                        continue
                    ClaimFactory.create(
                        employer=employer,
                        employee=employee,
                        fineos_absence_status_id=i,
                        claim_type_id=1,
                    )
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            test_db_session.commit()

        def _perform_api_call(self, url, client, employer_auth_token):
            return client.get(url, headers={"Authorization": f"Bearer {employer_auth_token}"},)

        def _perform_assertions(self, response, status_code, expected_count, valid_statuses):
            assert response.status_code == status_code
            response_body = response.get_json()
            claim_data = response_body.get("data", [])
            assert len(claim_data) == expected_count
            for claim in response_body.get("data", []):
                absence_status = claim.get("claim_status", None)
                assert absence_status in valid_statuses

        def test_get_claims_with_status_filter_one_claim(self, client, employer_auth_token):
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Approved", client, employer_auth_token
            )
            self._perform_assertions(
                resp,
                status_code=200,
                expected_count=self.NUM_CLAIM_PER_STATUS,
                valid_statuses=["Approved"],
            )

        def test_get_claims_with_status_filter_pending(self, client, employer_auth_token):
            valid_statuses = [
                "Adjudication",
                "In Review",
                "Intake In Progress",
                None,
            ]
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Pending", client, employer_auth_token
            )
            self._perform_assertions(
                resp,
                status_code=200,
                expected_count=self.NUM_CLAIM_PER_STATUS * 4,
                valid_statuses=valid_statuses,
            )

        def test_get_claims_with_status_filter_multiple_statuses(self, client, employer_auth_token):
            valid_statuses = ["Approved", "Closed"]
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Approved,Closed", client, employer_auth_token
            )
            self._perform_assertions(
                resp,
                status_code=200,
                expected_count=self.NUM_CLAIM_PER_STATUS * 2,
                valid_statuses=valid_statuses,
            )

        def test_get_claims_with_status_filter_multiple_statuses_pending(
            self, client, employer_auth_token
        ):
            valid_statuses = [
                "Adjudication",
                "In Review",
                "Intake In Progress",
                None,
                "Closed",
                "Completed",
            ]
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Pending,Closed,Completed", client, employer_auth_token
            )
            self._perform_assertions(
                resp,
                status_code=200,
                expected_count=self.NUM_CLAIM_PER_STATUS * 6,
                valid_statuses=valid_statuses,
            )

        def test_get_claims_with_status_filter_unsupported_statuses(
            self, client, employer_auth_token
        ):
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Unknown", client, employer_auth_token
            )
            self._perform_assertions(resp, status_code=400, expected_count=0, valid_statuses=[])

    # Inner class for testing Claims with Managed Requirements
    class TestClaimsWithManagedRequirements:
        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture(autouse=True)
        def link(self, test_db_session, employer_user, employer, test_verification):
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            test_db_session.commit()

        @pytest.fixture()
        def claim(self, employer, employee):
            return ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.get_id("Completed"),
                claim_type_id=1,
            )

        @pytest.fixture
        def other_claims(self, employer, employee):
            return [
                ClaimFactory.create(
                    employer=employer,
                    employee=employee,
                    fineos_absence_status_id=AbsenceStatus.get_id("Completed"),
                    claim_type_id=1,
                )
                for _ in range(0, 2)
            ]

        @pytest.fixture()
        def managed_requirements(self, claim):
            return [
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                )
                for _ in range(0, 2)
            ]

        @pytest.fixture()
        def old_managed_requirements(self, claim):
            return [
                ManagedRequirementFactory.create(
                    claim=claim, follow_up_date=datetime_util.utcnow() - timedelta(days=3)
                )
                for _ in range(0, 2)
            ]

        @pytest.fixture()
        def complete_managed_requirements(self, claim):
            return [
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                )
                for _ in range(0, 2)
            ]

        @pytest.fixture
        def transfer_managed_requirement_ownership(
            self, test_db_session, other_claims, complete_managed_requirements
        ):
            # transfer ownership of claim
            for mr in complete_managed_requirements:
                mr.claim_id = other_claims[0].claim_id
            test_db_session.commit()

        def test_claim_managed_requirements(
            self,
            client,
            employer_auth_token,
            managed_requirements,
            old_managed_requirements,
            complete_managed_requirements,
        ):
            resp = client.get(
                "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 1
            claim = response_body["data"][0]
            assert len(claim.get("managed_requirements", [])) == len(managed_requirements)
            expected_type = (
                ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_description
            )
            expected_status = ManagedRequirementStatus.OPEN.managed_requirement_status_description
            for req in claim["managed_requirements"]:
                assert req["follow_up_date"] >= date.today().strftime("%Y-%m-%d")
                assert req["type"] == expected_type
                assert req["status"] == expected_status

        def test_claim_filter_has_open_managed_requirement(
            self,
            client,
            employer_auth_token,
            managed_requirements,
            transfer_managed_requirement_ownership,
        ):
            """
            db has:
            - one completed claim with at least one open managed requirements (should be returned since it has an open managed requirement)
            - one completed claim with some managed requirements but none are open (should  NOT be returned since has no open managed requirement)
            - one completed claim with no managed requirements (should NOT be returned since has no open managed requirement)
            """
            resp = client.get(
                f"/v1/claims?claim_status={ActionRequiredStatusFilter.OPEN_REQUIREMENT}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 1

        def test_claim_filter_has_pending_no_action(
            self,
            client,
            other_claims,
            employer_auth_token,
            test_db_session,
            claim,
            managed_requirements,
            transfer_managed_requirement_ownership,
        ):
            """
            db has:
            - one completed claim with at least one open managed requirements (should NOT be returned)
            - one completed claim with some managed requirements but none are open (should be returned)
            - one completed claim with no managed requirements (should be returned since has no open managed requirement)
            """
            test_db_session.commit()
            resp = client.get(
                f"/v1/claims?claim_status={ActionRequiredStatusFilter.PENDING_NO_ACTION}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == len(other_claims)
            for returned_claim in claim_data:
                assert len(returned_claim["managed_requirements"]) == 0

        def test_claim_filter_has_open_managed_requirement_has_pending_no_action(
            self,
            client,
            employer_auth_token,
            managed_requirements,
            transfer_managed_requirement_ownership,
        ):
            """
            db has:
            - one completed claim with at least one open managed requirements (should be returned since it has an open managed requirement)
            - one completed claim with some managed requirements but none are open (should be returned since has no open managed requirement)
            - one completed claim with no managed requirements (should be returned since has no open managed requirement)
            """
            resp = client.get(
                f"/v1/claims?claim_status={ActionRequiredStatusFilter.PENDING_NO_ACTION},{ActionRequiredStatusFilter.OPEN_REQUIREMENT}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 3

    # Inner class for testing Claims Search
    class TestClaimsSearch:
        @pytest.fixture()
        def X_NAME(self):
            return "xxxxx"

        @pytest.fixture()
        def XAbsenceCase(self):
            return "NTN-99-ABS-01"

        @pytest.fixture()
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture()
        def other_employer_user(self):
            return UserFactory.create(roles=[Role.EMPLOYER])

        @pytest.fixture
        def other_employer_claims(self, other_employer_user):
            return {
                "exp": datetime.now() + timedelta(days=1),
                "sub": str(other_employer_user.sub_id),
            }

        @pytest.fixture()
        def other_employer_auth_token(self, other_employer_claims, auth_private_key):
            return jwt.encode(other_employer_claims, auth_private_key, algorithm=ALGORITHMS.RS256)

        @pytest.fixture()
        def other_employer(self):
            return EmployerFactory.create()

        @pytest.fixture()
        def first_employee(self, X_NAME):
            return EmployeeFactory.create(
                first_name="FirstName", middle_name=X_NAME, last_name=X_NAME
            )

        @pytest.fixture()
        def middle_employee(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name="InMiddleName", last_name=X_NAME
            )

        @pytest.fixture()
        def last_employee(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name=X_NAME, last_name="AtTheLast"
            )

        @pytest.fixture()
        def id_employee(self, X_NAME):
            return EmployeeFactory.create(first_name=X_NAME, middle_name=X_NAME, last_name=X_NAME)

        @pytest.fixture()
        def john(self, X_NAME):
            return EmployeeFactory.create(first_name="John", middle_name=X_NAME, last_name=X_NAME)

        @pytest.fixture()
        def johnny(self, X_NAME):
            return EmployeeFactory.create(first_name=X_NAME, middle_name="Johnny", last_name=X_NAME)

        @pytest.fixture()
        def middlejohn(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name=X_NAME, last_name="Middlejohn"
            )

        @pytest.fixture()
        def johnson(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME, middle_name=X_NAME, last_name="Johnson"
            )

        @pytest.fixture(autouse=True)
        def load_test_db(
            self,
            employer_user,
            other_employer_user,
            test_verification,
            test_db_session,
            employer,
            other_employer,
            first_employee,
            middle_employee,
            last_employee,
            id_employee,
            john,
            johnny,
            middlejohn,
            johnson,
            XAbsenceCase,
        ):
            ClaimFactory.create(employer=employer, employee=first_employee, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=middle_employee, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=last_employee, claim_type_id=1)
            ClaimFactory.create(
                employer=employer,
                employee=id_employee,
                claim_type_id=1,
                fineos_absence_id=XAbsenceCase,
            )
            ClaimFactory.create(employer=employer, employee=john, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=johnny, claim_type_id=1)
            ClaimFactory.create(employer=employer, employee=middlejohn, claim_type_id=1)

            ClaimFactory.create(employer=other_employer, employee=johnson, claim_type_id=1)

            leave_admin = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            other_leave_admin = UserLeaveAdministrator(
                user_id=other_employer_user.user_id,
                employer_id=other_employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(leave_admin)
            test_db_session.add(other_leave_admin)
            test_db_session.commit()

        def perform_search(self, search_string, client, token):
            return client.get(
                f"/v1/claims?search={search_string}", headers={"Authorization": f"Bearer {token}"},
            )

        def test_get_claims_search_first_name(self, first_employee, client, employer_auth_token):
            response = self.perform_search("firstn", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["first_name"] == first_employee.first_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_middle_name(self, middle_employee, client, employer_auth_token):
            response = self.perform_search("inmidd", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["middle_name"] == middle_employee.middle_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_last_name(self, last_employee, client, employer_auth_token):
            response = self.perform_search("helast", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["last_name"] == last_employee.last_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_absence_id(self, XAbsenceCase, client, employer_auth_token):
            response = self.perform_search("NTN-99-ABS-01", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (c for c in response_body["data"] if c["fineos_absence_id"] == XAbsenceCase), None,
            )
            assert claim is not None

        def test_get_claims_search_common_name_different_employers(
            self,
            client,
            john,
            johnny,
            middlejohn,
            johnson,
            employer_auth_token,
            other_employer_auth_token,
        ):
            response = self.perform_search("john", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            john_claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["first_name"] == john.first_name
                ),
                None,
            )
            assert john_claim is not None

            johnny_claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["middle_name"] == johnny.middle_name
                ),
                None,
            )
            assert johnny_claim is not None

            middlejohn_claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["last_name"] == middlejohn.last_name
                ),
                None,
            )
            assert middlejohn_claim is not None

            empty_response = self.perform_search("johnson", client, employer_auth_token)

            assert empty_response.status_code == 200
            empty_response_body = empty_response.get_json()
            assert len(empty_response_body["data"]) == 0

            other_response = self.perform_search("john", client, other_employer_auth_token)

            assert other_response.status_code == 200
            other_response_body = other_response.get_json()

            johnson_claim = next(
                (
                    c
                    for c in other_response_body["data"]
                    if c["employee"]["last_name"] == johnson.last_name
                ),
                None,
            )
            assert johnson_claim is not None

        def test_get_claims_search_blank_string(self, client, employer_auth_token):
            response = self.perform_search("", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) >= 7

        def test_get_claims_search_not_used(self, client, employer_auth_token):
            response = client.get(
                "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) >= 7
