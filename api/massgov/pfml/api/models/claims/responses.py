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
from massgov.pfml.api.models.common import ConcurrentLeave
from massgov.pfml.db.models.employees import Claim, ManagedRequirement
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import (
    FEINFormattedStr,
    MaskedDateStr,
    MaskedTaxIdFormattedStr,
)


class EmployerResponse(PydanticBaseModel):
    employer_dba: str
    employer_fein: FEINFormattedStr
    employer_id: UUID4


class EmployeeResponse(PydanticBaseModel):
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    other_name: Optional[str]


class ManagedRequirementResponse(PydanticBaseModel):
    follow_up_date: Optional[date]
    responded_at: Optional[date]
    status: Optional[str]
    category: Optional[str]
    type: Optional[str]
    created_at: Optional[date]

    @classmethod
    def from_orm(cls, managed_requirement: ManagedRequirement) -> "ManagedRequirementResponse":
        managed_requirement_response = super().from_orm(managed_requirement)
        if managed_requirement.managed_requirement_status:
            managed_requirement_response.status = (
                managed_requirement.managed_requirement_status.managed_requirement_status_description
            )
        if managed_requirement.managed_requirement_category:
            managed_requirement_response.category = (
                managed_requirement.managed_requirement_category.managed_requirement_category_description
            )
        if managed_requirement.managed_requirement_type:
            managed_requirement_response.type = (
                managed_requirement.managed_requirement_type.managed_requirement_type_description
            )

        return managed_requirement_response


class ClaimResponse(PydanticBaseModel):
    fineos_absence_id: Optional[str]
    employer: Optional[EmployerResponse]
    employee: Optional[EmployeeResponse]
    fineos_notification_id: Optional[str]
    absence_period_start_date: Optional[date]
    absence_period_end_date: Optional[date]
    claim_status: Optional[str]
    claim_type_description: Optional[str]
    created_at: Optional[date]
    managed_requirements: Optional[List[ManagedRequirementResponse]]

    @classmethod
    def from_orm(cls, claim: Claim) -> "ClaimResponse":
        claim_response = super().from_orm(claim)
        if claim.fineos_absence_status:
            claim_response.claim_status = claim.fineos_absence_status.absence_status_description
        if claim.claim_type:
            claim_response.claim_type_description = claim.claim_type.claim_type_description
        return claim_response


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
    concurrent_leave: Optional[ConcurrentLeave]
    residential_address: Optional[Address]
    tax_identifier: Optional[MaskedTaxIdFormattedStr]
    follow_up_date: Optional[date]
    is_reviewable: Optional[bool]
    status: Optional[str]
    uses_second_eform_version: bool


class DocumentResponse(PydanticBaseModel):
    created_at: Optional[date]
    document_type: Optional[str]
    content_type: Optional[str]
    fineos_document_id: Optional[str]
    name: str
    description: str
