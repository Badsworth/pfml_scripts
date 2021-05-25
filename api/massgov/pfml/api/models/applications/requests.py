from datetime import date
from decimal import Decimal
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from pydantic import validator

from massgov.pfml.api.models.applications.common import (
    Address,
    ApplicationLeaveDetails,
    DocumentType,
    EmploymentStatus,
    Gender,
    Occupation,
    OtherIncome,
    PaymentPreference,
    Phone,
    WorkPattern,
)
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit, PreviousLeave
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINUnformattedStr, MassIdStr, TaxIdUnformattedStr


def max_date_of_birth_validator(date_of_birth, field):
    error_list = []
    if date_of_birth.year < date.today().year - 150:
        error_list.append(
            ValidationErrorDetail(
                message="Date of birth must be within the past 150 years",
                type="invalid_year_range",
                rule="date_of_birth_within_past_150_years",
                field=field,
            )
        )

    return error_list


def min_date_of_birth_validator(date_of_birth, field):
    error_list = []
    if date_of_birth > date.today() - relativedelta(years=14):
        error_list.append(
            ValidationErrorDetail(
                message="The person taking leave must be at least 14 years old",
                type="invalid_age",
                rule="older_than_14",
                field=field,
            )
        )
    return error_list


class ApplicationRequestBody(PydanticBaseModel):
    application_nickname: Optional[str]
    employee_ssn: Optional[TaxIdUnformattedStr]
    tax_identifier: Optional[TaxIdUnformattedStr]
    employer_fein: Optional[FEINUnformattedStr]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[Gender]
    has_continuous_leave_periods: Optional[bool]
    has_intermittent_leave_periods: Optional[bool]
    has_reduced_schedule_leave_periods: Optional[bool]
    has_state_id: Optional[bool]
    mass_id: Optional[MassIdStr]
    occupation: Optional[Occupation]
    hours_worked_per_week: Optional[Decimal]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[ApplicationLeaveDetails]
    work_pattern: Optional[WorkPattern]
    has_mailing_address: Optional[bool]
    mailing_address: Optional[Address]
    residential_address: Optional[Address]
    has_employer_benefits: Optional[bool]
    employer_benefits: Optional[List[EmployerBenefit]]
    has_other_incomes: Optional[bool]
    other_incomes_awaiting_approval: Optional[bool]
    other_incomes: Optional[List[OtherIncome]]
    phone: Optional[Phone]
    previous_leaves_other_reason: Optional[List[PreviousLeave]]
    previous_leaves_same_reason: Optional[List[PreviousLeave]]
    concurrent_leave: Optional[ConcurrentLeave]
    has_previous_leaves_other_reason: Optional[bool]
    has_previous_leaves_same_reason: Optional[bool]
    has_concurrent_leave: Optional[bool]

    @validator("date_of_birth")
    def date_of_birth_in_valid_range(cls, date_of_birth):  # noqa: B902
        """Applicant must be older than 14 and under 150"""
        if not date_of_birth:
            return date_of_birth

        max_date_of_birth_issue = max_date_of_birth_validator(date_of_birth, "date_of_birth")
        if max_date_of_birth_issue:
            raise ValidationException(
                errors=max_date_of_birth_issue, message="Validation error", data={}
            )

        min_date_of_birth_issue = min_date_of_birth_validator(date_of_birth, "date_of_birth")
        if min_date_of_birth_issue:
            raise ValidationException(
                errors=min_date_of_birth_issue, message="Validation error", data={}
            )

        return date_of_birth

    @validator("leave_details")
    def family_member_date_of_birth_in_valid_range(cls, leave_details):  # noqa: B902
        """Caring leave family member must be under 150 years old"""
        if (
            not leave_details.caring_leave_metadata
            or not leave_details.caring_leave_metadata.family_member_date_of_birth
        ):
            return leave_details

        max_date_of_birth_issue = max_date_of_birth_validator(
            leave_details.caring_leave_metadata.family_member_date_of_birth,
            "leave_details.caring_leave_metadata.family_member_date_of_birth",
        )
        if max_date_of_birth_issue:
            raise ValidationException(
                errors=max_date_of_birth_issue, message="Validation error", data={}
            )

        return leave_details

    @validator("work_pattern")
    def work_pattern_must_have_seven_days(cls, work_pattern):  # noqa: B902
        """Validates that work_pattern.work_pattern_days is properly formatted"""

        if not work_pattern:
            return work_pattern

        error_list = []
        api_work_pattern_days = work_pattern.work_pattern_days

        if api_work_pattern_days is not None:
            # when the user changes work_pattern_type, we pass an empty array, so no validation is required
            if len(api_work_pattern_days) == 0:
                return work_pattern

            provided_week_days = {day.day_of_week.value for day in api_work_pattern_days}
            week_days = {
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            }
            missing_days = week_days - provided_week_days

            if len(missing_days) > 0:
                error_list.append(
                    ValidationErrorDetail(
                        message=f"Provided work_pattern_days is missing {', '.join(sorted(missing_days))}.",
                        type="invalid_days",
                        rule="no_missing_days",
                        field="work_pattern.work_pattern_days",
                    )
                )

            if len(api_work_pattern_days) > 7:
                error_list.append(
                    ValidationErrorDetail(
                        message=f"Provided work_pattern_days has {len(api_work_pattern_days)} days. There should be 7 days.",
                        type="invalid_days",
                        rule="seven_days_required",
                        field="work_pattern.work_pattern_days",
                    )
                )

        if error_list:
            raise ValidationException(errors=error_list, message="Validation error", data={})
        return work_pattern


class DocumentRequestBody(PydanticBaseModel):
    document_type: DocumentType
    name: Optional[str]
    description: Optional[str]
    mark_evidence_received: Optional[bool]


class PaymentPreferenceRequestBody(PydanticBaseModel):
    payment_preference: Optional[PaymentPreference]
