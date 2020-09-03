from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import UUID4

from massgov.pfml.api.models.applications.common import (
    Address,
    ApplicationLeaveDetails,
    ApplicationPaymentAccountDetails,
    ApplicationPaymentChequeDetails,
    EmploymentStatus,
    Occupation,
    PaymentAccountType,
    PaymentMethod,
    PaymentPreferences,
)
from massgov.pfml.db.models.applications import Application, ApplicationPaymentPreference
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import FEINStr, MaskedMassIdStr, MaskedTaxIdFormattedStr


class ApplicationStatus(str, Enum):
    Started = "Started"
    Completed = "Completed"
    Submitted = "Submitted"


class ApplicationResponse(PydanticBaseModel):
    application_id: UUID4
    application_nickname: Optional[str]
    tax_identifier: Optional[MaskedTaxIdFormattedStr]
    employer_id: Optional[UUID4]
    employer_fein: Optional[FEINStr]
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[date]
    has_state_id: Optional[bool]
    mass_id: Optional[MaskedMassIdStr]
    occupation: Optional[Occupation]
    employment_status: Optional[EmploymentStatus]
    leave_details: Optional[ApplicationLeaveDetails]
    payment_preferences: Optional[List[PaymentPreferences]]
    updated_time: datetime
    status: Optional[ApplicationStatus]
    mailing_address: Optional[Address]
    residential_address: Optional[Address]

    @classmethod
    def from_orm(cls, application: Application) -> "ApplicationResponse":
        application_response = super().from_orm(application)
        application_response.application_nickname = application.nickname
        if application.mailing_address is not None:
            application_response.mailing_address = Address.from_orm(application.mailing_address)
        if application.residential_address is not None:
            application_response.residential_address = Address.from_orm(
                application.residential_address
            )
        application_response.leave_details = ApplicationLeaveDetails.from_orm(application)
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
) -> PaymentPreferences:
    payment_preference = PaymentPreferences.from_orm(db_payment_preference)

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
    payment_preference.account_details = ApplicationPaymentAccountDetails.from_orm(
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
