from typing import Dict

import newrelic.agent

import massgov
import massgov.pfml.api.app as app
from massgov.pfml.api.models.claims.responses import DetailedClaimResponse
from massgov.pfml.api.services.fineos_actions import (
    get_absence_periods,
    parse_fineos_absence_periods_to_absence_period_status_response,
)
from massgov.pfml.db.models.employees import Claim
from massgov.pfml.db.queries.absence_periods import sync_customer_api_absence_periods_to_db
from massgov.pfml.fineos import exception

logger = massgov.pfml.util.logging.get_logger(__name__)


class ClaimWithdrawnError(Exception):
    ...


def get_claim_detail(claim: Claim, log_attributes: Dict) -> DetailedClaimResponse:
    absence_id = claim.fineos_absence_id
    if absence_id is None:
        raise Exception("Can't get absence periods from FINEOS - No absence_id for claim")

    employee_tax_id = claim.employee_tax_identifier
    if not employee_tax_id:
        raise Exception("Can't get absence periods from FINEOS - No employee for claim")

    employer_fein = claim.employer_fein
    if not employer_fein:
        raise Exception("Can't get absence periods from FINEOS - No employer for claim")

    absence_periods = []

    with app.db_session() as db_session:
        try:
            absence_periods = get_absence_periods(
                employee_tax_id, employer_fein, absence_id, db_session
            )
        except exception.FINEOSForbidden as error:
            if _is_withdrawn_claim_error(error):
                raise ClaimWithdrawnError
            raise error

        if len(absence_periods) == 0:
            raise Exception("No absence periods found for claim")
        try:
            sync_customer_api_absence_periods_to_db(
                absence_periods, claim, db_session, log_attributes
            )
        except Exception as error:  # catch all exception handler
            logger.error(
                "Failed to handle update of absence period table.",
                extra=log_attributes,
                exc_info=error,
            )
            newrelic.agent.notice_error(attributes=log_attributes)
            db_session.rollback()  # handle insert errors

    detailed_claim = DetailedClaimResponse.from_orm(claim)
    detailed_claim.absence_periods = parse_fineos_absence_periods_to_absence_period_status_response(
        absence_periods
    )

    if claim.application:  # type: ignore
        detailed_claim.application_id = claim.application.application_id  # type: ignore

    return detailed_claim


def _is_withdrawn_claim_error(error: exception.FINEOSForbidden) -> bool:
    withdrawn_msg = "User does not have permission to access the resource or the instance data"
    return withdrawn_msg in error.message
