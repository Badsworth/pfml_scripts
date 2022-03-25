from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import UUID4

import massgov.pfml.api.app as app
from massgov.pfml.api.eligibility.handler import BenefitYearsResponse
from massgov.pfml.api.models.applications.common import (
    EmploymentStatus,
    Gender,
    MaskedAddress,
    MaskedApplicationLeaveDetails,
    MaskedPaymentPreference,
    Occupation,
    OrganizationUnit,
    OrganizationUnitSelection,
    OtherIncome,
    PaymentMethod,
    WorkPattern,
)
from massgov.pfml.api.models.claims.common import PreviousLeave
from massgov.pfml.api.models.common import (
    ComputedStartDates,
    ConcurrentLeave,
    EmployerBenefit,
    MaskedPhoneResponse,
    get_application_earliest_submission_date,
    get_computed_start_dates,
    get_earliest_start_date,
    get_leave_reason,
)
from massgov.pfml.api.services.applications import (
    ApplicationSplit,
    StartEndDates,
    get_application_split,
)
from massgov.pfml.db.models.applications import Application, ApplicationPaymentPreference
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import (
    FEINFormattedStr,
    MaskedDateStr,
    MaskedMassIdStr,
    MaskedTaxIdFormattedStr,
)


class ApplicationStatus(str, Enum):
    Started = "Started"
    Completed = "Completed"
    Submitted = "Submitted"


class ApplicationSplitResponse(PydanticBaseModel):
    crossed_benefit_year: BenefitYearsResponse
    application_dates_in_benefit_year: StartEndDates
    application_dates_outside_benefit_year: StartEndDates
    application_outside_benefit_year_submittable_on: date

    @classmethod
    def from_orm(cls, application_split: ApplicationSplit) -> "ApplicationSplitResponse":
        return ApplicationSplitResponse(
            crossed_benefit_year=BenefitYearsResponse.from_orm(
                application_split.crossed_benefit_year
            ),
            application_dates_in_benefit_year=application_split.application_dates_in_benefit_year,
            application_dates_outside_benefit_year=application_split.application_dates_outside_benefit_year,
            application_outside_benefit_year_submittable_on=application_split.application_outside_benefit_year_submittable_on,
        )


class ApplicationResponse(PydanticBaseModel):
    application_id: UUID4
    organization_unit_id: Optional[UUID4]
    organization_unit_selection: Optional[OrganizationUnitSelection]
    tax_identifier: Optional[MaskedTaxIdFormattedStr]
    employee_id: Optional[UUID4]
    employer_fein: Optional[FEINFormattedStr]
    fineos_absence_id: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[MaskedDateStr]
    gender: Optional[Gender]
    has_continuous_leave_periods: Optional[bool]
    has_intermittent_leave_periods: Optional[bool]
    has_reduced_schedule_leave_periods: Optional[bool]
    has_state_id: Optional[bool]
    has_submitted_payment_preference: Optional[bool]
    mass_id: Optional[MaskedMassIdStr]
    occupation: Optional[Occupation]
    organization_unit: Optional[OrganizationUnit]
    hours_worked_per_week: Optional[Decimal]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[MaskedApplicationLeaveDetails]
    payment_preference: Optional[MaskedPaymentPreference]
    work_pattern: Optional[WorkPattern]
    updated_time: Optional[datetime]
    status: Optional[ApplicationStatus]
    has_mailing_address: Optional[bool]
    mailing_address: Optional[MaskedAddress]
    residential_address: Optional[MaskedAddress]
    has_employer_benefits: Optional[bool]
    employer_benefits: Optional[List[EmployerBenefit]]
    employee_organization_units: List[OrganizationUnit]
    employer_organization_units: List[OrganizationUnit]
    has_other_incomes: Optional[bool]
    other_incomes: Optional[List[OtherIncome]]
    phone: Optional[MaskedPhoneResponse]
    previous_leaves_other_reason: Optional[List[PreviousLeave]]
    previous_leaves_same_reason: Optional[List[PreviousLeave]]
    concurrent_leave: Optional[ConcurrentLeave]
    has_previous_leaves: Optional[bool]
    has_previous_leaves_other_reason: Optional[bool]
    has_previous_leaves_same_reason: Optional[bool]
    has_concurrent_leave: Optional[bool]
    is_withholding_tax: Optional[bool]
    imported_from_fineos_at: Optional[datetime]
    updated_at: datetime
    computed_start_dates: Optional[ComputedStartDates]
    split_from_application_id: Optional[UUID4]
    split_into_application_id: Optional[UUID4]
    computed_earliest_submission_date: Optional[date]
    computed_application_split: Optional[ApplicationSplitResponse]

    @classmethod
    def from_orm(cls, application: Application) -> "ApplicationResponse":
        application_response = super().from_orm(application)
        if application.mailing_address is not None:
            application_response.mailing_address = MaskedAddress.from_orm(
                application.mailing_address
            )
        if application.residential_address is not None:
            application_response.residential_address = MaskedAddress.from_orm(
                application.residential_address
            )
        application_response.leave_details = MaskedApplicationLeaveDetails.from_orm(application)
        if application.payment_preference is not None:
            application_response.payment_preference = build_payment_preference(
                application.payment_preference
            )

        if application.phone is not None:
            application_response.phone = MaskedPhoneResponse.from_orm(application.phone)

        if application.completed_time:
            application_response.status = ApplicationStatus.Completed
        elif application.submitted_time:
            application_response.status = ApplicationStatus.Submitted
        else:
            application_response.status = ApplicationStatus.Started

        if application.claim is not None:
            application_response.fineos_absence_id = application.claim.fineos_absence_id

        if application.employee is not None:
            application_response.employee_id = application.employee.employee_id
            application_response.computed_application_split = _get_application_split_response(
                application
            )

        application_response.updated_time = application_response.updated_at
        application_response.computed_start_dates = _get_computed_start_dates(application)
        application_response.computed_earliest_submission_date = (
            get_application_earliest_submission_date(application)
        )

        return application_response


def _get_computed_start_dates(application: Application) -> ComputedStartDates:
    earliest_start_date = get_earliest_start_date(application)
    leave_reason = get_leave_reason(application)
    return get_computed_start_dates(earliest_start_date, leave_reason)


def _get_application_split_response(application: Application) -> Optional[ApplicationSplitResponse]:
    with app.db_session() as db_session:
        split = get_application_split(application, db_session)

    if split is None:
        return None
    else:
        return ApplicationSplitResponse.from_orm(split)


def build_payment_preference(
    db_payment_preference: ApplicationPaymentPreference,
) -> MaskedPaymentPreference:
    payment_preference = MaskedPaymentPreference.from_orm(db_payment_preference)

    if db_payment_preference.payment_method is not None:
        payment_preference.payment_method = PaymentMethod(
            db_payment_preference.payment_method.payment_method_description
        )

    return payment_preference
