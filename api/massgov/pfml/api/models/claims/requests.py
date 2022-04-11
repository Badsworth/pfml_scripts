from datetime import date
from enum import Enum
from typing import Optional, Set

from pydantic import UUID4, Extra, Field, validator

from massgov.pfml.api.models.claims.common import ChangeRequestType, EmployerClaimReview
from massgov.pfml.api.models.common import SearchEnvelope
from massgov.pfml.util.pydantic import PydanticBaseModel


class RequestDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"
    CANCELLED = "cancelled"


class EmployerClaimReviewRequest(EmployerClaimReview):
    pass


class ClaimSearchTerms(PydanticBaseModel):
    # Aliases specified for backward compatibility with query params from `GET
    # /claims`
    employer_ids: Optional[Set[UUID4]] = Field(None, alias="employer_id")
    employee_ids: Optional[Set[UUID4]] = Field(None, alias="employee_id")
    search: Optional[str] = None
    is_reviewable: Optional[bool] = None
    request_decision: Optional[RequestDecision] = None

    @validator("employer_ids", "employee_ids", pre=True)
    def split_str(cls, v):  # noqa: B902
        if isinstance(v, str):
            return v.split(",")
        return v

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


ClaimSearchRequest = SearchEnvelope[ClaimSearchTerms]


class ChangeRequestUpdate(PydanticBaseModel):
    change_request_type: Optional[ChangeRequestType]
    start_date: Optional[date]
    end_date: Optional[date]
