from dataclasses import dataclass
from typing import List

import massgov.pfml.db as db
from massgov.pfml.db.models.employees import AbsenceStatus, Claim, Employee

OUTBOUND_STATUSES = {
    AbsenceStatus.ADJUDICATION.absence_status_id,
    AbsenceStatus.APPROVED.absence_status_id,
    AbsenceStatus.CLOSED.absence_status_id,
    AbsenceStatus.COMPLETED.absence_status_id,
    AbsenceStatus.IN_REVIEW.absence_status_id,
}


# Used by DIA/DUA reductions-process-agency-data to determine if any eligible files were found
@dataclass
class AgencyLoadResult:
    found_pending_files: bool = False


def get_claims_for_outbound(db_session: db.Session) -> List[Claim]:
    """Return claims with the statuses relevant to send to DUA/DIA"""
    return (
        db_session.query(Claim).filter(Claim.fineos_absence_status_id.in_(OUTBOUND_STATUSES)).all()
    )


def get_claimants_for_outbound(db_session: db.Session) -> List[Employee]:
    """Return employees that have claims with the statuses relevant to send to DUA/DIA"""
    return (
        db_session.query(Employee)
        .join(Claim)
        .filter(Claim.fineos_absence_status_id.in_(OUTBOUND_STATUSES))
        .all()
    )
