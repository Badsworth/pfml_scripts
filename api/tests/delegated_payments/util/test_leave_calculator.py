from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, NamedTuple, Optional, Tuple

import pytest

from massgov.pfml.db.models.employees import AbsencePeriod, BenefitYear, Claim, Employee, Employer
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    BenefitYearFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
)
from massgov.pfml.delegated_payments.util.leave_calculator import (
    LeaveCalculator,
    LeaveDurationResult,
)
from tests.delegated_payments.util import (
    multiple_claims_multiple_absence_periods,
    multiple_claims_with_absence_periods_one_day_long,
    one_claim_multiple_absence_periods,
    one_claim_multiple_absence_periods_one_day_long,
    one_claim_single_absence_period,
)


class AbsencePeriodDates(NamedTuple):
    start_date: date
    end_date: date


@dataclass
class ClaimDescriptor:
    start_date: date
    end_date: date
    absence_periods: List[Tuple[date, date]] = None
    employer: Optional[Employer] = None


@dataclass
class LeaveData:
    claims: List[Claim]
    absence_periods: List[AbsencePeriod]
    benefit_year: BenefitYear
    employer: Employer


@pytest.fixture
def use_employee(test_db_session, initialize_factories_session):
    return EmployeeFactory.create()


@pytest.fixture
def employer_1(test_db_session, initialize_factories_session):
    return EmployerFactory.create(fineos_employer_id=123)


@pytest.fixture
def employer_2(test_db_session, initialize_factories_session):
    return EmployerFactory.create(fineos_employer_id=456)


@pytest.fixture
def employer_3(test_db_session, initialize_factories_session):
    return EmployerFactory.create(fineos_employer_id=789)


@pytest.fixture
def benefit_year_1(test_db_session, initialize_factories_session, use_employee):
    return BenefitYearFactory.create(
        employee=use_employee, start_date=date(2020, 1, 5), end_date=date(2021, 1, 2),
    )


@pytest.fixture
def benefit_year_2(test_db_session, initialize_factories_session, use_employee):
    return BenefitYearFactory.create(
        employee=use_employee, start_date=date(2021, 1, 3), end_date=date(2022, 1, 1),
    )


@pytest.fixture
def benefit_year_3(test_db_session, initialize_factories_session, use_employee):
    return BenefitYearFactory.create(
        employee=use_employee, start_date=date(2022, 1, 2), end_date=date(2022, 12, 31),
    )


def test_set_benefit_year_absence_period__absence_period_missing_data__mixed(
    use_employee: Employee,
):
    benefit_year_start_date = date(2020, 1, 5)
    benefit_year_end_date = date(2021, 1, 2)

    benefit_year = BenefitYearFactory.create(
        start_date=benefit_year_start_date, end_date=benefit_year_end_date,
    )
    leave_calc = LeaveCalculator(benefit_years=[benefit_year])

    # Missing claim, absence_period_start_date, absence_period_end_date
    absence_period = AbsencePeriodFactory.create(
        absence_period_start_date=None, absence_period_end_date=None,
    )
    leave_calc.set_benefit_year_absence_period(benefit_year, absence_period)
    assert leave_calc.benefit_year_absences == {}
    assert leave_calc.consolidated_leave == {}

    # Claim missing employer, absence_period_start_date
    absence_period = AbsencePeriodFactory.create(
        claim=ClaimFactory.create(employee=use_employee, employer=None),
        absence_period_start_date=date(2021, 1, 10),
        absence_period_end_date=date(2021, 1, 15),
    )
    leave_calc.set_benefit_year_absence_period(benefit_year, absence_period)
    assert leave_calc.benefit_year_absences == {}
    assert leave_calc.consolidated_leave == {}

    # Claim missing absence_period_start_date
    absence_period = AbsencePeriodFactory.create(
        claim=ClaimFactory.create(employee=use_employee),
        absence_period_start_date=date(2021, 1, 10),
        absence_period_end_date=date(2021, 1, 15),
    )
    leave_calc.set_benefit_year_absence_period(benefit_year, absence_period)
    assert leave_calc.benefit_year_absences == {}
    assert leave_calc.consolidated_leave == {}

    # Claim missing employer
    absence_period = AbsencePeriodFactory.create(
        claim=ClaimFactory.create(
            employee=use_employee,
            absence_period_start_date=date(2021, 1, 10),
            absence_period_end_date=date(2021, 1, 15),
            employer=None,
        ),
        absence_period_start_date=date(2021, 1, 10),
        absence_period_end_date=date(2021, 1, 15),
    )
    leave_calc.set_benefit_year_absence_period(benefit_year, absence_period)
    assert leave_calc.benefit_year_absences == {}
    assert leave_calc.consolidated_leave == {}

    # Employer missing fein
    leave_data = one_claim_single_absence_period(use_employee, benefit_year)
    leave_data.claims[0].employer.fineos_employer_id = None
    leave_calc.set_benefit_year_absence_period(benefit_year, leave_data.absence_periods[0])
    assert leave_calc.benefit_year_absences == {}
    assert leave_calc.consolidated_leave == {}

    # Claim start date before benefit year
    leave_data = one_claim_single_absence_period(use_employee, benefit_year)
    leave_data.claims[0].absence_period_start_date = benefit_year.start_date - timedelta(days=1)

    leave_calc.set_benefit_year_absence_period(benefit_year, leave_data.absence_periods[0])
    assert leave_calc.benefit_year_absences == {}
    assert leave_calc.consolidated_leave == {}

    # Claim start date after benefit year
    leave_data = one_claim_single_absence_period(use_employee, benefit_year)
    leave_data.claims[0].absence_period_start_date = benefit_year.end_date + timedelta(days=1)

    leave_calc.set_benefit_year_absence_period(benefit_year, leave_data.absence_periods[0])
    assert leave_calc.benefit_year_absences == {}
    assert leave_calc.consolidated_leave == {}


