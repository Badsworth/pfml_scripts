from decimal import Decimal
from typing import Optional

import massgov.pfml.api.eligibility.eligibility_util as eligibility_util
import massgov.pfml.api.eligibility.wage as wage
from massgov.pfml.api.eligibility.eligibility_date import eligibility_date
from massgov.pfml.api.models.applications.common import EmploymentStatus
from massgov.pfml.util.pydantic import PydanticBaseModel


class EligibilityResponse(PydanticBaseModel):
    financially_eligible: bool
    description: str
    total_wages: Optional[Decimal]
    state_average_weekly_wage: Optional[int]
    unemployment_minimum: Optional[int]


def calculate_effective_date(leave_start_date, application_submitted_date):
    return eligibility_date(leave_start_date, application_submitted_date)


def get_financially_eligible(description):
    if description == "Financially eligible":
        return True

    return False


def compute_financial_eligibility(
    db_session,
    employee_id,
    employer_fein,
    leave_start_date,
    application_submitted_date,
    employment_status,
):
    effective_date = calculate_effective_date(leave_start_date, application_submitted_date)
    state_metric_data = eligibility_util.fetch_state_metric(db_session, effective_date)
    state_average_weekly_wage = state_metric_data.average_weekly_wage
    unemployment_minimum = state_metric_data.unemployment_minimum_earnings

    # Calculate various wages by fetching them from DOR
    wage_calculator = wage.get_wage_calculator(employee_id, effective_date, db_session)
    total_wages = wage_calculator.compute_total_wage()
    individual_average_weekly_wage = wage_calculator.compute_average_weekly_wage()
    quarterly_wages = wage_calculator.compute_total_quarterly_wages()

    unemployment_min_met = eligibility_util.wages_gte_unemployment_min(
        total_wages, unemployment_minimum
    )

    gte_thirty_times_wba = eligibility_util.wages_gte_thirty_times_wba(
        total_wages, individual_average_weekly_wage, state_average_weekly_wage
    )

    # Check various financial eligibility thresholds, set the description accordingly
    if not unemployment_min_met:
        description = "Unemployment minimum not met"

    elif not gte_thirty_times_wba:
        description = "Total wages below 30x weekly benefit"

    elif employment_status == EmploymentStatus.self_employed and len(quarterly_wages) < 2:
        description = "Does not meet the self-employment requirement to contribute in at least 2 of the last 4 quarters"

    else:
        description = "Financially eligible"

    financially_eligible = get_financially_eligible(description)

    return EligibilityResponse(
        financially_eligible=financially_eligible,
        description=description,
        total_wages=total_wages,
        state_average_weekly_wage=state_average_weekly_wage,
        unemployment_minimum=unemployment_minimum,
    )
