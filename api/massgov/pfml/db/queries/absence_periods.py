from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

import newrelic.agent
from sqlalchemy.orm.session import Session

import massgov
import massgov.pfml.util.newrelic.events as newrelic_util
from massgov.pfml.api.models.claims.responses import (
    AbsencePeriodResponse,
    remap_absence_period_type,
)
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.models.absences import (
    AbsencePeriodType,
    AbsenceReason,
    AbsenceReasonQualifierOne,
    AbsenceReasonQualifierTwo,
)
from massgov.pfml.db.models.employees import AbsencePeriod, Claim, LeaveRequestDecision
from massgov.pfml.fineos.models.customer_api import AbsencePeriod as FineosAbsencePeriod
from massgov.pfml.fineos.models.group_client_api import Period
from massgov.pfml.fineos.models.group_client_api.spec import LeaveRequest

logger = massgov.pfml.util.logging.get_logger(__name__)


def split_fineos_absence_period_id(id: str) -> Tuple[int, int]:
    period_ids = id.split("-")
    if len(period_ids) < 3:
        message = "Invalid fineos absence period unique identifier (id/periodReference)"
        validation_error = ValidationErrorDetail(
            message=message, type=IssueType.fineos_client, field="id/periodReference"
        )
        raise ValidationException(errors=[validation_error], message=message, data={})
    return int(period_ids[1]), int(period_ids[2])


def split_fineos_leave_request_id(id: str, log_attributes: Dict) -> int:
    period_ids = id.split("-")
    if len(period_ids) != 3 or not period_ids[2].isdigit():
        message = f"Invalid fineos leave request id format, leave request id: {id}"
        logger.error(
            message, extra={"fineos_leave_request_id": id, **log_attributes},
        )
        validation_error = ValidationErrorDetail(
            message=message, type=IssueType.value_error, field="id/periodReference"
        )
        raise ValidationException(errors=[validation_error], message=message, data={})
    return int(period_ids[2])


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


def get_employee_absence_periods(
    db_session: Session,
    employee_id: UUID,
    fineos_absence_status_ids: Optional[List[int]] = None,
    absence_period_type_id: Optional[int] = None,
) -> List[AbsencePeriod]:
    filters = [Claim.employee_id == employee_id]
    if fineos_absence_status_ids is not None and len(fineos_absence_status_ids) > 0:
        filters.append(Claim.fineos_absence_status_id.in_(fineos_absence_status_ids))

    if absence_period_type_id is not None:
        filters.append(AbsencePeriod.absence_period_type_id == absence_period_type_id)

    return (
        db_session.query(AbsencePeriod)
        .join(Claim)
        .filter(*filters)
        .order_by(AbsencePeriod.absence_period_start_date)
        .all()
    )


def get_employee_absence_periods_for_leave_request(
    db_session: Session, employee_id: UUID, fineos_leave_request_id: int
) -> List[AbsencePeriod]:
    absence_periods: List[AbsencePeriod] = (
        db_session.query(AbsencePeriod)
        .join(Claim)
        .filter(
            Claim.employee_id == employee_id,
            AbsencePeriod.fineos_leave_request_id == fineos_leave_request_id,
        )
        .order_by(AbsencePeriod.absence_period_start_date)
        .all()
    )
    return absence_periods


def create_absence_period_from_fineos_id_and_claim_id(
    claim_id: UUID, class_id: int, index_id: int
) -> AbsencePeriod:
    absence_period = AbsencePeriod()
    absence_period.fineos_absence_period_class_id = class_id
    absence_period.fineos_absence_period_index_id = index_id
    absence_period.claim_id = claim_id
    return absence_period


def parse_fineos_period_leave_request(
    db_absence_period: AbsencePeriod, leave_request: LeaveRequest, log_attributes: Dict
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
    if leave_request.id:
        db_absence_period.fineos_leave_request_id = split_fineos_leave_request_id(
            leave_request.id, log_attributes
        )
    return db_absence_period


def upsert_absence_period_from_fineos_period(
    db_session: Session,
    claim_id: UUID,
    fineos_period: Union[Period, FineosAbsencePeriod],
    log_attributes: Dict,
) -> None:
    """
    Update or Insert Fineos Period from the Group Client API
    or Fineos Absence Period from the Customer Client API
    """
    fineos_period = convert_customer_api_period_to_group_client_period(fineos_period)

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
        db_absence_period, fineos_period.leaveRequest, log_attributes
    )
    db_session.add(db_absence_period)
    return


def convert_customer_api_period_to_group_client_period(
    fineos_absence_period: Union[Period, FineosAbsencePeriod]
) -> Period:
    """
    convert from Customer Client API model to Group Client API model
    """
    if isinstance(fineos_absence_period, Period):
        return fineos_absence_period
    leave_request = LeaveRequest(
        qualifier1=fineos_absence_period.reasonQualifier1,
        qualifier2=fineos_absence_period.reasonQualifier2,
        reasonName=fineos_absence_period.reason,
        decisionStatus=fineos_absence_period.requestStatus,
    )
    return Period(
        periodReference=fineos_absence_period.id,
        startDate=fineos_absence_period.startDate,
        endDate=fineos_absence_period.endDate,
        type=fineos_absence_period.absenceType,
        leaveRequest=leave_request,
    )


def convert_fineos_absence_period_to_claim_response_absence_period(
    period: Union[Period, FineosAbsencePeriod], log_attributes: Dict
) -> AbsencePeriodResponse:

    fineos_period = convert_customer_api_period_to_group_client_period(period)
    absence_period = AbsencePeriodResponse()

    absence_period.absence_period_start_date = fineos_period.startDate
    absence_period.absence_period_end_date = fineos_period.endDate
    absence_period.period_type = remap_absence_period_type(fineos_period.type)
    if fineos_period.leaveRequest is None:
        newrelic_util.log_and_capture_exception(
            "Failed to extract leave request from fineos period.", extra=log_attributes
        )
        return absence_period
    leave_request = fineos_period.leaveRequest
    absence_period.reason = leave_request.reasonName
    absence_period.reason_qualifier_one = leave_request.qualifier1
    absence_period.reason_qualifier_two = leave_request.qualifier2
    absence_period.request_decision = leave_request.decisionStatus
    if leave_request.id:
        try:
            absence_period.fineos_leave_request_id = split_fineos_leave_request_id(
                leave_request.id, log_attributes
            )
        except ValidationException:
            newrelic.agent.notice_error(attributes=log_attributes)
    return absence_period


def sync_customer_api_absence_periods_to_db(
    absence_periods: List[FineosAbsencePeriod],
    claim: Claim,
    db_session: Session,
    log_attributes: Dict,
) -> None:
    # add/update absence period table
    try:
        for absence_period in absence_periods:
            upsert_absence_period_from_fineos_period(
                db_session, claim.claim_id, absence_period, log_attributes
            )
    except Exception as error:
        logger.exception(
            "Failed while populating AbsencePeriod Table", extra={**log_attributes},
        )
        raise error
    # only commit if there were no errors
    db_session.commit()
    return
