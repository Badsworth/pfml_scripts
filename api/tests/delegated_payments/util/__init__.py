from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional

from massgov.pfml.db.models.employees import AbsencePeriod, BenefitYear, Claim, Employee, Employer
from massgov.pfml.db.models.factories import AbsencePeriodFactory, ClaimFactory, EmployerFactory


@dataclass
class LeaveData:
    claims: List[Claim]
    absence_periods: List[AbsencePeriod]
    benefit_year: BenefitYear


def one_claim_single_absence_period(
    employee: Employee, benefit_year: BenefitYear, employer: Optional[Employer] = None
):
    """
    One claim with single absence period
    Leave duration: 6 days
    """
    start_date = benefit_year.start_date
    end_date = start_date + timedelta(days=5)
    employer = employer if employer else EmployerFactory.create()
    claim = ClaimFactory.create(
        employer=employer,
        employee=employee,
        absence_period_start_date=start_date,
        absence_period_end_date=end_date,
    )
    absence_period = AbsencePeriodFactory.create(
        claim=claim, absence_period_start_date=start_date, absence_period_end_date=end_date,
    )
    return LeaveData([claim], [absence_period], benefit_year)


def one_claim_multiple_absence_periods(
    employee: Employee, benefit_year: BenefitYear, employer: Optional[Employer] = None
):
    """
    One claim with multiple absence periods
    Leave duration: 35 days
    """
    start_date = benefit_year.start_date
    end_date = start_date + timedelta(weeks=26)
    employer = employer if employer else EmployerFactory.create()
    claim = ClaimFactory.create(
        employer=employer,
        employee=employee,
        absence_period_start_date=start_date,
        absence_period_end_date=end_date,
    )
    absence_periods = [
        AbsencePeriodFactory.create(
            claim=claim, absence_period_start_date=start_date, absence_period_end_date=end_date,
        )
        for start_date, end_date in [
            (start_date + timedelta(weeks=i, days=1), start_date + timedelta(weeks=i + 1))
            for i in range(5)
        ]
    ]
    return LeaveData([claim], absence_periods, benefit_year)


def multiple_claims_multiple_absence_periods(
    employee: Employee, benefit_year: BenefitYear, employer: Optional[Employer] = None
):
    """
    One claim with multiple absence periods
    Leave duration: 175 days
    """
    employer = employer if employer else EmployerFactory.create()
    claims = []
    absence_periods = []
    for _ in range(5):
        absence_data = one_claim_multiple_absence_periods(employee, benefit_year, employer)
        claims.extend(absence_data.claims)
        absence_periods.extend(absence_data.absence_periods)

    return LeaveData(claims, absence_periods, benefit_year)


def one_claim_multiple_absence_periods_one_day_long(
    employee: Employee, benefit_year: BenefitYear, employer: Optional[Employer] = None
):
    """
    One claim with multiple absence periods starting and stopping on the same day.
    Leave duration: 5 days
    """
    start_date = benefit_year.start_date
    end_date = start_date + timedelta(days=5)
    employer = employer if employer else EmployerFactory.create()
    claim = ClaimFactory.create(
        employer=employer,
        employee=employee,
        absence_period_start_date=start_date,
        absence_period_end_date=end_date,
    )
    absence_periods = [
        AbsencePeriodFactory.create(
            claim=claim, absence_period_start_date=leave_date, absence_period_end_date=leave_date,
        )
        for leave_date in [start_date + timedelta(days=i) for i in range(5)]
    ]
    return LeaveData([claim], absence_periods, benefit_year)


def multiple_claims_with_absence_periods_one_day_long(
    employee: Employee, benefit_year: BenefitYear, employer: Optional[Employer] = None
):
    """
    Multiple claims with absence periods starting and stopping on the same day
    Leave duration: 25 days
    """
    claims = []
    absence_periods = []
    employer = employer if employer else EmployerFactory.create()
    for _ in range(5):
        data = one_claim_multiple_absence_periods_one_day_long(employee, benefit_year, employer)
        claims.extend(data.claims)
        absence_periods.extend(data.absence_periods)

    return LeaveData(claims, absence_periods, benefit_year)
