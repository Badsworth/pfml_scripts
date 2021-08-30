from datetime import date, timedelta
from unittest import mock

import pytest

from massgov.pfml.api.models.notifications.requests import NotificationRequest
from massgov.pfml.api.services.managed_requirements import (
    get_fineos_managed_requirements_from_notification,
)
from massgov.pfml.db.models.employees import (
    Claim,
    ManagedRequirement,
    ManagedRequirementCategory,
    ManagedRequirementStatus,
    ManagedRequirementType,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployerFactory,
    ManagedRequirementFactory,
)
from massgov.pfml.db.queries.managed_requirements import (
    create_managed_requirement_from_fineos,
    get_managed_requirement_by_fineos_managed_requirement_id,
    update_managed_requirement_from_fineos,
)
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails

# every test in here requires real resources
pytestmark = pytest.mark.integration


leave_admin_body = {
    "absence_case_id": "NTN-111-ABS-01",
    "document_type": "Approval Notice",
    "fein": "71-6779225",
    "organization_name": "Wayne Enterprises",
    "trigger": "Designation Notice",
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


@pytest.fixture
def employer():
    return EmployerFactory.create(employer_fein="716779225")


class TestManagedRequirementQuery:
    @classmethod
    def managed_requirement(cls):
        return {
            "managedReqId": 100,
            "status": ManagedRequirementStatus.get_description(1),
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

    @pytest.fixture
    def claim(self, employer):
        return ClaimFactory.create(
            employer_id=employer.employer_id, fineos_absence_id=leave_admin_body["absence_case_id"],
        )

    @pytest.fixture
    def fineos_managed_requirement(self):
        return ManagedRequirementDetails.parse_obj(self.managed_requirement())

    def _assert_managed_requirement_data(
        self,
        claim: Claim,
        managed_requirement: ManagedRequirement,
        fineos_managed_requirement: ManagedRequirementDetails,
    ):
        assert managed_requirement is not None
        assert str(managed_requirement.claim_id) == str(claim.claim_id)
        assert managed_requirement.fineos_managed_requirement_id == str(
            fineos_managed_requirement.managedReqId
        )
        assert managed_requirement.follow_up_date == fineos_managed_requirement.followUpDate
        assert (
            managed_requirement.managed_requirement_status.managed_requirement_status_description
            == fineos_managed_requirement.status
        )

    def test_create_managed_requirement_from_fineos(
        self, client, test_db_session, claim, fineos_managed_requirement
    ):
        create_managed_requirement_from_fineos(
            test_db_session, claim.claim_id, fineos_managed_requirement, {}
        )
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )
        self._assert_managed_requirement_data(
            claim, managed_requirement, fineos_managed_requirement
        )

    def test_update_managed_requirement_from_fineos(
        self, client, test_db_session, claim, fineos_managed_requirement
    ):
        db_requirement = create_managed_requirement_from_fineos(
            test_db_session, claim.claim_id, fineos_managed_requirement, {}
        )

        # create existing managed requirements in db not in sync with fineos managed requirements
        fineos_managed_requirement.followUpDate = date.today() + timedelta(days=7)
        fineos_managed_requirement.status = ManagedRequirementStatus.get_description(2)
        update_managed_requirement_from_fineos(
            test_db_session, fineos_managed_requirement, db_requirement, {}
        )

        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_requirement.managedReqId, test_db_session
        )

        self._assert_managed_requirement_data(
            claim, managed_requirement, fineos_managed_requirement
        )

    def test_get_managed_requirement_by_fineos_managed_requirement_id(
        self, client, test_db_session, claim
    ):
        fineos_managed_req_id = ManagedRequirementFactory.create().fineos_managed_requirement_id
        ManagedRequirementFactory.create()
        test_db_session.commit()
        managed_requirement = get_managed_requirement_by_fineos_managed_requirement_id(
            fineos_managed_req_id, test_db_session
        )
        assert managed_requirement is not None
        assert int(managed_requirement.fineos_managed_requirement_id) == fineos_managed_req_id

    @mock.patch("massgov.pfml.fineos.mock_client.MockFINEOSClient.get_managed_requirements")
    def test_get_fineos_managed_requirements_from_notification(
        self, mock_get_req, client, fineos_managed_requirement
    ):
        mock_get_req.return_value = [fineos_managed_requirement]
        managed_requirements = get_fineos_managed_requirements_from_notification(
            NotificationRequest(**leave_admin_body), {}
        )
        assert len(managed_requirements) == 1
