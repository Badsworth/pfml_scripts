from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import UUID4

from massgov.pfml.api.models.common import (
    ConcurrentLeave,
    EmployerBenefit,
    LookupEnum,
    PreviousLeave,
)
from massgov.pfml.db.models.employees import ChangeRequest as change_request_db_model
from massgov.pfml.db.models.employees import LkChangeRequestType
from massgov.pfml.util.pydantic import PydanticBaseModel


class Address(PydanticBaseModel):
    line_1: Optional[str]
    line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]


class StandardLeavePeriod(PydanticBaseModel):
    start_date: date
    end_date: date


class IntermittentLeavePeriod(PydanticBaseModel):
    start_date: date
    end_date: date
    duration: Optional[float]
    duration_basis: Optional[str]
    frequency: Optional[int]
    frequency_interval: Optional[float]
    frequency_interval_basis: Optional[str]


class LeaveDetails(PydanticBaseModel):
    reason: Optional[str]
    continuous_leave_periods: Optional[List[StandardLeavePeriod]]
    intermittent_leave_periods: Optional[List[IntermittentLeavePeriod]]
    reduced_schedule_leave_periods: Optional[List[StandardLeavePeriod]]


class YesNoUnknown(str, Enum):
    YES = "Yes"
    NO = "No"
    UNKNOWN = "Unknown"


class EmployerClaimReview(PydanticBaseModel):
    """Defines the Employer info request / response format"""

    uses_second_eform_version: bool = False
    comment: Optional[str]
    employer_benefits: List[EmployerBenefit]
    concurrent_leave: Optional[ConcurrentLeave]
    hours_worked_per_week: Optional[Decimal]
    previous_leaves: List[PreviousLeave]
    employer_decision: Optional[str]
    fraud: Optional[str]
    has_amendments: bool = False
    leave_reason: Optional[str]
    believe_relationship_accurate: Optional[YesNoUnknown]
    relationship_inaccurate_reason: Optional[str]


class ChangeRequestType(str, LookupEnum):
    MODIFICATION = "Modification"
    WITHDRAWAL = "Withdrawal"
    MEDICAL_TO_BONDING = "Medical To Bonding Transition"


class ChangeRequest(PydanticBaseModel):
    """Defines the ChangeRequest format"""

    change_request_type: Optional[ChangeRequestType]
    start_date: Optional[date]
    end_date: Optional[date]

    def to_db_model(
        self, change_type: LkChangeRequestType, claim_id: UUID4
    ) -> change_request_db_model:
        return change_request_db_model(
            claim_id=claim_id,
            change_request_type_instance=change_type,
            start_date=self.start_date,
            end_date=self.end_date,
        )
