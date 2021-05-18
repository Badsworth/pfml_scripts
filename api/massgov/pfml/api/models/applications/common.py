from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

import phonenumbers
from phonenumbers.phonenumberutil import region_code_for_country_code, region_code_for_number
from pydantic import UUID4, root_validator

import massgov.pfml.db.models.applications as db_application_models
import massgov.pfml.db.models.employees as db_employee_models
import massgov.pfml.util.pydantic.mask as mask
from massgov.pfml.api.models.common import LookupEnum
from massgov.pfml.api.validation.exceptions import ValidationErrorDetail, ValidationException
from massgov.pfml.util.pydantic import PydanticBaseModel
from massgov.pfml.util.pydantic.types import (
    FinancialRoutingNumber,
    MaskedDateStr,
    MaskedFinancialAcctNum,
    MaskedFinancialRoutingNumber,
)

# Applications I/O types


class Occupation(str, LookupEnum):
    sales_clerk = "Sales Clerk"
    administrative = "Administrative"
    engineer = "Engineer"
    health_care = "Health Care"

    @classmethod
    def get_lookup_model(cls):
        return db_employee_models.LkOccupation


class EmploymentStatus(str, LookupEnum):
    employed = "Employed"
    unemployed = "Unemployed"
    self_employed = "Self-Employed"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkEmploymentStatus


class LeaveReason(str, LookupEnum):
    pregnancy = "Pregnancy/Maternity"
    child_bonding = "Child Bonding"
    serious_health_condition_employee = "Serious Health Condition - Employee"
    caring_leave = "Care for a Family Member"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkLeaveReason


class LeaveReasonQualifier(str, LookupEnum):
    newborn = "Newborn"
    adoption = "Adoption"
    foster_care = "Foster Care"
    serious_health_condition = "Serious Health Condition"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkLeaveReasonQualifier


class RelationshipToCaregiver(str, LookupEnum):
    spouse = "Spouse"
    parent = "Parent"
    child = "Child"
    grandparent = "Grandparent"
    grandchild = "Grandchild"
    other_family_member = "Other Family Member"
    service_member = "Service Member"
    inlaw = "Inlaw"
    sibling = "Sibling - Brother/Sister"
    other = "Other"
    employee = "Employee"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkRelationshipToCaregiver


class RelationshipQualifier(str, LookupEnum):
    adoptive = "Adoptive"
    biological = "Biological"
    foster = "Foster"
    custodial_parent = "Custodial Parent"
    legal_guardian = "Legal Guardian"
    step_parent = "Step Parent"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkRelationshipQualifier


class EmployerNotificationMethod(str, LookupEnum):
    in_writing = "In Writing"
    in_person = "In Person"
    by_telephone = "By Telephone"
    other = "Other"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkNotificationMethod


class ReducedScheduleLeavePeriods(PydanticBaseModel):
    leave_period_id: Optional[UUID4]
    start_date: Optional[date]
    end_date: Optional[date]
    thursday_off_minutes: Optional[int]
    friday_off_minutes: Optional[int]
    saturday_off_minutes: Optional[int]
    sunday_off_minutes: Optional[int]
    monday_off_minutes: Optional[int]
    tuesday_off_minutes: Optional[int]
    wednesday_off_minutes: Optional[int]


class ContinuousLeavePeriods(PydanticBaseModel):
    leave_period_id: Optional[UUID4]
    start_date: Optional[date]
    end_date: Optional[date]
    last_day_worked: Optional[date]
    expected_return_to_work_date: Optional[date]
    start_date_full_day: Optional[bool]
    start_date_off_hours: Optional[int]
    start_date_off_minutes: Optional[int]
    end_date_full_day: Optional[bool]
    end_date_off_hours: Optional[int]
    end_date_off_minutes: Optional[int]


class FrequencyIntervalBasis(str, Enum):
    days = "Days"
    weeks = "Weeks"
    months = "Months"


class DurationBasis(str, Enum):
    minutes = "Minutes"
    hours = "Hours"
    days = "Days"


class IntermittentLeavePeriods(PydanticBaseModel):
    leave_period_id: Optional[UUID4]
    start_date: Optional[date]
    end_date: Optional[date]
    frequency: Optional[int]
    frequency_interval: Optional[int]
    frequency_interval_basis: Optional[FrequencyIntervalBasis]
    duration: Optional[int]
    duration_basis: Optional[DurationBasis]


class Address(PydanticBaseModel):
    line_1: Optional[str]
    line_2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]


class MaskedAddress(Address):
    @classmethod
    def from_orm(cls, address: db_employee_models.Address) -> "MaskedAddress":
        address_response = super().from_orm(address)
        address_response.zip = mask.mask_zip(address.zip_code)
        address_response.state = (
            address.geo_state.geo_state_description if address.geo_state else None
        )
        address_response.line_1 = mask.mask_address(address.address_line_one)
        address_response.line_2 = mask.mask_address(address.address_line_two)

        return address_response


