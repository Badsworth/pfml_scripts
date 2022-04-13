from dataclasses import dataclass
from typing import List

from sqlalchemy import not_

import massgov.pfml.db as db
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.employees import Claim, Employee

OUTBOUND_STATUSES = {
    AbsenceStatus.ADJUDICATION.absence_status_id,
    AbsenceStatus.APPROVED.absence_status_id,
    AbsenceStatus.CLOSED.absence_status_id,
    AbsenceStatus.COMPLETED.absence_status_id,
    AbsenceStatus.IN_REVIEW.absence_status_id,
}

HISTORICAL_ABSENCE_CASE_PREFIX = "H-"


# Used by DIA/DUA reductions-process-agency-data to determine if any eligible files were found
@dataclass
class AgencyLoadResult:
    found_pending_files: bool = False


def get_claimants_for_outbound(db_session: db.Session) -> List[Employee]:
    """Return employees that have claims with the statuses relevant to send to DUA/DIA"""
    return (
        db_session.query(Employee)
        .join(Claim)
        .filter(Claim.fineos_absence_status_id.in_(OUTBOUND_STATUSES))
        .filter(not_(Claim.fineos_absence_id.startswith(HISTORICAL_ABSENCE_CASE_PREFIX)))
        .all()
    )