def test_set_benefit_year_absence_period__duplicate_absence_period(
    test_db_session,
    initialize_factories_session,
    use_employee: Employee,
    benefit_year_1: BenefitYear,
    employer_1: Employer,
):
    # Each absence period should only be counted one time
    employer_1 = EmployerFactory.create()
    leave_data = one_claim_single_absence_period(use_employee, benefit_year_1, employer_1)

    assert len(leave_data.absence_periods) == 1
    absence_period = leave_data.absence_periods[0]

    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.set_benefit_year_absence_period(benefit_year_1, absence_period)
    leave_calc.set_benefit_year_absence_period(benefit_year_1, absence_period)
    leave_calc.set_benefit_year_absence_period(benefit_year_1, absence_period)

    benefit_year_id = benefit_year_1.benefit_year_id
    employer_id = employer_1.employer_id
    assert leave_calc.consolidated_leave == {benefit_year_id: {employer_id: 6}}


def test_set_benefit_year_absence_periods__one_claim_single_absence_period(
    use_employee: Employee, benefit_year_1: BenefitYear, employer_1: Employer
):
    benefit_year_id = benefit_year_1.benefit_year_id
    employer_id = employer_1.employer_id
    leave_data = one_claim_single_absence_period(use_employee, benefit_year_1, employer_1)

    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.set_benefit_year_absence_periods(leave_data.absence_periods)
    assert leave_calc.consolidated_leave == {benefit_year_id: {employer_id: 6}}


def test_set_benefit_year_absence_periods__one_claim_multiple_absence_periods(
    use_employee: Employee, benefit_year_1: BenefitYear, employer_1: Employer,
):
    benefit_year_id = benefit_year_1.benefit_year_id
    employer_id = employer_1.employer_id

    leave_data = one_claim_multiple_absence_periods(use_employee, benefit_year_1, employer_1)

    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.set_benefit_year_absence_periods(leave_data.absence_periods)
    benefit_year_id = benefit_year_1.benefit_year_id
    assert leave_calc.consolidated_leave == {benefit_year_id: {employer_id: 35}}


def test_set_benefit_year_absence_periods__multiple_claims_multiple_absence_periods(
    use_employee: Employee, benefit_year_1: BenefitYear, employer_1: Employer
):
    benefit_year_id = benefit_year_1.benefit_year_id
    employer_id = employer_1.employer_id

    leave_data = multiple_claims_multiple_absence_periods(use_employee, benefit_year_1, employer_1)

    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.set_benefit_year_absence_periods(leave_data.absence_periods)
    benefit_year_id = benefit_year_1.benefit_year_id
    assert leave_calc.consolidated_leave == {benefit_year_id: {employer_id: 175}}


