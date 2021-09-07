import copy
from datetime import date, datetime, timedelta
from typing import List
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
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.exceptions import ObjectNotFound
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail
from massgov.pfml.db.models.applications import FINEOSWebIdExt
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    Claim,
    LkManagedRequirementStatus,
    ManagedRequirement,
    ManagedRequirementCategory,
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
    TaxIdentifierFactory,
    UserFactory,
    VerificationFactory,
)
from massgov.pfml.db.queries.get_claims_query import ActionRequiredStatusFilter
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
)
from massgov.pfml.fineos import models
from massgov.pfml.fineos.mock_client import MockFINEOSClient
from massgov.pfml.fineos.models.group_client_api import (
    Base64EncodedFileData,
    ManagedRequirementDetails,
)
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
    def document_data(self):
        return Base64EncodedFileData(
            fileName="test.pdf",
            fileExtension="pdf",
            base64EncodedFileContents="Zm9v",  # decodes to "foo"
            contentType="application/pdf",
            description=None,
            fileSizeInBytes=0,
            managedReqId=None,
        )

    @pytest.fixture
    def request_params(self, claim, employer_auth_token):
        class EmployerDocumentDownloadRequestParams(object):
            __slots__ = ["absence_id", "document_id", "auth_token"]

            def __init__(self, absence_id, document_id, auth_token):
                self.absence_id = absence_id
                self.document_id = document_id
                self.auth_token = auth_token

        return EmployerDocumentDownloadRequestParams(
            claim.fineos_absence_id, "doc_id", employer_auth_token
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

    @mock.patch("massgov.pfml.api.claims.download_document_as_leave_admin")
    def test_employers_receive_200(self, mock_download, document_data, client, request_params):
        mock_download.return_value = document_data

        response = self.download_document(client, request_params)
        assert response.status_code == 200

    @mock.patch("massgov.pfml.api.claims.download_document_as_leave_admin")
    def test_cannot_download_documents_not_attached_to_absence(
        self, mock_download, client, request_params, caplog
    ):
        mock_download.side_effect = ObjectNotFound(
            description="Unable to find FINEOS document for user"
        )

        response = self.download_document(client, request_params)
        assert response.status_code == 404

        response_json = response.get_json()
        message = response_json["message"]
        assert message == "Unable to find FINEOS document for user"

        assert "Unable to find FINEOS document for user" in caplog.text

    @mock.patch("massgov.pfml.api.claims.download_document_as_leave_admin")
    def test_cannot_download_non_downloadable_doc_types(
        self, mock_download, client, request_params, caplog
    ):
        error_message = "User is not authorized to access documents of type: identification proof"
        mock_download.side_effect = NotAuthorizedForAccess(
            description=error_message,
            error_type="unauthorized_document_type",
            data={"doc_type": "identification proof"},
        )

        response = self.download_document(client, request_params)
        assert response.status_code == 403

        response_json = response.get_json()
        message = response_json["message"]
        assert message == error_message

        assert error_message in caplog.text


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
            headers={"Authorization": f"Bearer {employer_auth_token}",},
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
    def test_second_eform_version_defaults_to_true(
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
            headers={"Authorization": f"Bearer {employer_auth_token}",},
        )
        response_data = response.get_json()["data"]

        assert response.status_code == 200
        assert response_data["uses_second_eform_version"] is True

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

    @pytest.fixture
    def managed_requirements(self):
        return [
            {
                "managedReqId": 123,
                "category": "Employer Confirmation",
                "type": "Employer Confirmation of Leave Data",
                "followUpDate": date(2021, 2, 1),
                "documentReceived": True,
                "creator": "Fake Creator",
                "status": "Open",
                "subjectPartyName": "Fake Name",
                "sourceOfInfoPartyName": "Fake Sourcee",
                "creationDate": date(2020, 1, 1),
                "dateSuppressed": date(2020, 3, 1),
            },
            {
                "managedReqId": 124,
                "category": "Employer Confirmation",
                "type": "Employer Confirmation of Leave Data",
                "followUpDate": date(2021, 2, 1),
                "documentReceived": True,
                "creator": "Fake Creator",
                "status": "Complete",
                "subjectPartyName": "Fake Name",
                "sourceOfInfoPartyName": "Fake Sourcee",
                "creationDate": date(2020, 1, 1),
                "dateSuppressed": date(2020, 3, 1),
            },
        ]

    @pytest.fixture
    def fineos_managed_requirements(self, managed_requirements):
        return [ManagedRequirementDetails.parse_obj(mr) for mr in managed_requirements]

    def _managed_requirements_by_fineos_absence_id(
        self, db_session, fineos_absence_id
    ) -> List[ManagedRequirement]:
        return (
            db_session.query(ManagedRequirement)
            .join(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .all()
        )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_employer_get_claim_review_create_managed_requirements(
        self,
        mock_get_req,
        fineos_managed_requirements,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
    ):
        mock_get_req.return_value = fineos_managed_requirements
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

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        requirements = self._managed_requirements_by_fineos_absence_id(
            test_db_session, claim.fineos_absence_id
        )
        assert len(requirements) == len(fineos_managed_requirements)
        for db_mr in requirements:
            searched_mr = [
                m
                for m in fineos_managed_requirements
                if str(m.managedReqId) == db_mr.fineos_managed_requirement_id
            ]
            assert len(searched_mr) == 1
            mr = searched_mr[0]
            assert mr.followUpDate == db_mr.follow_up_date
            assert mr.type == db_mr.managed_requirement_type.managed_requirement_type_description
            assert (
                mr.status == db_mr.managed_requirement_status.managed_requirement_status_description
            )
            assert (
                mr.category
                == db_mr.managed_requirement_category.managed_requirement_category_description
            )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_employer_get_claim_review_update_managed_requirements(
        self,
        mock_get_req,
        fineos_managed_requirements,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
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

        for mr in fineos_managed_requirements:
            create_managed_requirement_from_fineos(test_db_session, claim.claim_id, mr, {})
            mr.followUpDate = mr.followUpDate - timedelta(days=3)
            mr.status = ManagedRequirementStatus.SUPPRESSED.managed_requirement_status_description
        mock_get_req.return_value = fineos_managed_requirements

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        requirements = self._managed_requirements_by_fineos_absence_id(
            test_db_session, claim.fineos_absence_id
        )
        assert len(requirements) == len(fineos_managed_requirements)
        for db_mr in requirements:
            searched_mr = [
                m
                for m in fineos_managed_requirements
                if str(m.managedReqId) == db_mr.fineos_managed_requirement_id
            ]
            assert len(searched_mr) == 1
            mr = searched_mr[0]
            assert mr.followUpDate == db_mr.follow_up_date
            assert mr.type == db_mr.managed_requirement_type.managed_requirement_type_description
            assert (
                mr.status == db_mr.managed_requirement_status.managed_requirement_status_description
            )
            assert (
                mr.category
                == db_mr.managed_requirement_category.managed_requirement_category_description
            )

    @mock.patch("massgov.pfml.api.claims.handle_managed_requirements")
    def test_employer_get_claim_review_failure_managed_requirement_handling(
        self,
        mock_handle,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
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

        mock_handle.side_effect = Exception("Unexpected failure")
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200


@pytest.mark.integration
class TestUpdateClaim:
    @pytest.fixture(autouse=True)
    def setup_db(self, claim, employer, user_leave_admin, test_db_session):
        test_db_session.add(employer)
        test_db_session.add(claim)
        test_db_session.add(user_leave_admin)
        test_db_session.commit()

    def test_non_employees_cannot_access_employer_update_claim_review(
        self, client, auth_token, update_claim_body
    ):

        response = client.patch(
            "/v1/employers/claims/3/review",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=update_claim_body,
        )

        assert response.status_code == 403

    @mock.patch("massgov.pfml.api.claims.logger.info")
    @mock.patch(
        "massgov.pfml.api.claims.claim_rules.get_employer_claim_review_issues", return_value=[]
    )
    def test_employer_update_claim_review_success_case(
        self,
        mock_get_issues,
        mock_info_logger,
        employer_auth_token,
        claim,
        client,
        update_claim_body,
    ):
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )
        assert response.status_code == 200
        mock_get_issues.assert_called_once_with(EmployerClaimReview.parse_obj(update_claim_body))

        assert mock_info_logger.call_count == 2
        msg_arg, kwargs = mock_info_logger.call_args_list[1]
        assert msg_arg[0] == "Updated claim"
        assert kwargs["extra"]["absence_case_id"] == claim.fineos_absence_id
        assert kwargs["extra"]["user_leave_admin.employer_id"] == claim.employer_id
        assert kwargs["extra"]["claim_request.employer_decision"] == "Approve"
        assert kwargs["extra"]["num_employers"] == 1
        assert kwargs["extra"]["claim_request.num_previous_leaves"] == 1

    @mock.patch("massgov.pfml.api.claims.claim_rules.get_employer_claim_review_issues")
    def test_employer_update_claim_err_handling_response(
        self, mock_get_issues, client, employer_auth_token, update_claim_body, claim
    ):
        mock_get_issues.return_value = [
            ValidationErrorDetail(
                message="hours_worked_per_week must be populated",
                type="required",
                field="hours_worked_per_week",
            )
        ]
        request_body = update_claim_body
        response = client.patch(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=request_body,
        )
        assert response.status_code == 400
        assert response.get_json().get("errors")
        assert response.get_json().get("message") == "Invalid claim review body"

    def test_employer_update_claim_review_validates_previous_leaves_length(
        self, client, employer_auth_token, update_claim_body, claim,
    ):
        previous_leaves = [
            {
                "leave_end_date": "2020-10-04",
                "leave_start_date": "2020-10-01",
                "leave_reason": "Pregnancy",
            }
        ] * 17

        request_with_17_previous_leaves = {**update_claim_body, "previous_leaves": previous_leaves}

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
        self, client, employer_auth_token, claim, update_claim_body
    ):

        request_with_11_employer_benefits = {
            **update_claim_body,
            "employer_benefits": [
                {
                    "benefit_amount_dollars": 0,
                    "benefit_amount_frequency": "Per Day",
                    "benefit_end_date": "2021-01-05",
                    "benefit_start_date": "2021-02-06",
                    "benefit_type": "Accrued paid leave",
                }
            ]
            * 11,
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

    def test_employer_confirmation_sent_with_employer_update_claim_review(
        self, client, employer_auth_token, claim
    ):

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

    class TestClaimReviewUpdatesManagedRequirements:
        @pytest.fixture
        def get_managed_requirement_by_fineos_managed_req_id(self, test_db_session):
            def _managed_requirement_by_fineos_managed_req_id(fineos_managed_requirement_id):
                return get_managed_requirement_by_fineos_managed_requirement_id(
                    int(fineos_managed_requirement_id), test_db_session
                )

            return _managed_requirement_by_fineos_managed_req_id

        @pytest.fixture
        def fineos_man_req(self, claim):
            def _fineos_managed_requirement(managed_req_id=None, status=None, type=None):
                man_req = ManagedRequirementFactory.create(claim=claim)

                requirement = {
                    "managedReqId": int(man_req.fineos_managed_requirement_id),
                    "status": ManagedRequirementStatus.get_description(2),
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

                if managed_req_id is not None:
                    requirement["managedReqId"] = int(managed_req_id)

                if status is not None:
                    requirement["status"] = status

                if type is not None:
                    requirement["type"] = type

                return ManagedRequirementDetails.parse_obj(requirement)

            return _fineos_managed_requirement

        @pytest.fixture
        def update_request_body(self):
            return {
                "comment": "",
                "employer_benefits": [],
                "employer_decision": "Approve",
                "fraud": "Yes",
                "has_amendments": False,
                "hours_worked_per_week": 16,
                "previous_leaves": [],
            }

        @pytest.fixture(autouse=True)
        def with_mock_client_capture(self):
            massgov.pfml.fineos.mock_client.start_capture()

        @pytest.fixture(autouse=True)
        def with_user_leave_admin(self, user_leave_admin, test_db_session):
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
        def complete_valid_fineos_managed_requirement(
            self, fineos_man_req,
        ):
            return fineos_man_req()

        @pytest.fixture
        def wrong_type_invalid_fineos_managed_requirement(self, fineos_man_req):
            man_req_id = None
            man_req_status = None
            return fineos_man_req(man_req_id, man_req_status, "Invalid Type")

        @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
        def test_employer_update_claim_review_updates_valid_managed_requirements(
            self,
            mock_get_managed_requirements,
            complete_valid_fineos_managed_requirement,
            client,
            employer_auth_token,
            claim,
            update_request_body,
            user_leave_admin,
            get_managed_requirement_by_fineos_managed_req_id,
        ):
            mock_get_managed_requirements.return_value = [complete_valid_fineos_managed_requirement]

            client.patch(
                f"/v1/employers/claims/{claim.fineos_absence_id}/review",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=update_request_body,
            )

            managed_req = get_managed_requirement_by_fineos_managed_req_id(
                complete_valid_fineos_managed_requirement.managedReqId
            )

            assert managed_req is not None
            assert managed_req.respondent_user_id == user_leave_admin.user_id
            assert (
                managed_req.managed_requirement_status.managed_requirement_status_description
                == complete_valid_fineos_managed_requirement.status
            )

        @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
        def test_employer_update_claim_review_does_not_fail_on_invalid_requirements(
            self,
            mock_get_managed_requirements,
            wrong_type_invalid_fineos_managed_requirement,
            client,
            employer_auth_token,
            claim,
            update_request_body,
        ):
            mock_get_managed_requirements.return_value = [
                wrong_type_invalid_fineos_managed_requirement
            ]

            response = client.patch(
                f"/v1/employers/claims/{claim.fineos_absence_id}/review",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=update_request_body,
            )

            errors = response.get_json().get("errors")
            assert response.status_code == 200
            assert errors is None

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


def assert_detailed_claim_response_equal_to_claim_query(
    claim_response, claim_query, application=None
) -> bool:
    if application:
        assert claim_response["application_id"] == str(application.application_id)
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


def leave_period_response_equal_leave_period_query(
    leave_period_response, leave_period_query
) -> bool:
    return (
        leave_period_response["fineos_leave_period_id"]
        == leave_period_query["fineos_leave_period_id"]
        and leave_period_response["absence_period_start_date"]
        == leave_period_query["absence_period_start_date"]
        and leave_period_response["absence_period_end_date"]
        == leave_period_query["absence_period_end_date"]
        and leave_period_response["request_decision"] == leave_period_query["request_decision"]
        and leave_period_response["period_type"] == leave_period_query["period_type"]
        and leave_period_response["reason"] == leave_period_query["reason"]
        and leave_period_response["reason_qualifier_one"]
        == leave_period_query["reason_qualifier_one"]
    )


class TestGetClaimEndpoint:
    def test_get_claim_claim_does_not_exist(self, caplog, client, employer_auth_token):
        response = client.get(
            "/v1/claims/NTN-100-ABS-01", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 400
        tests.api.validate_error_response(response, 400, message="Claim not in PFML database.")
        assert "Claim not in PFML database." in caplog.text

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
        assert_detailed_claim_response_equal_to_claim_query(claim_data, claim)

    def test_get_claim_user_has_access_as_claimant(
        self, caplog, client, auth_token, user, test_db_session
    ):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)
        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )
        ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_detailed_claim_response_equal_to_claim_query(claim_data, claim)

    def test_get_claim_with_no_employer_employee(
        self, caplog, client, auth_token, user, test_db_session
    ):
        claim = ClaimFactory.create(
            employer=None,
            employee=None,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
            employee_id=None,
        )
        ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data["absence_periods"]) == 0

    def test_get_claim_with_no_tax_identifier(
        self, caplog, client, auth_token, user, test_db_session
    ):
        employer = EmployerFactory.create(employer_fein="813648030")
        employee = EmployeeFactory.create(tax_identifier=None, tax_identifier_id=None)

        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )
        ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data["absence_periods"]) == 0

    def test_get_claim_with_leave_periods(self, caplog, client, auth_token, user, test_db_session):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)
        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )

        application = ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        leave_period = {
            "absence_period_end_date": "2021-01-30",
            "absence_period_start_date": "2021-01-29",
            "evidence_status": None,
            "fineos_leave_period_id": "PL-14449-0000002237",
            "period_type": "Continuous",
            "reason": "Child Bonding",
            "reason_qualifier_one": "Foster Care",
            "reason_qualifier_two": "",
            "request_decision": "Pending",
        }

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_detailed_claim_response_equal_to_claim_query(claim_data, claim, application)
        assert leave_period_response_equal_leave_period_query(
            claim_data["absence_periods"][0], leave_period
        )

    def test_get_claim_with_managed_requirements(self, client, auth_token, user, test_db_session):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)

        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "pfml_api_468df93c-cb2d-424e-9690-f61cc65506bb"
        test_db_session.add(fineos_web_id_ext)

        test_db_session.commit()
        claim = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="NTN-304363-ABS-01",
        )

        managed_requirement: ManagedRequirement = ManagedRequirementFactory.create(
            claim=claim, claim_id=claim.claim_id
        )
        ManagedRequirementFactory.create(claim=claim, claim_id=claim.claim_id)

        application = ApplicationFactory.create(user=user, claim=claim)
        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert_detailed_claim_response_equal_to_claim_query(claim_data, claim, application)
        managed_requirement_response = claim_data["managed_requirements"]
        assert len(managed_requirement_response) == 2
        assert (
            managed_requirement.follow_up_date.strftime("%Y-%m-%d")
            == managed_requirement_response[0]["follow_up_date"]
        )
        assert (
            managed_requirement.managed_requirement_status.managed_requirement_status_description
            == managed_requirement_response[0]["status"]
        )
        assert (
            managed_requirement.managed_requirement_type.managed_requirement_type_description
            == managed_requirement_response[0]["type"]
        )
        assert (
            managed_requirement.managed_requirement_category.managed_requirement_category_description
            == managed_requirement_response[0]["category"]
        )


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

    class TestClaimsOrderManagedRequirements:
        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture(autouse=True)
        def link(self, employer_user, test_verification, employer, test_db_session):
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            test_db_session.commit()

        # first
        @pytest.fixture
        def claim_with_soonest_open_reqs(self, employer, employee):
            # should be returned first because the managed requirements
            #  have the soonest follow_up_date
            claim = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.CLOSED.absence_status_id,
                claim_type_id=1,
            )
            # soonest managed requirement
            ManagedRequirementFactory.create(
                claim=claim,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=datetime_util.utcnow(),
            )
            for i in range(0, 2):
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                    follow_up_date=datetime_util.utcnow() + timedelta(days=20 + i),
                )
            return claim

        # second
        @pytest.fixture
        def claim_with_open_reqs(self, employer, employee):
            # should be returned second because it has the second soonest managed requirements
            claim = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.CLOSED.absence_status_id,
                claim_type_id=1,
            )
            for i in range(0, 2):
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                    follow_up_date=datetime_util.utcnow() + timedelta(days=15 + i),
                )
            return claim

        # third
        @pytest.fixture
        def claim_without_reqs_intake_in_progress(self, employer, employee):
            # should be returned third because it's status is intake in progress
            # sort_order = 1 in lk_absence_status table
            claim = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.INTAKE_IN_PROGRESS.absence_status_id,
                claim_type_id=1,
            )
            return claim

        # fourth
        @pytest.fixture(autouse=True)
        def claim_with_complete_reqs(self, employer, employee):
            # should be returned fourth because it has COMPLETE managed requirements
            #  and it's status is completed
            # sort_order = 6 in lk_absence_status table
            claim = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
                claim_type_id=1,
            )
            for i in range(0, 2):
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                    follow_up_date=datetime_util.utcnow() + timedelta(days=100 + i),
                )
            return claim

        @pytest.fixture
        def claims_order_asc(
            self,
            claim_with_open_reqs,
            claim_with_soonest_open_reqs,
            claim_without_reqs_intake_in_progress,
            claim_with_complete_reqs,
        ):
            return [
                claim_with_soonest_open_reqs,
                claim_with_open_reqs,
                claim_without_reqs_intake_in_progress,
                claim_with_complete_reqs,
            ]

        @pytest.fixture
        def claims_order_next_day(
            self,
            claim_with_open_reqs,
            claim_with_soonest_open_reqs,
            claim_without_reqs_intake_in_progress,
            claim_with_complete_reqs,
        ):
            return [
                claim_with_open_reqs,
                claim_without_reqs_intake_in_progress,
                claim_with_complete_reqs,
                claim_with_soonest_open_reqs,
            ]

        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        def _perform_assertion(self, claims_order, response):
            assert response.status_code == 200
            response_body = response.get_json()
            claims = response_body.get("data", [])
            assert len(claims) == len(claims_order)
            for claim, expected in zip(claims, claims_order):
                assert claim["fineos_absence_id"] == expected.fineos_absence_id

        def test_get_claims_order_status_with_requirements_desc(
            self, client, employer_auth_token, claims_order_asc
        ):
            claims_order = claims_order_asc.copy()
            claims_order.reverse()
            request = {"order_direction": "descending", "order_by": "fineos_absence_status"}
            response = self._perform_api_call(request, client, employer_auth_token)
            self._perform_assertion(claims_order, response)

        def test_get_claims_order_status_with_requirements_asc(
            self, client, employer_auth_token, claims_order_asc
        ):
            claims_order = claims_order_asc
            request = {"order_direction": "ascending", "order_by": "fineos_absence_status"}
            response = self._perform_api_call(request, client, employer_auth_token)
            self._perform_assertion(claims_order, response)

        def test_get_claims_order_status_with_requirements_asc_next_day(
            self, client, employer_auth_token, claims_order_next_day
        ):
            tomorrow = datetime_util.utcnow() + timedelta(days=1)
            freezer = freeze_time(tomorrow.strftime("%Y-%m-%d %H:%M:%S"))
            freezer.start()
            claims_order = claims_order_next_day
            request = {"order_direction": "ascending", "order_by": "fineos_absence_status"}
            response = self._perform_api_call(request, client, employer_auth_token)
            self._perform_assertion(claims_order, response)
            freezer.stop()

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

    def test_get_claims_no_employee(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()

        for _ in range(5):
            ClaimFactory.create(
                employer=employer, fineos_absence_status_id=1, claim_type_id=1,
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
            f"/v1/claims?employer_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5

    def test_get_claims_no_employer(self, client, auth_token, user):
        employee = EmployeeFactory.create()

        for _ in range(5):
            application = ApplicationFactory.create(user=user)
            ClaimFactory.create(
                employee=employee,
                application=application,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )

        response = client.get("/v1/claims", headers={"Authorization": f"Bearer {auth_token}"},)

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5

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
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1,)

        @pytest.fixture
        def claim_pending_no_action(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1,)

        @pytest.fixture
        def third_claim(self, employer, employee):
            return ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.get_id("Adjudication"),
                claim_type_id=1,
            )

        @pytest.fixture
        def completed_claim(self, employer, employee):
            return ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.get_id("Completed"),
                claim_type_id=1,
            )

        def _add_managed_requirements_to_claim(
            self, claim, status: LkManagedRequirementStatus, count=2
        ):
            return [
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=status.managed_requirement_status_id,
                )
                for _ in range(0, count)
            ]

        @pytest.fixture
        def claims_with_managed_requirements(
            self, claim, claim_pending_no_action, third_claim, completed_claim
        ):
            # claim has both open and completed requirements
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.OPEN)
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.COMPLETE)

            # claim_pending_no_action has completed requirements
            self._add_managed_requirements_to_claim(
                claim_pending_no_action, ManagedRequirementStatus.COMPLETE
            )

            # third_claim does not have managed requirements

            # completed claim does not have managed requirements and is Completed, should NOT be returned

        @pytest.fixture()
        def old_managed_requirements(self, claim):
            return [
                ManagedRequirementFactory.create(
                    claim=claim, follow_up_date=datetime_util.utcnow() - timedelta(days=3)
                )
                for _ in range(0, 2)
            ]

        def test_claim_managed_requirements(
            self, client, employer_auth_token, claim, old_managed_requirements,
        ):
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.OPEN, 2)
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.COMPLETE)
            resp = client.get(
                "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 1
            claim = response_body["data"][0]
            assert len(claim.get("managed_requirements", [])) == 2
            expected_type = (
                ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_description
            )
            expected_status = ManagedRequirementStatus.OPEN.managed_requirement_status_description
            for req in claim["managed_requirements"]:
                assert req["follow_up_date"] >= date.today().strftime("%Y-%m-%d")
                assert req["type"] == expected_type
                assert req["status"] == expected_status

        def test_claim_filter_has_open_managed_requirement(
            self, client, employer_auth_token, claims_with_managed_requirements
        ):
            # claim has both open and completed requirements, should be returned
            # claim_pending_no_action has completed requirements, should NOT be returned
            # third_claim does not have managed requirements, should NOT be returned
            # completed claim does not have managed requirements and is Completed, should NOT be returned

            resp = client.get(
                f"/v1/claims?claim_status={ActionRequiredStatusFilter.OPEN_REQUIREMENT}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 1

        def test_claim_filter_has_pending_no_action(
            self, client, employer_auth_token, claims_with_managed_requirements
        ):
            # claim has both open and completed requirements, should NOT be returned
            # claim_pending_no_action has completed requirements, should be returned
            # third_claim does not have managed requirements, should be returned
            # completed claim does not have managed requirements but is Completed, should NOT be returned

            resp = client.get(
                f"/v1/claims?claim_status={ActionRequiredStatusFilter.PENDING_NO_ACTION}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 2
            for returned_claim in claim_data:
                assert len(returned_claim["managed_requirements"]) == 0

        def test_claim_filter_has_open_managed_requirement_has_pending_no_action(
            self, client, employer_auth_token, claims_with_managed_requirements
        ):
            # claim has both open and completed requirements, should be returned
            # claim_pending_no_action has completed requirements, should be returned
            # third_claim does not have managed requirements, should be returned
            # completed claim does not have managed requirements and is Completed, should NOT be returned

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

    class TestClaimsSearchFullName:
        @pytest.fixture()
        def X_NAME(self):
            return "xxxxx"

        @pytest.fixture()
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture()
        def full_name_employees(self, X_NAME):
            similar_employees = []
            full_name_employee = EmployeeFactory.create()

            similar_employees.append(full_name_employee)
            similar_employees.append(EmployeeFactory.create())

            # same first_name
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=full_name_employee.first_name, middle_name=X_NAME, last_name=X_NAME
                )
            )
            # same middle_name
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=X_NAME, middle_name=full_name_employee.middle_name, last_name=X_NAME
                )
            )
            # same last_name
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=X_NAME, middle_name=X_NAME, last_name=full_name_employee.last_name
                )
            )
            # same first_name and last_name should be returned in first_last and last_first search
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=full_name_employee.first_name,
                    middle_name=X_NAME,
                    last_name=full_name_employee.last_name,
                )
            )
            return similar_employees

        @pytest.fixture()
        def full_name_employee(self, full_name_employees):
            return full_name_employees[0]

        @pytest.fixture(autouse=True)
        def load_test_db(
            self, employer_user, employer, test_verification, test_db_session, full_name_employees
        ):

            for employee_full_name in full_name_employees:
                ClaimFactory.create(employer=employer, employee=employee_full_name, claim_type_id=1)

            leave_admin = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(leave_admin)
            test_db_session.commit()

        def perform_search(self, search_string, client, token):
            return client.get(
                f"/v1/claims?search={search_string}", headers={"Authorization": f"Bearer {token}"},
            )

        def test_get_claims_search_full_name(self, client, employer_auth_token, full_name_employee):
            search_string = f"{full_name_employee.first_name} {full_name_employee.middle_name} {full_name_employee.last_name}"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

        def test_get_claims_search_full_name_with_extra_spaces(
            self, client, employer_auth_token, full_name_employee
        ):
            search_string = f" {full_name_employee.first_name}     {full_name_employee.middle_name}   {full_name_employee.last_name} "
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

        def test_get_claims_search_first_last(
            self, client, employer_auth_token, full_name_employee
        ):
            search_string = f"{full_name_employee.first_name} {full_name_employee.last_name}"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 2

        def test_get_claims_search_last_first(
            self, client, employer_auth_token, full_name_employee
        ):
            search_string = f"{full_name_employee.last_name} {full_name_employee.first_name}"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 2

        def test_claims_search_wildcard_input(
            self, client, employer_auth_token, full_name_employee
        ):
            response = self.perform_search("%", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 0

        def test_claims_search_wildcard_input_full_name(
            self, client, employer_auth_token, full_name_employee
        ):
            response = self.perform_search(
                f"{full_name_employee.last_name}%{full_name_employee.first_name}",
                client,
                employer_auth_token,
            )

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 0

    # Test the combination of claims feature
    # ordering, filtering and search
    class TestClaimsMultipleParams:
        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture
        def other_employee(self):
            return EmployeeFactory.create()

        @pytest.fixture(autouse=True)
        def load_test_db(
            self, employer_user, test_verification, test_db_session, employee, other_employee
        ):
            employer = EmployerFactory.create()

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
            test_db_session.add(other_link)

            for _ in range(5):
                ClaimFactory.create(
                    employer=employer,
                    employee=employee,
                    fineos_absence_status_id=AbsenceStatus.ADJUDICATION.absence_status_id,
                    claim_type_id=1,
                )
                ClaimFactory.create(
                    employer=other_employer,
                    employee=other_employee,
                    fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
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
                    fineos_absence_status_id=AbsenceStatus.INTAKE_IN_PROGRESS.absence_status_id,
                    claim_type_id=1,
                    created_at=factory.Faker(
                        "date_between_dates",
                        date_start=date(2021, 1, 1),
                        date_end=date(2021, 1, 15),
                    ),
                )
                claim = ClaimFactory.create(
                    employer=employer,
                    employee=employee,
                    fineos_absence_status_id=AbsenceStatus.IN_REVIEW.absence_status_id,
                    claim_type_id=1,
                )
                ManagedRequirementFactory.create(
                    claim=claim,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                )
            self.claims_count = 20
            test_db_session.commit()

        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        def test_get_claims_absence_status_order_filter_employee_search_pending_no_action(
            self, client, employer_auth_token, other_employee
        ):
            params = {
                "claim_status": ActionRequiredStatusFilter.PENDING_NO_ACTION,
                "search": other_employee.first_name,
                "order_by": "employee",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == self.claims_count / 4

        def test_get_claims_absence_status_order_filter_employee_search_open_requirements(
            self, client, employer_auth_token, employee
        ):
            params = {
                "claim_status": ActionRequiredStatusFilter.OPEN_REQUIREMENT,
                "search": employee.first_name,
                "order_by": "employee",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == self.claims_count / 4

    # Test validation of claims endpoint query param validation
    class TestClaimsAPIInputValidation:
        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        def _assert_400_error_response(self, response):
            assert response.status_code == 400

        def test_claims_invalid_param_field(self, client, employer_auth_token):
            params = {"invalid": "invalid"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

        def test_claims_invalid_order_by(self, client, employer_auth_token):
            params = {"order_by": "bad"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

        def test_claims_unsupported_column_order_by(self, client, employer_auth_token):
            params = {"order_by": "updated_at"}
            response = self._perform_api_call(params, client, employer_auth_token)
            self._assert_400_error_response(response)

        def test_claims_bad_absence_status(self, client, employer_auth_token):
            bad_statuses = [
                "--",
                "%",
                "Intake In Progress!",
                "Intake In Progress%",
                "Pending--",
                "; Select",
            ]
            for status in bad_statuses:
                params = {"claim_status": status}

                response = self._perform_api_call(params, client, employer_auth_token)
                self._assert_400_error_response(response)
                err_details = response.get_json()["detail"]
                assert "Invalid claim status" in err_details or "does not match" in err_details