class BaseCaringLeaveMetadata(PydanticBaseModel):
    caring_leave_metadata_id: Optional[UUID4]
    family_member_first_name: Optional[str]
    family_member_middle_name: Optional[str]
    family_member_last_name: Optional[str]
    relationship_to_caregiver: Optional[RelationshipToCaregiver]


class CaringLeaveMetadata(BaseCaringLeaveMetadata):
    family_member_date_of_birth: Optional[date]


class MaskedCaringLeaveMetadata(BaseCaringLeaveMetadata):
    family_member_date_of_birth: Optional[MaskedDateStr]


class BaseApplicationLeaveDetails(PydanticBaseModel):
    reason: Optional[LeaveReason]
    reason_qualifier: Optional[LeaveReasonQualifier]
    reduced_schedule_leave_periods: Optional[List[ReducedScheduleLeavePeriods]]
    continuous_leave_periods: Optional[List[ContinuousLeavePeriods]]
    intermittent_leave_periods: Optional[List[IntermittentLeavePeriods]]
    relationship_to_caregiver: Optional[RelationshipToCaregiver]
    relationship_qualifier: Optional[RelationshipQualifier]
    pregnant_or_recent_birth: Optional[bool]
    employer_notified: Optional[bool]
    employer_notification_date: Optional[date]
    employer_notification_method: Optional[EmployerNotificationMethod]
    has_future_child_date: Optional[bool]


class MaskedApplicationLeaveDetails(BaseApplicationLeaveDetails):
    child_birth_date: Optional[MaskedDateStr]
    child_placement_date: Optional[MaskedDateStr]
    caring_leave_metadata: Optional[MaskedCaringLeaveMetadata]

    @classmethod
    def from_orm(
        cls, application: db_application_models.Application
    ) -> "MaskedApplicationLeaveDetails":
        leave_details = super().from_orm(application)

        # This model is shared by requests and responses but some fields need to
        # be loaded from different keys in the different situations:
        #
        # - `reason` on request bodies
        # - `leave_reason` on an Application
        #
        # And similarly:
        #
        # - `reason_qualifier` on request bodies
        # - `leave_reason_qualifier` on an Application
        #
        # The alias feature in pydantic applies to every situation data is
        # parsed from a source, therefore can't be used to support reading from
        # two different field names.
        #
        # Since loading from an Application is almost always going to be through
        # the `from_orm` method, we'll do the aliases ourselves for that use
        # case.
        if application.leave_reason is not None:
            leave_details.reason = LeaveReason(application.leave_reason.leave_reason_description)

        if application.leave_reason_qualifier is not None:
            leave_details.reason_qualifier = LeaveReasonQualifier(
                application.leave_reason_qualifier.leave_reason_qualifier_description
            )

        return leave_details


class ApplicationLeaveDetails(BaseApplicationLeaveDetails):
    child_birth_date: Optional[date]
    child_placement_date: Optional[date]
    caring_leave_metadata: Optional[CaringLeaveMetadata]


class PaymentMethod(str, LookupEnum):
    ach = "Elec Funds Transfer"
    check = "Check"
    debit = "Debit"

    @classmethod
    def get_lookup_model(cls):
        return db_employee_models.LkPaymentMethod


class BankAccountType(str, LookupEnum):
    savings = "Savings"
    checking = "Checking"

    @classmethod
    def get_lookup_model(cls):
        return db_employee_models.LkBankAccountType


class WorkPatternType(str, LookupEnum):
    fixed = "Fixed"
    rotating = "Rotating"
    variable = "Variable"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkWorkPatternType


class DayOfWeek(str, LookupEnum):
    sunday = "Sunday"
    monday = "Monday"
    tuesday = "Tuesday"
    wednesday = "Wednesday"
    thursday = "Thursday"
    friday = "Friday"
    saturday = "Saturday"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkDayOfWeek


class BasePaymentPreference(PydanticBaseModel):
    payment_method: Optional[PaymentMethod]
    bank_account_type: Optional[BankAccountType]


class PaymentPreference(BasePaymentPreference):
    account_number: Optional[str]
    routing_number: Optional[FinancialRoutingNumber]


class MaskedPaymentPreference(BasePaymentPreference):
    account_number: Optional[MaskedFinancialAcctNum]
    routing_number: Optional[MaskedFinancialRoutingNumber]


class WorkPatternDay(PydanticBaseModel):
    day_of_week: DayOfWeek
    minutes: Optional[int]


class WorkPattern(PydanticBaseModel):
    work_pattern_type: Optional[WorkPatternType]
    work_pattern_days: Optional[List[WorkPatternDay]]


