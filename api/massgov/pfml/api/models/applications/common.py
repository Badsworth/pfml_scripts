from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import UUID4

import massgov.pfml.db.models.applications as db_application_models
import massgov.pfml.db.models.employees as db_employee_models
import massgov.pfml.util.pydantic.mask as mask
from massgov.pfml.api.models.common import LookupEnum
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

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkLeaveReason


class LeaveReasonQualifier(str, LookupEnum):
    newborn = "Newborn"
    adoption = "Adoption"
    foster_care = "Foster Care"

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkLeaveReasonQualifier


class RelationshipToCaregiver(str, LookupEnum):
    parent = "Parent"
    child = "Child"
    grandparent = "Grandparent"
    grandchild = "Grandchild"
    other_family_member = "Other Family Member"
    service_member = "Service Member"
    inlaw = "Inlaw"
    sibling = "Sibling"
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
        return db_application_models.NotificationMethod


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
    is_estimated: Optional[bool] = True


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
    is_estimated: Optional[bool] = True


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


class PaymentMethod(str, LookupEnum):
    ach = "ACH"
    check = "Check"
    debit = "Debit"

    @classmethod
    def get_lookup_model(cls):
        return db_employee_models.LkPaymentType


class PaymentAccountType(str, Enum):
    checking = "Checking"
    savings = "Savings"


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


class BaseApplicationPaymentAccountDetails(PydanticBaseModel):
    account_name: Optional[str]
    account_type: Optional[PaymentAccountType]


class ApplicationPaymentAccountDetails(BaseApplicationPaymentAccountDetails):
    account_number: Optional[str]
    routing_number: Optional[FinancialRoutingNumber]


class MaskedApplicationPaymentAccountDetails(BaseApplicationPaymentAccountDetails):
    account_number: Optional[MaskedFinancialAcctNum]
    routing_number: Optional[MaskedFinancialRoutingNumber]


class ApplicationPaymentChequeDetails(PydanticBaseModel):
    name_to_print_on_check: Optional[str]


class BasePaymentPreferences(PydanticBaseModel):
    payment_preference_id: Optional[UUID4]
    description: Optional[str]
    payment_method: Optional[PaymentMethod]
    is_default: Optional[bool]
    cheque_details: Optional[ApplicationPaymentChequeDetails]


class PaymentPreferences(BasePaymentPreferences):
    account_details: Optional[ApplicationPaymentAccountDetails]


class MaskedPaymentPreferences(BasePaymentPreferences):
    account_details: Optional[MaskedApplicationPaymentAccountDetails]


class WorkPatternDay(PydanticBaseModel):
    day_of_week: DayOfWeek
    week_number: int
    minutes: Optional[int]


class WorkPattern(PydanticBaseModel):
    work_pattern_type: Optional[WorkPatternType]
    work_week_starts: Optional[DayOfWeek]
    pattern_start_date: Optional[date]
    work_pattern_days: Optional[List[WorkPatternDay]]


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
