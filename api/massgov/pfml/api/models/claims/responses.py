from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import UUID4

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


class FineosAbsenceStatusResponse(PydanticBaseModel):
    absence_status_description: str


class ClaimTypeResponse(PydanticBaseModel):
    claim_type_description: str


class EmployerResponse(PydanticBaseModel):
    employer_dba: str
    employer_fein: FEINFormattedStr


class EmployeeResponse(PydanticBaseModel):
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    other_name: Optional[str]


class ClaimResponse(PydanticBaseModel):
    fineos_absence_id: Optional[str]
    employer: Optional[EmployerResponse]
    employee: Optional[EmployeeResponse]
    fineos_notification_id: Optional[str]
    absence_period_start_date: Optional[date]
    absence_period_end_date: Optional[date]
    fineos_absence_status: Optional[FineosAbsenceStatusResponse]
    claim_type: Optional[ClaimTypeResponse]
    created_at: Optional[date]


class ClaimReviewResponse(PydanticBaseModel):
    date_of_birth: Optional[MaskedDateStr]
    employer_benefits: Optional[List[EmployerBenefit]]
    employer_dba: str
    employer_fein: FEINFormattedStr
    employer_id: UUID4
    fineos_absence_id: Optional[str]
    first_name: Optional[str]
    hours_worked_per_week: Optional[Decimal]
    last_name: Optional[str]
    leave_details: Optional[LeaveDetails]
    middle_name: Optional[str]
    previous_leaves: Optional[List[PreviousLeave]]
    residential_address: Optional[Address]
    tax_identifier: Optional[MaskedTaxIdFormattedStr]
    follow_up_date: Optional[date]
    is_reviewable: Optional[bool]
    status: Optional[str]


class DocumentResponse(PydanticBaseModel):
    created_at: Optional[date]
    document_type: Optional[str]
    content_type: Optional[str]
    fineos_document_id: Optional[str]
    name: str
    description: str
