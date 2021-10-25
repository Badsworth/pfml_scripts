from collections import defaultdict
from typing import Any, Dict, Optional

import massgov.pfml.util.logging
from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.claims.responses import (
    AbsencePeriodStatusResponse,
    DetailedClaimResponse,
)
from massgov.pfml.db.models.employees import Claim

logger = massgov.pfml.util.logging.get_logger(__name__)


def get_claim_log_attributes(claim: Optional[Claim]) -> Dict[str, Any]:
    if claim is None:
        return {}

    application = claim.application  # type: ignore
    if application is None:
        return {}

    leave_reason = (
        application.leave_reason.leave_reason_description if application.leave_reason else None
    )

    return {"leave_reason": leave_reason}


def get_claim_review_log_attributes(claim_review: Optional[EmployerClaimReview]) -> Dict[str, Any]:
    if claim_review is None:
        return {}

    relationship_accurate_val = (
        claim_review.believe_relationship_accurate.value
        if claim_review.believe_relationship_accurate
        else None
    )

    return {
        "claim_request.believe_relationship_accurate": relationship_accurate_val,
        "claim_request.employer_decision": claim_review.employer_decision,
        "claim_request.fraud": claim_review.fraud,
        "claim_request.has_amendments": claim_review.has_amendments,
        "claim_request.has_comment": str(bool(claim_review.comment)),
        "claim_request.num_previous_leaves": len(claim_review.previous_leaves),
        "claim_request.num_employer_benefits": len(claim_review.employer_benefits),
        "claim_request.num_concurrent_leave": 1 if claim_review.concurrent_leave else 0,
    }


def log_get_claim_metrics(claim: DetailedClaimResponse) -> None:
    periods = claim.absence_periods if claim.absence_periods is not None else []
    period_dict = defaultdict(list)

    for period in periods:
        period_dict[period.request_decision].append(period)

        # log individual absence period info as well
        _log_get_claim_absence_period(claim, period)

    approved_periods = period_dict["Approved"]
    denied_periods = period_dict["Denied"]
    pending_periods = period_dict["Pending"]

    log_attributes: Dict[str, Any] = {
        "absence_id": claim.fineos_absence_id,
        "num_absence_periods": len(periods),
        "num_approved_absence_periods": len(approved_periods),
        "num_denied_absence_periods": len(denied_periods),
        "num_pending_absence_periods": len(pending_periods),
    }

    # if we have pending absence periods, add logs for the managed requirements
    if len(pending_periods) >= 1:
        requirements = claim.managed_requirements

        if requirements is None or len(requirements) == 0:
            logger.warning(
                "get_claim - No managed requirements found for claim with pending absence period",
                extra={"absence_id": claim.fineos_absence_id},
            )
        else:
            open_requirements = list(filter(lambda r: r.status == "Open", requirements))

            if len(open_requirements) == 0:
                pass  # no open requirements - nothing to log
            elif len(open_requirements) == 1:
                requirement = open_requirements[0]
                log_attributes.update({"employer_follow_up_date": requirement.follow_up_date})
            else:
                logger.warning(
                    "get_claim - Multiple open requirements for claim",
                    extra={"absence_id": claim.fineos_absence_id},
                )

    logger.info("get_claim success", extra=log_attributes)


def _log_get_claim_absence_period(
    claim: DetailedClaimResponse, absence_period: AbsencePeriodStatusResponse
) -> None:
    log_attributes = {
        "absence_id": claim.fineos_absence_id,
        "leave_period_id": absence_period.fineos_leave_period_id,
        "reason": absence_period.reason,
        "request_decision": absence_period.request_decision,
        "start_date": absence_period.absence_period_start_date,
        "end_date": absence_period.absence_period_end_date,
    }

    logger.info("get_claim - Found absence period for claim", extra=log_attributes)
