from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from dateutil.relativedelta import relativedelta

from massgov.pfml import db
from massgov.pfml.api.eligibility import eligibility
from massgov.pfml.api.eligibility.benefit_year import (
    CreateBenefitYearContribution,
    _create_benefit_year,
)
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.api.eligibility.eligibility import EligibilityResponse
from massgov.pfml.api.eligibility.eligibility_date import eligibility_date
from massgov.pfml.api.eligibility.mock.scenarios import (
    EligibilityScenarioDescriptor,
    EligibilityScenarioName,
)
from massgov.pfml.api.eligibility.wage import WageCalculator
from massgov.pfml.api.models.applications.common import EligibilityEmploymentStatus
from massgov.pfml.db.models.employees import BenefitYear, Employee, Employer
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.util.datetime import quarter


@dataclass
class ScenarioData:
    scenario_name: Optional[EligibilityScenarioName]
    employee: Employee
    employer: Employer
    leave_start_date: date
    application_submitted_date: date
    employment_status: EligibilityEmploymentStatus
    active_benefit_year: Optional[BenefitYear] = None
    future_benefit_year: Optional[BenefitYear] = None
    other_employer: Optional[Employer] = None


def generate_eligibility_scenario_data_in_db(
    scenario_descriptor: EligibilityScenarioDescriptor, db_session: db.Session
) -> ScenarioData:
    employee = EmployeeFactory.create()
    employer = EmployerFactory.create()

    benefit_year_dates = get_benefit_year_dates(scenario_descriptor.leave_start_date)
    effective_date = eligibility_date(
        benefit_year_dates.start_date, scenario_descriptor.application_submitted_date
    )
    starting_quarter = quarter.Quarter.from_date(effective_date)

    for i in range(len(scenario_descriptor.last_x_quarters_wages)):
        quarters_to_subtract = i if scenario_descriptor.current_quarter_has_data else i + 1
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=employer,
            filing_period=starting_quarter.subtract_quarters(quarters_to_subtract).start_date(),
            employee_qtr_wages=scenario_descriptor.last_x_quarters_wages[i],
        )

    if scenario_descriptor.last_x_quarters_wages_other_employer:
        other_employer = EmployerFactory.create()
        for i in range(len(scenario_descriptor.last_x_quarters_wages_other_employer)):
            quarters_to_subtract = i if scenario_descriptor.current_quarter_has_data else i + 1
            WagesAndContributionsFactory.create(
                employee=employee,
                employer=other_employer,
                filing_period=starting_quarter.subtract_quarters(quarters_to_subtract).start_date(),
                employee_qtr_wages=scenario_descriptor.last_x_quarters_wages_other_employer[i],
            )
    else:
        other_employer = None

    if scenario_descriptor.active_benefit_year:
        benefit_year_dates = get_benefit_year_dates(
            scenario_descriptor.leave_start_date - relativedelta(months=6)
        )
        total_wages = Decimal(scenario_descriptor.active_benefit_year.total_wages)
        wage_calculator = WageCalculator()
        wage_calculator.employer_average_weekly_wage[employer.employer_id] = Decimal(
            scenario_descriptor.active_benefit_year.employer_IAWW
        )
        employer_contributions = CreateBenefitYearContribution.from_wage_quarters(wage_calculator)

        active_benefit_year = _create_benefit_year(
            db_session,
            employee.employee_id,
            benefit_year_dates.start_date,
            total_wages,
            employer_contributions,
        )
        db_session.commit()
    else:
        active_benefit_year = None

    if scenario_descriptor.future_benefit_year:
        benefit_year_dates = get_benefit_year_dates(
            scenario_descriptor.leave_start_date + relativedelta(months=1)
        )
        total_wages = Decimal(scenario_descriptor.future_benefit_year.total_wages)
        wage_calculator = WageCalculator()
        wage_calculator.employer_average_weekly_wage[employer.employer_id] = Decimal(
            scenario_descriptor.future_benefit_year.employer_IAWW
        )
        employer_contributions = CreateBenefitYearContribution.from_wage_quarters(wage_calculator)

        future_benefit_year = _create_benefit_year(
            db_session,
            employee.employee_id,
            benefit_year_dates.start_date,
            total_wages,
            employer_contributions,
        )
        db_session.commit()
    else:
        future_benefit_year = None

    return ScenarioData(
        scenario_descriptor.scenario_name,
        employee,
        employer,
        scenario_descriptor.leave_start_date,
        scenario_descriptor.application_submitted_date,
        scenario_descriptor.employment_status,
        active_benefit_year,
        future_benefit_year,
        other_employer,
    )


def run_eligibility_for_scenario(
    scenario_data: ScenarioData, db_session: db.Session
) -> EligibilityResponse:
    return eligibility.retrieve_financial_eligibility(
        db_session,
        scenario_data.employee.employee_id,
        scenario_data.employer.employer_id,
        scenario_data.leave_start_date,
        scenario_data.application_submitted_date,
        scenario_data.employment_status,
    )
