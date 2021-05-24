from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from massgov.pfml.api.models.common import PreviousLeave
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


class EmployerBenefit(PydanticBaseModel):
    benefit_amount_dollars: Optional[float]
    benefit_amount_frequency: Optional[str]
    benefit_start_date: Optional[date]
    benefit_end_date: Optional[date]
    benefit_type: Optional[str]
    program_type: Optional[str]


class NatureOfLeave(str, Enum):
    ILLNESS_OR_INJURY = "An illness or injury"
    PREGNANCY = "Pregnancy"
    CHILD_BONDING = "Bonding with my child after birth or placement"
    MILITARY_CAREGIVER = "Caring for a family member who serves in the armed forces"
    MILITARY_MANAGING_FAMILY = (
        "Managing family affairs while a family member is on active duty in the armed forces"
    )
    FAMILY_CAREGIVER = "Caring for a family member with a serious health condition"


class YesNoUnsure(str, Enum):
    YES = "Yes"
    NO = "No"
    UNSURE = "Don't Know"


class EmployerClaimReview(PydanticBaseModel):
    """ Defines the Employer info request / response format """

    comment: Optional[str]
    employer_benefits: List[EmployerBenefit]
    hours_worked_per_week: Optional[Decimal]
    previous_leaves: List[PreviousLeave]
    employer_decision: Optional[str]
    fraud: Optional[str]
    has_amendments: bool = False
    nature_of_leave: Optional[NatureOfLeave]
    believe_relationship_accurate: Optional[YesNoUnsure]
    relationship_inaccurate_reason: Optional[str]
