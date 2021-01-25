import flask
from sqlalchemy import desc
from werkzeug.exceptions import NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import READ, requires
from massgov.pfml.db.models.employees import EmployerQuarterlyContribution

logger = massgov.pfml.util.logging.get_logger(__name__)


@requires(READ, "EMPLOYER_API")
def employer_get_most_recent_withholding_dates(employer_id: str) -> flask.Response:
    with app.db_session() as db_session:

        contribution = (
            db_session.query(EmployerQuarterlyContribution)
            .filter(EmployerQuarterlyContribution.employer_id == employer_id)
            .order_by(desc(EmployerQuarterlyContribution.filing_period))
            .first()
        )

        if contribution is None:
            raise NotFound(description="No contributions found")

        response = {"filing_period": contribution.filing_period}

        return response_util.success_response(
            message="Successfully retrieved quarterly contribution", data=response, status_code=200
        ).to_api_response()
