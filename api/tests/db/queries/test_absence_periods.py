from typing import List, Optional

import pytest

from massgov.pfml import db
from massgov.pfml.db.models.absences import AbsencePeriodType, AbsenceStatus
from massgov.pfml.db.models.factories import AbsencePeriodFactory, ClaimFactory, EmployeeFactory
from massgov.pfml.db.queries.absence_periods import get_employee_absence_periods


@pytest.mark.parametrize(
    "absence_statuses",
    [None, [AbsenceStatus.APPROVED, AbsenceStatus.COMPLETED, AbsenceStatus.IN_REVIEW]],
)
@pytest.mark.parametrize("absence_period_type", [None, AbsencePeriodType.CONTINUOUS])
def test_get_employee_absence_periods(
    initialize_factories_session,
    test_db_session: db.Session,
    absence_statuses: Optional[List[AbsenceStatus]],
    absence_period_type: Optional[AbsencePeriodType],
):
    """
    The main logic we are testing is whether the conditionals are
    entered. There are a lot of scenarios to consider
    2^(7+1) * (10+1) = 256 * 11 = 2,816
    Above cases meant to cover the initial use case and some edge cases.
    """
    absence_period_type_id = (
        absence_period_type.absence_period_type_id if absence_period_type else None
    )
    absence_status_ids = (
        [absence_status.absence_status_id for absence_status in absence_statuses]
        if absence_statuses
        else None
    )

    # Create dummy claims for other employees
    for _ in range(3):
        claim = ClaimFactory.create()
        AbsencePeriodFactory.create(claim=claim)

    employee = EmployeeFactory.create()
    expected_number_of_absence_periods = 0

    # Create dummy claims for same employee
    for _ in range(3):
        claim = ClaimFactory.create(employee=employee)
        # AbsencePeriod Will only appear in results
        # when absence status and absence period type are undefined
        AbsencePeriodFactory.create(claim=claim)
        if (
            absence_status_ids is None or len(absence_status_ids) == 0
        ) and absence_period_type is None:
            expected_number_of_absence_periods += 1

    # Create some absence period periods on the claim to filter on
    for absence_status_id in absence_status_ids if absence_status_ids is not None else []:
        claim = ClaimFactory.create(employee=employee, fineos_absence_status_id=absence_status_id)
        AbsencePeriodFactory.create(claim=claim, absence_period_type_id=absence_period_type_id)
        expected_number_of_absence_periods += 1

        # AbsencePeriod Will only appear in results
        # when absence period type is undefined
        AbsencePeriodFactory.create(claim=claim)
        if absence_period_type is None:
            expected_number_of_absence_periods += 1

    absence_periods = get_employee_absence_periods(
        test_db_session, employee.employee_id, absence_status_ids, absence_period_type_id
    )

    assert len(absence_periods) == expected_number_of_absence_periods