def test_set_benefit_year_absence_periods__one_claim_multiple_absence_periods_one_day_long(
    use_employee: Employee, benefit_year_1: BenefitYear, employer_1: Employer
):
    benefit_year_id = benefit_year_1.benefit_year_id
    employer_id = employer_1.employer_id

    leave_data = one_claim_multiple_absence_periods_one_day_long(
        use_employee, benefit_year_1, employer_1
    )

    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.set_benefit_year_absence_periods(leave_data.absence_periods)
    benefit_year_id = benefit_year_1.benefit_year_id
    assert leave_calc.consolidated_leave == {benefit_year_id: {employer_id: 5}}


def test_set_benefit_year_absence_periods__multiple_claims_with_absence_periods_one_day_long(
    use_employee: Employee, benefit_year_1: BenefitYear, employer_1: Employer
):
    benefit_year_id = benefit_year_1.benefit_year_id
    employer_id = employer_1.employer_id

    leave_data = multiple_claims_with_absence_periods_one_day_long(
        use_employee, benefit_year_1, employer_1
    )

    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.set_benefit_year_absence_periods(leave_data.absence_periods)
    benefit_year_id = benefit_year_1.benefit_year_id
    assert leave_calc.consolidated_leave == {benefit_year_id: {employer_id: 25}}


def test_set_benefit_year_absence_periods__mixed(
    use_employee: Employee,
    benefit_year_1: BenefitYear,
    benefit_year_2: BenefitYear,
    benefit_year_3: BenefitYear,
    employer_1: Employer,
    employer_2: Employer,
    employer_3: Employer,
):

    benefit_year_1_id = benefit_year_1.benefit_year_id
    benefit_year_2_id = benefit_year_2.benefit_year_id
    benefit_year_3_id = benefit_year_3.benefit_year_id
    employer_1_id = employer_1.employer_id
    employer_2_id = employer_2.employer_id
    employer_3_id = employer_3.employer_id

    ### Benefit year 1
    BENEFIT_YEAR_1_SCENARIOS = [
        # Employer 1
        multiple_claims_multiple_absence_periods(use_employee, benefit_year_1, employer_1),
        # Employer 2
        one_claim_multiple_absence_periods(use_employee, benefit_year_1, employer_2),
        # Employer 3
        multiple_claims_with_absence_periods_one_day_long(use_employee, benefit_year_1, employer_3),
        one_claim_single_absence_period(use_employee, benefit_year_1, employer_3),
    ]
    absence_periods_1 = [
        item for sublist in BENEFIT_YEAR_1_SCENARIOS for item in sublist.absence_periods
    ]
    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.set_benefit_year_absence_periods(absence_periods_1)
    assert leave_calc.consolidated_leave[benefit_year_1_id] == {
        employer_1_id: 175,
        employer_2_id: 35,
        employer_3_id: 25 + 6,
    }

    ### Benefit year 2
    BENEFIT_YEAR_2_SCENARIOS = [
        # Employer 1
        one_claim_single_absence_period(use_employee, benefit_year_2, employer_1),
        # Employer 2
        one_claim_multiple_absence_periods_one_day_long(use_employee, benefit_year_2, employer_2),
    ]
    absence_periods_2 = [
        item for sublist in BENEFIT_YEAR_2_SCENARIOS for item in sublist.absence_periods
    ]
    leave_calc = LeaveCalculator([benefit_year_2])
    leave_calc.set_benefit_year_absence_periods(absence_periods_2)
    assert leave_calc.consolidated_leave[benefit_year_2_id] == {
        employer_1_id: 6,
        employer_2_id: 5,
    }

    ### Benefit year 3
    BENEFIT_YEAR_3_SCENARIOS = [
        # Employer 3
        one_claim_multiple_absence_periods(use_employee, benefit_year_3, employer_3),
    ]
    absence_periods_3 = [
        item for sublist in BENEFIT_YEAR_3_SCENARIOS for item in sublist.absence_periods
    ]
    leave_calc = LeaveCalculator([benefit_year_3])
    leave_calc.set_benefit_year_absence_periods(absence_periods_3)
    assert leave_calc.consolidated_leave[benefit_year_3_id] == {
        employer_3_id: 35,
    }

    # All scenarios combined
    leave_calc = LeaveCalculator([benefit_year_1, benefit_year_2, benefit_year_3])
    leave_calc.set_benefit_year_absence_periods(
        absence_periods_1 + absence_periods_2 + absence_periods_3,
    )
    assert leave_calc.consolidated_leave == {
        benefit_year_1_id: {employer_1_id: 175, employer_2_id: 35, employer_3_id: 31,},
        benefit_year_2_id: {employer_1_id: 6, employer_2_id: 5},
        benefit_year_3_id: {employer_3_id: 35},
    }


