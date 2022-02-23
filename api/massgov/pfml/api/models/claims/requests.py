from typing import List, Optional

from pydantic import UUID4, Extra, PositiveInt

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.common import OrderDirection
from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployerClaimReviewRequest(EmployerClaimReview):
    pass


class ClaimRequest(PydanticBaseModel, extra=Extra.forbid):
    # A constrant to allow int value greater or equal to 1
    page_size: Optional[PositiveInt]
    page_offset: Optional[PositiveInt]
    order_by: Optional[str]
    order_direction: Optional[OrderDirection] = OrderDirection.desc
    employer_id: Optional[UUID4]
    employee_id: Optional[List[UUID4]]
    claim_status: Optional[str]
    search: Optional[str]
    allow_hrd: Optional[bool]
    is_reviewable: Optional[str]
    request_decision: Optional[str]
