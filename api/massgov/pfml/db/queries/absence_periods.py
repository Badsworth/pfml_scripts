from typing import Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm.session import Session

import massgov
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    AbsencePeriodType,
    AbsenceReason,
    AbsenceReasonQualifierOne,
    AbsenceReasonQualifierTwo,
    LeaveRequestDecision,
)
from massgov.pfml.fineos.models.group_client_api import Period
from massgov.pfml.fineos.models.group_client_api.spec import LeaveRequest

logger = massgov.pfml.util.logging.get_logger(__name__)


def split_fineos_absence_period_id(id: str) -> Tuple[int, int]:
    period_ids = id.split("-")
    return int(period_ids[1]), int(period_ids[2])


def get_absence_period_by_claim_id_and_fineos_ids(
    db_session: Session, claim_id: UUID, class_id: int, index_id: int
) -> Optional[AbsencePeriod]:
    return (
        db_session.query(AbsencePeriod)
        .filter(
            AbsencePeriod.claim_id == claim_id,
            AbsencePeriod.fineos_absence_period_class_id == class_id,
            AbsencePeriod.fineos_absence_period_index_id == index_id,
        )
        .one_or_none()
    )


def create_absence_period_from_fineos_id_and_claim_id(
    claim_id: UUID, class_id: int, index_id: int
) -> AbsencePeriod:
    absence_period = AbsencePeriod()
    absence_period.fineos_absence_period_class_id = class_id
    absence_period.fineos_absence_period_index_id = index_id
    absence_period.claim_id = claim_id
    return absence_period


def parse_fineos_period_leave_request(
    db_absence_period: AbsencePeriod, leave_request: LeaveRequest
) -> AbsencePeriod:
    if leave_request.qualifier1:
        db_absence_period.absence_reason_qualifier_one_id = AbsenceReasonQualifierOne.get_id(
            leave_request.qualifier1
        )
    if leave_request.qualifier2:
        db_absence_period.absence_reason_qualifier_two_id = AbsenceReasonQualifierTwo.get_id(
            leave_request.qualifier2
        )
    db_absence_period.absence_reason_id = AbsenceReason.get_id(leave_request.reasonName)
    db_absence_period.leave_request_decision_id = LeaveRequestDecision.get_id(
        leave_request.decisionStatus
    )
    return db_absence_period


def upsert_absence_period_from_fineos_period(
    db_session: Session, claim_id: UUID, fineos_period: Period, log_attributes: Dict
) -> None:
    """
    Update or Insert Fineos Period from the Group Client API
    """
    if fineos_period.leaveRequest is None:
        logger.error(
            "Failed to extract leave request from fineos period.", extra=log_attributes,
        )
        return
    if fineos_period.periodReference:
        class_id, index_id = split_fineos_absence_period_id(fineos_period.periodReference)
    else:
        logger.error(
            "Failed to extract class and index id.", extra=log_attributes,
        )
        return

    db_absence_period = get_absence_period_by_claim_id_and_fineos_ids(
        db_session, claim_id, class_id, index_id
    )
    if db_absence_period is None:
        db_absence_period = create_absence_period_from_fineos_id_and_claim_id(
            claim_id, class_id, index_id
        )
    db_absence_period.absence_period_start_date = fineos_period.startDate
    db_absence_period.absence_period_end_date = fineos_period.endDate
    db_absence_period.absence_period_type_id = AbsencePeriodType.get_id(fineos_period.type)
    db_absence_period = parse_fineos_period_leave_request(
        db_absence_period, fineos_period.leaveRequest
    )
    db_session.add(db_absence_period)
    return
