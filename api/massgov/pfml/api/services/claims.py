import massgov.pfml.api.app as app
from massgov.pfml.api.models.claims.responses import DetailedClaimResponse
from massgov.pfml.api.services.fineos_actions import get_absence_periods
from massgov.pfml.db.models.employees import Claim
from massgov.pfml.fineos import exception


class ClaimWithdrawnError(Exception):
    ...


def get_claim_detail(claim: Claim) -> DetailedClaimResponse:
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

    detailed_claim = DetailedClaimResponse.from_orm(claim)
    detailed_claim.absence_periods = absence_periods

    if claim.application:  # type: ignore
        detailed_claim.application_id = claim.application.application_id  # type: ignore

    return detailed_claim


def _is_withdrawn_claim_error(error: exception.FINEOSForbidden) -> bool:
    withdrawn_msg = "User does not have permission to access the resource or the instance data"
    return withdrawn_msg in error.message
