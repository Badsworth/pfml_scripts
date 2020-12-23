from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import validator

from massgov.pfml.api.models.common import PreviousLeave
from massgov.pfml.api.util.response import IssueType
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
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
    benefit_start_date: date
    benefit_end_date: date
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

    @validator("hours_worked_per_week")
    def validate_hours_worked_per_week(cls, hours_worked_per_week):  # noqa: B902
        if hours_worked_per_week is None:
            error = ValidationErrorDetail(
                message="hours_worked_per_week must be populated",
                type="missing_expected_field",
                field="hours_worked_per_week",
            )
            raise ValidationException(errors=[error], message="Validation error", data={})

        # there are 168 hours in a week
        if hours_worked_per_week <= 0 or hours_worked_per_week > 168:
            error = ValidationErrorDetail(
                message="hours_worked_per_week must be greater than 0 and less than 168",
                type="invalid_hours_worked_per_week",
                field="hours_worked_per_week",
            )
            raise ValidationException(errors=[error], message="Validation error", data={})

        return hours_worked_per_week

    @validator("previous_leaves")
    def validate_previous_leaves(cls, previous_leaves):  # noqa: B902
        error_list = []

        if not previous_leaves:
            return previous_leaves

        for index, previous_leave in enumerate(previous_leaves):
            if previous_leave.leave_start_date < date(2021, 1, 1):
                error_list.append(
                    ValidationErrorDetail(
                        message="Previous leaves cannot start before 2021",
                        type="invalid_previous_leave_start_date",
                        field=f"previous_leaves[{index}].leave_start_date",
                    )
                )

            if previous_leave.leave_start_date > previous_leave.leave_end_date:
                error_list.append(
                    ValidationErrorDetail(
                        message="leave_end_date cannot be earlier than leave_start_date",
                        type=IssueType.minimum,
                        field=f"previous_leaves[{index}].leave_end_date",
                    )
                )

        if error_list:
            raise ValidationException(errors=error_list, message="Validation error", data={})
        return previous_leaves

    @validator("employer_benefits")
    def validate_employer_benefits(cls, employer_benefits):  # noqa: B902
        error_list = []

        if not employer_benefits:
            return employer_benefits

        for index, employer_benefit in enumerate(employer_benefits):
            if employer_benefit.benefit_start_date > employer_benefit.benefit_end_date:
                error_list.append(
                    ValidationErrorDetail(
                        message="benefit_end_date cannot be earlier than benefit_start_date",
                        type=IssueType.minimum,
                        field=f"employer_benefits[{index}].benefit_end_date",
                    )
                )

        if error_list:
            raise ValidationException(errors=error_list, message="Validation error", data={})
        return employer_benefits