def test_benefit_year_exceeding_threshold__mixed(
    benefit_year_1,
    benefit_year_2,
    benefit_year_3,
    employer_1: Employer,
    employer_2: Employer,
    employer_3: Employer,
):
    benefit_year_1_id = benefit_year_1.benefit_year_id
    benefit_year_2_id = benefit_year_2.benefit_year_id
    benefit_year_3_id = benefit_year_3.benefit_year_id
    employer_1_id = employer_1.employer_id
    employer_2_id = employer_2.employer_id
    employer_3_id = employer_3.employer_id

    # should not find anything when empty
    leave_calc = LeaveCalculator()
    assert leave_calc.benefit_years_exceeding_threshold(1) == []

    # should not error if missing benefit year data
    leave_calc.consolidated_leave = {benefit_year_1_id: {employer_1_id: 2}}
    assert leave_calc.benefit_years_exceeding_threshold(1) == []

    # should not find anything when missing employer data
    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.consolidated_leave = {benefit_year_1_id: {employer_1_id: 2}}
    assert leave_calc.benefit_years_exceeding_threshold(1) == []

    # should not find anything when threshold not met
    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.consolidated_leave = {benefit_year_1_id: {employer_1_id: 2}}
    leave_calc.employers = {employer_1_id: employer_1}
    assert leave_calc.benefit_years_exceeding_threshold(3) == []

    # should not find anything when duration exactly equals threshold
    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.consolidated_leave = {benefit_year_1_id: {employer_1_id: 2}}
    leave_calc.employers = {employer_1_id: employer_1}
    assert leave_calc.benefit_years_exceeding_threshold(2) == []

    # should find result when threshold met
    leave_calc = LeaveCalculator([benefit_year_1])
    leave_calc.consolidated_leave = {benefit_year_1_id: {employer_1_id: 2}}
    leave_calc.employers = {employer_1_id: employer_1}
    assert leave_calc.benefit_years_exceeding_threshold(1) == [
        LeaveDurationResult(
            benefit_year_1_id,
            benefit_year_1.start_date,
            benefit_year_1.end_date,
            employer_1_id,
            employer_1.fineos_employer_id,
            2,
        )
    ]

    # various threshold checks
    leave_calc = LeaveCalculator([benefit_year_1, benefit_year_2, benefit_year_3])
    leave_calc.employers = {
        employer_1_id: employer_1,
        employer_2_id: employer_2,
        employer_3_id: employer_3,
    }
    leave_calc.consolidated_leave = {
        benefit_year_1_id: {employer_1_id: 1, employer_2_id: 2, employer_3_id: 3},
        benefit_year_2_id: {employer_1_id: 4, employer_2_id: 5, employer_3_id: 6},
        benefit_year_3_id: {employer_1_id: 7, employer_2_id: 8, employer_3_id: 9},
    }

    # should not find anything
    assert leave_calc.benefit_years_exceeding_threshold(10) == []
    assert leave_calc.benefit_years_exceeding_threshold(9) == []

    # Starting from 8 we should start to get results
    for i in range(1, 9):
        threshold = 9 - i
        results = leave_calc.benefit_years_exceeding_threshold(threshold)
        assert len(results) == i
        _validate_leave_duration_results(results, threshold, leave_calc)


def _validate_leave_duration_results(
    results: List[LeaveDurationResult], threshold: int, leave_calc: LeaveCalculator
):
    for result in results:
        assert result.duration > threshold
        assert result.benefit_year_id in leave_calc.consolidated_leave
        assert result.benefit_year_id in leave_calc.benefit_years
        assert (
            result.benefit_year_start_date
            == leave_calc.benefit_years[result.benefit_year_id].start_date
        )
        assert (
            result.benefit_year_end_date
            == leave_calc.benefit_years[result.benefit_year_id].end_date
        )
        assert result.employer_id in leave_calc.consolidated_leave[result.benefit_year_id]
        assert (
            leave_calc.consolidated_leave[result.benefit_year_id][result.employer_id]
            == result.duration
        )
