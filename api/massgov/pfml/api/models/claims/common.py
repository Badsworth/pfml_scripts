from datetime import date
from decimal import Decimal
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


class EmployerClaimReview(PydanticBaseModel):
    """ Defines the Employer info request / response format """

    comment: Optional[str]
    employer_benefits: List[EmployerBenefit]
    hours_worked_per_week: Optional[Decimal]
    previous_leaves: List[PreviousLeave]
    employer_decision: Optional[str]
    fraud: Optional[str]
    has_amendments: bool = False
