from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, Union

import phonenumbers
from pydantic import UUID4, validator

import massgov.pfml.db.models.applications as db_application_models
import massgov.pfml.db.models.employees as db_employee_models
import massgov.pfml.db.models.payments as db_payment_models
import massgov.pfml.db.models.verifications as db_verification_models
import massgov.pfml.util.pydantic.mask as mask
from massgov.pfml.api.validation.exceptions import (
    IssueType,
    ValidationErrorDetail,
    ValidationException,
)
from massgov.pfml.db.lookup import LookupTable
from massgov.pfml.util.pydantic import PydanticBaseModel

PHONE_MISMATCH_MESSAGE = "E.164 phone number does not match provided phone number"
PHONE_MISMATCH_ERROR = ValidationErrorDetail(
    message=PHONE_MISMATCH_MESSAGE, type=IssueType.invalid_phone_number, field="e164",
)


class LookupEnum(Enum):
    @classmethod
    def get_lookup_model(cls):
        for model_collection in [
            db_application_models,
            db_employee_models,
            db_verification_models,
            db_payment_models,
        ]:
            class_with_same_name = getattr(model_collection, cls.__name__, None)

            if class_with_same_name is not None:
                break

        # we didn't find a matching model anywhere
        if class_with_same_name is None:
            raise ValueError(f"Can not find matching database lookup table for {cls.__name__}")

        if issubclass(class_with_same_name, LookupTable):
            db_table_model = class_with_same_name.model
        else:
            db_table_model = class_with_same_name

        return db_table_model

    @classmethod
    def get_lookup_value_column_name(cls):
        return "".join([cls.get_lookup_model().__tablename__.replace("lk_", "", 1), "_description"])

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        if isinstance(val, str):
            return cls(val)

        if not isinstance(val, cls.get_lookup_model()):
            raise TypeError(f"is not an instance of class {cls.get_lookup_model()}")

        # TODO: maybe more checking that we can actually retrieve the value?

        return cls(getattr(val, cls.get_lookup_value_column_name()))


class PreviousLeaveQualifyingReason(str, LookupEnum):
    PREGNANCY_MATERNITY = "Pregnancy"
    CARE_FOR_A_FAMILY_MEMBER = "Caring for a family member with a serious health condition"
    CHILD_BONDING = "Bonding with my child after birth or placement"
    MILITARY_CAREGIVER = "Caring for a family member who serves in the armed forces"
    MILITARY_EXIGENCY_FAMILY = (
        "Managing family affairs while a family member is on active duty in the armed forces"
    )
    UNKNOWN = "Unknown"
    AN_ILLNESS_OR_INJURY = "An illness or injury"


class PreviousLeave(PydanticBaseModel):
    is_for_current_employer: Optional[bool]
    leave_start_date: Optional[date]
    leave_end_date: Optional[date]
    leave_reason: Optional[PreviousLeaveQualifyingReason]
    previous_leave_id: Optional[UUID4]
    worked_per_week_minutes: Optional[int]
    leave_minutes: Optional[int]
    type: Optional[str]


class ConcurrentLeave(PydanticBaseModel):
    concurrent_leave_id: Optional[UUID4]
    is_for_current_employer: Optional[bool]
    leave_start_date: Optional[date]
    leave_end_date: Optional[date]


class AmountFrequency(str, LookupEnum):
    per_day = "Per Day"
    per_week = "Per Week"
    per_month = "Per Month"
    all_at_once = "In Total"
    unknown = "Unknown"


class EmployerBenefitType(str, LookupEnum):
    accrued_paid_leave = "Accrued paid leave"
    short_term_disability = "Short-term disability insurance"
    permanent_disability_insurance = "Permanent disability insurance"
    family_or_medical_leave_insurance = "Family or medical leave insurance"
    unknown = "Unknown"


class EmployerBenefit(PydanticBaseModel):
    employer_benefit_id: Optional[UUID4]
    benefit_type: Optional[EmployerBenefitType]
    benefit_start_date: Optional[date]
    benefit_end_date: Optional[date]
    benefit_amount_dollars: Optional[Decimal]
    benefit_amount_frequency: Optional[AmountFrequency]
    is_full_salary_continuous: Optional[bool]
    # program_type is only used by the claims API to filter out non-employer incomes
    # when ingesting from the Other Income eform. It isn't used by the portal and
    # isn't saved to the DB.
    program_type: Optional[str]


# Phone I/O Types


class PhoneType(str, LookupEnum):
    Cell = "Cell"
    Fax = "Fax"
    Phone = "Phone"


