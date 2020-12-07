from datetime import date
from typing import List, Optional

from massgov.pfml.api.models.claims.common import (
    Address,
    EmployerBenefit,
    LeaveDetails,
    PreviousLeave,
)
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import (
    FEINFormattedStr,
    MaskedDateStr,
    MaskedTaxIdFormattedStr,
)


class ClaimReviewResponse(PydanticBaseModel):
    date_of_birth: Optional[MaskedDateStr]
    employer_benefits: Optional[List[EmployerBenefit]]
    employer_fein: Optional[FEINFormattedStr]
    fineos_absence_id: Optional[str]
    first_name: Optional[str]
    hours_worked_per_week: Optional[int]
    last_name: Optional[str]
    leave_details: Optional[LeaveDetails]
    middle_name: Optional[str]
    previous_leaves: Optional[List[PreviousLeave]]
    residential_address: Optional[Address]
    tax_identifier: Optional[MaskedTaxIdFormattedStr]
    follow_up_date: Optional[date]


class DocumentResponse(PydanticBaseModel):
    created_at: Optional[date]
    document_type: Optional[str]
    content_type: Optional[str]
    fineos_document_id: Optional[str]
    name: str
    description: str
