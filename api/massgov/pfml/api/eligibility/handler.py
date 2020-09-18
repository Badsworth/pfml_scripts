from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    Employee,
    Employer,
    TaxIdentifier,
    WagesAndContributions,
)
from massgov.pfml.util.pydantic import PydanticBaseModel

from . import eligibility_date, eligibility_util, wage

logger = massgov.pfml.util.logging.get_logger(__name__)


class EligibilityResponse(PydanticBaseModel):
    financially_eligible: bool
    description: str
    total_wages: Optional[Decimal]
    state_average_weekly_wage: Optional[int]
    unemployment_minimum: Optional[int]


class EligibilityRequest(PydanticBaseModel):
    employer_fein: str
    leave_start_date: date
    application_submitted_date: date
    employment_status: str
    tax_identifier: str


def eligibility_post():
    request = EligibilityRequest.parse_obj(connexion.request.json)
    tax_identifier = request.tax_identifier
    fein = request.employer_fein
    leave_start_date = request.leave_start_date
    application_submitted_date = request.application_submitted_date

    _eligibility_date = eligibility_date.eligibility_date(
        leave_start_date, application_submitted_date
    )

    with app.db_session() as db_session:
        tax_record = (
            db_session.query(TaxIdentifier)
            .filter_by(tax_identifier=tax_identifier.replace("-", ""))
            .first()
        )
        employer = db_session.query(Employer).filter_by(employer_fein=fein.replace("-", "")).first()
        employee = db_session.query(Employee).filter_by(tax_identifier=tax_record).first()

        if tax_record is None or employer is None or employee is None:
            logger.error(
                "Unable to find record. Tax_Identifier={}, Employee={}, Employer={}".format(
                    tax_record, employee, employer
                )
            )
            return response_util.error_response(
                status_code=NotFound,
                message="Unable to find tax record for given tax_identifier={} and employer fein={}".format(
                    tax_identifier, fein
                ),
                errors=[],
                data={},
            ).to_api_response()

        employee_id: UUID = UUID(str(employee.employee_id))
        employer_id = employer.employer_id

        wages_and_contribution = (
            db_session.query(WagesAndContributions)
            .filter_by(employee_id=employee_id, employer_id=employer_id)
            .all()
        )
        state_metric_data = eligibility_util.fetch_state_metric(db_session, _eligibility_date)

    if not wages_and_contribution:
        logger.info("No wages found for employee {}".format(tax_identifier))
        no_wage_data_response = EligibilityResponse(
            financially_eligible=False,
            description="No wages found for employee {}".format(tax_identifier),
        )
        return response_util.success_response(
            message="Unable to find wage records for employee={} under employer={}".format(
                tax_identifier, fein
            ),
            data=EligibilityResponse.from_orm(no_wage_data_response).dict(exclude_none=True),
        ).to_api_response()

    total_wages = wage.get_total_wage(employee_id, _eligibility_date, db_session)

    if state_metric_data:
        state_average_weekly_wage = state_metric_data.average_weekly_wage
        unemployment_minimum = state_metric_data.unemployment_minimum_earnings
        wage_data_response = EligibilityResponse(
            financially_eligible=True,
            description="For employee={}, the total_wage={} and state_average_weekly_wage={} and the unemployment_minimum={}".format(
                tax_identifier, total_wages, state_average_weekly_wage, unemployment_minimum
            ),
            total_wages=total_wages,
            state_average_weekly_wage=state_average_weekly_wage,
            unemployment_minimum=unemployment_minimum,
        )
    else:
        wage_data_response = EligibilityResponse(
            financially_eligible=True,
            description="For employee={}, the total_wage={} and state_average_weekly_wage={} and the unemployment_minimum={}".format(
                tax_identifier, total_wages, state_average_weekly_wage, unemployment_minimum
            ),
            total_wages=total_wages,
        )

    return response_util.success_response(
        message="Calculated total_wage and average_weekly_wage for employee={}".format(
            tax_identifier
        ),
        data=EligibilityResponse.from_orm(wage_data_response).dict(exclude_none=True),
    ).to_api_response()
