from datetime import date
from decimal import Decimal
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from pydantic import validator

from massgov.pfml.api.models.applications.common import (
    Address,
    ApplicationLeaveDetails,
    DocumentCategory,
    DocumentType,
    EmploymentStatus,
    Occupation,
    PaymentPreferences,
)
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINStr, MassIdStr, TaxIdUnformattedStr


class ApplicationRequestBody(PydanticBaseModel):
    application_nickname: Optional[str]
    employee_ssn: Optional[TaxIdUnformattedStr]
    tax_identifier: Optional[TaxIdUnformattedStr]
    employer_fein: Optional[FEINStr]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    has_continuous_leave_periods: Optional[bool]
    has_intermittent_leave_periods: Optional[bool]
    has_reduced_schedule_leave_periods: Optional[bool]
    has_state_id: Optional[bool]
    mass_id: Optional[MassIdStr]
    occupation: Optional[Occupation]
    hours_worked_per_week: Optional[Decimal]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[ApplicationLeaveDetails]
    payment_preferences: Optional[List[PaymentPreferences]]
    mailing_address: Optional[Address]
    residential_address: Optional[Address]

    @validator("date_of_birth")
    def date_of_birth_in_valid_range(cls, date_of_birth):  # noqa: B902
        """Applicant must be older than 14 and under 100"""
        error_list = []
        today = date.today()
        if date_of_birth.year < today.year - 100 or today < date_of_birth:
            error_list.append(
                ValidationErrorDetail(
                    message="Date of birth must be within the past 100 years",
                    type="invalid_year_range",
                    rule="date_of_birth_within_past_100_years",
                    field="date_of_birth",
                )
            )

        elif date_of_birth > today - relativedelta(years=14):
            error_list.append(
                ValidationErrorDetail(
                    message="The person taking leave must be at least 14 years old",
                    type="invalid_age",
                    rule="older_than_14",
                    field="date_of_birth",
                )
            )

        if error_list:
            raise ValidationException(errors=error_list, message="Validation error", data={})
        return date_of_birth


class DocumentRequestBody(PydanticBaseModel):
    document_category: DocumentCategory
    document_type: DocumentType
    name: Optional[str]
    description: Optional[str]
