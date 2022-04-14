from datetime import date
from typing import Optional, Set

from pydantic import UUID4, Extra, Field

from massgov.pfml.api.models.claims.common import ChangeRequestType, EmployerClaimReview
from massgov.pfml.api.models.common import SearchEnvelope
from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployerClaimReviewRequest(EmployerClaimReview):
    pass


class ClaimSearchTerms(PydanticBaseModel):
    employer_ids: Optional[Set[UUID4]] = Field(None, alias="employer_id")
    # Alias specified for backward compatibility with the UI param "employee_id"
    employee_ids: Optional[Set[UUID4]] = Field(None, alias="employee_id")
    search: Optional[str]
    is_reviewable: Optional[str]
    request_decision: Optional[str]

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


ClaimSearchRequest = SearchEnvelope[ClaimSearchTerms]


class ChangeRequestUpdate(PydanticBaseModel):
    change_request_type: Optional[ChangeRequestType]
    start_date: Optional[date]
    end_date: Optional[date]
