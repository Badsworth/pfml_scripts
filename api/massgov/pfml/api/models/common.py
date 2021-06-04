from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import UUID4

import massgov.pfml.db.models.applications as db_application_models
from massgov.pfml.util.pydantic import PydanticBaseModel


class LookupEnum(Enum):
    @classmethod
    def get_lookup_model(cls):
        return getattr(db_application_models, cls.__name__)

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

    @classmethod
    def get_lookup_model(cls):
        return db_application_models.LkPreviousLeaveQualifyingReason


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
