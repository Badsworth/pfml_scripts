from typing import Any, Dict, Optional

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.db.models.employees import Claim


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
