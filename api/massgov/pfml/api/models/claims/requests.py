from typing import Optional, Set

from pydantic import UUID4, Extra, Field

from massgov.pfml.api.models.claims.common import EmployerClaimReview
from massgov.pfml.api.models.common import SearchEnvelope
from massgov.pfml.util.pydantic import PydanticBaseModel


class EmployerClaimReviewRequest(EmployerClaimReview):
    pass


class ClaimSearchTerms(PydanticBaseModel):
    employer_ids: Optional[Set[UUID4]] = Field(None, alias="employer_id")
    # Alias specified for backward compatibility with the UI param "employee_id"
    employee_ids: Optional[Set[UUID4]] = Field(None, alias="employee_id")
    claim_status: Optional[str]
    search: Optional[str]
    is_reviewable: Optional[str]
    request_decision: Optional[str]

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


ClaimSearchRequest = SearchEnvelope[ClaimSearchTerms]
