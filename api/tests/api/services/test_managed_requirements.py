from datetime import date, timedelta

import pytest

from massgov.pfml.api.services.managed_requirements import update_employer_confirmation_requirements
from massgov.pfml.db.models.employees import (
    ManagedRequirementCategory,
    ManagedRequirementStatus,
    ManagedRequirementType,
    UserLeaveAdministrator,
)
from massgov.pfml.db.models.factories import (
    EmployerFactory,
    ManagedRequirementFactory,
    VerificationFactory,
)
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails


# Run `initialize_factories_session` for all tests,
# so that it doesn't need to be manually included
@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


@pytest.fixture
def test_verification():
    return VerificationFactory.create()


@pytest.fixture
def employer():
    return EmployerFactory.create()


@pytest.fixture
def user_leave_admin(employer_user, employer, test_verification):
    return UserLeaveAdministrator(
        user_id=employer_user.user_id,
        employer_id=employer.employer_id,
        fineos_web_id="fake-fineos-web-id",
        verification=test_verification,
    )


class TestManagedRequirementService:
    @pytest.fixture
    def fineos_man_req(self):
        def _fineos_managed_requirement(managed_req_id=None, status=None, type=None):
            man_req = ManagedRequirementFactory.create()

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
    def man_req_status_open(self):
        return ManagedRequirementStatus.OPEN.managed_requirement_status_description

    @pytest.fixture
    def man_req_status_complete(self):
        return ManagedRequirementStatus.COMPLETE.managed_requirement_status_description

    @pytest.fixture
    def man_req_status_suppressed(self):
        return ManagedRequirementStatus.SUPPRESSED.managed_requirement_status_description

    @pytest.fixture
    def managed_requirement_record(self):
        return ManagedRequirementFactory.create()

    @pytest.fixture
    def complete_valid_fineos_managed_requirement(
        self, fineos_man_req,
    ):
        return fineos_man_req()

    @pytest.fixture
    def suppressed_valid_fineos_managed_requirement(
        self, fineos_man_req, man_req_status_suppressed
    ):
        man_req_id = None
        return fineos_man_req(man_req_id, man_req_status_suppressed)

    @pytest.fixture
    def wrong_type_invalid_fineos_managed_requirement(self, fineos_man_req):
        man_req_id = None
        man_req_status = None
        return fineos_man_req(man_req_id, man_req_status, "Invalid Type")

    @pytest.fixture
    def not_found_invalid_fineos_managed_requirement(self, fineos_man_req):
        man_req_id = 0
        return fineos_man_req(man_req_id)

    class TestUpdateEmployerConfirmationRequirements:
        def test_update_valid_employer_confirmation_requirements(
            self,
            test_db_session,
            user_leave_admin,
            complete_valid_fineos_managed_requirement,
            suppressed_valid_fineos_managed_requirement,
            man_req_status_open,
            man_req_status_complete,
            man_req_status_suppressed,
        ):
            fin_man_reqs = [
                complete_valid_fineos_managed_requirement,
                suppressed_valid_fineos_managed_requirement,
            ]
            updated_man_reqs = update_employer_confirmation_requirements(
                test_db_session, user_leave_admin.user_id, fin_man_reqs,
            )

            assert len(updated_man_reqs) == 2
            for r in updated_man_reqs:
                assert (
                    r.managed_requirement_status.managed_requirement_status_description
                    != man_req_status_open
                )
                assert r.respondent_user_id == user_leave_admin.user_id
                assert r.responded_at is not None

            completed_req = next(
                (
                    r
                    for r in updated_man_reqs
                    if r.managed_requirement_status.managed_requirement_status_description
                    == man_req_status_complete
                ),
                None,
            )
            assert completed_req is not None

            suppressed_req = next(
                (
                    r
                    for r in updated_man_reqs
                    if r.managed_requirement_status.managed_requirement_status_description
                    == man_req_status_suppressed
                ),
                None,
            )
            assert suppressed_req is not None

        def test_update_fineos_managed_requirement_wrong_type_does_not_update(
            self,
            test_db_session,
            user_leave_admin,
            complete_valid_fineos_managed_requirement,
            wrong_type_invalid_fineos_managed_requirement,
            man_req_status_open,
        ):
            fin_man_reqs = [
                complete_valid_fineos_managed_requirement,
                wrong_type_invalid_fineos_managed_requirement,
            ]
            updated_man_reqs = update_employer_confirmation_requirements(
                test_db_session, user_leave_admin.user_id, fin_man_reqs,
            )

            assert len(updated_man_reqs) == 1
            for r in updated_man_reqs:
                assert (
                    r.managed_requirement_status.managed_requirement_status_description
                    != man_req_status_open
                )
                assert r.respondent_user_id == user_leave_admin.user_id
                assert r.responded_at is not None

        def test_update_fineos_managed_requirement_not_found(
            self,
            test_db_session,
            user_leave_admin,
            complete_valid_fineos_managed_requirement,
            not_found_invalid_fineos_managed_requirement,
            man_req_status_open,
        ):
            fin_man_reqs = [
                complete_valid_fineos_managed_requirement,
                not_found_invalid_fineos_managed_requirement,
            ]
            updated_man_reqs = update_employer_confirmation_requirements(
                test_db_session, user_leave_admin.user_id, fin_man_reqs,
            )

            assert len(updated_man_reqs) == 1
            for r in updated_man_reqs:
                assert (
                    r.managed_requirement_status.managed_requirement_status_description
                    != man_req_status_open
                )
                assert r.respondent_user_id == user_leave_admin.user_id
                assert r.responded_at is not None
