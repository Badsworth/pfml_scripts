from datetime import date
from typing import List, Optional

from massgov.pfml.api.models.claims.common import (
    Address,
    EmployerBenefit,
    LeaveDetails,
    PreviousLeave,
)
from massgov.pfml.util.pydantic import PydanticBaseModel


class ClaimReviewResponse(PydanticBaseModel):
    date_of_birth: Optional[date]
    employer_benefits: Optional[List[EmployerBenefit]]
    employer_fein: Optional[str]
    fineos_absence_id: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    leave_details: Optional[LeaveDetails]
    middle_name: Optional[str]
    previous_leaves: Optional[List[PreviousLeave]]
    residential_address: Optional[Address]
    tax_identifier: Optional[str]
