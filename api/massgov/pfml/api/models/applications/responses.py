from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import UUID4

from massgov.pfml.api.models.applications.common import (
    ApplicationPaymentChequeDetails,
    EmployerBenefit,
    EmploymentStatus,
    MaskedAddress,
    MaskedApplicationLeaveDetails,
    MaskedApplicationPaymentAccountDetails,
    MaskedPaymentPreferences,
    Occupation,
    OtherIncome,
    PaymentAccountType,
    PaymentMethod,
    WorkPattern,
)
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
    employer_id: Optional[UUID4]
    employer_fein: Optional[FEINFormattedStr]
    fineos_absence_id: Optional[str]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[MaskedDateStr]
    has_continuous_leave_periods: Optional[bool]
    has_intermittent_leave_periods: Optional[bool]
    has_reduced_schedule_leave_periods: Optional[bool]
    has_state_id: Optional[bool]
    mass_id: Optional[MaskedMassIdStr]
    occupation: Optional[Occupation]
    hours_worked_per_week: Optional[Decimal]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[MaskedApplicationLeaveDetails]
    payment_preferences: Optional[List[MaskedPaymentPreferences]]
    work_pattern: Optional[WorkPattern]
    updated_time: datetime
    status: Optional[ApplicationStatus]
    has_mailing_address: Optional[bool]
    mailing_address: Optional[MaskedAddress]
    residential_address: Optional[MaskedAddress]
    has_employer_benefits: Optional[bool]
    employer_benefits: Optional[List[EmployerBenefit]]
    has_other_incomes: Optional[bool]
    other_incomes_awaiting_approval: Optional[bool]
    other_incomes: Optional[List[OtherIncome]]

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
        application_response.payment_preferences = list(
            map(build_payment_preference, application.payment_preferences)
        )

        if application.completed_time:
            application_response.status = ApplicationStatus.Completed
        elif application.submitted_time:
            application_response.status = ApplicationStatus.Submitted
        else:
            application_response.status = ApplicationStatus.Started

        return application_response


def build_payment_preference(
    db_payment_preference: ApplicationPaymentPreference,
) -> MaskedPaymentPreferences:
    payment_preference = MaskedPaymentPreferences.from_orm(db_payment_preference)

    # some renames
    payment_preference.payment_preference_id = db_payment_preference.payment_pref_id  # type: ignore

    if db_payment_preference.payment_type is not None:
        payment_preference.payment_method = PaymentMethod(
            db_payment_preference.payment_type.payment_type_description
        )

    # the data for this comes from columns on ApplicationPaymentPreference, but
    # the response collects some of them under this `account_details` key, so
    # have to pull them out here manually since pydantic doesn't know how to do
    # that automatically
    payment_preference.account_details = MaskedApplicationPaymentAccountDetails.from_orm(
        db_payment_preference
    )

    # another rename
    if db_payment_preference.type_of_account is not None:
        payment_preference.account_details.account_type = PaymentAccountType(
            db_payment_preference.type_of_account
        )

    # similar as above, with a rename as well
    payment_preference.cheque_details = ApplicationPaymentChequeDetails(
        name_to_print_on_check=db_payment_preference.name_in_check
    )

    return payment_preference


class DocumentResponse(PydanticBaseModel):
    user_id: UUID4
    application_id: UUID4
    created_at: Optional[datetime]
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
