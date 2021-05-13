import pytest

import massgov.pfml.reductions.common as reductions_common
from massgov.pfml.db.models.employees import AbsenceStatus
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_get_claims_for_outbound(test_db_session, initialize_factories_session):
    claims_included = [
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.ADJUDICATION.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.CLOSED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.IN_REVIEW.absence_status_id),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.IN_REVIEW.absence_status_id),
    ]

    # claims that should not be included
    [
        ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.INTAKE_IN_PROGRESS.absence_status_id
        ),
        ClaimFactory.create(fineos_absence_status_id=AbsenceStatus.DECLINED.absence_status_id),
    ]

    assert reductions_common.get_claims_for_outbound(test_db_session) == claims_included


def test_get_claimants_for_outbound(test_db_session, initialize_factories_session):
    employee1 = EmployeeFactory.create()
    employee2 = EmployeeFactory.create()
    employee3 = EmployeeFactory.create()

    # existing employee without any claims should not be included
    EmployeeFactory.create()

    # employee1 just has the one claim
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee1
    )
    # employee2 has a couple of claims
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id, employee=employee2
    )
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.CLOSED.absence_status_id, employee=employee2
    )
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id, employee=employee2
    )
    # employee3 has one pending
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.IN_REVIEW.absence_status_id, employee=employee3
    ),

    # we should only see the unique employees
    assert reductions_common.get_claimants_for_outbound(test_db_session) == [
        employee1,
        employee2,
        employee3,
    ]
