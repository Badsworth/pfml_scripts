from typing import Any, Dict, Optional, Union

import massgov.pfml.util.logging
from massgov.pfml.api.models.claims.responses import AbsencePeriodResponse
from massgov.pfml.db.models.absences import AbsencePeriodType, AbsenceReason
from massgov.pfml.db.models.employees import AbsencePeriod, LeaveRequestDecision
from massgov.pfml.util.datetime import date_to_isoformat

logger = massgov.pfml.util.logging.get_logger(__name__)


def get_absence_period_log_attributes(
    absence_period: Union[AbsencePeriod, AbsencePeriodResponse],
) -> Dict[str, Any]:
    if isinstance(absence_period, AbsencePeriodResponse):
        absence_period_type = absence_period.period_type
        reason = absence_period.reason
        request_decision = absence_period.request_decision
        # These aren't set on this model:
        class_id = None
        index_id = None
    else:
        class_id = absence_period.fineos_absence_period_class_id
        index_id = absence_period.fineos_absence_period_index_id
        absence_period_type = (
            AbsencePeriodType.get_description(absence_period.absence_period_type_id)
            if absence_period.absence_period_type_id
            else None
        )
        reason = (
            AbsenceReason.get_description(absence_period.absence_reason_id)
            if absence_period.absence_reason_id
            else None
        )
        request_decision = (
            LeaveRequestDecision.get_description(absence_period.leave_request_decision_id)
            if absence_period.leave_request_decision_id
            else None
        )

    return {
        "absence_period_class_id": class_id,
        "absence_period_index_id": index_id,
        "start_date": date_to_isoformat(absence_period.absence_period_start_date),
        "end_date": date_to_isoformat(absence_period.absence_period_end_date),
        "leave_request_id": absence_period.fineos_leave_request_id,
        "absence_period_type": absence_period_type,
        "reason": reason,
        "request_decision": request_decision,
    }


def log_absence_period_response(
    fineos_absence_id: Optional[str], absence_period: AbsencePeriodResponse, message: str
) -> None:
    log_attributes = {
        "absence_id": fineos_absence_id,
        "absence_case_id": fineos_absence_id,
        **get_absence_period_log_attributes(absence_period),
    }

    logger.info(message, extra=log_attributes)
