from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.eligibility.eligibility as eligibility
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import CREATE, ensure
from massgov.pfml.api.models.applications.common import EligibilityEmploymentStatus
from massgov.pfml.db.models.employees import Employee, Employer, TaxIdentifier
from massgov.pfml.util.pydantic import PydanticBaseModel

logger = massgov.pfml.util.logging.get_logger(__name__)


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


def eligibility_post():
    # Bounce them out if they do not have access
    ensure(CREATE, "Financial Eligibility Calculation")

    request = EligibilityRequest.parse_obj(connexion.request.json)
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
        return response_util.success_response(
            message="success",
            data=EligibilityResponse(
                financially_eligible=False,
                description="Not Known: invalid employment status",
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

        employee_id: UUID = UUID(str(employee.employee_id))
        employer_id: UUID = UUID(str(employer.employer_id))

    try:
        wage_data_response = eligibility.compute_financial_eligibility(
            db_session,
            employee_id,
            employer_id,
            fein,
            leave_start_date,
            application_submitted_date,
            employment_status,
        )

        logger.info(
            "Calculated financial eligibility",
            extra={
                "financially_eligible": wage_data_response.financially_eligible,
                "description": wage_data_response.description,
                "employee_id": employee_id,
                "employer_id": employer_id,
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
