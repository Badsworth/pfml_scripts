from datetime import date

import connexion
import flask
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, Unauthorized

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml.api.authorization.flask import READ, requires
from massgov.pfml.api.validation.exceptions import PaymentRequired
from massgov.pfml.db.models.employees import (
    Employer,
    EmployerQuarterlyContribution,
    UserLeaveAdministrator,
    UserLeaveAdminDepartment,
)
from massgov.pfml.util import feature_gate
from massgov.pfml.util.strings import format_fein, sanitize_fein

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

        if not employer or not employer.fineos_employer_id:
            return response_util.error_response(
                status_code=BadRequest,
                message="Invalid FEIN",
                errors=[
                    response_util.custom_issue(
                        type="invalid", message="Invalid FEIN", field="employer_fein",
                    )
                ],
                data={},
            ).to_api_response()

        verification_required = app.get_config().enforce_verification or feature_gate.check_enabled(
            feature_name=feature_gate.LEAVE_ADMIN_VERIFICATION,
            user_email=current_user.email_address,
        )

        if verification_required and employer.has_verification_data is False:
            return response_util.error_response(
                status_code=PaymentRequired,
                message="Employer has no verification data",
                errors=[
                    response_util.custom_issue(
                        type="employer_verification_data_required",
                        message="Employer has no verification data",
                        rule="employer_requires_verification_data",
                        field="employer_fein",
                    )
                ],
                data={},
            ).to_api_response()

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
                    response_util.custom_issue(
                        field="employer_fein",
                        type="duplicate",
                        message="Duplicate employer for user",
                    )
                ],
            ).to_api_response()

        response_data = {
            "employer_dba": employer.employer_dba,
            "employer_id": employer.employer_id,
            "employer_fein": format_fein(employer.employer_fein),
        }

        return response_util.success_response(
            message="Successfully added FEIN to user", status_code=201, data=response_data
        ).to_api_response()


def employer_add_departments() -> flask.Response:
    body = connexion.request.json
    fein = sanitize_fein(body["employer_fein"])
    departments = body["departments"]

    current_user = app.current_user()
    if current_user is None:
        raise Unauthorized()

    with app.db_session() as db_session:

        employer = (
            db_session.query(Employer).filter(Employer.employer_fein == fein).one_or_none()
        )

        if not employer:
            return response_util.error_response(
                status_code=BadRequest,
                message="Invalid FEIN",
                errors=[
                    response_util.custom_issue(
                        type="invalid", message="Invalid FEIN", field="employer_fein",
                    )
                ],
                data={},
            ).to_api_response()

        leave_admin = (
            db_session.query(UserLeaveAdministrator).filter(UserLeaveAdministrator.employer_id == employer.employer_id and UserLeaveAdministrator.user_id == current_user.user_id).one()
        )
        # @todo: in the UserLeaveAdministrator model to auto fetch departments for the portal
        
        for department in departments:
            newLeaveAdminDepartment = UserLeaveAdminDepartment(
                department_id=department
                user_leave_administrator_id=leave_admin.user_leave_administrator_id
                user_id=current_user.user_id
                employer_id=employer.employer_id
            )

            db_session.add(newLeaveAdminDepartment)

        db_session.commit()
        db_session.refresh(leave_admin)
        
    return leave_admin
