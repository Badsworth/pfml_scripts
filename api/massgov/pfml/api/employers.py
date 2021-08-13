from datetime import date

import connexion
import flask
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Conflict, NotFound, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import READ, requires
from massgov.pfml.api.models.employers.requests import EmployerAddFeinRequest
from massgov.pfml.api.models.employers.responses import EmployerAddFeinResponse
from massgov.pfml.api.services.employer_rules import (
    EmployerRequiresVerificationDataException,
    validate_employer_being_added,
)
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    PaymentRequired,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.employees import (
    Employer,
    EmployerQuarterlyContribution,
    UserLeaveAdministrator,
)

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
    add_fein_request = EmployerAddFeinRequest.parse_obj(connexion.request.json)
    current_user = app.current_user()

    if current_user is None:
        raise Unauthorized()

    if add_fein_request.employer_fein is None:
        raise ValidationException(
            errors=[
                ValidationErrorDetail(
                    field="employer_fein",
                    type=IssueType.required,
                    message="employer_fein is required",
                )
            ],
        )

    with app.db_session() as db_session:
        employer = (
            db_session.query(Employer)
            .filter(Employer.employer_fein == add_fein_request.employer_fein)
            .one_or_none()
        )

        try:
            validate_employer_being_added(employer)
        except EmployerRequiresVerificationDataException as e:
            return response_util.error_response(
                status_code=PaymentRequired, errors=e.errors, data={}, message="Invalid request"
            ).to_api_response()

        if employer is not None:
            link = UserLeaveAdministrator(
                user_id=current_user.user_id, employer_id=employer.employer_id,
            )
            db_session.add(link)

        try:
            db_session.commit()
        except IntegrityError:
            logger.error("Duplicate employer for user")
            db_session.rollback()

            return response_util.error_response(
                data={},
                status_code=Conflict,
                message="Duplicate employer for user",
                errors=[
                    ValidationErrorDetail(
                        field="employer_fein",
                        type=IssueType.duplicate,
                        message="Duplicate employer for user",
                    )
                ],
            ).to_api_response()

        return response_util.success_response(
            message="Successfully added FEIN to user",
            status_code=201,
            data=EmployerAddFeinResponse.from_orm(employer).dict(),
        ).to_api_response()
