"""
Tests for /employers/claims endpoints
"""
import copy
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List
from unittest import mock

import pytest
from freezegun import freeze_time

import massgov.pfml.fineos.mock_client
import tests.api
from massgov.pfml.api.authorization.exceptions import NotAuthorizedForAccess
from massgov.pfml.api.exceptions import ObjectNotFound
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail
from massgov.pfml.db.models.absences import AbsencePeriodType
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    Claim,
    ManagedRequirement,
    ManagedRequirementCategory,
    ManagedRequirementStatus,
    ManagedRequirementType,
    UserLeaveAdministrator,
    UserLeaveAdministratorOrgUnit,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    ManagedRequirementFactory,
    OrganizationUnitFactory,
    TaxIdentifierFactory,
    VerificationFactory,
)
from massgov.pfml.db.queries.absence_periods import (
    split_fineos_absence_period_id,
    upsert_absence_period_from_fineos_period,
)
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
)
from massgov.pfml.fineos import models
from massgov.pfml.fineos.mock_client import MockFINEOSClient
from massgov.pfml.fineos.models.customer_api import AbsenceDetails
from massgov.pfml.fineos.models.group_client_api import (
    Base64EncodedFileData,
    ManagedRequirementDetails,
    PeriodDecisions,
)


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


def download_document(client, params):
    return client.get(
        f"/v1/employers/claims/{params.absence_id}/documents/{params.document_id}",
        headers={"Authorization": f"Bearer {params.auth_token}"},
    )


def get_documents(client, params):
    return client.get(
        f"/v1/employers/claims/{params.absence_id}/documents",
        headers={"Authorization": f"Bearer {params.auth_token}"},
    )


# testing class for employer_get_claim_documents
@dataclass
class GetClaimDocumentsRequestParams:
    absence_id: str
    auth_token: str


# testing class for employer_document_download
@dataclass
class EmployerDocumentDownloadRequestParams:
    absence_id: str
    document_id: str
    auth_token: str


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


class TestEmployerGetClaimDocuments:
    @pytest.fixture
    def test_verification(self):
        return VerificationFactory.create()

    @pytest.fixture
    def employer(self):
        return EmployerFactory.create()

    @pytest.fixture
    def user_leave_admin(self, employer_user, employer, test_verification, test_db_session):
        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(leave_admin)
        test_db_session.commit()

    def test_non_employers_cannot_access(self, client, auth_token, claim):

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 403

    def test_employers_receive_200(self, client, claim, employer_auth_token, user_leave_admin):
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/documents",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response.status_code == 200


