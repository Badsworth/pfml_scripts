#
# Financial eligibility - main algorithm.
#

from datetime import date
from decimal import Decimal
from typing import Optional, TypedDict

from pydantic.types import UUID4

import massgov.pfml.api.eligibility.benefit_year as benefit_year
import massgov.pfml.api.eligibility.eligibility_util as eligibility_util
import massgov.pfml.api.eligibility.wage as wage
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.eligibility.benefit_year import CreateBenefitYearContribution
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.api.eligibility.eligibility_date import eligibility_date
from massgov.pfml.api.models.applications.common import EligibilityEmploymentStatus
from massgov.pfml.util.pydantic import PydanticBaseModel

logger = massgov.pfml.util.logging.get_logger(__name__)


class EligibilityResponse(PydanticBaseModel):
    financially_eligible: bool
    description: str
    total_wages: Optional[Decimal]
    state_average_weekly_wage: Optional[Decimal]
    unemployment_minimum: Optional[Decimal]
    employer_average_weekly_wage: Optional[Decimal]


class EligibilityLogExtra(TypedDict):
    employee_id: UUID4
    employer_id: UUID4
    benefit_year_id: Optional[UUID4]
    quarterly_wages: str


def _compute_financial_eligibility(
    employment_status: str,
    state_average_weekly_wage: Decimal,
    maximum_weekly_benefit_amount: Decimal,
    unemployment_minimum_earnings: Decimal,
    wage_data: wage.ComputeDORWageData,
    employer_average_weekly_wage: Decimal,
) -> EligibilityResponse:

    unemployment_min_met = eligibility_util.wages_gte_unemployment_min(
        wage_data.total_wages, unemployment_minimum_earnings
    )

    gte_thirty_times_wba = eligibility_util.wages_gte_thirty_times_wba(
        wage_data.total_wages,
        wage_data.consolidated_weekly_wage,
        state_average_weekly_wage,
        maximum_weekly_benefit_amount,
    )

    # Check various financial eligibility thresholds, set the description accordingly
    financially_eligible = False
    if not unemployment_min_met:
        description = "Claimant wages under minimum"

    elif not gte_thirty_times_wba:
        description = "Claimant wages failed 30x rule"

    elif (
        employment_status == EligibilityEmploymentStatus.self_employed
        and len(wage_data.quarterly_wages) < 2
    ):
        description = "Opt-in quarterly contributions not met"

    else:
        financially_eligible = True
        description = "Financially eligible"

    return EligibilityResponse(
        financially_eligible=financially_eligible,
        description=description,
        total_wages=wage_data.total_wages,
        state_average_weekly_wage=state_average_weekly_wage,
        unemployment_minimum=unemployment_minimum_earnings,
        employer_average_weekly_wage=employer_average_weekly_wage,
    )


def compute_financial_eligibility(
    db_session: db.Session,
    employee_id: UUID4,
    employer_id: UUID4,
    leave_start_date: date,
    application_submitted_date: date,
    employment_status: EligibilityEmploymentStatus,
) -> EligibilityResponse:

    benefit_year_dates = get_benefit_year_dates(leave_start_date)
    effective_date = eligibility_date(benefit_year_dates.start_date, application_submitted_date)
    (benefits_metrics, unemployment_metric) = eligibility_util.fetch_state_metric(
        db_session, benefit_year_dates.start_date
    )
    wage_calculator = wage.get_wage_calculator(employee_id, effective_date, db_session)
    wage_data = wage_calculator.compute_employee_dor_wage_data()
    employer_average_weekly_wage = wage_calculator.get_employer_average_weekly_wage(
        employer_id, Decimal("0"), True
    )

    return _compute_financial_eligibility(
        employment_status=employment_status,
        state_average_weekly_wage=benefits_metrics.average_weekly_wage,
        maximum_weekly_benefit_amount=benefits_metrics.maximum_weekly_benefit_amount,
        unemployment_minimum_earnings=unemployment_metric.unemployment_minimum_earnings,
        wage_data=wage_data,
        employer_average_weekly_wage=employer_average_weekly_wage,
    )


