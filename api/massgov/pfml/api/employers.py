from datetime import date

import connexion
import flask
from sqlalchemy import desc
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import READ, requires
from massgov.pfml.api.validation import PaymentRequired
from massgov.pfml.db.models.employees import (
    Employer,
    EmployerQuarterlyContribution,
    UserLeaveAdministrator,
)
from massgov.pfml.util.strings import mask_fein, sanitize_fein

logger = massgov.pfml.util.logging.get_logger(__name__)


@requires(READ, "EMPLOYER_API")
def employer_get_most_recent_withholding_dates(employer_id: str) -> flask.Response:
    with app.db_session() as db_session:

        current_date = date.today()
        last_years_date = date(current_date.year - 1, current_date.month, current_date.day)

        employer = (
            db_session.query(Employer).filter(Employer.employer_id == employer_id).one_or_none()
        )

        if employer is None:
            raise NotFound(description="Employer not found")

        contribution = (
            db_session.query(EmployerQuarterlyContribution)
            .filter(EmployerQuarterlyContribution.employer_id == employer_id)
            .filter(EmployerQuarterlyContribution.employer_total_pfml_contribution > 0)
            .filter(
                EmployerQuarterlyContribution.filing_period.between(last_years_date, current_date)
            )
            .order_by(desc(EmployerQuarterlyContribution.filing_period))
            .first()
        )

        if contribution is None:
            raise PaymentRequired(description="No valid contributions found")

        response = {"filing_period": contribution.filing_period}

        return response_util.success_response(
            message="Successfully retrieved quarterly contribution", data=response, status_code=200
        ).to_api_response()


@requires(READ, "EMPLOYER_API")
def employer_add_fein() -> flask.Response:
    body = connexion.request.json
    fein_to_add = sanitize_fein(body["employer_fein"])

    current_user = app.current_user()
    if current_user is None:
        raise Unauthorized()

    with app.db_session() as db_session:
        employer = (
            db_session.query(Employer).filter(Employer.employer_fein == fein_to_add).one_or_none()
        )

        if employer is None:
            raise BadRequest(description="Invalid FEIN")

        link = UserLeaveAdministrator(
            user_id=current_user.user_id, employer_id=employer.employer_id,
        )
        db_session.add(link)
        db_session.commit()

        response_data = {
            "employer_dba": employer.employer_dba,
            "employer_id": employer.employer_id,
            "employer_fein": mask_fein(employer.employer_fein),
        }

        return response_util.success_response(
            message="Successfully added FEIN to user", status_code=201, data=response_data
        ).to_api_response()