class TestGetClaimReview:
    @pytest.fixture
    def test_verification(self):
        return VerificationFactory.create()

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

    def test_claim_employee_relationship_added_if_missing(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create(employer_fein="999999999", employer_dba="Acme Co")
        tax_identifier = TaxIdentifierFactory.create(tax_identifier="123121234")
        employee = EmployeeFactory.create()
        employee.tax_identifier = tax_identifier
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        claim.employee_id = None
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(link)
        test_db_session.commit()
        assert claim.employee_id is None
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        post_call_claim = test_db_session.query(Claim).one_or_none()
        assert post_call_claim.employee_id is not None
        assert post_call_claim.employee_id == employee.employee_id
        assert response.status_code == 200

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
            headers={"Authorization": f"Bearer {employer_auth_token}"},
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
                )
            ]

        monkeypatch.setattr(
            MockFINEOSClient, "get_managed_requirements", patched_managed_requirements
        )

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response.status_code == 200

    @freeze_time("2020-12-07")
    def test_employers_with_int_hours_worked_per_week_receive_200_from_get_claim_review(
        self, client, employer_user, employer_auth_token, test_db_session, test_verification
    ):
        employer = EmployerFactory.create(employer_fein="999999999", employer_dba="Acme Co")
        ClaimFactory.create(
            employer_id=employer.employer_id, fineos_absence_id="int_fake_hours_worked_per_week"
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

    def test_employers_receive_proper_claim_using_correct_fineos_web_id(
        self,
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
    def open_managed_requirements(self):
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
                "status": "Open",
                "subjectPartyName": "Fake Name",
                "sourceOfInfoPartyName": "Fake Sourcee",
                "creationDate": date(2020, 1, 1),
                "dateSuppressed": date(2020, 3, 1),
            },
        ]

    @pytest.fixture
    def fineos_managed_requirements(self, managed_requirements):
        return [ManagedRequirementDetails.parse_obj(mr) for mr in managed_requirements]

    @pytest.fixture
    def fineos_open_managed_requirements(self, open_managed_requirements):
        return [ManagedRequirementDetails.parse_obj(mr) for mr in open_managed_requirements]

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
        caplog,
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
    def test_employer_get_claim_review_create_managed_requirements_log_db_managed_requirements_not_in_fineos(
        self,
        mock_get_req,
        fineos_managed_requirements,
        client,
        caplog,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
    ):
        mock_get_req.return_value = fineos_managed_requirements[1:]
        employer = EmployerFactory.create()
        claim = ClaimFactory.create(employer_id=employer.employer_id)
        link = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        db_mr = create_managed_requirement_from_fineos(
            test_db_session, claim.claim_id, fineos_managed_requirements[0]
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
        assert (
            "Claim has managed requirements not present in the data received from fineos."
            in caplog.text
        )

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_employer_get_claim_review_create_managed_requirements_and_log_multiple_open_managed_requirements(
        self,
        mock_get_req,
        fineos_open_managed_requirements,
        client,
        caplog,
        employer_user,
        employer_auth_token,
        test_db_session,
        test_verification,
    ):
        mock_get_req.return_value = fineos_open_managed_requirements
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
        assert len(requirements) == len(fineos_open_managed_requirements)
        for db_mr in requirements:
            searched_mr = [
                m
                for m in fineos_open_managed_requirements
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
        assert "Multiple open managed requirements were found." in caplog.text

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
    def mock_absence_details(self, absence_id):
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
    def mock_customer_absence_details(self, mock_absence_details):
        # Our claim review endpoint uses a mixture of decisions and periods at
        # the moment, and we want their data to be consistent.
        return {
            "absenceId": mock_absence_details["decisions"][0]["absence"]["id"],
            "absencePeriods": [
                {
                    "absenceType": decision["period"]["type"],
                    "id": decision["period"]["periodReference"],
                    "startDate": decision["period"]["startDate"],
                    "endDate": decision["period"]["endDate"],
                    "status": decision["period"]["status"],
                    "reason": decision["period"]["leaveRequest"]["reasonName"],
                    "reasonQualifier1": decision["period"]["leaveRequest"]["qualifier1"],
                    "reasonQualifier2": decision["period"]["leaveRequest"]["qualifier2"],
                    "requestStatus": decision["period"]["leaveRequest"]["decisionStatus"],
                }
                for decision in mock_absence_details["decisions"]
            ],
        }

    @pytest.fixture
    def mock_period_decisions_create(self, mock_absence_details):
        return PeriodDecisions.parse_obj(mock_absence_details)

    @pytest.fixture
    def mock_absence_details_create(self, mock_customer_absence_details):
        return AbsenceDetails.parse_obj(mock_customer_absence_details)

    @pytest.fixture
    def mock_absence_details_no_decisions(self, mock_absence_details):
        empty_decisions = mock_absence_details.copy()
        empty_decisions["decisions"] = []
        return PeriodDecisions.parse_obj(empty_decisions)

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
        period_id = period.id.split("-")
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
            == period.requestStatus
        )

    def _assert_no_absence_period_data_for_claim(self, test_db_session, claim):
        db_periods = (
            test_db_session.query(AbsencePeriod)
            .join(Claim)
            .filter(Claim.claim_id == claim.claim_id)
            .all()
        )
        assert len(db_periods) == 0

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_raises_withdrawn_claim_when_no_decisions(
        self,
        mock_get_decisions,
        test_db_session,
        client,
        employer_auth_token,
        mock_absence_details_no_decisions,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        mock_get_decisions.return_value = mock_absence_details_no_decisions
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 403
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
    def test_employer_get_claim_review_returns_and_creates_absence_period(
        self,
        mock_get_absence,
        mock_get_decisions,
        mock_absence_details_create,
        mock_period_decisions_create,
        test_db_session,
        client,
        employer_auth_token,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)

        mock_get_decisions.return_value = mock_period_decisions_create
        mock_get_absence.return_value = mock_absence_details_create

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        absence_period_responses = response.get_json()["data"]["absence_periods"]
        expected_fineos_absence_periods = mock_absence_details_create.dict()["absencePeriods"]

        assert len(absence_period_responses) == 2
        assert absence_period_responses[0]["reason"] == expected_fineos_absence_periods[0]["reason"]
        assert absence_period_responses[1]["reason"] == expected_fineos_absence_periods[1]["reason"]

        for period in mock_absence_details_create.absencePeriods:
            self._assert_absence_period_data(test_db_session, claim, period)

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_withdrawn_claim_no_absence_period_decisions(
        self, mock_get_decisions, client, employer_auth_token, claim
    ):
        mock_get_decisions.return_value = PeriodDecisions()
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response.status_code == 403

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence")
    def test_employer_get_claim_review_updates_absence_period(
        self,
        mock_get_absence,
        mock_get_decisions,
        mock_absence_details_create,
        mock_period_decisions_create,
        test_db_session,
        client,
        employer_auth_token,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        for absence_period in mock_absence_details_create.absencePeriods:
            stale_absence_period = absence_period.copy()
            stale_absence_period.requestStatus = None

            upsert_absence_period_from_fineos_period(
                test_db_session, claim.claim_id, absence_period, {}
            )

        mock_get_decisions.return_value = mock_period_decisions_create
        mock_get_absence.return_value = mock_absence_details_create

        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )

        assert response.status_code == 200
        for absence_period in mock_absence_details_create.absencePeriods:
            self._assert_absence_period_data(test_db_session, claim, absence_period)

    @mock.patch("massgov.pfml.api.employer_claim.sync_customer_api_absence_periods_to_db")
    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_review_creates_absence_period_failure(
        self,
        mock_get_decisions,
        mock_sync_customer_api_absence_periods_to_db,
        test_db_session,
        client,
        mock_period_decisions_create,
        employer_auth_token,
        claim,
    ):
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)
        mock_sync_customer_api_absence_periods_to_db.side_effect = Exception("Unexpected failure")
        mock_get_decisions.return_value = mock_period_decisions_create
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        assert response.status_code == 500  # err is 500 b/c exception bubbles up
        self._assert_no_absence_period_data_for_claim(test_db_session, claim)

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_absence_period_decisions")
    def test_employer_get_claim_returns_absence_periods_from_fineos(
        self, mock_get_decisions, client, employer_auth_token, mock_period_decisions_create, claim
    ):
        mock_get_decisions.return_value = mock_period_decisions_create
        response = client.get(
            f"/v1/employers/claims/{claim.fineos_absence_id}/review",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
        )
        response_data = response.get_json()["data"]
        absence_periods = response_data["absence_periods"]
        assert response.status_code == 200
        periods = [decision.period for decision in mock_period_decisions_create.decisions]
        for fineos_period_data, absence_data in zip(periods, absence_periods):
            class_id, index_id = split_fineos_absence_period_id(fineos_period_data.periodReference)
            assert absence_data["fineos_leave_request_id"] is None
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


class TestEmployerWithOrgUnitsAccess:
    """
    This class groups the tests that ensure that the user leave administrators of employers
    that use organization units can only access claims of an organization unit they service
    """

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
    def test_verification(self):
        return VerificationFactory.create()

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
            employer_id=leave_admin_org_unit.employer_id, organization_unit=leave_admin_org_unit
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
        self, client, employer_auth_token, claim_with_same_org_unit, non_leave_admin_org_unit
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
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
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
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json={"terms": {}},
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
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == 0

        # POST /claims/search
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json={"terms": {}},
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == 0

    def test_employers_can_view_claims_with_their_organization_units(
        self, client, employer_auth_token, claim_with_same_org_unit
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
            "/v1/claims", headers={"Authorization": f"Bearer {employer_auth_token}"}
        )

        response_body = response.get_json()
        claim_data = response_body.get("data")
        assert response.status_code == 200
        assert len(claim_data) == len(generated_claims)

        # POST /claims/search
        response = client.post(
            "/v1/claims/search",
            headers={"Authorization": f"Bearer {employer_auth_token}"},
            json={"terms": {}},
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

    @mock.patch("massgov.pfml.api.employer_claim.download_document_as_leave_admin")
    def test_employers_can_download_documents_with_claims_organization_unit(
        self, mock_download, document_data, client, employer_auth_token, claim_with_same_org_unit
    ):
        mock_download.return_value = document_data
        request_params = EmployerDocumentDownloadRequestParams(
            claim_with_same_org_unit.fineos_absence_id, "doc_id", employer_auth_token
        )
        response = download_document(client, request_params)
        assert response.status_code == 200

    def test_employers_cannot_update_claim_without_claims_organization_unit(
        self, client, claim_with_different_org_unit, employer_auth_token, update_claim_body
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
        self, client, claim_with_invalid_org_unit, employer_auth_token, update_claim_body
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
        "massgov.pfml.api.employer_claim.claim_rules.get_employer_claim_review_issues",
        return_value=[],
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


class TestUpdateClaim:
    @pytest.fixture
    def test_verification(self):
        return VerificationFactory.create()

    @pytest.fixture
    def employer(self):
        return EmployerFactory.create()

    @pytest.fixture
    def user_leave_admin(self, employer_user, employer, test_verification, test_db_session):
        leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
        test_db_session.add(leave_admin)
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

    @mock.patch("massgov.pfml.api.employer_claim.logger.info")
    @mock.patch(
        "massgov.pfml.api.employer_claim.claim_rules.get_employer_claim_review_issues",
        return_value=[],
    )
    def test_employer_update_claim_review_success_case(
        self,
        mock_get_issues,
        mock_info_logger,
        employer_auth_token,
        claim,
        client,
        update_claim_body,
        user_leave_admin,
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

    @mock.patch("massgov.pfml.api.employer_claim.claim_rules.get_employer_claim_review_issues")
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
        self, client, employer_auth_token, update_claim_body, claim
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
        self, client, employer_auth_token, claim, user_leave_admin
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


class TestEmployerDocumentDownload:
    @pytest.fixture
    def test_verification(self):
        return VerificationFactory.create()

    @pytest.fixture
    def user_leave_admin(self, employer_user, employer, test_verification, test_db_session):
        user_leave_admin = UserLeaveAdministrator(
            user_id=employer_user.user_id,
            employer_id=employer.employer_id,
            fineos_web_id="fake-fineos-web-id",
            verification=test_verification,
        )
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

    @mock.patch("massgov.pfml.api.employer_claim.download_document_as_leave_admin")
    def test_employers_receive_200(
        self, mock_download, document_data, client, request_params, user_leave_admin
    ):
        mock_download.return_value = document_data

        response = download_document(client, request_params)
        assert response.status_code == 200

    @mock.patch("massgov.pfml.api.employer_claim.download_document_as_leave_admin")
    def test_cannot_download_documents_not_attached_to_absence(
        self, mock_download, client, request_params, caplog, user_leave_admin
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

    @mock.patch("massgov.pfml.api.employer_claim.download_document_as_leave_admin")
    def test_cannot_download_non_downloadable_doc_types(
        self, mock_download, client, request_params, caplog, user_leave_admin
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


class TestClaimReviewUpdatesManagedRequirements:
    @pytest.fixture
    def test_verification(self):
        return VerificationFactory.create()

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
    def complete_valid_fineos_managed_requirement(self, fineos_man_req):
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
        mock_get_managed_requirements.return_value = [wrong_type_invalid_fineos_managed_requirement]

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
            employer_id=employer.employer_id, fineos_absence_id="NTN-CASE-WITHOUT-OUTSTANDING-INFO"
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
            employer_id=employer.employer_id, fineos_absence_id="NTN-CASE-WITHOUT-OUTSTANDING-INFO"
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
            )
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
