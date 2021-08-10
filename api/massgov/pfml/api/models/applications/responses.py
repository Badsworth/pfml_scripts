from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import UUID4

from massgov.pfml.api.models.applications.common import (
    EmploymentStatus,
    Gender,
    MaskedAddress,
    MaskedApplicationLeaveDetails,
    MaskedPaymentPreference,
    MaskedPhone,
    Occupation,
    OtherIncome,
    PaymentMethod,
    ReportingUnit,
    WorkPattern,
)
from massgov.pfml.api.models.claims.common import PreviousLeave
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit
from massgov.pfml.db.models.applications import Application, ApplicationPaymentPreference, Document
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


class ApplicationResponse(PydanticBaseModel):
    application_id: UUID4
    application_nickname: Optional[str]
    tax_identifier: Optional[MaskedTaxIdFormattedStr]
    employer_fein: Optional[FEINFormattedStr]
    fineos_absence_id: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[MaskedDateStr]
    gender: Optional[Gender]
    reporting_unit: Optional[ReportingUnit]
    has_continuous_leave_periods: Optional[bool]
    has_intermittent_leave_periods: Optional[bool]
    has_reduced_schedule_leave_periods: Optional[bool]
    has_state_id: Optional[bool]
    has_submitted_payment_preference: Optional[bool]
    mass_id: Optional[MaskedMassIdStr]
    occupation: Optional[Occupation]
    hours_worked_per_week: Optional[Decimal]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[MaskedApplicationLeaveDetails]
    payment_preference: Optional[MaskedPaymentPreference]
    work_pattern: Optional[WorkPattern]
    updated_time: datetime
    status: Optional[ApplicationStatus]
    has_mailing_address: Optional[bool]
    mailing_address: Optional[MaskedAddress]
    residential_address: Optional[MaskedAddress]
    has_employer_benefits: Optional[bool]
    employer_benefits: Optional[List[EmployerBenefit]]
    has_other_incomes: Optional[bool]
    other_incomes: Optional[List[OtherIncome]]
    phone: Optional[MaskedPhone]
    previous_leaves_other_reason: Optional[List[PreviousLeave]]
    previous_leaves_same_reason: Optional[List[PreviousLeave]]
    concurrent_leave: Optional[ConcurrentLeave]
    has_previous_leaves: Optional[bool]
    has_previous_leaves_other_reason: Optional[bool]
    has_previous_leaves_same_reason: Optional[bool]
    has_concurrent_leave: Optional[bool]

    @classmethod
    def from_orm(cls, application: Application) -> "ApplicationResponse":
        application_response = super().from_orm(application)
        application_response.application_nickname = application.nickname
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
            application_response.phone = MaskedPhone.from_orm(application.phone)

        if application.completed_time:
            application_response.status = ApplicationStatus.Completed
        elif application.submitted_time:
            application_response.status = ApplicationStatus.Submitted
        else:
            application_response.status = ApplicationStatus.Started

        if application.claim is not None:
            application_response.fineos_absence_id = application.claim.fineos_absence_id

        return application_response


def build_payment_preference(
    db_payment_preference: ApplicationPaymentPreference,
) -> MaskedPaymentPreference:
    payment_preference = MaskedPaymentPreference.from_orm(db_payment_preference)

    if db_payment_preference.payment_method is not None:
        payment_preference.payment_method = PaymentMethod(
            db_payment_preference.payment_method.payment_method_description
        )

    return payment_preference


class DocumentResponse(PydanticBaseModel):
    user_id: UUID4
    application_id: UUID4
    created_at: Optional[date]
    document_type: Optional[str]
    content_type: Optional[str]
    fineos_document_id: Optional[str]
    name: str
    description: str

    @classmethod
    def from_orm(cls, document: Document) -> "DocumentResponse":
        document_response = super().from_orm(document)
        document_response.fineos_document_id = str(document.fineos_id)
        document_response.document_type = document.document_type_instance.document_type_description
        document_response.content_type = document.content_type_instance.content_type_description
        return document_response