class AmountFrequency(str, LookupEnum):
    per_day = "Per Day"
    per_week = "Per Week"
    per_month = "Per Month"
    all_at_once = "In Total"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkAmountFrequency


class EmployerBenefitType(str, LookupEnum):
    accrued_paid_leave = "Accrued paid leave"
    short_term_disability = "Short-term disability insurance"
    permanent_disability_insurance = "Permanent disability insurance"
    family_or_medical_leave_insurance = "Family or medical leave insurance"
    unknown = "Unknown"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkEmployerBenefitType


class OtherIncomeType(str, LookupEnum):
    workers_comp = "Workers Compensation"
    unemployment = "Unemployment Insurance"
    ssdi = "SSDI"
    retirement_disability = "Disability benefits under Gov't retirement plan"
    jones_act = "Jones Act benefits"
    railroad_retirement = "Railroad Retirement benefits"
    other_employer = "Earnings from another employment/self-employment"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkOtherIncomeType


class EmployerBenefit(PydanticBaseModel):
    employer_benefit_id: Optional[UUID4]
    benefit_type: Optional[EmployerBenefitType]
    benefit_start_date: Optional[date]
    benefit_end_date: Optional[date]
    benefit_amount_dollars: Optional[Decimal]
    benefit_amount_frequency: Optional[AmountFrequency]
    is_full_salary_continuous: Optional[bool]


class OtherIncome(PydanticBaseModel):
    other_income_id: Optional[UUID4]
    income_type: Optional[OtherIncomeType]
    income_start_date: Optional[date]
    income_end_date: Optional[date]
    income_amount_dollars: Optional[Decimal]
    income_amount_frequency: Optional[AmountFrequency]


# Document I/O Types


class DocumentType(str, LookupEnum):
    passport = "Passport"
    drivers_license_mass = "Driver's License Mass"
    drivers_license_other_state = "Driver's License Other State"
    identification_proof = "Identification Proof"
    state_managed_paid_leave_confirmation = "State managed Paid Leave Confirmation"
    approval_notice = "Approval Notice"
    request_for_more_information = "Request for More Information"
    denial_notice = "Denial Notice"
    own_serious_health_condition_form = "Own serious health condition form"
    pregnancy_maternity_form = "Pregnancy/Maternity form"
    child_bonding_evidence_form = "Child bonding evidence form"
    care_for_a_family_member_form = "Care for a family member form"
    military_exigency_form = "Military exigency form"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkDocumentType


class ContentType(str, LookupEnum):
    pdf = "application/pdf"
    jpeg = "image/jpeg"
    png = "image/png"
    webp = "image/tiff"
    heic = "image/heic"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkContentType


# Phone I/O Types


class PhoneType(str, LookupEnum):
    Cell = "Cell"
    Fax = "Fax"
    Phone = "Phone"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkPhoneType


class Phone(PydanticBaseModel):
    # Phone dict coming from front end contains int_code and phone_number separately
    # Values are Optional, deviating from OpenAPI spec to allow for None values in Response
    int_code: Optional[str]
    phone_number: Optional[str]
    phone_type: Optional[PhoneType]

    @root_validator(pre=False)
    def check_phone_number(cls, values):  # noqa: B902
        error_list = []
        n = None

        int_code = values.get("int_code")
        phone_number = values.get("phone_number")
        if phone_number is None:
            # if phone_number is removed by masking rules, skip validation
            return values

        try:
            # int_code is present in the PATCH request, but not when the Response is being processed
            if int_code:
                n = phonenumbers.parse(phone_number, region_code_for_country_code(int(int_code)))
            else:
                n = phonenumbers.parse(phone_number)
        except phonenumbers.NumberParseException:
            error_list.append(
                ValidationErrorDetail(
                    message="Phone number must be a valid number",
                    type="invalid_phone_number",
                    rule="phone_number_must_be_valid_number",
                    field="phone.phone_number",
                )
            )

        if not phonenumbers.is_valid_number(n):
            error_list.append(
                ValidationErrorDetail(
                    message="Phone number must be a valid number",
                    type="invalid_phone_number",
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

        return values


class MaskedPhone(Phone):
    @classmethod
    def from_orm(cls, phone: db_application_models.Phone) -> "MaskedPhone":
        phone_response = super().from_orm(phone)

        if phone.phone_number:
            parsed_phone_number = phonenumbers.parse(phone.phone_number)

            locally_formatted_number = phonenumbers.format_number(
                parsed_phone_number, region_code_for_number(parsed_phone_number)
            )

            phone_response.phone_number = mask.mask_phone(locally_formatted_number)
            phone_response.int_code = str(parsed_phone_number.country_code)
        if phone.phone_type_instance:
            phone_response.phone_type = PhoneType[phone.phone_type_instance.phone_type_description]

        return phone_response
