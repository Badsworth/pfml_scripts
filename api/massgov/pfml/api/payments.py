from typing import Optional

import flask
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

import massgov.pfml.api.app as app
import massgov.pfml.api.util.response as response_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.authorization.flask import READ, can
from massgov.pfml.api.services.payments import get_payments_with_status
from massgov.pfml.api.util.claims import user_has_access_to_claim
from massgov.pfml.db.models.employees import Claim

logger = massgov.pfml.util.logging.get_logger(__name__)


def get_payments() -> flask.Response:
    absence_case_id = flask.request.args.get("absence_case_id")
    extra = {"absence_case_id": absence_case_id}

    # OpenApi should catch this before we ever get here
    # But mypy complains anyway, so we need this guard clause
    if absence_case_id is None:
        raise BadRequest()

    is_employer = can(READ, "EMPLOYER_API")
    if is_employer:
        error = response_util.error_response(
            Forbidden, "Employers are not allowed to access claimant payment info", errors=[]
        )
        return error.to_api_response()

    with app.db_session() as db_session:
        current_user = app.current_user()

        claim = _get_claim_from_db(db_session, absence_case_id)

        if claim is None:
            logger.warning(
                "Claim not in PFML database. Could not retrieve payments for claim", extra=extra
            )
            error = response_util.error_response(
                NotFound,
                "No claim found for absence_case_id. Unable to retrieve payments.",
                errors=[],
            )
            return error.to_api_response()

        if not user_has_access_to_claim(claim, current_user):
            logger.warning(
                "get_payments failure - User does not have access to claim.", extra=extra
            )
            error = response_util.error_response(
                Forbidden, "User does not have access to claim.", errors=[]
            )
            return error.to_api_response()

        payments_response = get_payments_with_status(db_session, claim)

    return response_util.success_response(
        message="Successfully retrieved payments", data=payments_response, status_code=200
    ).to_api_response()


def _get_claim_from_db(db_session: db.Session, fineos_absence_id: str) -> Optional[Claim]:
    return (
        db_session.query(Claim).filter(Claim.fineos_absence_id == fineos_absence_id).one_or_none()
    )
