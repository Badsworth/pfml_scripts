#
# Financial eligibility - main algorithm.
#

from decimal import Decimal
from typing import Optional

import massgov.pfml.api.eligibility.eligibility_util as eligibility_util
import massgov.pfml.evaluate_new_eligibility.wage as wage
from massgov.pfml.api.eligibility.eligibility_date import eligibility_date
from massgov.pfml.api.models.applications.common import EligibilityEmploymentStatus
from massgov.pfml.util.pydantic import PydanticBaseModel


class EligibilityResponse(PydanticBaseModel):
    financially_eligible: bool
    description: str
    total_wages: Optional[Decimal]
    state_average_weekly_wage: Optional[Decimal]
    unemployment_minimum: Optional[Decimal]
    employer_average_weekly_wage: Optional[Decimal]


def compute_financial_eligibility(
    db_session,
    employee_id,
    employer_id,
    employer_fein,
    leave_start_date,
    application_submitted_date,
    employment_status,
    diff_reason_csv=None,
):
    effective_date = eligibility_date(leave_start_date, application_submitted_date)
    state_metric_data = eligibility_util.fetch_state_metric(db_session, effective_date)
    state_average_weekly_wage = state_metric_data.average_weekly_wage
    unemployment_minimum = state_metric_data.unemployment_minimum_earnings

    # Calculate various wages by fetching them from DOR
    wage_calculator = wage.get_wage_calculator(
        employee_id, effective_date, db_session, diff_reason_csv
    )
    total_wages = wage_calculator.compute_total_wage()
    consolidated_weekly_wage = wage_calculator.compute_consolidated_aww()
    wage_calculator.set_each_employers_average_weekly_wage()
    quarterly_wages = wage_calculator.compute_total_quarterly_wages()

    # multiple employer
    if diff_reason_csv and len(wage_calculator.employer_average_weekly_wage.keys()) >= 1:
        diff_reason_csv.writerow(
            [str(employee_id), str(employer_id), leave_start_date, "multiple_employers"]
        )

    unemployment_min_met = eligibility_util.wages_gte_unemployment_min(
        total_wages, unemployment_minimum
    )

    gte_thirty_times_wba = eligibility_util.wages_gte_thirty_times_wba(
        total_wages, consolidated_weekly_wage, state_average_weekly_wage, effective_date
    )
    # Check various financial eligibility thresholds, set the description accordingly
    financially_eligible = False
    if not unemployment_min_met:
        description = "Claimant wages under minimum"

    elif not gte_thirty_times_wba:
        description = "Claimant wages failed 30x rule"

    elif (
        employment_status == EligibilityEmploymentStatus.self_employed and len(quarterly_wages) < 2
    ):
        description = "Opt-in quarterly contributions not met"

    else:
        financially_eligible = True
        description = "Financially eligible"

    try:
        employer_average_weekly_wage = round(
            wage_calculator.get_employer_average_weekly_wage(employer_id), 2
        )
    except KeyError:
        employer_average_weekly_wage = 0

    return EligibilityResponse(
        financially_eligible=financially_eligible,
        description=description,
        total_wages=total_wages,
        state_average_weekly_wage=state_average_weekly_wage,
        unemployment_minimum=unemployment_minimum,
        employer_average_weekly_wage=employer_average_weekly_wage,
    )
