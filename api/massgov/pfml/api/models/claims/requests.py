from typing import Optional, Set

from pydantic import UUID4, Extra, Field, PositiveInt

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.common import OrderDirection
from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployerClaimReviewRequest(EmployerClaimReview):
    pass


class ClaimRequest(PydanticBaseModel):
    # A constrant to allow int value greater or equal to 1
    page_size: Optional[PositiveInt]
    page_offset: Optional[PositiveInt]
    order_by: Optional[str]
    order_direction: Optional[OrderDirection] = OrderDirection.desc
    employer_ids: Optional[Set[UUID4]] = Field(None, alias="employer_id")
    # Alias specified for backward compatibility with the UI param "employee_id"
    employee_ids: Optional[Set[UUID4]] = Field(None, alias="employee_id")
    claim_status: Optional[str]
    search: Optional[str]
    allow_hrd: Optional[bool]
    is_reviewable: Optional[str]
    request_decision: Optional[str]

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True
