import copy
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
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
from massgov.pfml.api.claims import map_request_decision_param_to_db_columns
from massgov.pfml.api.exceptions import ObjectNotFound
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.services.claims import ClaimWithdrawnError
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail
from massgov.pfml.db.models.absences import AbsencePeriodType, AbsenceStatus
from massgov.pfml.db.models.applications import FINEOSWebIdExt
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    Claim,
    LeaveRequestDecision,
    LkManagedRequirementStatus,
    ManagedRequirement,
    ManagedRequirementCategory,
    ManagedRequirementStatus,
    ManagedRequirementType,
    Role,
    State,
    UserLeaveAdministrator,
    UserLeaveAdministratorOrgUnit,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployeeWithFineosNumberFactory,
    EmployerFactory,
    ManagedRequirementFactory,
    OrganizationUnitFactory,
    TaxIdentifierFactory,
    UserFactory,
    VerificationFactory,
)
from massgov.pfml.db.queries.absence_periods import (
    split_fineos_absence_period_id,
    split_fineos_leave_request_id,
    upsert_absence_period_from_fineos_period,
)
from massgov.pfml.db.queries.get_claims_query import ActionRequiredStatusFilter
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.fineos import models
from massgov.pfml.fineos.mock_client import MockFINEOSClient
from massgov.pfml.fineos.models.group_client_api import (
    Base64EncodedFileData,
    ManagedRequirementDetails,
    PeriodDecisions,
)
from massgov.pfml.util.pydantic.types import FEINFormattedStr
from massgov.pfml.util.strings import format_fein


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
@dataclass
class GetClaimDocumentsRequestParams:
    absence_id: str
    auth_token: str


def get_documents(client, params):
    return client.get(
        f"/v1/employers/claims/{params.absence_id}/documents",
        headers={"Authorization": f"Bearer {params.auth_token}"},
    )


class TestEmployerGetClaimDocuments:
    @pytest.fixture(autouse=True)
    def setup_db(self, claim, employer, user_leave_admin, test_db_session):
        test_db_session.add(user_leave_admin)
        test_db_session.commit()

    @pytest.fixture
    def request_params(self, claim, employer_auth_token):
        return GetClaimDocumentsRequestParams(claim.fineos_absence_id, employer_auth_token)

    def test_non_employers_cannot_access(self, client, request_params, auth_token):
        request_params.auth_token = auth_token

        response = get_documents(client, request_params)
        assert response.status_code == 403

    def test_employers_receive_200(self, client, request_params):
        response = get_documents(client, request_params)
        assert response.status_code == 200


# testing class for employer_document_download
@dataclass
class EmployerDocumentDownloadRequestParams:
    absence_id: str
    document_id: str
    auth_token: str


def download_document(client, params):
    return client.get(
        f"/v1/employers/claims/{params.absence_id}/documents/{params.document_id}",
        headers={"Authorization": f"Bearer {params.auth_token}"},
    )


@pytest.fixture
def document_data():
    return Base64EncodedFileData(
        fileName="test.pdf",
        fileExtension="pdf",
        base64EncodedFileContents="Zm9v",  # decodes to "foo"
        contentType="application/pdf",
        description=None,
        fileSizeInBytes=0,
        managedReqId=None,
    )


class TestEmployerDocumentDownload:
    @pytest.fixture(autouse=True)
    def setup_db(self, claim, employer, user_leave_admin, test_db_session):
        test_db_session.add(user_leave_admin)
        test_db_session.commit()

    @pytest.fixture
    def request_params(self, claim, employer_auth_token):
        return EmployerDocumentDownloadRequestParams(
            claim.fineos_absence_id, "doc_id", employer_auth_token
        )

    def test_non_employers_receive_403(self, client, request_params, auth_token):
        request_params.auth_token = auth_token

        response = download_document(client, request_params)
        assert response.status_code == 403

        response_json = response.get_json()
        message = response_json["message"]
        assert "does not have read access" in message

    @mock.patch("massgov.pfml.api.claims.download_document_as_leave_admin")
    def test_employers_receive_200(self, mock_download, document_data, client, request_params):
        mock_download.return_value = document_data

        response = download_document(client, request_params)
        assert response.status_code == 200

    @mock.patch("massgov.pfml.api.claims.download_document_as_leave_admin")
    def test_cannot_download_documents_not_attached_to_absence(
        self, mock_download, client, request_params, caplog
    ):
        mock_download.side_effect = ObjectNotFound(
            description="Unable to find FINEOS document for user"
        )

        response = download_document(client, request_params)
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

        response = download_document(client, request_params)
        assert response.status_code == 403

        response_json = response.get_json()
        message = response_json["message"]
        assert message == error_message

        assert error_message in caplog.text


