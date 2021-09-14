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


class AbsencePeriodStatusResponse(PydanticBaseModel):
    fineos_leave_period_id: Optional[str]
    absence_period_start_date: Optional[date]
    absence_period_end_date: Optional[date]
    reason: Optional[str]
    reason_qualifier_one: Optional[str]
    reason_qualifier_two: Optional[str]
    period_type: Optional[str]
    request_decision: Optional[str]
    # Not in absence_period yet. Should be N/A, Pending, Waived, Satisfied, Not Satisfied, Not Required
    evidence_status: Optional[str]


class EvidenceDetail(PydanticBaseModel):
    document_name: Optional[str]
    is_document_received: Optional[bool]


class OutstandingEvidenceResponse(PydanticBaseModel):
    employee_evidence: Optional[List[EvidenceDetail]]
    employer_evidence: Optional[List[EvidenceDetail]]


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


# This class is intended to show more granular data about a claim that is not shown in the dashboard,
# where ClaimResponse is used. For now the detailed data is absence_periods and outstanding evidence.
class DetailedClaimResponse(PydanticBaseModel):
    application_id: Optional[str]
    fineos_absence_id: Optional[str]
    employer: Optional[EmployerResponse]
    employee: Optional[EmployeeResponse]
    fineos_notification_id: Optional[str]
    claim_status: Optional[str]
    created_at: Optional[date]
    absence_periods: Optional[List[AbsencePeriodStatusResponse]]
    managed_requirements: Optional[List[ManagedRequirementResponse]]
    # Place holder for future implementation.
    outstanding_evidence: Optional[OutstandingEvidenceResponse]

    @classmethod
    def from_orm(cls, claim: Claim) -> "DetailedClaimResponse":
        claim_response = super().from_orm(claim)
        if claim.fineos_absence_status:
            claim_response.claim_status = claim.fineos_absence_status.absence_status_description
        # Dropping data from DB acquired automatically through the super()_from_orm call.
        # The periods are populated using FINEOS API data.
        claim_response.absence_periods = []
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
    document_type: str
    content_type: Optional[str]
    fineos_document_id: str
    name: Optional[str]
    description: Optional[str]