class Phone(PydanticBaseModel):
    # Phone dict coming from front end contains int_code and phone_number separately
    # Values are Optional, deviating from OpenAPI spec to allow for None values in Response
    int_code: Optional[str]
    phone_number: Optional[str]
    phone_type: Optional[PhoneType]
    e164: Optional[str]

    @validator("phone_number")
    def check_phone_number(cls, phone_number, values):  # noqa: B902
        # Import here to avoid circular import
        from massgov.pfml.api.util.phone import parse_number

        error_list = []
        n = None

        int_code = values.get("int_code")
        if phone_number is None:
            # if phone_number is removed by masking rules, skip validation
            return None

        n = parse_number(phone_number, int_code)

        if n is None or not phonenumbers.is_valid_number(n):
            error_list.append(
                ValidationErrorDetail(
                    message="Phone number must be a valid number",
                    type=IssueType.invalid_phone_number,
                    rule="phone_number_must_be_valid_number",
                    field="phone.phone_number",
                )
            )

        if error_list:
            raise ValidationException(
                errors=error_list,
                message="Validation error",
                data={"phone_number": phone_number, "int_code": int_code},
            )

        return phone_number

    @validator("e164", always=True)
    def populate_e164_if_phone_number(cls, e164_phone_number, values):  # noqa: B902
        # Import here to avoid circular import
        from massgov.pfml.api.util.phone import convert_to_E164

        is_phone_number_provided = "phone_number" in values and values["phone_number"]

        if not e164_phone_number and is_phone_number_provided:
            return convert_to_E164(values.get("phone_number"), values.get("int_code"))

        if e164_phone_number is not None and is_phone_number_provided:
            checked_number = convert_to_E164(values.get("phone_number"), values.get("int_code"))
            if e164_phone_number != checked_number:
                raise ValidationException(
                    errors=[PHONE_MISMATCH_ERROR], message=PHONE_MISMATCH_MESSAGE
                )

        return e164_phone_number

    @validator("e164")
    def check_e164(cls, e164_phone_number):  # noqa: B902
        # because the other validator for "e164" is always=True, this validator
        # seems to be called regardless of if an "e164" value is available
        # (either from the request directly or populate_e164_if_phone_number),
        # so check before doing any validation
        #
        # if/when populate_e164_if_phone_number is removed, shouldn't need to do
        # this check
        if not e164_phone_number:
            return None

        validation_exception = ValidationException(
            errors=[
                ValidationErrorDetail(
                    message="Phone number must be a valid number",
                    type=IssueType.invalid_phone_number,
                    rule="phone_number_must_be_valid_number",
                    field="phone.e164",
                )
            ],
            message="Validation error",
        )

        try:
            n = phonenumbers.parse(e164_phone_number)
        except phonenumbers.NumberParseException:
            raise validation_exception

        if not phonenumbers.is_valid_number(n):
            raise validation_exception

        return e164_phone_number


class MaskedPhone(Phone):
    @classmethod
    def from_orm(cls, phone: Union[db_application_models.Phone, str]) -> "MaskedPhone":
        phone_response = PhoneResponse.from_orm(phone)

        return MaskedPhone(
            int_code=phone_response.int_code,
            phone_number=mask.mask_phone(phone_response.phone_number),
            phone_type=phone_response.phone_type,
        )


class MaskedPhoneResponse(PydanticBaseModel):
    int_code: Optional[str]
    phone_number: Optional[str]
    phone_type: Optional[PhoneType]

    @classmethod
    def from_orm(cls, phone: Union[db_application_models.Phone, str]) -> "MaskedPhoneResponse":
        phone_response = PhoneResponse.from_orm(phone)
        phone_response.phone_number = mask.mask_phone(phone_response.phone_number)

        return MaskedPhoneResponse(
            int_code=phone_response.int_code,
            phone_number=phone_response.phone_number,
            phone_type=phone_response.phone_type,
        )


# Create this response class to capture phone data without the validators above
class PhoneResponse(PydanticBaseModel):
    int_code: Optional[str]
    phone_number: Optional[str]
    phone_type: Optional[PhoneType]
    e164: Optional[str]

    @classmethod
    def from_orm(cls, phone: Union[db_application_models.Phone, str]) -> "PhoneResponse":
        if isinstance(phone, db_application_models.Phone):
            phone_response = super().from_orm(phone)
            if phone.phone_type_instance:
                phone_response.phone_type = PhoneType[
                    phone.phone_type_instance.phone_type_description
                ]
        else:
            phone_response = cls(phone_number=phone)

        if phone_response.phone_number:
            parsed_phone_number = phonenumbers.parse(phone_response.phone_number)
            number = str(parsed_phone_number.national_number)

            phone_response.e164 = phonenumbers.format_number(
                parsed_phone_number, phonenumbers.PhoneNumberFormat.E164
            )
            phone_response.phone_number = f"{number[0:3]}-{number[3:6]}-{number[-4:]}"
            phone_response.int_code = str(parsed_phone_number.country_code)

        return phone_response
