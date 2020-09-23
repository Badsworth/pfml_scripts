from decimal import Decimal
from typing import Optional

import massgov.pfml.api.eligibility.eligibility_util as eligibility_util
import massgov.pfml.api.eligibility.wage as wage
from massgov.pfml.api.eligibility.eligibility_date import eligibility_date
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
    total_wages = wage.get_total_wage(employee_id, effective_date, db_session)
    individual_average_weekly_wage = wage.get_average_weekly_wage(
        employee_id, effective_date, db_session
    )

    unemployment_min_met = eligibility_util.wages_gte_unemployment_min(
        total_wages, unemployment_minimum
    )

    if not unemployment_min_met:
        description = "Unemployment minimum not met"

    gte_thirty_times_wba = eligibility_util.wages_gte_thirty_times_wba(
        total_wages, individual_average_weekly_wage, state_average_weekly_wage
    )

    if not gte_thirty_times_wba:
        description = "Total wages below 30x weekly benefit"
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
