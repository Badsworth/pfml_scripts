import flask
from sqlalchemy import desc
from sqlalchemy.orm.exc import MultipleResultsFound
from werkzeug.exceptions import BadRequest, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import READ, requires
from massgov.pfml.db.models.employees import Employer, EmployerQuarterlyContribution
from massgov.pfml.util.strings import sanitize_fein

logger = massgov.pfml.util.logging.get_logger(__name__)


@requires(READ, "EMPLOYER_API")
def employer_get_most_recent_withholding_dates(employer_fein: str) -> flask.Response:
    with app.db_session() as db_session:

        try:
            employer = (
                db_session.query(Employer)
                .filter(Employer.employer_fein == sanitize_fein(employer_fein))
                .one_or_none()
            )
        except MultipleResultsFound as exc:
            logger.error("Multiple employers found for specified FEIN", exc_info=exc)
            return response_util.error_response(
                status_code=BadRequest,
                message="Multiple employers found for specified FEIN",
                errors=[],
            ).to_api_response()

        if employer is None:
            raise BadRequest(description="Invalid FEIN")

        contribution = (
            db_session.query(EmployerQuarterlyContribution)
            .filter(EmployerQuarterlyContribution.employer_id == employer.employer_id)
            .order_by(desc(EmployerQuarterlyContribution.filing_period))
            .first()
        )

        if contribution is None:
            raise NotFound(description="No contributions found")

        response = {"filing_period": contribution.filing_period}

        return response_util.success_response(
            message="Successfully retrieved quarterly contribution", data=response, status_code=200
        ).to_api_response()
