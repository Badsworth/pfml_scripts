from datetime import datetime
from typing import Dict, List
from uuid import UUID

import newrelic.agent
from sqlalchemy.orm.session import Session

import massgov
import massgov.pfml.api.app as app
import massgov.pfml.api.models.claims.common as api_models
import massgov.pfml.db.lookups as db_lookups
import massgov.pfml.db.models.employees as db_models
from massgov.pfml.api.models.claims.responses import DetailedClaimResponse
from massgov.pfml.api.services.fineos_actions import get_absence_periods
from massgov.pfml.db.queries.absence_periods import (
    convert_fineos_absence_period_to_claim_response_absence_period,
    sync_customer_api_absence_periods_to_db,
)
from massgov.pfml.fineos import exception

logger = massgov.pfml.util.logging.get_logger(__name__)


class ClaimWithdrawnError(Exception):
    ...


def get_claim_detail(claim: db_models.Claim, log_attributes: Dict) -> DetailedClaimResponse:
    absence_periods = []

    with app.db_session() as db_session:
        try:
            absence_periods = get_absence_periods(claim, db_session)
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
    detailed_claim.absence_periods = [
        convert_fineos_absence_period_to_claim_response_absence_period(
            absence_period, log_attributes
        )
        for absence_period in absence_periods
    ]
    if claim.application:  # type: ignore
        detailed_claim.application_id = claim.application.application_id  # type: ignore

    return detailed_claim


def _is_withdrawn_claim_error(error: exception.FINEOSForbidden) -> bool:
    withdrawn_msg = "User does not have permission to access the resource or the instance data"
    return withdrawn_msg in error.message


def get_change_requests_from_db(
    claim_id: UUID, db_session: Session
) -> List[db_models.ChangeRequest]:

    change_requests = (
        db_session.query(db_models.ChangeRequest)
        .filter(db_models.ChangeRequest.claim_id == claim_id)
        .all()
    )

    return change_requests


def add_change_request_to_db(
    change_request: api_models.ChangeRequest, claim_id: UUID, submitted_time: datetime
) -> db_models.ChangeRequest:
    with app.db_session() as db_session:
        change_request_type = db_lookups.by_value(
            db_session, db_models.LkChangeRequestType, change_request.change_request_type
        )
        # needed for linter
        assert isinstance(change_request_type, db_models.LkChangeRequestType)
        db_request = change_request.to_db_model(change_request_type, claim_id, submitted_time)
        db_session.add(db_request)
        return db_request