def retrieve_financial_eligibility(
    db_session: db.Session,
    employee_id: UUID4,
    employer_id: UUID4,
    leave_start_date: date,
    application_submitted_date: date,
    employment_status: EligibilityEmploymentStatus,
) -> EligibilityResponse:
    """Checks to see if a Benefit Year exists for the given employee's leave start date,
    If one exists, use persisted values for the employee's total wages and employer IAWW
    to serve financial eligibility request.
    Otherwise, Compute financial eligibility to serve the request and store on a new
    Benefit Year values for the employee's total wages and employer IAWW.
    """
    meta: EligibilityLogExtra = {
        "employee_id": employee_id,
        "employer_id": employer_id,
        "benefit_year_id": None,
        "quarterly_wages": "",
    }

    benefit_year_dates = get_benefit_year_dates(leave_start_date)
    effective_date = eligibility_date(benefit_year_dates.start_date, application_submitted_date)
    (benefits_metrics, unemployment_metric) = eligibility_util.fetch_state_metric(
        db_session, benefit_year_dates.start_date
    )

    # Determine if the new given leave date falls within an existing benefit year
    found_benefit_year = benefit_year.get_benefit_year_by_employee_id(
        db_session, employee_id, leave_start_date
    )

    if found_benefit_year:
        meta["benefit_year_id"] = found_benefit_year.benefit_year_id
        employer_average_weekly_wage = benefit_year.get_employer_aww(
            db_session, found_benefit_year, employer_id
        )
        eligibility_response = EligibilityResponse(
            financially_eligible=True,
            description="Financially eligible",
            total_wages=found_benefit_year.total_wages,
            state_average_weekly_wage=benefits_metrics.average_weekly_wage,
            unemployment_minimum=unemployment_metric.unemployment_minimum_earnings,
            employer_average_weekly_wage=employer_average_weekly_wage,
        )
        logger.info(
            "Financial eligibility was loaded from a Benefit Year.",
            extra={**eligibility_response.dict(), **meta},
        )
        return eligibility_response

    # Benefit year was not found, calculate financial eligibility from new data.
    wage_calculator = wage.get_wage_calculator(employee_id, effective_date, db_session)
    wage_data = wage_calculator.compute_employee_dor_wage_data()
    employer_average_weekly_wage = wage_calculator.get_employer_average_weekly_wage(
        employer_id, default=Decimal("0"), should_round=True
    )

    # Convert to dict from default dict to remove defaultdict type from string
    meta["quarterly_wages"] = str(dict(wage_calculator.employer_quarter_wage))

    eligibility_response = _compute_financial_eligibility(
        employment_status=employment_status,
        state_average_weekly_wage=benefits_metrics.average_weekly_wage,
        maximum_weekly_benefit_amount=benefits_metrics.maximum_weekly_benefit_amount,
        unemployment_minimum_earnings=unemployment_metric.unemployment_minimum_earnings,
        wage_data=wage_data,
        employer_average_weekly_wage=employer_average_weekly_wage,
    )

    if eligibility_response.financially_eligible:
        # Store the results to a new Benefit Year
        base_period = wage_calculator.get_base_period_quarters_as_dates()
        employer_contributions = CreateBenefitYearContribution.from_wage_quarters(wage_calculator)
        new_benefit_year = benefit_year.create_benefit_year_by_employee_id(
            db_session,
            employee_id=employee_id,
            leave_start_date=leave_start_date,
            total_wages=eligibility_response.total_wages,
            employer_contributions=employer_contributions,
            base_period_dates=base_period,
        )

        # This should only happen in a race condition where another call to financial eligibility creates a new
        # benefit year after we already checked for an existing benefit year within this call
        if not new_benefit_year:
            logger.info("Could not store the financial eligibility results to a benefit year.")

            found_benefit_year = benefit_year.get_benefit_year_by_employee_id(
                db_session, employee_id, leave_start_date
            )

            if found_benefit_year:
                meta["benefit_year_id"] = found_benefit_year.benefit_year_id
                employer_average_weekly_wage = benefit_year.get_employer_aww(
                    db_session, found_benefit_year, employer_id
                )

                # Update the total wages and employer aww based on the found benefit year
                eligibility_response.total_wages = found_benefit_year.total_wages
                eligibility_response.employer_average_weekly_wage = benefit_year.get_employer_aww(
                    db_session, found_benefit_year, employer_id
                )
                logger.info(
                    "Financial eligibility was loaded from a Benefit Year.",
                    extra={**eligibility_response.dict(), **meta},
                )
                return eligibility_response

            # This should never actually happen, but including some logging as a fail-safe
            else:
                logger.error(
                    "No existing benefit year was found after failing to create a new one",
                    extra={"employee_id": employee_id, "leave_start_date": leave_start_date},
                )
                raise

    logger.info(
        "Financial eligibility was computed without a Benefit Year.",
        extra={**eligibility_response.dict(), **meta},
    )
    return eligibility_response
