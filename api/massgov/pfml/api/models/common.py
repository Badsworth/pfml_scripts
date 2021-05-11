from datetime import date
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
    PREGNANCY_MATERNITY = "Pregnancy / Maternity"
    SERIOUS_HEALTH_CONDITION = "Serious health condition"
    CARE_FOR_A_FAMILY_MEMBER = "Care for a family member"
    CHILD_BONDING = "Child bonding"
    MILITARY_CAREGIVER = "Military caregiver"
    MILITARY_EXIGENCY_FAMILY = "Military exigency family"
    UNKNOWN = "Unknown"

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
