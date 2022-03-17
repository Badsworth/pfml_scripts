from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import UUID4

import massgov.pfml.db.models.applications as db_application_models
import massgov.pfml.db.models.employees as db_employee_models
import massgov.pfml.util.pydantic.mask as mask
from massgov.pfml.api.models.common import (
    AmountFrequency,
    LookupEnum,
    PreviousLeaveQualifyingReason,
)
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


class EligibilityEmploymentStatus(str, LookupEnum):
    employed = "Employed"
    unemployed = "Unemployed"
    self_employed = "Self-Employed"
    unknown = "Unknown"
    retired = "Retired"


class EmploymentStatus(str, LookupEnum):
    employed = "Employed"
    unemployed = "Unemployed"
    self_employed = "Self-Employed"


class LeaveReason(str, LookupEnum):
    pregnancy = "Pregnancy/Maternity"
    child_bonding = "Child Bonding"
    serious_health_condition_employee = "Serious Health Condition - Employee"
    caring_leave = "Care for a Family Member"

    @classmethod
    def to_previous_leave_qualifying_reason(
        cls, leave_reason: "LeaveReason"
    ) -> PreviousLeaveQualifyingReason:
        if leave_reason == LeaveReason.pregnancy:
            return PreviousLeaveQualifyingReason.PREGNANCY_MATERNITY
        elif leave_reason == LeaveReason.child_bonding:
            return PreviousLeaveQualifyingReason.CHILD_BONDING
        elif leave_reason == LeaveReason.serious_health_condition_employee:
            return PreviousLeaveQualifyingReason.AN_ILLNESS_OR_INJURY
        elif leave_reason == LeaveReason.caring_leave:
            return PreviousLeaveQualifyingReason.CARE_FOR_A_FAMILY_MEMBER
        else:
            raise ValueError("unexpected value reason mapping -- was a new value added recently?")


class LeaveReasonQualifier(str, LookupEnum):
    newborn = "Newborn"
    serious_health_condition = "Serious Health Condition"
    # This reason qualifier is not currently being used. See API-389 & PR #1280.
    work_related_accident_injury = "Work Related Accident/Injury"
    adoption = "Adoption"
    foster_care = "Foster Care"
    not_work_related = "Not Work Related"
    sickness = "Sickness"
    postnatal_disability = "Postnatal Disability"
    work_related = "Work Related"
    blood = "Blood"
    blood_stem_cell = "Blood Stem Cell"
    bone_marrow = "Bone Marrow"
    organ = "Organ"
    other = "Other"
    prenatal_care = "Prenatal Care"
    prenatal_disability = "Prenatal Disability"
    pregnancy_related = "Pregnancy Related"
    right_to_leave = "Right to Leave"
    sickness_non_serious_health_condition = "Sickness - Non-Serious Health Condition"
    childcare = "Childcare"
    counseling = "Counseling"
    financial_and_legal_arrangements = "Financial & Legal Arrangements"
    military_events_and_related_activities = "Military Events & Related Activities"
    other_additional_activities = "Other Additional Activities"
    post_deployment_activites_including_bereavement = (
        "Post Deployment Activities - Including Bereavement"
    )
    rest_and_recuperation = "Rest & Recuperation"
    short_notice_deployment = "Short Notice Deployment"
    closure_of_school_childcare = "Closure of School/Childcare"
    quarantine_isolation_non_sick = "Quarantine/Isolation - Not Sick"
    birth_disability = "Birth Disability"
    childcare_and_school_activities = "Childcare and School Activities"


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


class RelationshipQualifier(str, LookupEnum):
    adoptive = "Adoptive"
    biological = "Biological"
    foster = "Foster"
    custodial_parent = "Custodial Parent"
    legal_guardian = "Legal Guardian"
    step_parent = "Step Parent"


class NotificationMethod(str, LookupEnum):
    in_writing = "In Writing"
    in_person = "In Person"
    by_telephone = "By Telephone"
    other = "Other"


class OrganizationUnitSelection(str, Enum):
    not_listed = "not_listed"
    not_selected = "not_selected"


class OrganizationUnit(PydanticBaseModel):
    organization_unit_id: Optional[UUID4]
    employer_id: Optional[UUID4]
    fineos_id: Optional[str]
    name: Optional[str]


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
    employer_notification_method: Optional[NotificationMethod]
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


class BankAccountType(str, LookupEnum):
    savings = "Savings"
    checking = "Checking"


class WorkPatternType(str, LookupEnum):
    fixed = "Fixed"
    rotating = "Rotating"
    variable = "Variable"


class DayOfWeek(str, LookupEnum):
    sunday = "Sunday"
    monday = "Monday"
    tuesday = "Tuesday"
    wednesday = "Wednesday"
    thursday = "Thursday"
    friday = "Friday"
    saturday = "Saturday"


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


class OtherIncomeType(str, LookupEnum):
    workers_comp = "Workers Compensation"
    unemployment = "Unemployment Insurance"
    ssdi = "SSDI"
    retirement_disability = "Disability benefits under Gov't retirement plan"
    jones_act = "Jones Act benefits"
    railroad_retirement = "Railroad Retirement benefits"
    other_employer = "Earnings from another employment/self-employment"


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
    certification_form = (
        "Certification Form"  # only used when Portal uploads a certification document
    )
    own_serious_health_condition_form = "Own serious health condition form"
    pregnancy_maternity_form = "Pregnancy/Maternity form"
    child_bonding_evidence_form = "Child bonding evidence form"
    care_for_a_family_member_form = "Care for a family member form"
    military_exigency_form = "Military exigency form"
    withdrawal_notice = "Pending Application Withdrawn"
    appeal_acknowledgment = "Appeal Acknowledgment"
    maximum_weekly_benefit_change_notice = "Maximum Weekly Benefit Change Notice"
    benefit_amount_change_notice = "Benefit Amount Change Notice"
    leave_allotment_change_notice = "Leave Allotment Change Notice"
    approved_time_cancelled = "Approved Time Cancelled"
    change_request_approved = "Change Request Approved"
    change_request_denied = "Change Request Denied"


class ContentType(str, LookupEnum):
    pdf = "application/pdf"
    jpeg = "image/jpeg"
    png = "image/png"
    webp = "image/tiff"
    heic = "image/heic"


# Gender I/O Types
class Gender(str, LookupEnum):
    woman = "Woman"
    man = "Man"
    non_binary = "Non-binary"
    not_listed = "Gender not listed"
    no_answer = "Prefer not to answer"