class TestGetClaimReview:
    def test_non_employers_cannot_access_get_claim_review(self, client, auth_token):
        response = client.get(
            "/v1/employers/claims/NTN-100-ABS-01/review",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403

    @freeze_time("2020-12-07")
    def test_employers_receive_200_from_get_claim_review(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification,
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

        # This field is set in mock_client.py::get_customer_occupations
        assert response_data["hours_worked_per_week"] == 37.5
        assert response_data["employer_dba"] == "Acme Co"
        assert response_data["employer_fein"] == "99-9999999"
        assert response_data["employer_id"] == str(employer.employer_id)
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
        self, client, employer_user, employer_auth_token, test_db_session, test_verification,
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
        assert response.status_code == 200

    @freeze_time("2020-12-07")
    def test_employers_with_int_hours_worked_per_week_receive_200_from_get_claim_review(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification,
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

        # This field is set in mock_client.py::get_customer_occupations
        assert response_data["hours_worked_per_week"] == 37
        assert response_data["employer_dba"] == "Acme Co"
        assert response_data["employer_fein"] == "99-9999999"
        # The fields below are set in mock_client.py::mock_customer_info
        assert response_data["date_of_birth"] == "****-12-25"
        assert response_data["tax_identifier"] == "***-**-1234"
        assert response_data["residential_address"]["city"] == "Atlanta"
        assert response_data["residential_address"]["line_1"] == "55 Trinity Ave."
        assert response_data["residential_address"]["line_2"] == "Suite 3450"
        assert response_data["residential_address"]["state"] == "GA"
        assert response_data["residential_address"]["zip"] == "30303"

    @mock.patch("massgov.pfml.api.claims.upsert_absence_period_from_fineos_period")
    def test_employers_receive_proper_claim_using_correct_fineos_web_id(
        self,
        mock_upsert_absence_period,
        client,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
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

    def _retrieve_managed_requirements_by_fineos_absence_id(
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
        requirements = self._retrieve_managed_requirements_by_fineos_absence_id(
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
        ## Test set up
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
            db_mr = create_managed_requirement_from_fineos(test_db_session, claim.claim_id, mr)
            mr.followUpDate = mr.followUpDate - timedelta(days=3)
            mr.status = ManagedRequirementStatus.SUPPRESSED.managed_requirement_status_description
        mock_get_req.return_value = fineos_managed_requirements

        requirements = self._retrieve_managed_requirements_by_fineos_absence_id(
            test_db_session, claim.fineos_absence_id
        )

        ## Test that after call managed requirements changes are reflected in db and that mr returned from endpoint
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        assert len(response.get_json()["data"]["managed_requirements"]) == 2
        for managed_requirement in response.get_json()["data"]["managed_requirements"]:
            assert "responded_at" in managed_requirement
            assert managed_requirement["category"] == ManagedRequirementCategory.get_description(1)
            assert "classExtensionInformation" not in managed_requirement

        requirements = self._retrieve_managed_requirements_by_fineos_absence_id(
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

    @mock.patch(
        "massgov.pfml.db.queries.managed_requirements.get_managed_requirement_by_fineos_managed_requirement_id"
    )
    def test_employer_get_claim_review_managed_requirement_failure_errors(
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
        assert response.status_code == 500

    @pytest.fixture
    def absence_id(self):
        return "NTN-20133-ABS-01"

    @pytest.fixture
    def absence_details_data(self, absence_id):
        return {
            "startDate": "2021-01-01",
            "endDate": "2021-01-31",
            "decisions": [
                {
                    "absence": {"id": "NTN-111111-ABS-01", "caseReference": "NTN-111111-ABS-01"},
                    "employee": {"id": "111222333", "name": "Fake Person"},
                    "period": {
                        "periodReference": "PL-00000-0000000000",
                        "parentPeriodReference": "",
                        "relatedToEpisodic": False,
                        "startDate": "2021-01-01",
                        "endDate": "2021-01-31",
                        "balanceDeduction": 0,
                        "timeRequested": "",
                        "timeDeducted": "",
                        "timeDeductedBasis": "",
                        "timeDecisionStatus": "",
                        "timeDecisionReason": "",
                        "type": "Time off period",
                        "status": "Known",
                        "leaveRequest": {
                            "id": "PL-14432-00001",
                            "reasonName": "Child Bonding",
                            "qualifier1": "Newborn",
                            "qualifier2": "",
                            "decisionStatus": "Denied",
                            "approvalReason": "Please Select",
                            "denialReason": "No Applicable Plans",
                        },
                    },
                },
                {
                    "absence": {"id": "NTN-111111-ABS-01", "caseReference": "NTN-111111-ABS-01"},
                    "employee": {"id": "111222333", "name": "Fake Person"},
                    "period": {
                        "periodReference": "PL-00001-0000000001",
                        "parentPeriodReference": "",
                        "relatedToEpisodic": False,
                        "startDate": "2021-01-01",
                        "endDate": "2021-01-31",
                        "balanceDeduction": 0,
                        "timeRequested": "",
                        "timeDeducted": "",
                        "timeDeductedBasis": "",
                        "timeDecisionStatus": "",
                        "timeDecisionReason": "",
                        "type": "Time off period",
                        "status": "Known",
                        "leaveRequest": {
                            "id": "PL-14432-00002",
                            "reasonName": "Child Bonding",
                            "qualifier1": "Newborn",
                            "qualifier2": "",
                            "decisionStatus": "Denied",
                            "approvalReason": "Please Select",
                            "denialReason": "No Applicable Plans",
                        },
                    },
                },
            ],
        }

    @pytest.fixture
    def mock_absence_details_create(self, absence_details_data):
        return PeriodDecisions.parse_obj(absence_details_data)

    @pytest.fixture
    def mock_absence_details_no_decisions(self, absence_details_data):
        empty_decisions = absence_details_data.copy()
        empty_decisions["decisions"] = []
        return PeriodDecisions.parse_obj(empty_decisions)

    @pytest.fixture
    def mock_absence_details_update(self, absence_details_data):
        absence_details = absence_details_data.copy()
        decisions = []
        for decision in absence_details["decisions"]:
            decision["period"]["startDate"] = datetime.today()
            decision["period"]["endDate"] = datetime.today()
            decision["period"]["status"] = "Pending"
            decisions.append(decision)
        absence_details["decisions"] = decisions
        return PeriodDecisions.parse_obj(absence_details)

    @pytest.fixture
    def mock_absence_details_invalid_leave_request_id(self, absence_details_data):
        absence_details = absence_details_data.copy()
        absence_details["decisions"][0]["period"]["leaveRequest"]["id"] = "PL0000100001"
        absence_details["decisions"][1]["period"]["leaveRequest"]["id"] = "PL-00001-one"
        return PeriodDecisions.parse_obj(absence_details)

    @pytest.fixture
    def employer(self):
        return EmployerFactory.create(employer_fein="112222222")

    @pytest.fixture
    def claim(self, test_db_session, employer_user, employer, test_verification):
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

    def _assert_absence_period_data(self, test_db_session, claim, period):
        period_id = period.periodReference.split("-")
        class_id = int(period_id[1])
        index_id = int(period_id[2])
        db_period = (
            test_db_session.query(AbsencePeriod)
            .join(Claim)
            .filter(
                Claim.claim_id == claim.claim_id,
                AbsencePeriod.fineos_absence_period_index_id == index_id,
                AbsencePeriod.fineos_absence_period_class_id == class_id,
            )
            .one()
        )
        assert db_period.absence_period_start_date == period.startDate
        assert db_period.absence_period_end_date == period.endDate
        assert (
            db_period.leave_request_decision.leave_request_decision_description
            == period.leaveRequest.decisionStatus
        )

    def _assert_no_absence_period_data_for_claim(self, test_db_session, claim):
        db_periods = (
            test_db_session.query(AbsencePeriod)
            .join(Claim)
            .filter(Claim.claim_id == claim.claim_id,)
            .all()
        )
        assert len(db_periods) == 0

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_raises_withdrawn_claim_when_no_decisions(
        self,
        mock_get_absence,
        test_db_session,
        client,
        employer_auth_token,
        mock_absence_details_no_decisions,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        mock_get_absence.return_value = mock_absence_details_no_decisions
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_creates_absence_period(
        self,
        mock_get_absence,
        test_db_session,
        client,
        employer_auth_token,
        mock_absence_details_create,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        mock_get_absence.return_value = mock_absence_details_create
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        for decision in mock_absence_details_create.decisions:
            self._assert_absence_period_data(test_db_session, claim, decision.period)

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_withdrawn_claim_no_absence_period_decisions(
        self, mock_get_absence, client, employer_auth_token, claim,
    ):
        mock_get_absence.return_value = PeriodDecisions()
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response.status_code == 403

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_updates_absence_period(
        self,
        mock_get_absence,
        test_db_session,
        client,
        employer_auth_token,
        mock_absence_details_create,
        mock_absence_details_update,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        absence_periods = [decision.period for decision in mock_absence_details_create.decisions]
        for absence_period in absence_periods:
            upsert_absence_period_from_fineos_period(
                test_db_session, claim.claim_id, absence_period, {}
            )
        mock_get_absence.return_value = mock_absence_details_update
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        for decision in mock_absence_details_update.decisions:
            self._assert_absence_period_data(test_db_session, claim, decision.period)

    @mock.patch("massgov.pfml.api.claims.upsert_absence_period_from_fineos_period")
    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_creates_absence_period_failure(
        self,
        mock_get_absence,
        mock_upsert_absence_periods_from_fineos_decisions,
        test_db_session,
        client,
        mock_absence_details_create,
        employer_auth_token,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        mock_upsert_absence_periods_from_fineos_decisions.side_effect = Exception(
            "Unexpected failure"
        )
        mock_get_absence.return_value = mock_absence_details_create
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response.status_code == 500  # err is 500 b/c exception bubbles up
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_creates_absence_period_invalid_leave_request_id(
        self,
        mock_get_absence,
        test_db_session,
        client,
        employer_auth_token,
        mock_absence_details_invalid_leave_request_id,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        mock_get_absence.return_value = mock_absence_details_invalid_leave_request_id
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 400
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_returns_absence_periods_from_fineos(
        self, mock_get_absence, client, employer_auth_token, mock_absence_details_create, claim,
    ):
        mock_get_absence.return_value = mock_absence_details_create
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        response_data = response.get_json()["data"]
        absence_periods = response_data["absence_periods"]
        assert response.status_code == 200
        periods = [decision.period for decision in mock_absence_details_create.decisions]
        for fineos_period_data, absence_data in zip(periods, absence_periods):
            class_id, index_id = split_fineos_absence_period_id(fineos_period_data.periodReference)
            leave_request_id = split_fineos_leave_request_id(fineos_period_data.leaveRequest.id, {})
            assert leave_request_id == absence_data["fineos_leave_request_id"]
            assert (
                absence_data["period_type"]
                == AbsencePeriodType.CONTINUOUS.absence_period_type_description
            )
            assert (
                fineos_period_data.startDate.isoformat()
                == absence_data["absence_period_start_date"]
            )
            assert fineos_period_data.endDate.isoformat() == absence_data["absence_period_end_date"]
            assert fineos_period_data.leaveRequest.reasonName == absence_data["reason"]
            assert (
                fineos_period_data.leaveRequest.qualifier1 == absence_data["reason_qualifier_one"]
            )
            assert (
                fineos_period_data.leaveRequest.qualifier2 == absence_data["reason_qualifier_two"]
            )
            assert (
                fineos_period_data.leaveRequest.decisionStatus == absence_data["request_decision"]
            )


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


def assert_claim_response_equal_to_claim_query(
    claim_response, claim_query, has_paid_payments=False
) -> bool:
    if claim_query.absence_period_end_date:
        assert claim_response[
            "absence_period_end_date"
        ] == claim_query.absence_period_end_date.strftime("%Y-%m-%d")
    else:
        assert claim_response["absence_period_end_date"] is None
    if claim_query.absence_period_start_date:
        assert claim_response[
            "absence_period_start_date"
        ] == claim_query.absence_period_start_date.strftime("%Y-%m-%d")
    else:
        assert claim_response["absence_period_start_date"] is None
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
    assert claim_response["has_paid_payments"] == has_paid_payments


def assert_claim_pfml_crm_response_equal_to_claim_query(claim_response, claim_query) -> bool:
    assert claim_response["fineos_absence_id"] == claim_query.fineos_absence_id
    assert claim_response["fineos_notification_id"] == claim_query.fineos_notification_id
    assert claim_response["employee"]["employee_id"] == str(claim_query.employee.employee_id)
    assert (
        claim_response["employee"]["fineos_customer_number"]
        == claim_query.employee.fineos_customer_number
    )
    assert claim_response["employee"]["first_name"] == claim_query.employee.first_name
    assert claim_response["employee"]["middle_name"] == claim_query.employee.middle_name
    assert claim_response["employee"]["last_name"] == claim_query.employee.last_name
    assert claim_response["employee"]["other_name"] == claim_query.employee.other_name

    # Ensure only fields in ClaimForPfmlCrmResponse are returned
    assert "claim_status" not in claim_response
    assert "claim_type_description" not in claim_response
    assert "has_paid_payments" not in claim_response
    assert "employer" not in claim_response
    assert "created_at" not in claim_response
    assert "absence_period_end_date" not in claim_response
    assert "absence_period_start_date" not in claim_response
    assert "absence_periods" not in claim_response
    assert "managed_requirements" not in claim_response


def assert_detailed_claim_response_equal_to_claim_query(
    claim_response, claim_query, application=None, has_paid_payments=False
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
    assert claim_response["has_paid_payments"] == has_paid_payments


def leave_period_response_equal_leave_period_query(
    leave_period_response, leave_period_query
) -> bool:
    return (
        leave_period_response["absence_period_start_date"]
        == leave_period_query["absence_period_start_date"]
        and leave_period_response["absence_period_end_date"]
        == leave_period_query["absence_period_end_date"]
        and leave_period_response["request_decision"] == leave_period_query["request_decision"]
        and leave_period_response["period_type"] == leave_period_query["period_type"]
        and leave_period_response["reason"] == leave_period_query["reason"]
        and leave_period_response["reason_qualifier_one"]
        == leave_period_query["reason_qualifier_one"]
    )


# TODO (CP-2636): Refactor tests to use fixtures
class TestGetClaimEndpoint:
    @pytest.fixture
    def setup_db(self, test_db_session, fineos_web_id_ext, application):
        test_db_session.add(fineos_web_id_ext)
        test_db_session.commit()

    @pytest.fixture
    def employer(self):
        return EmployerFactory.create(employer_fein="112222222")

    @pytest.fixture
    def employee(self):
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="123456789")
        return EmployeeFactory.create(tax_identifier_id=tax_identifier.tax_identifier_id)

    @pytest.fixture
    def fineos_web_id_ext(self, employee, employer):
        fineos_web_id_ext = FINEOSWebIdExt()
        fineos_web_id_ext.employee_tax_identifier = employee.tax_identifier.tax_identifier
        fineos_web_id_ext.employer_fein = employer.employer_fein
        fineos_web_id_ext.fineos_web_id = "web_id"

        return fineos_web_id_ext

    @pytest.fixture
    def claim(self, employer, employee):
        return ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
            fineos_absence_id="foo",
        )

    @pytest.fixture
    def application(self, user, claim):
        return ApplicationFactory.create(user=user, claim=claim)

    def test_get_claim_claim_does_not_exist(self, caplog, client, auth_token):
        response = client.get(
            "/v1/claims/NTN-100-ABS-01", headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404
        tests.api.validate_error_response(response, 404, message="Claim not in PFML database.")
        assert "Claim not in PFML database." in caplog.text

    def test_get_claim_user_has_no_access(self, caplog, client, auth_token):
        claim = ClaimFactory.create()

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403
        tests.api.validate_error_response(
            response, 403, message="User does not have access to claim."
        )
        assert "User does not have access to claim." in caplog.text

    def test_get_claim_as_employer_returns_403(
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

        assert response.status_code == 403

        message = response.get_json().get("message")
        assert message == "Employers are not allowed to access claimant claim info"

    def test_get_claim_employee_different_fineos_names(
        self, caplog, client, auth_token, user, test_db_session
    ):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(
            tax_identifier_id=tax_identifier.tax_identifier_id,
            first_name="Foo",
            last_name="Bar",
            middle_name="Baz",
            fineos_employee_first_name="Foo2",
            fineos_employee_last_name="Bar2",
            fineos_employee_middle_name="Baz2",
        )

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

        assert claim_data["employee"]["first_name"] == "Foo2"
        assert claim_data["employee"]["middle_name"] == "Baz2"
        assert claim_data["employee"]["last_name"] == "Bar2"

    def test_get_claim_employee_no_fineos_names(
        self, caplog, client, auth_token, user, test_db_session
    ):
        employer = EmployerFactory.create(employer_fein="813648030")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
        employee = EmployeeFactory.create(
            tax_identifier_id=tax_identifier.tax_identifier_id,
            first_name="Foo",
            last_name="Bar",
            middle_name="Baz",
            fineos_employee_first_name=None,
            fineos_employee_last_name=None,
            fineos_employee_middle_name=None,
        )

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

        assert claim_data["employee"]["first_name"] == "Foo"
        assert claim_data["employee"]["middle_name"] == "Baz"
        assert claim_data["employee"]["last_name"] == "Bar"

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
            "fineos_leave_request_id": None,
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

    @mock.patch("massgov.pfml.api.claims.get_claim_detail")
    def test_withdrawn_claim_returns_403(
        self, mock_get_claim_detail, claim, client, auth_token, setup_db
    ):
        mock_get_claim_detail.side_effect = ClaimWithdrawnError()

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 403

        response_body = response.get_json()
        issues = response_body.get("errors")
        assert issues[0].get("type") == "fineos_claim_withdrawn"

    @mock.patch("massgov.pfml.api.claims.get_claim_detail")
    def test_with_get_claim_detail_error_returns_500(
        self, mock_get_claim_detail, claim, client, auth_token, setup_db, caplog
    ):
        error_msg = "oops :("
        mock_get_claim_detail.side_effect = Exception(error_msg)

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 500
        assert "get_claim failure" in caplog.text
        assert error_msg in caplog.text

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

    def test_get_claim_with_paid_payments(self, test_db_session, client, auth_token, user):
        payment_factory = DelegatedPaymentFactory(
            test_db_session, fineos_absence_id="NTN-304363-ABS-01"
        )
        claim = payment_factory.get_or_create_claim()
        payment_factory.get_or_create_payment_with_state(
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
        )
        ApplicationFactory.create(user=user, claim=claim)

        response = client.get(
            f"/v1/claims/{claim.fineos_absence_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert claim_data["has_paid_payments"] is True


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

        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == len(generated_claims)
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

        # POST /claims/search
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json={},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == len(generated_claims)
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

    def test_get_claims_as_pfml_crm_user(self, client, snow_user_headers):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        employee_with_fineos_customer_number = EmployeeWithFineosNumberFactory.create()

        generated_claims = [
            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
            )
            for _ in range(3)
        ]

        generated_claims.append(
            ClaimFactory.create(employer=employer, employee=employee_with_fineos_customer_number)
        )

        # GET /claims deprecated
        response = client.get("/v1/claims", headers=snow_user_headers)
        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")

        # assert that all created claims are returned
        assert len(claim_data) == len(generated_claims)

        for response_claim, generated_claim in zip(claim_data, reversed(generated_claims)):
            assert_claim_pfml_crm_response_equal_to_claim_query(response_claim, generated_claim)

        # POST /claims/search
        response = client.post("/v1/claims/search", headers=snow_user_headers, json={})
        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")

        # assert that all created claims are returned
        assert len(claim_data) == len(generated_claims)

        for response_claim, generated_claim in zip(claim_data, reversed(generated_claims)):
            assert_claim_pfml_crm_response_equal_to_claim_query(response_claim, generated_claim)

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

            # GET /claims deprecated
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

            # POST /claims/search

            post_body = {**scenario["request"]}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
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

    def test_get_claims_with_paid_payments(
        self, client, test_db_session, employer_user, employer_auth_token, test_verification
    ):
        payment_factory = DelegatedPaymentFactory(test_db_session, fineos_absence_status_id=1)
        claim = payment_factory.get_or_create_claim()
        payment_factory.get_or_create_payment_with_state(
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
        )

        claim2 = ClaimFactory.create(
            employer=payment_factory.employer,
            employee=payment_factory.employee,
            fineos_absence_status_id=1,
            claim_type_id=1,
        )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=payment_factory.employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 2

        # Sort order places most recent claims first
        assert_claim_response_equal_to_claim_query(claim_data[0], claim2, has_paid_payments=False)
        assert_claim_response_equal_to_claim_query(claim_data[1], claim, has_paid_payments=True)

        # POST /claims/search
        response = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {employer_auth_token}"}, json={}
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 2

        # Sort order places most recent claims first
        assert_claim_response_equal_to_claim_query(claim_data[0], claim2, has_paid_payments=False)
        assert_claim_response_equal_to_claim_query(claim_data[1], claim, has_paid_payments=True)

    # Inner class for testing Claims With Status Filtering
    class TestClaimsOrder:
        @pytest.fixture()
        def load_test_db_with_managed_requirements(
            self, employer_user, test_verification, test_db_session
        ):
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
            claim_one = ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1
            )
            claim_two = ClaimFactory.create(
                employer=other_employer, employee=other_employee, fineos_absence_status_id=2
            )
            claim_three = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
                claim_type_id=1,
            )
            claim_four = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
                claim_type_id=1,
            )
            ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
                claim_type_id=1,
            )
            ManagedRequirementFactory.create(
                claim=claim_three,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date="2022-01-01",
            )
            ManagedRequirementFactory.create(
                claim=claim_three,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date="2022-02-02",
            )
            ManagedRequirementFactory.create(
                claim=claim_four,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date="2021-01-01",
            )
            ManagedRequirementFactory.create(
                claim=claim_one,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=datetime_util.utcnow() + timedelta(days=15),
            )
            ManagedRequirementFactory.create(
                claim=claim_two,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=datetime_util.utcnow() + timedelta(days=30),
            )
            test_db_session.commit()

        @pytest.fixture()
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

        def test_get_claims_with_order_default(self, client, employer_auth_token, load_test_db):
            request = {}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = [d["created_at"] for d in response_body.get("data", [])]
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=True)

        def test_get_claims_with_order_default_asc(self, client, employer_auth_token, load_test_db):
            request = {"order_direction": "ascending"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = [d["created_at"] for d in response_body.get("data", [])]
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=False)

        def test_get_claims_with_order_unsupported_key(
            self, client, employer_auth_token, load_test_db
        ):
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

        def test_get_claims_with_order_employee_asc(
            self, client, employer_auth_token, load_test_db
        ):
            request = {"order_direction": "ascending", "order_by": "employee"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = self._extract_employee_name(response_body)
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=False)

        def test_get_claims_with_order_by_follow_up_date_desc(
            self, client, employer_auth_token, load_test_db_with_managed_requirements
        ):
            request = {"order_direction": "descending", "order_by": "latest_follow_up_date"}
            response = self._perform_api_call(request, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()
            claim_one, claim_two, claim_three, claim_four, claim_five = response_body["data"]

            # The first claims are Open, ordered chronologically (e.g. first 2022-02-18 then 2022-03-05)
            assert (
                claim_one["managed_requirements"][0]["follow_up_date"]
                < claim_two["managed_requirements"][0]["follow_up_date"]
            )
            assert claim_one["managed_requirements"][0]["status"] == "Open"
            assert claim_two["managed_requirements"][0]["status"] == "Open"
            # Next are any not-Open claims (or open claims with expired follow up date), ordered reverse chronologically (e.g. first 2022-02-02 then 2021-01-01)
            assert "2022-02-02" in [
                req["follow_up_date"] for req in claim_three["managed_requirements"]
            ]
            assert "2022-01-01" in [
                req["follow_up_date"] for req in claim_three["managed_requirements"]
            ]
            assert claim_three["managed_requirements"][0]["status"] == "Complete"
            assert (
                claim_four["managed_requirements"][0]["status"] == "Open"
            )  # Open but expired follow-up date
            assert claim_four["managed_requirements"][0]["follow_up_date"] == "2021-01-01"
            # Finally, claims without any associated managed requirements are last
            assert claim_five["managed_requirements"] == []

        def test_get_claims_with_order_by_follow_up_date_asc(
            self,
            client,
            employer_auth_token,
            load_test_db_with_managed_requirements,
            test_db_session,
        ):
            request = {"order_direction": "ascending", "order_by": "latest_follow_up_date"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            claim_one, claim_two, claim_three, claim_four, claim_five = response_body["data"]

            # First are not-Open claims (or open claims with expired follow up date), ordered chronologically (e.g. first 2021-01-01 then 2022-01-01)
            assert (
                claim_one["managed_requirements"][0]["status"] == "Open"
            )  # Open but expired follow-up date
            assert claim_two["managed_requirements"][0]["status"] == "Complete"
            assert claim_one["managed_requirements"][0]["follow_up_date"] == "2021-01-01"
            assert (
                claim_one["managed_requirements"][0]["follow_up_date"]
                < claim_two["managed_requirements"][0]["follow_up_date"]
            )

            # Next are open claims, ordered chronologically (e.g. first "2022-01-01" then "2022-03-03")
            assert (
                claim_three["managed_requirements"][0]["follow_up_date"]
                < claim_four["managed_requirements"][0]["follow_up_date"]
            )
            assert claim_three["managed_requirements"][0]["status"] == "Open"
            assert claim_four["managed_requirements"][0]["status"] == "Open"
            # Finally, claims without any associated managed requirements are last
            assert claim_five["managed_requirements"] == []

        def test_get_claims_with_order_employee_desc(
            self, client, employer_auth_token, load_test_db
        ):
            request = {"order_direction": "descending", "order_by": "employee"}
            response = self._perform_api_call(request, client, employer_auth_token)
            assert response.status_code == 200
            response_body = response.get_json()
            data = self._extract_employee_name(response_body)
            assert len(data) == self.claims_count
            self._assert_data_order(data, desc=True)

        def test_get_claims_with_order_fineos_absence_status_asc(
            self, client, employer_auth_token, test_db_session, load_test_db
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

        # GET /claims deprecated
        response = client.get(
            f"/v1/claims?employer_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5
        for claim in response_body["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(employer.employer_fein)

        # POST /claims/search
        post_body = {"employer_id": [employer.employer_id]}
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )

        assert response.status_code == 200

    def test_user_claim_access_via_employer_id(
        self, client, user, auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employerB = EmployerFactory.create()
        employerC = EmployerFactory.create()

        employee = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )

        new_claim = ClaimFactory.create(
            employer=employerB, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )
        ApplicationFactory.create(user=user, claim=new_claim)

        new_claim2 = ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )
        ApplicationFactory.create(user=user, claim=new_claim2)

        ClaimFactory.create(
            employer=employerC, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )

        test_db_session.commit()

        # GET /claims to make sure regular user cannot access claims they shouldn't
        response1 = client.get(
            f"/v1/claims?employer_id={employerC.employer_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 0

        response2 = client.get(
            f"/v1/claims?employer_id={employerB.employer_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 1

        response2 = client.get(
            f"/v1/claims?employer_id={employer.employer_id},{employerB.employer_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 2

    def test_get_claims_for_many_employer_ids(
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
            f"/v1/claims?employer_id={employer.employer_id},{other_employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        response_body = response.get_json()

        assert len(response_body["data"]) == 10
        for claim in response_body["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(
                employer.employer_fein
            ) or claim["employer"]["employer_fein"] == format_fein(other_employer.employer_fein)

        # POST /claims/search
        post_body = {"employer_id": [employer.employer_id, other_employer.employer_id]}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 10
        for claim in response_body1["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(
                employer.employer_fein
            ) or claim["employer"]["employer_fein"] == format_fein(other_employer.employer_fein)

    def test_get_claims_for_employee_id_as_employer(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )
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

        # GET /claims deprecated
        # Verify we can find the employee in question
        response1 = client.get(
            f"/v1/claims?employee_id={employee.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # POST /claims/search
        post_body = {"employee_id": [employee.employee_id]}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # Verify we're filtering OUT results if the employee isn't found
        response2 = client.get(
            f"/v1/claims?employee_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 0

        # POST /claims/search
        post_body = {"employee_id": [employer.employer_id]}
        response2 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 0

    def test_get_claims_valid_employee_id_invalid_employer_id(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )
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

        # GET /claims deprecated
        # Verify the wrong employer_id fails to find anything
        response1 = client.get(
            f"/v1/claims?employer_id={employee.employee_id}&employee_id={employee.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 0

        # POST /claims/search
        post_body = {"employer_id": [employee.employee_id], "employee_id": [employer.employer_id]}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 0

        # Verify the right employer_id and employee_id work together
        response2 = client.get(
            f"/v1/claims?employer_id={employer.employer_id}&employee_id={employee.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 1
        assert response_body2["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # POST /claims/search
        post_body = {"employer_id": [employer.employer_id], "employee_id": [employee.employee_id]}
        response2 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 1
        assert response_body2["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

    def test_get_claims_for_multiple_employee_ids_as_employer(
        self, client, employer_auth_token, employer_user, test_db_session, test_verification
    ):
        employer = EmployerFactory.create()
        employee = EmployeeFactory.create()
        employee2 = EmployeeFactory.create()

        ClaimFactory.create(
            employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
        )

        for _ in range(5):
            ClaimFactory.create(
                employer=employer, employee=employee2, fineos_absence_status_id=1, claim_type_id=1,
            )

        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

        # GET /claims deprecated
        # Verify we can find a single valid employee_id when sending one
        response1 = client.get(
            f"/v1/claims?employee_id={employee.employee_id},{employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # POST /claims/search
        post_body = {"employee_id": [employee.employee_id, employer.employer_id]}
        response1 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        assert len(response_body1["data"]) == 1
        assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

        # Verify we can find both valid employee_ids when sending multiple
        response2 = client.get(
            f"/v1/claims?employee_id={employee.employee_id},{employee2.employee_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 6
        eids_to_find = [str(employee.employee_id), str(employee2.employee_id)]
        for found_employee in response_body2["data"]:
            assert found_employee["employee"]["employee_id"] in eids_to_find

        # POST /claims/search
        post_body = {"employee_id": [employee.employee_id, employee2.employee_id]}
        response2 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        assert len(response_body2["data"]) == 6
        eids_to_find = [str(employee.employee_id), str(employee2.employee_id)]
        for found_employee in response_body2["data"]:
            assert found_employee["employee"]["employee_id"] in eids_to_find

        # Verify malformed e.g. trailing comma is rejected
        response3 = client.get(
            f"/v1/claims?employee_id={employee.employee_id},",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response3.status_code == 400

        # POST /claims/search
        post_body = {"employee_id": f"{employee.employee_id},"}
        response3 = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        assert response3.status_code == 400

    def test_get_claims_for_employee_id_as_claimant(
        self, client, auth_token, user, test_db_session, test_verification
    ):
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

        response1 = client.get(
            f"/v1/claims?employee_id={employeeB.employee_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response1.status_code == 200
        response_body1 = response1.get_json()
        claim_data1 = response_body1.get("data")
        assert len(claim_data1) == 0

        # POST /claims/search
        post_body = {"employee_id": [employeeB.employee_id]}
        response1 = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {auth_token}"}, json=post_body
        )
        assert response1.status_code == 200
        response_body1 = response1.get_json()
        claim_data1 = response_body1.get("data")
        assert len(claim_data1) == 0

        response2 = client.get(
            f"/v1/claims?employee_id={employeeA.employee_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        claim_data2 = response_body2.get("data")
        assert len(claim_data2) == 3
        for found_claim in response_body2["data"]:
            assert found_claim["employee"]["employee_id"] == str(employeeA.employee_id)

        # POST /claims/search
        post_body = {"employee_id": [employeeA.employee_id]}
        response2 = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {auth_token}"}, json=post_body
        )
        assert response2.status_code == 200
        response_body2 = response2.get_json()
        claim_data2 = response_body2.get("data")
        assert len(claim_data2) == 3
        for found_claim in response_body2["data"]:
            assert found_claim["employee"]["employee_id"] == str(employeeA.employee_id)

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

        # GET /claims deprecated
        response = client.get("/v1/claims", headers={"Authorization": f"Bearer {auth_token}"},)

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 3
        for i in range(3):
            assert_claim_response_equal_to_claim_query(claim_data[i], generated_claims[2 - i])

        # POST /claims/search
        response = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {auth_token}"}, json={}
        )

        assert response.status_code == 200
        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert len(claim_data) == 3
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

        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5
        for claim in response_body["data"]:
            assert claim["employer"]["employer_fein"] == format_fein(other_employer.employer_fein)

        # POST /claims/search
        response = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {employer_auth_token}"}, json={}
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

        # GET /claims deprecated
        response = client.get(
            f"/v1/claims?employer_id={employer.employer_id}",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        response_body = response.get_json()

        assert len(response_body["data"]) == 5

        # POST /claims/search
        post_body = {"employer_id": [employer.employer_id]}
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
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

        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture
        def review_by_claim(self, employer, employee):
            # Approved claim with open managed requirements i.e review by
            claim_review_by = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            for _ in range(2):
                ManagedRequirementFactory.create(
                    claim=claim_review_by,
                    managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                    follow_up_date=date.today() + timedelta(days=10),
                )
            return claim_review_by

        @pytest.fixture
        def no_action_claim(self, employer, employee):
            # Approved claim with completed managed requirements
            claim_no_action = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            ManagedRequirementFactory.create(
                claim=claim_no_action,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date=date.today() + timedelta(days=10),
            )
            return claim_no_action

        @pytest.fixture
        def expired_requirements_claim(self, employer, employee):
            # Approved claim with expired managed requirements
            claim_expired = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            ManagedRequirementFactory.create(
                claim=claim_expired,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=date.today() - timedelta(days=2),
            )
            return claim_expired

        @pytest.fixture
        def no_open_requirement_claims(self, employer, employee):
            claims = []
            statuses = [
                AbsenceStatus.APPROVED,
                AbsenceStatus.CLOSED,
                AbsenceStatus.DECLINED,
                AbsenceStatus.COMPLETED,
            ]
            for status in statuses:
                for _ in range(self.NUM_CLAIM_PER_STATUS):
                    claim = ClaimFactory.create(
                        employer=employer,
                        employee=employee,
                        fineos_absence_status_id=status.absence_status_id,
                        claim_type_id=1,
                    )
                    claims.append(claim)
            return claims

        @pytest.fixture
        def pending_claims(self, employer, employee):
            # does not include review by claims
            claims = []
            statuses = [
                AbsenceStatus.INTAKE_IN_PROGRESS,
                AbsenceStatus.IN_REVIEW,
                AbsenceStatus.ADJUDICATION,
            ]
            for status in statuses:
                for _ in range(self.NUM_CLAIM_PER_STATUS):
                    claim = ClaimFactory.create(
                        employer=employer,
                        employee=employee,
                        fineos_absence_status_id=status.absence_status_id,
                        # fineos_absence_status=status,
                        claim_type_id=1,
                    )
                    claims.append(claim)
            for _ in range(self.NUM_CLAIM_PER_STATUS):  # for fineos_absence_status = NULL
                claim = ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1,)
                claims.append(claim)
            return claims

        @pytest.fixture(autouse=True)
        def load_test_db(
            self,
            employer,
            employee,
            employer_user,
            test_verification,
            test_db_session,
            no_open_requirement_claims,
            pending_claims,
            review_by_claim,
            no_action_claim,
            expired_requirements_claim,
        ):
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

        def _perform_assertions(self, response, status_code, expected_claims):
            expected_claims_fineos_absence_id = [
                claim.fineos_absence_id for claim in expected_claims
            ]
            assert response.status_code == status_code
            response_body = response.get_json()
            claim_data = response_body.get("data", [])
            for claim in response_body.get("data", []):
                fineos_absence_id = claim.get("fineos_absence_id", None)
                assert fineos_absence_id in expected_claims_fineos_absence_id
            assert len(claim_data) == len(expected_claims)

        def filter_claims_by_status(self, claims, valid_statuses):
            valid_statuses_id = [status.absence_status_id for status in valid_statuses]
            return [
                claim for claim in claims if claim.fineos_absence_status_id in valid_statuses_id
            ]

        def test_get_claims_with_status_filter_one_claim(
            self,
            client,
            employer_auth_token,
            no_open_requirement_claims,
            no_action_claim,
            expired_requirements_claim,
        ):
            expected_claims = self.filter_claims_by_status(
                no_open_requirement_claims, [AbsenceStatus.APPROVED]
            ) + [no_action_claim, expired_requirements_claim]
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Approved", client, employer_auth_token
            )
            self._perform_assertions(resp, status_code=200, expected_claims=expected_claims)

            # POST /claims/search
            post_body = {"claim_status": "Approved"}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            self._perform_assertions(response, status_code=200, expected_claims=expected_claims)

        def test_get_claims_with_status_filter_is_reviewable_yes(
            self, client, employer_auth_token, review_by_claim
        ):
            resp = self._perform_api_call(
                "/v1/claims?is_reviewable=yes", client, employer_auth_token
            )
            self._perform_assertions(resp, status_code=200, expected_claims=[review_by_claim])

            # POST /claims/search
            post_body = {"is_reviewable": "yes"}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            self._perform_assertions(response, status_code=200, expected_claims=[review_by_claim])

        def test_get_claims_with_status_filter_is_reviewable_no(
            self,
            client,
            employer_auth_token,
            no_open_requirement_claims,
            pending_claims,
            expired_requirements_claim,
            no_action_claim,
        ):
            resp = self._perform_api_call(
                "/v1/claims?is_reviewable=no", client, employer_auth_token
            )
            self._perform_assertions(
                resp,
                status_code=200,
                expected_claims=[
                    *no_open_requirement_claims,
                    *pending_claims,
                    expired_requirements_claim,
                    no_action_claim,
                ],
            )

            # POST /claims/search
            post_body = {"is_reviewable": "no"}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            self._perform_assertions(
                response,
                status_code=200,
                expected_claims=[
                    *no_open_requirement_claims,
                    *pending_claims,
                    expired_requirements_claim,
                    no_action_claim,
                ],
            )

        def test_get_claims_with_status_filter_is_reviewable_invalid_parameter(
            self, client, employer_auth_token
        ):
            resp = self._perform_api_call(
                "/v1/claims?is_reviewable=invalid", client, employer_auth_token
            )
            response_body = resp.get_json()
            assert resp.status_code == 400
            assert "'invalid' is not one of" in response_body["detail"]

            # POST /claims/search
            post_body = {"is_reviewable": "invalid"}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            response_body = response.get_json()
            assert resp.status_code == 400

        def test_get_claims_with_status_filter_multiple_statuses(
            self,
            client,
            employer_auth_token,
            no_open_requirement_claims,
            no_action_claim,
            expired_requirements_claim,
        ):
            expected_claims = self.filter_claims_by_status(
                no_open_requirement_claims, [AbsenceStatus.APPROVED, AbsenceStatus.CLOSED]
            ) + [no_action_claim, expired_requirements_claim]
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Approved,Closed", client, employer_auth_token
            )
            self._perform_assertions(resp, status_code=200, expected_claims=expected_claims)

            # POST /claims/search
            post_body = {"claim_status": "Approved,Closed"}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            self._perform_assertions(response, status_code=200, expected_claims=expected_claims)

        def test_get_claims_with_status_filter_unsupported_statuses(
            self, client, employer_auth_token
        ):
            resp = self._perform_api_call(
                "/v1/claims?claim_status=Unknown", client, employer_auth_token
            )
            self._perform_assertions(resp, status_code=400, expected_claims=[])

            # POST /claims/search
            post_body = {"claim_status": "Unknown"}
            response = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            self._perform_assertions(response, status_code=400, expected_claims=[])

    # Inner class for testing Claims with Absence Periods
    class TestClaimsWithAbsencePeriods:
        @pytest.fixture
        def employer(self):
            return EmployerFactory.create()

        @pytest.fixture
        def employee(self):
            return EmployeeFactory.create()

        @pytest.fixture()
        def claim(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)

        @pytest.fixture()
        def claim_no_absence_period(self, employer, employee):
            return ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)

        @pytest.fixture()
        def absence_periods(self, claim):
            start = date.today() + timedelta(days=5)
            periods = []
            for _ in range(5):
                end = start + timedelta(days=10)
                period = AbsencePeriodFactory.create(
                    claim=claim, absence_period_start_date=start, absence_period_end_date=end,
                )
                periods.append(period)
                start = start + timedelta(days=20)
            return periods

        @pytest.fixture()
        def claims(self, employer, employee):
            claims = []
            for _ in range(8):
                claim = ClaimFactory.create(employer=employer, employee=employee, claim_type_id=1)
                claims.append(claim)
            return claims

        @pytest.fixture()
        def varied_absence_periods(self, claims):
            start = date.today() + timedelta(days=5)
            periods = []
            num_request_decision_types = 8
            for i in range(num_request_decision_types):
                end = start + timedelta(days=10)
                period = AbsencePeriodFactory.create(
                    claim=claims[i],
                    absence_period_start_date=start,
                    absence_period_end_date=end,
                    leave_request_decision_id=i + 1,
                )
                periods.append(period)
                start = start + timedelta(days=20)
            return periods

        @pytest.fixture(autouse=True)
        def load_test_db(self, claim, test_db_session, employer_user, employer, test_verification):
            link = UserLeaveAdministrator(
                user_id=employer_user.user_id,
                employer_id=employer.employer_id,
                fineos_web_id="fake-fineos-web-id",
                verification=test_verification,
            )
            test_db_session.add(link)
            test_db_session.commit()

        def _find_absence_period_by_fineos_leave_request_id(
            self, fineos_leave_request_id: str, absence_periods: List[AbsencePeriod]
        ) -> Optional[AbsencePeriod]:
            absence_period = [
                period
                for period in absence_periods
                if period.fineos_leave_request_id == fineos_leave_request_id
            ]
            return absence_period[0] if len(absence_period) else None

        def _assert_claim_data(
            self, claim_data: Dict, claim: Claim, absence_periods: List[AbsencePeriod]
        ):
            assert claim_data["fineos_absence_id"] == claim.fineos_absence_id
            assert len(claim_data["absence_periods"]) == len(absence_periods)
            for absence_period_data in claim_data["absence_periods"]:
                absence_period = self._find_absence_period_by_fineos_leave_request_id(
                    absence_period_data["fineos_leave_request_id"], absence_periods
                )
                assert absence_period is not None
                assert (
                    absence_period.absence_period_start_date.isoformat()
                    == absence_period_data["absence_period_start_date"]
                )
                assert (
                    absence_period.absence_period_end_date.isoformat()
                    == absence_period_data["absence_period_end_date"]
                )

        def test_claim_with_absence_periods(
            self, client, employer_auth_token, claim, claim_no_absence_period, absence_periods
        ):
            resp = client.get(
                "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 2
            claim_data_with_absence_period = [
                claim for claim in claim_data if claim["absence_periods"]
            ][0]
            claim_data_no_absence_period = [
                claim for claim in claim_data if not claim["absence_periods"]
            ][0]
            self._assert_claim_data(claim_data_with_absence_period, claim, absence_periods)
            self._assert_claim_data(claim_data_no_absence_period, claim_no_absence_period, [])

        @pytest.mark.parametrize(
            "request_decision, num_claims_returned, expected_req_decs_returned",
            [
                ["approved", 1, [LeaveRequestDecision.APPROVED.leave_request_decision_description]],
                ["denied", 1, [LeaveRequestDecision.DENIED.leave_request_decision_description]],
                [
                    "withdrawn",
                    1,
                    [LeaveRequestDecision.WITHDRAWN.leave_request_decision_description],
                ],
                [
                    "pending",
                    3,
                    [
                        LeaveRequestDecision.PENDING.leave_request_decision_description,
                        LeaveRequestDecision.IN_REVIEW.leave_request_decision_description,
                        LeaveRequestDecision.PROJECTED.leave_request_decision_description,
                    ],
                ],
                [
                    "cancelled",
                    2,
                    [
                        LeaveRequestDecision.CANCELLED.leave_request_decision_description,
                        LeaveRequestDecision.VOIDED.leave_request_decision_description,
                    ],
                ],
            ],
        )
        def test_claim_request_decision_filter(
            self,
            request_decision,
            num_claims_returned,
            expected_req_decs_returned,
            client,
            employer_auth_token,
            claims,
            varied_absence_periods,
        ):
            # Note that for this test, our test data puts in the db 1 claim per absence period request decision type
            resp = client.get(
                f"/v1/claims?request_decision={request_decision}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claims_returned = response_body.get("data")
            assert len(claims_returned) == num_claims_returned
            for claim in claims_returned:
                for absence_period in claim["absence_periods"]:
                    assert absence_period["request_decision"] in expected_req_decs_returned

        def test_claim_request_decision_filter_invalid_param(
            self, client, employer_auth_token, claims, varied_absence_periods
        ):
            resp = client.get(
                "/v1/claims?request_decision=foobar",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )
            assert resp.status_code == 400
            response_body = resp.get_json()
            assert "'foobar' is not one of" in response_body["detail"]

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
        def claim_expired_requirements(self, employer, employee):
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
            self,
            claim,
            claim_pending_no_action,
            claim_expired_requirements,
            third_claim,
            completed_claim,
        ):
            # claim has both open and completed requirements
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.OPEN)
            self._add_managed_requirements_to_claim(claim, ManagedRequirementStatus.COMPLETE)

            # claim_pending_no_action has completed requirements
            self._add_managed_requirements_to_claim(
                claim_pending_no_action, ManagedRequirementStatus.COMPLETE
            )

            # claim_expired_requirements
            ManagedRequirementFactory.create(
                claim=claim_expired_requirements,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=date.today() - timedelta(days=2),
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
            assert len(claim.get("managed_requirements", [])) == 6

            resp = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json={},
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 1
            claim = response_body["data"][0]
            assert len(claim.get("managed_requirements", [])) == 6

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

            post_body = {"claim_status": ActionRequiredStatusFilter.OPEN_REQUIREMENT}
            resp = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
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
            assert len(claim_data) == 3
            for returned_claim in claim_data:
                assert (
                    len(
                        [
                            claim
                            for claim in returned_claim["managed_requirements"]
                            if claim["status"] == "Open"
                            and claim["follow_up_date"] >= datetime.today().strftime("%Y-%m-%d")
                        ]
                    )
                    == 0
                )

            post_body = {"claim_status": ActionRequiredStatusFilter.PENDING_NO_ACTION}
            resp = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 3
            for returned_claim in claim_data:
                assert (
                    len(
                        [
                            claim
                            for claim in returned_claim["managed_requirements"]
                            if claim["status"] == "Open"
                            and claim["follow_up_date"] >= datetime.today().strftime("%Y-%m-%d")
                        ]
                    )
                    == 0
                )

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
            assert len(claim_data) == 4

            post_body = {
                "claim_status": f"{ActionRequiredStatusFilter.PENDING_NO_ACTION},{ActionRequiredStatusFilter.OPEN_REQUIREMENT}"
            }
            resp = client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=post_body,
            )
            assert resp.status_code == 200
            response_body = resp.get_json()
            claim_data = response_body.get("data")
            assert len(claim_data) == 4

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

        @pytest.fixture()
        def employee_different_fineos_dor_first_name(self, X_NAME):
            return EmployeeFactory.create(
                first_name="Jane",
                middle_name=X_NAME,
                last_name=X_NAME,
                fineos_employee_first_name="Alice",
            )

        @pytest.fixture()
        def employee_different_fineos_dor_middle_name(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME,
                middle_name="Marie",
                last_name=X_NAME,
                fineos_employee_middle_name="Ann",
            )

        @pytest.fixture()
        def employee_different_fineos_dor_last_name(self, X_NAME):
            return EmployeeFactory.create(
                first_name=X_NAME,
                middle_name=X_NAME,
                last_name="Doe",
                fineos_employee_last_name="Jones",
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
            employee_different_fineos_dor_first_name,
            employee_different_fineos_dor_middle_name,
            employee_different_fineos_dor_last_name,
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

            ClaimFactory.create(
                employer=employer,
                employee=employee_different_fineos_dor_first_name,
                claim_type_id=1,
            )
            ClaimFactory.create(
                employer=employer,
                employee=employee_different_fineos_dor_middle_name,
                claim_type_id=1,
            )
            ClaimFactory.create(
                employer=employer, employee=employee_different_fineos_dor_last_name, claim_type_id=1
            )

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

        def perform_search_with_headers(self, search_string, client, headers):
            return client.get(f"/v1/claims?search={search_string}", headers=headers)

        def test_get_claims_snow_user(self, client, snow_user_headers):
            response = self.perform_search_with_headers("firstn", client, snow_user_headers)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = response_body["data"][0]
            assert "has_paid_payments" not in claim

        def test_get_claims_search_absence_id_snow_user(
            self, XAbsenceCase, client, snow_user_headers
        ):
            response = self.perform_search_with_headers("NTN-99-ABS-01", client, snow_user_headers)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (c for c in response_body["data"] if c["fineos_absence_id"] == XAbsenceCase), None,
            )
            assert claim is not None

        def test_get_claims_for_multiple_employee_ids_as_snow_user(
            self, client, snow_user_headers, employer_user, test_db_session
        ):
            employer = EmployerFactory.create()
            employee = EmployeeFactory.create()
            employee2 = EmployeeFactory.create()

            ClaimFactory.create(
                employer=employer, employee=employee, fineos_absence_status_id=1, claim_type_id=1,
            )

            for _ in range(5):
                ClaimFactory.create(
                    employer=employer,
                    employee=employee2,
                    fineos_absence_status_id=1,
                    claim_type_id=1,
                )

            test_db_session.commit()

            # Verify we can find a single valid employee_id when sending one
            response1 = client.get(
                f"/v1/claims?employee_id={employee.employee_id},{employer.employer_id}",
                headers=snow_user_headers,
            )
            assert response1.status_code == 200
            response_body1 = response1.get_json()
            assert len(response_body1["data"]) == 1
            assert response_body1["data"][0]["employee"]["employee_id"] == str(employee.employee_id)

            # Verify we can find both valid employee_ids when sending multiple
            response2 = client.get(
                f"/v1/claims?employee_id={employee.employee_id},{employee2.employee_id}",
                headers=snow_user_headers,
            )
            assert response2.status_code == 200
            response_body2 = response2.get_json()
            assert len(response_body2["data"]) == 6
            eids_to_find = [str(employee.employee_id), str(employee2.employee_id)]
            for found_employee in response_body2["data"]:
                assert found_employee["employee"]["employee_id"] in eids_to_find

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

        def test_get_claims_search_first_name_fineos(
            self, employee_different_fineos_dor_first_name, client, employer_auth_token
        ):
            response = self.perform_search("lice", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["first_name"]
                    == employee_different_fineos_dor_first_name.fineos_employee_first_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_middle_name_fineos(
            self, employee_different_fineos_dor_middle_name, client, employer_auth_token
        ):
            response = self.perform_search("nn", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["middle_name"]
                    == employee_different_fineos_dor_middle_name.fineos_employee_middle_name
                ),
                None,
            )
            assert claim is not None

        def test_get_claims_search_last_name_fineos(
            self, employee_different_fineos_dor_last_name, client, employer_auth_token
        ):
            response = self.perform_search("Jon", client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            claim = next(
                (
                    c
                    for c in response_body["data"]
                    if c["employee"]["last_name"]
                    == employee_different_fineos_dor_last_name.fineos_employee_last_name
                ),
                None,
            )
            assert claim is not None

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

        def test_get_claims_search_no_employee(self, client, employer_auth_token, employer):
            claim = ClaimFactory.create(
                employer=employer, employee_id=None, employee=None, claim_type_id=1
            )
            response = self.perform_search(claim.fineos_absence_id, client, employer_auth_token)
            response_body = response.get_json()
            assert len(response_body["data"]) == 1
            assert response_body["data"][0]["fineos_absence_id"] == claim.fineos_absence_id
            assert response_body["data"][0]["employee"] is None

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
            # same first_name and last_name should be returned in first_last and
            # last_first search, but unique if search terms are the FINEOS names
            # (in this dataset)
            similar_employees.append(
                EmployeeFactory.create(
                    first_name=full_name_employee.first_name,
                    middle_name=X_NAME,
                    last_name=full_name_employee.last_name,
                    fineos_employee_first_name="123",
                    fineos_employee_last_name="456",
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

        def test_get_claims_search_last_first_fineos(self, client, employer_auth_token):
            search_string = "123 456"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

        def test_get_claims_search_first_last_fineos(self, client, employer_auth_token):
            search_string = "456 123"
            response = self.perform_search(search_string, client, employer_auth_token)

            assert response.status_code == 200
            response_body = response.get_json()

            assert len(response_body["data"]) == 1

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
    # TODO: (PORTAL-1561) - delete this test class
    class TestClaimsMultipleParamsOld:
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

        def test_get_claims_is_reviewable_yes_absence_status_order(
            self, client, employer_auth_token, employee
        ):
            params = {
                "claim_status": ActionRequiredStatusFilter.OPEN_REQUIREMENT,
                "order_by": "employee",
                "is_reviewable": "yes",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == self.claims_count / 4

        def test_get_claims_is_reviewable_no_absence_status_order(
            self, client, employer_auth_token, employee
        ):
            params = {
                "claim_status": ActionRequiredStatusFilter.OPEN_REQUIREMENT,
                "order_by": "employee",
                "is_reviewable": "no",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == 0

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

    # Test validation of claims/search endpoint request body
    class TestClaimsAPIRequestBodyValidation:
        def _perform_api_call(self, request, client, employer_auth_token):
            return client.post(
                "/v1/claims/search",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
                json=request,
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

    # Test the combination of claims filters and search
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

            # create 10 claims
            # employee claims are Open, other employee are not Open
            # varied absence periods for employee claims
            # always withdrawn for other employee claims
            for i in range(5):
                employee_claim = ClaimFactory.create(
                    employer=employer, employee=employee, claim_type_id=1,
                )
                other_employee_claim = ClaimFactory.create(
                    employer=other_employer,
                    employee=other_employee,
                    claim_type_id=1,
                    created_at=factory.Faker(
                        "date_between_dates",
                        date_start=date(2021, 1, 1),
                        date_end=date(2021, 1, 15),
                    ),
                )
                ManagedRequirementFactory.create(
                    claim=employee_claim,
                    managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                )
                ManagedRequirementFactory.create(
                    claim=other_employee_claim,
                    managed_requirement_status_id=ManagedRequirementStatus.SUPPRESSED.managed_requirement_status_id,
                )
                AbsencePeriodFactory.create(
                    claim=employee_claim,
                    absence_period_start_date=date.today() + timedelta(days=5),
                    absence_period_end_date=date.today() + timedelta(days=20),
                    leave_request_decision_id=i + 1,
                )
                AbsencePeriodFactory.create(
                    claim=other_employee_claim,
                    absence_period_start_date=date.today() + timedelta(days=5),
                    absence_period_end_date=date.today() + timedelta(days=20),
                    leave_request_decision_id=LeaveRequestDecision.WITHDRAWN.leave_request_decision_id,
                )

            self.claims_count = 10
            test_db_session.commit()

        def _perform_api_call(self, request, client, employer_auth_token):
            query_string = "&".join([f"{key}={value}" for key, value in request.items()])
            return client.get(
                f"/v1/claims?{query_string}",
                headers={"Authorization": f"Bearer {employer_auth_token}"},
            )

        @pytest.mark.parametrize(
            "is_reviewable, request_decision, expected_output_len",
            [
                ["yes", "approved", 1],
                ["no", "approved", 0],
                ["no", "pending", 0],
                ["yes", "pending", 2],
            ],
        )
        def test_get_claims_is_reviewable_and_request_decision_filter(
            self, is_reviewable, request_decision, expected_output_len, client, employer_auth_token
        ):
            params = {"is_reviewable": is_reviewable, "request_decision": request_decision}
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == expected_output_len

        def test_get_claims_filter_by_request_decision_with_search(
            self, client, employer_auth_token, other_employee
        ):
            params = {
                "request_decision": "withdrawn",
                "search": other_employee.first_name,
                "order_by": "employee",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == 5

        def test_get_claims_filter_by_request_decision_with_search_no_result(
            self, client, employer_auth_token, other_employee
        ):
            params = {
                "request_decision": "approved",
                "search": other_employee.first_name,
                "order_by": "employee",
            }
            resp = self._perform_api_call(params, client, employer_auth_token)
            assert resp.status_code == 200
            response_body = resp.get_json()
            data = response_body.get("data", [])
            assert len(data) == 0

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


class TestEmployerWithOrgUnitsAccess:
    """
    This class groups the tests that ensure that the user leave administrators of employers
    that use organization units can only access claims of an organization unit they service
    """

    @pytest.fixture()
    def employer(self):
        employer = EmployerFactory.create(employer_fein="112222222")
        return employer

    @pytest.fixture()
    def user_leave_admin(self, employer_user, employer, test_verification):
        return UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )

    @pytest.fixture()
    def non_leave_admin_org_unit(self, employer):
        organization_unit = OrganizationUnitFactory.create(employer=employer)
        return organization_unit

    @pytest.fixture
    def leave_admin_org_unit(self, test_db_session, employer, user_leave_admin):
        test_db_session.add(user_leave_admin)
        test_db_session.commit()
        org_unit = OrganizationUnitFactory.create(employer=employer)
        la_org_unit = UserLeaveAdministratorOrgUnit(
            user_leave_administrator_id=user_leave_admin.user_leave_administrator_id,
            organization_unit_id=org_unit.organization_unit_id,
        )
        test_db_session.add(la_org_unit)
        test_db_session.commit()
        return org_unit

    @pytest.fixture
    def leave_admin_invalid_org_unit(
        self, test_db_session, employer, user_leave_admin, non_leave_admin_org_unit
    ):
        test_db_session.add(user_leave_admin)
        test_db_session.commit()
        OrganizationUnitFactory.create(employer=employer)
        org_unit = OrganizationUnitFactory.create(employer=employer, fineos_id=None)
        la_org_unit = UserLeaveAdministratorOrgUnit(
            user_leave_administrator_id=user_leave_admin.user_leave_administrator_id,
            organization_unit_id=org_unit.organization_unit_id,
        )
        test_db_session.add(la_org_unit)
        test_db_session.commit()
        return org_unit

    @pytest.fixture
    def claim_with_same_org_unit(self, leave_admin_org_unit):
        claim = ClaimFactory.create(
            employer_id=leave_admin_org_unit.employer_id, organization_unit=leave_admin_org_unit,
        )
        return claim

    @pytest.fixture
    def claim_with_different_org_unit(self, leave_admin_org_unit, non_leave_admin_org_unit):
        claim = ClaimFactory.create(
            employer_id=non_leave_admin_org_unit.employer_id,
            organization_unit=non_leave_admin_org_unit,
        )
        return claim

    @pytest.fixture
    def claim_with_invalid_org_unit(self, leave_admin_invalid_org_unit):
        claim = ClaimFactory.create(
            employer_id=leave_admin_invalid_org_unit.employer_id,
            organization_unit=leave_admin_invalid_org_unit,
        )
        return claim

    def test_employers_cannot_access_claim_without_claims_organization_unit(
        self, client, employer_auth_token, claim_with_different_org_unit
    ):
        response = client.get(
            f"/v1/employers/claims/{claim_with_different_org_unit.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "The leave admin cannot access claims of this organization unit"
        )

    def test_employers_cannot_access_claim_with_invalid_organization_unit(
        self, client, employer_auth_token, claim_with_invalid_org_unit
    ):
        response = client.get(
            f"/v1/employers/claims/{claim_with_invalid_org_unit.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "The leave admin cannot access claims of this organization unit"
        )

    def test_employers_can_access_claim_with_claims_organization_unit(
        self, client, employer_auth_token, claim_with_same_org_unit
    ):
        response = client.get(
            f"/v1/employers/claims/{claim_with_same_org_unit.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200

    def test_employers_cannot_view_claims_not_in_their_organization_units(
        self, client, employer_auth_token, claim_with_same_org_unit, non_leave_admin_org_unit,
    ):
        generated_claims = ClaimFactory.create_batch(
            size=3,
            employer=claim_with_same_org_unit.employer,
            employee=claim_with_same_org_unit.employee,
            organization_unit=non_leave_admin_org_unit,
            fineos_absence_status_id=1,
            claim_type_id=1,
        )

        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == 1
        assert claim_data[0].get("fineos_absence_id") not in [
            c.fineos_absence_id for c in generated_claims
        ]
        assert claim_data[0].get("fineos_absence_id") == claim_with_same_org_unit.fineos_absence_id

        # POST /claims/search
        response = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {employer_auth_token}"}, json={}
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == 1
        assert claim_data[0].get("fineos_absence_id") not in [
            c.fineos_absence_id for c in generated_claims
        ]
        assert claim_data[0].get("fineos_absence_id") == claim_with_same_org_unit.fineos_absence_id

    def test_employers_cannot_view_claims_with_invalid_organization_unit(
        self, client, employer_auth_token, claim_with_invalid_org_unit
    ):
        generated_claims = [claim_with_invalid_org_unit]
        generated_claims.extend(
            ClaimFactory.create_batch(
                size=3,
                employer=claim_with_invalid_org_unit.employer,
                employee=claim_with_invalid_org_unit.employee,
                organization_unit=claim_with_invalid_org_unit.organization_unit,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )
        )
        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == 0

        # POST /claims/search
        response = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {employer_auth_token}"}, json={}
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == 0

    def test_employers_can_view_claims_with_their_organization_units(
        self, client, employer_auth_token, claim_with_same_org_unit,
    ):
        generated_claims = [claim_with_same_org_unit]
        generated_claims.extend(
            ClaimFactory.create_batch(
                size=3,
                employer=claim_with_same_org_unit.employer,
                employee=claim_with_same_org_unit.employee,
                organization_unit=claim_with_same_org_unit.organization_unit,
                fineos_absence_status_id=1,
                claim_type_id=1,
            )
        )

        # GET /claims deprecated
        response = client.get(
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == len(generated_claims)

        # POST /claims/search
        response = client.post(
            "/v1/claims/search", headers={"Authorization": f"Bearer {employer_auth_token}"}, json={}
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == len(generated_claims)

    def test_employers_cannot_get_documents_without_claims_organization_unit(
        self, client, employer_auth_token, claim_with_different_org_unit
    ):
        request_params = GetClaimDocumentsRequestParams(
            claim_with_different_org_unit.fineos_absence_id, employer_auth_token
        )
        response = get_documents(client, request_params)
        assert response.status_code == 403

    def test_employers_cannot_get_documents_with_invalid_organization_unit(
        self, client, employer_auth_token, claim_with_invalid_org_unit
    ):
        request_params = GetClaimDocumentsRequestParams(
            claim_with_invalid_org_unit.fineos_absence_id, employer_auth_token
        )
        response = get_documents(client, request_params)
        assert response.status_code == 403

    def test_employers_can_get_documents_with_claims_organization_unit(
        self, client, employer_auth_token, claim_with_same_org_unit
    ):
        request_params = GetClaimDocumentsRequestParams(
            claim_with_same_org_unit.fineos_absence_id, employer_auth_token
        )
        response = get_documents(client, request_params)
        assert response.status_code == 200

    def test_employers_cannot_download_documents_without_claims_organization_unit(
        self, client, employer_auth_token, claim_with_different_org_unit
    ):
        request_params = EmployerDocumentDownloadRequestParams(
            claim_with_different_org_unit.fineos_absence_id, "doc_id", employer_auth_token
        )
        response = download_document(client, request_params)
        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "The leave admin cannot access claims of this organization unit"
        )

    def test_employers_cannot_download_documents_with_invalid_organization_unit(
        self, client, employer_auth_token, claim_with_invalid_org_unit
    ):
        request_params = EmployerDocumentDownloadRequestParams(
            claim_with_invalid_org_unit.fineos_absence_id, "doc_id", employer_auth_token
        )
        response = download_document(client, request_params)
        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "The leave admin cannot access claims of this organization unit"
        )

    @mock.patch("massgov.pfml.api.claims.download_document_as_leave_admin")
    def test_employers_can_download_documents_with_claims_organization_unit(
        self, mock_download, document_data, client, employer_auth_token, claim_with_same_org_unit,
    ):
        mock_download.return_value = document_data
        request_params = EmployerDocumentDownloadRequestParams(
            claim_with_same_org_unit.fineos_absence_id, "doc_id", employer_auth_token
        )
        response = download_document(client, request_params)
        assert response.status_code == 200

    def test_employers_cannot_update_claim_without_claims_organization_unit(
        self, client, claim_with_different_org_unit, employer_auth_token, update_claim_body,
    ):
        response = client.patch(
            f"/v1/employers/claims/{claim_with_different_org_unit.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )
        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "The leave admin cannot access claims of this organization unit"
        )

    def test_employers_cannot_update_claim_with_invalid_organization_unit(
        self, client, claim_with_invalid_org_unit, employer_auth_token, update_claim_body,
    ):
        response = client.patch(
            f"/v1/employers/claims/{claim_with_invalid_org_unit.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )
        assert response.status_code == 403
        assert (
            response.get_json()["message"]
            == "The leave admin cannot access claims of this organization unit"
        )

    @mock.patch(
        "massgov.pfml.api.claims.claim_rules.get_employer_claim_review_issues", return_value=[]
    )
    def test_employers_can_update_claim_with_claims_organization_unit(
        self,
        mock_get_issues,
        client,
        claim_with_same_org_unit,
        employer_auth_token,
        update_claim_body,
    ):
        response = client.patch(
            f"/v1/employers/claims/{claim_with_same_org_unit.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=update_claim_body,
        )
        assert response.status_code == 200


class TestClaimsHelpers:
    @pytest.mark.parametrize(
        "request_decision_param, expected_output",
        [
            ["approved", set([LeaveRequestDecision.APPROVED.leave_request_decision_id])],
            ["denied", set([LeaveRequestDecision.DENIED.leave_request_decision_id])],
            ["withdrawn", set([LeaveRequestDecision.WITHDRAWN.leave_request_decision_id])],
            [
                "pending",
                set(
                    [
                        LeaveRequestDecision.PENDING.leave_request_decision_id,
                        LeaveRequestDecision.IN_REVIEW.leave_request_decision_id,
                        LeaveRequestDecision.PROJECTED.leave_request_decision_id,
                    ]
                ),
            ],
            [
                "cancelled",
                set(
                    [
                        LeaveRequestDecision.CANCELLED.leave_request_decision_id,
                        LeaveRequestDecision.VOIDED.leave_request_decision_id,
                    ]
                ),
            ],
            [None, set()],
        ],
    )
    def test_map_request_decision_param_to_db_columns(
        self, request_decision_param, expected_output
    ):
        assert map_request_decision_param_to_db_columns(request_decision_param) == expected_output


class TestReviewByFilter:
    @pytest.fixture
    def employer(self):
        return EmployerFactory.create()

    @pytest.fixture
    def employee(self):
        return EmployeeFactory.create()

    @pytest.fixture
    def review_by_claims(self, employer, employee):
        # Approved claim with open managed requirements i.e review by
        claims = []
        for _ in range(30):
            claim = ClaimFactory.create(
                employer=employer,
                employee=employee,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                claim_type_id=1,
            )
            claims.append(claim)
            ManagedRequirementFactory.create(
                claim=claim,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                follow_up_date=date.today() + timedelta(days=5),
            )
            ManagedRequirementFactory.create(
                claim=claim,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.SUPPRESSED.managed_requirement_status_id,
                follow_up_date=date.today() + timedelta(days=5),
            )
            ManagedRequirementFactory.create(
                claim=claim,
                managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
                managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
                follow_up_date=date.today() + timedelta(days=5),
            )
        return claims

    @pytest.fixture
    def no_action_claim(self, employer, employee):
        # Approved claim with completed managed requirements
        claim_no_action = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
            claim_type_id=1,
        )
        ManagedRequirementFactory.create(
            claim=claim_no_action,
            managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
            managed_requirement_status_id=ManagedRequirementStatus.COMPLETE.managed_requirement_status_id,
            follow_up_date=date.today() + timedelta(days=10),
        )
        return claim_no_action

    @pytest.fixture
    def expired_requirements_claim(self, employer, employee):
        # Approved claim with expired managed requirements
        claim_expired = ClaimFactory.create(
            employer=employer,
            employee=employee,
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
            claim_type_id=1,
        )
        ManagedRequirementFactory.create(
            claim=claim_expired,
            managed_requirement_type_id=ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
            managed_requirement_status_id=ManagedRequirementStatus.OPEN.managed_requirement_status_id,
            follow_up_date=date.today() - timedelta(days=2),
        )
        return claim_expired

    @pytest.fixture(autouse=True)
    def load_test_db(
        self,
        employer,
        employer_user,
        test_verification,
        test_db_session,
        review_by_claims,
        no_action_claim,
        expired_requirements_claim,
    ):
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()

    def _assert_only_approved_claims_with_open_requirements(
        self, response, status_code, expected_claims
    ):
        expected_claims_fineos_absence_id = [claim.fineos_absence_id for claim in expected_claims]
        assert response.status_code == status_code
        response_body = response.get_json()
        for claim in response_body.get("data", []):
            assert claim["claim_status"] == "Approved"
            managed_requirements = claim.get("managed_requirements", None)
            assert len([req for req in managed_requirements if req["status"] == "Open"]) == 1
            fineos_absence_id = claim.get("fineos_absence_id", None)
            assert fineos_absence_id in expected_claims_fineos_absence_id

    def test_review_by_filter(
        self, client, employer_auth_token, review_by_claims,
    ):
        resp = client.get(
            "/v1/claims?claim_status=Open+requirement",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        self._assert_only_approved_claims_with_open_requirements(
            resp, status_code=200, expected_claims=review_by_claims
        )

        post_body = {"claim_status": "Open requirement"}
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json=post_body,
        )
        self._assert_only_approved_claims_with_open_requirements(
            response, status_code=200, expected_claims=review_by_claims
        )


class TestPostChangeRequest:
    @pytest.fixture
    def request_body(self) -> Dict[str, str]:
        return {
            "change_request_type": "Modification",
            "start_date": "2022-01-01",
            "end_date": "2022-02-01",
        }

    @freeze_time("2022-02-22")
    @mock.patch("massgov.pfml.api.services.claims.add_change_request_to_db")
    @mock.patch("massgov.pfml.api.claims.claim_rules.get_change_request_issues", return_value=[])
    @mock.patch("massgov.pfml.api.claims.get_claim_from_db")
    def test_successful_call(
        self,
        mock_get_claim,
        mock_change_request_issues,
        mock_add_change,
        auth_token,
        claim,
        client,
        request_body,
    ):
        submitted_time = datetime_util.utcnow()
        mock_add_change.return_value = submitted_time
        mock_get_claim.return_value = claim
        response = client.post(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_body,
        )
        response_body = response.get_json().get("data")
        assert response.status_code == 201
        assert response_body.get("change_request_type") == request_body["change_request_type"]
        assert response_body.get("fineos_absence_id") == claim.fineos_absence_id
        assert response_body.get("start_date") == request_body["start_date"]
        assert response_body.get("end_date") == request_body["end_date"]
        assert response_body.get("end_date") == request_body["end_date"]
        assert response_body.get("submitted_time") == str(submitted_time.isoformat())

    @mock.patch("massgov.pfml.api.claims.claim_rules.get_change_request_issues", return_value=[])
    @mock.patch("massgov.pfml.api.claims.get_claim_from_db", return_value=None)
    def test_missing_claim(
        self, mock_get_claim, mock_change_request_issues, auth_token, claim, client, request_body,
    ):
        response = client.post(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_body,
        )
        assert response.status_code == 404
        assert response.get_json()["message"] == "Claim does not exist for given absence ID"

    @mock.patch("massgov.pfml.api.claims.get_claim_from_db")
    def test_validation_issues(self, mock_get_claim, auth_token, claim, client, request_body):
        claim.absence_period_start_date = date(2021, 1, 1)
        claim.fineos_absence_status_id = 1
        mock_get_claim.return_value = claim
        del request_body["end_date"]
        response = client.post(
            "/v1/change-request?fineos_absence_id={}".format(claim.fineos_absence_id),
            headers={"Authorization": f"Bearer {auth_token}"},
            json=request_body,
        )
        assert response.status_code == 400
        assert response.get_json()["message"] == "Invalid change request body"
