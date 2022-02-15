from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

import connexion
from sqlalchemy import desc
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.eligibility.eligibility as eligibility
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.models.applications.common import EligibilityEmploymentStatus
from massgov.pfml.db.models.applications import Application
from massgov.pfml.db.models.employees import BenefitYear, Employee, Employer, TaxIdentifier
from massgov.pfml.util.pydantic import PydanticBaseModel

logger = massgov.pfml.util.logging.get_logger(__name__)


class BenefitYearsSearchRequest(PydanticBaseModel):
    employee_id: Optional[str]


class BenefitYearsSearchResponse(PydanticBaseModel):
    benefit_year_end_date: date
    benefit_year_start_date: date
    employee_id: str
    current_benefit_year: bool

    @classmethod
    def from_orm(cls, benefit_year: BenefitYear) -> "BenefitYearsSearchResponse":
        today = date.today()
        current_benefit_year = today >= benefit_year.start_date and today <= benefit_year.end_date
        return BenefitYearsSearchResponse(
            benefit_year_end_date=benefit_year.end_date,
            benefit_year_start_date=benefit_year.start_date,
            employee_id=benefit_year.employee_id.__str__(),
            current_benefit_year=current_benefit_year,
        )


class EligibilityResponse(PydanticBaseModel):
    financially_eligible: bool
    description: str
    total_wages: Optional[Decimal]
    state_average_weekly_wage: Optional[int]
    unemployment_minimum: Optional[int]
    employer_average_weekly_wage: Optional[Decimal]


class EligibilityRequest(PydanticBaseModel):
    employer_fein: str
    leave_start_date: date
    application_submitted_date: date
    employment_status: EligibilityEmploymentStatus
    tax_identifier: str


def benefit_years_search():
    with app.db_session() as db_session:
        current_user = app.current_user()
        # Grab all the applications that the user has submitted
        applications = (
            db_session.query(Application).filter(Application.user_id == current_user.user_id).all()
        )
        # Filter to only applications where the employee has been set (via tax_id).
        # See: https://github.com/EOLWD/pfml/blob/0ac0c389695edf9338c23142eef141a2d4399b91/api/massgov/pfml/db/models/applications.py#L390
        valid_applications = [va for va in applications if va.employee]
        if len(valid_applications) == 0:
            logger.info("Benefit years search did not return any applications for the user")
            return response_util.success_response(message="success", data=[]).to_api_response()
        else:
            employee_ids = []
            for valid_application in valid_applications:
                # This check is here for mypy, but this array is already filtered to only
                # include applications where the employee can be found
                if valid_application.employee:
                    employee_ids.append(valid_application.employee.employee_id)
            benefit_years = (
                db_session.query(BenefitYear)
                .filter(BenefitYear.employee_id.in_(employee_ids))
                .order_by(BenefitYear.employee_id, desc(BenefitYear.start_date))
                .all()
            )
            benefit_year_responses = []
            for benefit_year in benefit_years:
                benefit_year_responses.append(
                    BenefitYearsSearchResponse.from_orm(benefit_year).dict()
                )
            return response_util.success_response(
                message="success", data=benefit_year_responses
            ).to_api_response()


def eligibility_post():
    # Bounce them out if they do not have access
    ensure(CREATE, "Financial Eligibility Calculation")

    request = EligibilityRequest.parse_obj(connexion.request.json)

    logger.info(
        "Received financial eligibility request",
        extra={
            "leave_start_date": str(request.leave_start_date),
            "application_submitted_date": str(request.application_submitted_date),
            "employment_status": request.employment_status,
        },
    )

    tax_identifier = request.tax_identifier
    fein = request.employer_fein
    leave_start_date = request.leave_start_date
    application_submitted_date = request.application_submitted_date
    employment_status = request.employment_status

    if employment_status not in [
        EligibilityEmploymentStatus.employed,
        EligibilityEmploymentStatus.self_employed,
        EligibilityEmploymentStatus.unemployed,
    ]:
        invalid_employment_status_description = "Not Known: invalid employment status"
        logger.info(
            "Cannot calculate financial eligibility: invalid employment status",
            extra={
                "employment_status": request.employment_status,
                "financially_eligible": False,
                "description": invalid_employment_status_description,
            },
        )
        return response_util.success_response(
            message="success",
            data=EligibilityResponse(
                financially_eligible=False,
                description=invalid_employment_status_description,
                total_wages=None,
                state_average_weekly_wage=None,
                unemployment_minimum=None,
                employer_average_weekly_wage=None,
            ).dict(),
        ).to_api_response()

    with app.db_session() as db_session:
        tax_record = (
            db_session.query(TaxIdentifier)
            .filter_by(tax_identifier=tax_identifier.replace("-", ""))
            .first()
        )
        employer = db_session.query(Employer).filter_by(employer_fein=fein.replace("-", "")).first()
        employee = db_session.query(Employee).filter_by(tax_identifier=tax_record).first()

        if tax_record is None or employer is None or employee is None:
            logger.warning("Unable to find record. Tax record or employee or employer is None")
            return response_util.error_response(
                status_code=NotFound, message="Non-eligible employee", errors=[], data={},
            ).to_api_response()

        employee_id: UUID = employee.employee_id
        employer_id: UUID = employer.employer_id

    try:
        wage_data_response = eligibility.retrieve_financial_eligibility(
            db_session,
            employee_id,
            employer_id,
            leave_start_date,
            application_submitted_date,
            employment_status,
        )

        logger.info(
            "Calculated financial eligibility",
            extra={
                "employee_id": employee_id,
                "employer_id": employer_id,
                "financially_eligible": wage_data_response.financially_eligible,
                "description": wage_data_response.description,
                "total_wages": str(wage_data_response.total_wages),
                "state_average_weekly_wage": wage_data_response.state_average_weekly_wage,
                "unemployment_minimum": wage_data_response.unemployment_minimum,
                "employer_average_weekly_wage": str(
                    wage_data_response.employer_average_weekly_wage
                ),
            },
        )

        return response_util.success_response(
            message="Calculated financial eligibility",
            data=EligibilityResponse.from_orm(wage_data_response).dict(exclude_none=True),
        ).to_api_response()
    except Exception:
        logger.exception(
            "Compute financial eligibility failed",
            extra={"employee_id": employee_id, "employer_id": employer_id},
        )
        raise
