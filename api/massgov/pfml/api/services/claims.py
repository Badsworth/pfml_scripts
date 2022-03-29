from typing import Dict, Optional

import newrelic.agent

import massgov
import massgov.pfml.api.app as app
from massgov.pfml.api.models.claims.responses import DetailedClaimResponse
from massgov.pfml.api.services.fineos_actions import get_absence_periods_from_claim
from massgov.pfml.db.models.employees import Claim, Employee, TaxIdentifier
from massgov.pfml.db.queries.absence_periods import (
    convert_fineos_absence_period_to_claim_response_absence_period,
    sync_customer_api_absence_periods_to_db,
)
from massgov.pfml.fineos import exception

logger = massgov.pfml.util.logging.get_logger(__name__)


class ClaimWithdrawnError(Exception):
    ...


def get_claim_detail(claim: Claim, log_attributes: Dict) -> DetailedClaimResponse:
    absence_periods = []

    with app.db_session() as db_session:
        try:
            absence_periods = get_absence_periods_from_claim(claim, db_session)
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


def get_claim_from_db(fineos_absence_id: Optional[str]) -> Optional[Claim]:
    if fineos_absence_id is None:
        return None

    with app.db_session() as db_session:
        claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

    return claim


def maybe_update_employee_relationship(fineos_absence_id: str, tax_identifier: str) -> None:
    """
    Helper to add employee relationship to the claim if it is missing.

    The association could be missing for claims created via the contact center directly in FINEOS
    the notification endpoint fails to set the association, and if the leave admin visits the review page
    prior to the nightly extract.
    """

    with app.db_session() as db_session:
        claim = claim = (
            db_session.query(Claim)
            .filter(Claim.fineos_absence_id == fineos_absence_id)
            .one_or_none()
        )

        if not claim:
            return
        if claim.employee_id:
            return

        try:
            employee = (
                db_session.query(Employee)
                .join(TaxIdentifier)
                .filter(TaxIdentifier.tax_identifier == tax_identifier)
                .one_or_none()
            )
            if employee:
                claim.employee_id = employee.employee_id
        except Exception:
            logger.warning(
                "Failed to update employee relationship for claim",
                extra={"absence_case_id": claim.fineos_absence_id, "claim_id": claim.claim_id},
                exc_info=True,
            )

        db_session.commit()
        return
