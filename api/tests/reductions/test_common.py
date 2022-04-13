import massgov.pfml.reductions.common as reductions_common
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory


def test_get_claimants_for_outbound(test_db_session, initialize_factories_session):
    employee1 = EmployeeFactory.create()
    employee2 = EmployeeFactory.create()
    employee3 = EmployeeFactory.create()
    employee4 = EmployeeFactory.create()

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

    # employee4 has a historical absence case
    ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        employee=employee4,
        fineos_absence_id="H-00-ABS-00",
    )

    # we should only see the unique employees
    assert reductions_common.get_claimants_for_outbound(test_db_session) == [
        employee1,
        employee2,
        employee3,
    ]
