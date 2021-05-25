from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from massgov.pfml.api.models.common import EmployerBenefit, PreviousLeave
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
    """ Defines the Employer info request / response format """

    comment: Optional[str]
    employer_benefits: List[EmployerBenefit]
    hours_worked_per_week: Optional[Decimal]
    previous_leaves: List[PreviousLeave]
    employer_decision: Optional[str]
    fraud: Optional[str]
    has_amendments: bool = False
    leave_reason: Optional[str]
    believe_relationship_accurate: Optional[YesNoUnknown]
    relationship_inaccurate_reason: Optional[str]
