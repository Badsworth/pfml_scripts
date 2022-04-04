from typing import List

from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ManagedRequirementFactory,
    OpenManagedRequirementFactory,
    PendingAbsencePeriodFactory,
)
from massgov.pfml.fineos.mock_client import mock_managed_requirements_parsed
from massgov.pfml.fineos.models.group_client_api import ManagedRequirementDetails
from massgov.pfml.util.logging.managed_requirements import log_managed_requirement_issues


class TestLogManagedRequirementIssues:
    def test_open_reqs_with_pending_decisions(self, caplog, initialize_factories_session):
        fineos_managed_requirements: List[ManagedRequirementDetails] = []
        managed_requirements = [OpenManagedRequirementFactory.create()]
        db_absence_periods = [AbsencePeriodFactory.create(), PendingAbsencePeriodFactory.create()]

        log_managed_requirement_issues(
            fineos_managed_requirements, managed_requirements, db_absence_periods, {}
        )

        assert (
            "Claim has open managed requirement but all absence periods already have a final decision."
            not in caplog.text
        )

    def test_open_reqs_with_no_pending_decisions(self, caplog, initialize_factories_session):
        fineos_managed_requirements: List[ManagedRequirementDetails] = []
        managed_requirements = [OpenManagedRequirementFactory.create()]
        db_absence_periods = [AbsencePeriodFactory.create()]

        log_managed_requirement_issues(
            fineos_managed_requirements, managed_requirements, db_absence_periods, {}
        )

        assert (
            "Claim has open managed requirement but all absence periods already have a final decision."
            in caplog.text
        )

    def test_open_reqs_with_no_absence_periods_provided(self, caplog, initialize_factories_session):
        """
        If absence period syncing fails and we don't get any periods passed in,
        we can't assume the absence periods are up to date. So we should be avoiding
        logging this scenario.
        """
        fineos_managed_requirements: List[ManagedRequirementDetails] = []
        managed_requirements = [OpenManagedRequirementFactory.create()]
        db_absence_periods = None

        log_managed_requirement_issues(
            fineos_managed_requirements, managed_requirements, db_absence_periods, {}
        )

        assert (
            "Claim has open managed requirement but all absence periods already have a final decision."
            not in caplog.text
        )

    def test_multiple_open_reqs(self, caplog, initialize_factories_session):
        fineos_managed_requirements: List[ManagedRequirementDetails] = []
        db_absence_periods = None

        managed_requirements = [
            OpenManagedRequirementFactory.create(),
            OpenManagedRequirementFactory.create(),
        ]

        log_managed_requirement_issues(
            fineos_managed_requirements, managed_requirements, db_absence_periods, {}
        )

        assert "Multiple open managed requirements were found." in caplog.text

    def test_single_open_req(self, caplog, initialize_factories_session):
        fineos_managed_requirements: List[ManagedRequirementDetails] = []
        db_absence_periods = None

        managed_requirements = [
            OpenManagedRequirementFactory.create(),
        ]

        log_managed_requirement_issues(
            fineos_managed_requirements, managed_requirements, db_absence_periods, {}
        )

        assert "Multiple open managed requirements were found." not in caplog.text

    def test_db_reqs_not_in_fineos(self, caplog, initialize_factories_session):
        fineos_managed_requirements: List[
            ManagedRequirementDetails
        ] = mock_managed_requirements_parsed()

        managed_requirements = [
            ManagedRequirementFactory.create(
                fineos_managed_requirement_id=fineos_managed_requirements[0].managedReqId + 101
            ),
        ]

        db_absence_periods = None

        log_managed_requirement_issues(
            fineos_managed_requirements, managed_requirements, db_absence_periods, {}
        )

        assert (
            "Claim has managed requirements not present in the data received from fineos."
            in caplog.text
        )

    def test_db_reqs_all_in_fineos(self, caplog, initialize_factories_session):
        fineos_managed_requirements: List[
            ManagedRequirementDetails
        ] = mock_managed_requirements_parsed()

        managed_requirements = [
            ManagedRequirementFactory.create(fineos_managed_requirement_id=r.managedReqId)
            for r in fineos_managed_requirements
        ]

        db_absence_periods = None

        log_managed_requirement_issues(
            fineos_managed_requirements, managed_requirements, db_absence_periods, {}
        )

        assert (
            "Claim has managed requirements not present in the data received from fineos."
            not in caplog.text
        )
