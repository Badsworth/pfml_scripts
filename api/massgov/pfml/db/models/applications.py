import datetime
from decimal import Decimal
from enum import Enum
from itertools import chain
from typing import Optional

from sqlalchemy import TIMESTAMP, Boolean, Column, Date, ForeignKey, Integer, Numeric, Text, case
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, object_session, relationship

import massgov.pfml.util.logging
from massgov.pfml.db.models.base import deferred
from massgov.pfml.db.models.employees import (
    Address,
    Claim,
    ClaimType,
    Employee,
    Employer,
    LkBankAccountType,
    LkGender,
    LkOccupation,
    LkPaymentMethod,
    OrganizationUnit,
    TaxIdentifier,
    User,
)
from massgov.pfml.rmv.models import RmvAcknowledgement
from massgov.pfml.util.decimals import round_nearest_hundredth

from ..lookup import LookupTable
from .base import Base, TimestampMixin, uuid_gen
from .common import PostgreSQLUUID, StrEnum

logger = massgov.pfml.util.logging.get_logger(__name__)


class NoClaimTypeForAbsenceType(Exception):
    pass


class LkEmploymentStatus(Base):
    __tablename__ = "lk_employment_status"
    employment_status_id = Column(Integer, primary_key=True, autoincrement=True)
    employment_status_description = Column(Text, nullable=False)
    fineos_label = Column(Text)

    def __init__(self, employment_status_id, employment_status_description, fineos_label):
        self.employment_status_id = employment_status_id
        self.employment_status_description = employment_status_description
        self.fineos_label = fineos_label


class LkLeaveReason(Base):
    __tablename__ = "lk_leave_reason"
    leave_reason_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_reason_description = Column(Text, nullable=False)
    _map = None

    def __init__(self, leave_reason_id, leave_reason_description):
        self.leave_reason_id = leave_reason_id
        self.leave_reason_description = leave_reason_description

    @classmethod
    def generate_map(cls):
        return {
            LeaveReason.CARE_FOR_A_FAMILY_MEMBER.leave_reason_id: ClaimType.FAMILY_LEAVE.claim_type_id,
            LeaveReason.PREGNANCY_MATERNITY.leave_reason_id: ClaimType.FAMILY_LEAVE.claim_type_id,
            LeaveReason.CHILD_BONDING.leave_reason_id: ClaimType.FAMILY_LEAVE.claim_type_id,
            LeaveReason.SERIOUS_HEALTH_CONDITION_EMPLOYEE.leave_reason_id: ClaimType.MEDICAL_LEAVE.claim_type_id,
        }

    @hybrid_property
    def absence_to_claim_type(self) -> int:
        if not self._map:
            self._map = self.generate_map()
        if self.leave_reason_id not in self._map:
            raise NoClaimTypeForAbsenceType(f"{self.leave_reason_id} not in the lookup table")
        return self._map[self.leave_reason_id]


class LkLeaveReasonQualifier(Base):
    __tablename__ = "lk_leave_reason_qualifier"
    leave_reason_qualifier_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_reason_qualifier_description = Column(Text, nullable=False)

    def __init__(self, leave_reason_qualifier_id, leave_reason_qualifier_description):
        self.leave_reason_qualifier_id = leave_reason_qualifier_id
        self.leave_reason_qualifier_description = leave_reason_qualifier_description


class LkRelationshipToCaregiver(Base):
    __tablename__ = "lk_relationship_to_caregiver"
    relationship_to_caregiver_id = Column(Integer, primary_key=True, autoincrement=True)
    relationship_to_caregiver_description = Column(Text, nullable=False)

    def __init__(self, relationship_to_caregiver_id, relationship_to_caregiver_description):
        self.relationship_to_caregiver_id = relationship_to_caregiver_id
        self.relationship_to_caregiver_description = relationship_to_caregiver_description


class LkRelationshipQualifier(Base):
    __tablename__ = "lk_relationship_qualifier"
    relationship_qualifier_id = Column(Integer, primary_key=True, autoincrement=True)
    relationship_qualifier_description = Column(Text, nullable=False)

    def __init__(self, relationship_qualifier_id, relationship_qualifier_description):
        self.relationship_qualifier_id = relationship_qualifier_id
        self.relationship_qualifier_description = relationship_qualifier_description


class LkNotificationMethod(Base):
    __tablename__ = "lk_notification_method"
    notification_method_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_method_description = Column(Text, nullable=False)

    def __init__(self, notification_method_id, notification_method_description):
        self.notification_method_id = notification_method_id
        self.notification_method_description = notification_method_description


class LkFrequencyOrDuration(Base):
    __tablename__ = "lk_frequency_or_duration"
    frequency_or_duration_id = Column(Integer, primary_key=True, autoincrement=True)
    frequency_or_duration_description = Column(Text, nullable=False)

    def __init__(self, frequency_or_duration_id, frequency_or_duration_description):
        self.frequency_or_duration_id = frequency_or_duration_id
        self.frequency_or_duration_description = frequency_or_duration_description


class LkWorkPatternType(Base):
    __tablename__ = "lk_work_pattern_type"
    work_pattern_type_id = Column(Integer, primary_key=True, autoincrement=True)
    work_pattern_type_description = Column(Text, nullable=False)

    def __init__(self, work_pattern_type_id, work_pattern_type_description):
        self.work_pattern_type_id = work_pattern_type_id
        self.work_pattern_type_description = work_pattern_type_description


class LkDayOfWeek(Base):
    __tablename__ = "lk_day_of_week"
    day_of_week_id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week_description = Column(Text, nullable=False)

    def __init__(self, day_of_week_id, day_of_week_description):
        self.day_of_week_id = day_of_week_id
        self.day_of_week_description = day_of_week_description


class LkAmountFrequency(Base):
    __tablename__ = "lk_amount_frequency"
    amount_frequency_id = Column(Integer, primary_key=True, autoincrement=True)
    amount_frequency_description = Column(Text, nullable=False)

    def __init__(self, amount_frequency_id, amount_frequency_description):
        self.amount_frequency_id = amount_frequency_id
        self.amount_frequency_description = amount_frequency_description


class LkEmployerBenefitType(Base):
    __tablename__ = "lk_employer_benefit_type"
    employer_benefit_type_id = Column(Integer, primary_key=True, autoincrement=True)
    employer_benefit_type_description = Column(Text, nullable=False)

    def __init__(self, employer_benefit_type_id, employer_benefit_type_description):
        self.employer_benefit_type_id = employer_benefit_type_id
        self.employer_benefit_type_description = employer_benefit_type_description


class LkOtherIncomeType(Base):
    __tablename__ = "lk_other_income_type"
    other_income_type_id = Column(Integer, primary_key=True, autoincrement=True)
    other_income_type_description = Column(Text, nullable=False)

    def __init__(self, other_income_type_id, other_income_type_description):
        self.other_income_type_id = other_income_type_id
        self.other_income_type_description = other_income_type_description


class LkPreviousLeaveQualifyingReason(Base):
    __tablename__ = "lk_previous_leave_qualifying_reason"
    previous_leave_qualifying_reason_id = Column(Integer, primary_key=True, autoincrement=True)
    previous_leave_qualifying_reason_description = Column(Text, nullable=False)

    def __init__(
        self, previous_leave_qualifying_reason_id, previous_leave_qualifying_reason_description
    ):
        self.previous_leave_qualifying_reason_id = previous_leave_qualifying_reason_id
        self.previous_leave_qualifying_reason_description = (
            previous_leave_qualifying_reason_description
        )


class LkPhoneType(Base):
    __tablename__ = "lk_phone_type"
    phone_type_id = Column(Integer, primary_key=True, autoincrement=True)
    phone_type_description = Column(Text, nullable=False)

    def __init__(self, phone_type_id, phone_type_description):
        self.phone_type_id = phone_type_id
        self.phone_type_description = phone_type_description


class Phone(Base, TimestampMixin):
    __tablename__ = "phone"
    application = relationship("Application", back_populates="phone")
    fineos_phone_id = Column(Integer)
    phone_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    phone_number = Column(Text)  # Formatted in E.164
    phone_type_id = Column(Integer, ForeignKey("lk_phone_type.phone_type_id"))
    phone_type_instance = relationship(LkPhoneType)


class ConcurrentLeave(Base, TimestampMixin):
    __tablename__ = "concurrent_leave"
    concurrent_leave_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    application_id = Column(
        PostgreSQLUUID, ForeignKey("application.application_id"), index=True, nullable=False
    )
    is_for_current_employer = Column(Boolean)
    leave_start_date = Column(Date)
    leave_end_date = Column(Date)
    application = relationship("Application")


class PreviousLeave(Base, TimestampMixin):
    # Caution: records of this model get recreated frequently as part of the PATCH /applications/:id endpoint.
    # Only the Application model should hold foreign keys to these records to avoid referenced objects being unexpectedly deleted.
    __tablename__ = "previous_leave"
    previous_leave_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    application_id = Column(
        PostgreSQLUUID, ForeignKey("application.application_id"), index=True, nullable=False
    )
    leave_start_date = Column(Date)
    leave_end_date = Column(Date)
    is_for_current_employer = Column(Boolean)
    leave_reason_id = Column(
        Integer,
        ForeignKey("lk_previous_leave_qualifying_reason.previous_leave_qualifying_reason_id"),
    )
    worked_per_week_minutes = Column(Integer)
    leave_minutes = Column(Integer)
    leave_reason = relationship(LkPreviousLeaveQualifyingReason)
    type = Column(Text)

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "previous_leave"}


# The Application model will have references to previous_leaves for both other and same reasons
# In order for sqlalchemy to distinguish between the 2, we are making PreviousLeave polymorphic
# https://docs.sqlalchemy.org/en/14/orm/inheritance.html#single-table-inheritance
class PreviousLeaveOtherReason(PreviousLeave):
    application = relationship("Application", back_populates="previous_leaves_other_reason")
    __mapper_args__ = {"polymorphic_identity": "other_reason"}


class PreviousLeaveSameReason(PreviousLeave):
    application = relationship("Application", back_populates="previous_leaves_same_reason")
    __mapper_args__ = {"polymorphic_identity": "same_reason"}


class Application(Base, TimestampMixin):
    __tablename__ = "application"
    application_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    user_id = Column(PostgreSQLUUID, ForeignKey("user.user_id"), nullable=False, index=True)
    organization_unit_id = Column(
        PostgreSQLUUID, ForeignKey("organization_unit.organization_unit_id"), nullable=True
    )
    tax_identifier_id = Column(
        PostgreSQLUUID, ForeignKey("tax_identifier.tax_identifier_id"), index=True
    )
    nickname = Column(Text)
    requestor = Column(Integer)
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), nullable=True, unique=True)
    has_mailing_address = Column(Boolean)
    mailing_address_id = Column(PostgreSQLUUID, ForeignKey("address.address_id"), nullable=True)
    residential_address_id = Column(PostgreSQLUUID, ForeignKey("address.address_id"), nullable=True)
    phone_id = Column(PostgreSQLUUID, ForeignKey("phone.phone_id"), nullable=True)
    employer_fein = Column(Text)
    first_name = Column(Text)
    last_name = Column(Text)
    middle_name = Column(Text, nullable=True)
    date_of_birth = Column(Date)
    has_continuous_leave_periods = Column(Boolean)
    has_intermittent_leave_periods = Column(Boolean)
    has_reduced_schedule_leave_periods = Column(Boolean)
    has_state_id = Column(Boolean)
    mass_id = Column(Text)
    occupation_id = Column(Integer, ForeignKey("lk_occupation.occupation_id"))
    organization_unit_selection = Column(Text)
    gender_id = Column(Integer, ForeignKey("lk_gender.gender_id"))
    hours_worked_per_week = Column(Numeric)
    relationship_to_caregiver_id = Column(
        Integer, ForeignKey("lk_relationship_to_caregiver.relationship_to_caregiver_id")
    )
    relationship_qualifier_id = Column(
        Integer, ForeignKey("lk_relationship_qualifier.relationship_qualifier_id")
    )
    pregnant_or_recent_birth = Column(Boolean)
    child_birth_date = Column(Date)
    child_placement_date = Column(Date)
    has_future_child_date = Column(Boolean)
    employer_notified = Column(Boolean)
    employer_notification_date = Column(Date)
    employer_notification_method_id = Column(
        Integer, ForeignKey("lk_notification_method.notification_method_id")
    )
    leave_reason_id = Column(Integer, ForeignKey("lk_leave_reason.leave_reason_id"))
    leave_reason_qualifier_id = Column(
        Integer, ForeignKey("lk_leave_reason_qualifier.leave_reason_qualifier_id")
    )
    employment_status_id = Column(Integer, ForeignKey("lk_employment_status.employment_status_id"))
    work_pattern_id = Column(PostgreSQLUUID, ForeignKey("work_pattern.work_pattern_id"))
    payment_preference_id = Column(
        PostgreSQLUUID, ForeignKey("application_payment_preference.payment_pref_id")
    )
    imported_from_fineos_at = Column(TIMESTAMP(timezone=True))

    start_time = deferred(Column(TIMESTAMP(timezone=True)))
    updated_time = deferred(Column(TIMESTAMP(timezone=True)))

    completed_time = Column(TIMESTAMP(timezone=True))
    submitted_time = Column(TIMESTAMP(timezone=True))
    has_employer_benefits = Column(Boolean)
    has_other_incomes = Column(Boolean)
    has_submitted_payment_preference = Column(Boolean)
    caring_leave_metadata_id = Column(
        PostgreSQLUUID, ForeignKey("caring_leave_metadata.caring_leave_metadata_id")
    )
    has_previous_leaves_same_reason = Column(Boolean)
    has_previous_leaves_other_reason = Column(Boolean)
    has_concurrent_leave = Column(Boolean)
    is_withholding_tax = Column(Boolean, nullable=True)

    split_from_application_id = Column(
        PostgreSQLUUID,
        ForeignKey("application.application_id"),
        nullable=True,
        index=True,
    )

    user = relationship(User)
    caring_leave_metadata = relationship("CaringLeaveMetadata", back_populates="application")
    claim = relationship(Claim, backref=backref("application", uselist=False))
    occupation = relationship(LkOccupation)
    organization_unit = relationship(OrganizationUnit)
    gender = relationship(LkGender)
    leave_reason = relationship(LkLeaveReason)
    leave_reason_qualifier = relationship(LkLeaveReasonQualifier)
    employment_status = relationship(LkEmploymentStatus)
    relationship_to_caregiver = relationship(LkRelationshipToCaregiver)
    relationship_qualifier = relationship(LkRelationshipQualifier)
    employer_notification_method = relationship(LkNotificationMethod)
    tax_identifier = relationship(TaxIdentifier)
    mailing_address = relationship(Address, foreign_keys=[mailing_address_id])
    residential_address = relationship(Address, foreign_keys=[residential_address_id])
    payment_preference = relationship("ApplicationPaymentPreference", back_populates="application")
    phone = relationship("Phone", back_populates="application", uselist=False)
    work_pattern = relationship("WorkPattern", back_populates="applications", uselist=False)
    split_from_application = relationship(
        "Application",
        backref=backref("split_into_application", uselist=False),
        remote_side=[application_id],
    )

    # `uselist` default is True, but for mypy need to state it explicitly so it
    # detects the relationship as many-to-one
    #
    # https://github.com/dropbox/sqlalchemy-stubs/issues/152
    continuous_leave_periods = relationship(
        "ContinuousLeavePeriod",
        back_populates="application",
        uselist=True,
        cascade="all, delete-orphan",
    )
    intermittent_leave_periods = relationship(
        "IntermittentLeavePeriod",
        back_populates="application",
        uselist=True,
        cascade="all, delete-orphan",
    )
    reduced_schedule_leave_periods = relationship(
        "ReducedScheduleLeavePeriod",
        back_populates="application",
        uselist=True,
        cascade="all, delete-orphan",
    )
    employer_benefits = relationship("EmployerBenefit", back_populates="application", uselist=True)
    other_incomes = relationship("OtherIncome", back_populates="application", uselist=True)
    previous_leaves_other_reason = relationship(
        "PreviousLeaveOtherReason", back_populates="application", uselist=True
    )
    previous_leaves_same_reason = relationship(
        "PreviousLeaveSameReason", back_populates="application", uselist=True
    )
    concurrent_leave = relationship("ConcurrentLeave", back_populates="application", uselist=False)

    @property
    def employee(self) -> Optional[Employee]:
        if not self.tax_identifier:
            return None
        return (
            object_session(self)
            .query(Employee)
            .join(TaxIdentifier)
            .filter(TaxIdentifier.tax_identifier == self.tax_identifier.tax_identifier)
            .one_or_none()
        )

    @property
    def employer(self) -> Optional[Employer]:
        if not self.employer_fein:
            return None
        return (
            object_session(self)
            .query(Employer)
            .filter(Employer.employer_fein == self.employer_fein)
            .one_or_none()
        )

    @property
    def employee_organization_units(self) -> list[OrganizationUnit]:
        if not self.employee or not self.employer:
            return []
        units = self.employee.get_organization_units(self.employer)
        logger.info(
            "Application found Employee's organization units",
            extra={
                "employer.employer_id": self.employer.employer_id,
                "employee.organization_unit_ids": ",".join(
                    str(r.organization_unit_id) for r in units
                ),
            },
        )
        return units

    @property
    def employer_organization_units(self) -> list[OrganizationUnit]:
        if not self.employer:
            return []
        units = self.employer.organization_units
        logger.info(
            "Application found Employer's organization units",
            extra={
                "employer.employer_id": self.employer.employer_id,
                "employer.organization_unit_ids": ",".join(
                    str(r.organization_unit_id) for r in units
                ),
            },
        )
        return units

    @hybrid_property
    def all_leave_periods(self) -> Optional[list]:
        leave_periods = list(
            chain(
                self.continuous_leave_periods,
                self.intermittent_leave_periods,
                self.reduced_schedule_leave_periods,
            )
        )
        return leave_periods

    @hybrid_property
    def split_into_application_id(self):
        return self.split_into_application.application_id if self.split_into_application else None  # type: ignore

    @hybrid_property
    def fineos_absence_id(self) -> Optional[str]:
        if not self.claim:
            return None

        return self.claim.fineos_absence_id


class CaringLeaveMetadata(Base, TimestampMixin):
    __tablename__ = "caring_leave_metadata"
    caring_leave_metadata_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    family_member_first_name = Column(Text)
    family_member_last_name = Column(Text)
    family_member_middle_name = Column(Text)
    family_member_date_of_birth = Column(Date)
    relationship_to_caregiver_id = Column(
        Integer, ForeignKey("lk_relationship_to_caregiver.relationship_to_caregiver_id")
    )

    relationship_to_caregiver = relationship(LkRelationshipToCaregiver)
    application = relationship("Application", back_populates="caring_leave_metadata", uselist=False)


class ApplicationPaymentPreference(Base, TimestampMixin):
    __tablename__ = "application_payment_preference"
    payment_pref_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    payment_method_id = Column(Integer, ForeignKey("lk_payment_method.payment_method_id"))
    account_number = Column(Text)
    routing_number = Column(Text)
    bank_account_type_id = Column(
        Integer, ForeignKey("lk_bank_account_type.bank_account_type_id"), nullable=True
    )

    application = relationship("Application", back_populates="payment_preference", uselist=False)
    payment_method = relationship(LkPaymentMethod)
    bank_account_type = relationship(LkBankAccountType)


class ContinuousLeavePeriod(Base, TimestampMixin):
    __tablename__ = "continuous_leave_period"
    leave_period_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    application_id = Column(PostgreSQLUUID, ForeignKey("application.application_id"), index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    is_estimated = Column(Boolean, default=True, nullable=False)
    last_day_worked = Column(Date)
    expected_return_to_work_date = Column(Date)
    start_date_full_day = Column(Boolean)
    start_date_off_hours = Column(Integer)
    start_date_off_minutes = Column(Integer)
    end_date_full_day = Column(Boolean)
    end_date_off_hours = Column(Integer)
    end_date_off_minutes = Column(Integer)

    application = relationship(Application, back_populates="continuous_leave_periods")


class IntermittentLeavePeriod(Base, TimestampMixin):
    __tablename__ = "intermittent_leave_period"
    leave_period_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    application_id = Column(PostgreSQLUUID, ForeignKey("application.application_id"), index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    frequency = Column(Integer)
    frequency_interval = Column(Integer)
    frequency_interval_basis = Column(Text)
    duration = Column(Integer)
    duration_basis = Column(Text)

    application = relationship(Application, back_populates="intermittent_leave_periods")


class ReducedScheduleLeavePeriod(Base, TimestampMixin):
    __tablename__ = "reduced_schedule_leave_period"
    leave_period_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    application_id = Column(PostgreSQLUUID, ForeignKey("application.application_id"), index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    is_estimated = Column(Boolean, default=True, nullable=False)
    sunday_off_minutes = Column(Integer)
    monday_off_minutes = Column(Integer)
    tuesday_off_minutes = Column(Integer)
    wednesday_off_minutes = Column(Integer)
    thursday_off_minutes = Column(Integer)
    friday_off_minutes = Column(Integer)
    saturday_off_minutes = Column(Integer)

    application = relationship(Application, back_populates="reduced_schedule_leave_periods")


class EmployerBenefit(Base, TimestampMixin):
    # Caution: records of this model get recreated frequently as part of the PATCH /applications/:id endpoint.
    # Only the Application model should hold foreign keys to these records to avoid referenced objects being unexpectedly deleted.
    __tablename__ = "employer_benefit"
    employer_benefit_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    application_id = Column(
        PostgreSQLUUID, ForeignKey("application.application_id"), index=True, nullable=False
    )
    benefit_start_date = Column(Date)
    benefit_end_date = Column(Date)
    benefit_type_id = Column(
        Integer, ForeignKey("lk_employer_benefit_type.employer_benefit_type_id")
    )
    benefit_amount_dollars = Column(Numeric(asdecimal=True))
    benefit_amount_frequency_id = Column(
        Integer, ForeignKey("lk_amount_frequency.amount_frequency_id")
    )
    is_full_salary_continuous = Column(Boolean)

    application = relationship(Application, back_populates="employer_benefits")
    benefit_type = relationship(LkEmployerBenefitType)
    benefit_amount_frequency = relationship(LkAmountFrequency)


class OtherIncome(Base, TimestampMixin):
    # Caution: records of this model get recreated frequently as part of the PATCH /applications/:id endpoint.
    # Only the Application model should hold foreign keys to these records to avoid referenced objects being unexpectedly deleted.
    __tablename__ = "other_income"
    other_income_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    application_id = Column(
        PostgreSQLUUID, ForeignKey("application.application_id"), index=True, nullable=False
    )
    income_start_date = Column(Date)
    income_end_date = Column(Date)
    income_type_id = Column(Integer, ForeignKey("lk_other_income_type.other_income_type_id"))
    income_amount_dollars = Column(Numeric(asdecimal=True))
    income_amount_frequency_id = Column(
        Integer, ForeignKey("lk_amount_frequency.amount_frequency_id")
    )

    application = relationship(Application, back_populates="other_incomes")
    income_type = relationship(LkOtherIncomeType)
    income_amount_frequency = relationship(LkAmountFrequency)


class WorkPattern(Base, TimestampMixin):
    __tablename__ = "work_pattern"
    work_pattern_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    work_pattern_type_id = Column(Integer, ForeignKey("lk_work_pattern_type.work_pattern_type_id"))

    applications = relationship("Application", back_populates="work_pattern", uselist=True)
    work_pattern_type = relationship(LkWorkPatternType)
    work_pattern_days = relationship(
        "WorkPatternDay",
        back_populates="work_pattern",
        uselist=True,
        order_by="asc(WorkPatternDay.sort_order)",
    )


class WorkPatternDay(Base, TimestampMixin):
    __tablename__ = "work_pattern_day"
    work_pattern_id = Column(
        PostgreSQLUUID, ForeignKey("work_pattern.work_pattern_id"), primary_key=True
    )
    day_of_week_id = Column(Integer, ForeignKey("lk_day_of_week.day_of_week_id"), primary_key=True)
    minutes = Column(Integer)

    work_pattern = relationship("WorkPattern", back_populates="work_pattern_days", uselist=False)
    day_of_week = relationship(LkDayOfWeek)
    relationship(WorkPattern, back_populates="work_pattern_days")

    @hybrid_property
    def sort_order(self):
        """Set sort order of Sunday to 0"""
        day_of_week_is_sunday = self.day_of_week_id == 7
        return case([(day_of_week_is_sunday, 0)], else_=self.day_of_week_id)  # type: ignore


class WorkPatternType(LookupTable):
    model = LkWorkPatternType
    column_names = ("work_pattern_type_id", "work_pattern_type_description")

    FIXED = LkWorkPatternType(0, "Fixed")
    ROTATING = LkWorkPatternType(1, "Rotating")
    VARIABLE = LkWorkPatternType(2, "Variable")


class DayOfWeek(LookupTable):
    model = LkDayOfWeek
    column_names = ("day_of_week_id", "day_of_week_description")

    MONDAY = LkDayOfWeek(1, "Monday")
    TUESDAY = LkDayOfWeek(2, "Tuesday")
    WEDNESDAY = LkDayOfWeek(3, "Wednesday")
    THURSDAY = LkDayOfWeek(4, "Thursday")
    FRIDAY = LkDayOfWeek(5, "Friday")
    SATURDAY = LkDayOfWeek(6, "Saturday")
    SUNDAY = LkDayOfWeek(7, "Sunday")


class LeaveReason(LookupTable):
    model = LkLeaveReason
    column_names = ("leave_reason_id", "leave_reason_description")

    CARE_FOR_A_FAMILY_MEMBER = LkLeaveReason(1, "Care for a Family Member")
    PREGNANCY_MATERNITY = LkLeaveReason(2, "Pregnancy/Maternity")
    CHILD_BONDING = LkLeaveReason(3, "Child Bonding")
    SERIOUS_HEALTH_CONDITION_EMPLOYEE = LkLeaveReason(4, "Serious Health Condition - Employee")


class LeaveReasonQualifier(LookupTable):
    model = LkLeaveReasonQualifier
    column_names = ("leave_reason_qualifier_id", "leave_reason_qualifier_description")

    NEWBORN = LkLeaveReasonQualifier(1, "Newborn")
    SERIOUS_HEALTH_CONDITION = LkLeaveReasonQualifier(2, "Serious Health Condition")
    # This reason qualifier is not currently being used. See API-389 & PR #1280.
    WORK_RELATED_ACCIDENT_INJURY = LkLeaveReasonQualifier(3, "Work Related Accident/Injury")
    ADOPTION = LkLeaveReasonQualifier(4, "Adoption")
    FOSTER_CARE = LkLeaveReasonQualifier(5, "Foster Care")
    NOT_WORK_RELATED = LkLeaveReasonQualifier(6, "Not Work Related")
    SICKNESS = LkLeaveReasonQualifier(7, "Sickness")
    POSTNATAL_DISABILITY = LkLeaveReasonQualifier(8, "Postnatal Disability")


class RelationshipToCaregiver(LookupTable):
    model = LkRelationshipToCaregiver
    column_names = ("relationship_to_caregiver_id", "relationship_to_caregiver_description")

    PARENT = LkRelationshipToCaregiver(1, "Parent")
    CHILD = LkRelationshipToCaregiver(2, "Child")
    GRANDPARENT = LkRelationshipToCaregiver(3, "Grandparent")
    GRANDCHILD = LkRelationshipToCaregiver(4, "Grandchild")
    OTHER_FAMILY_MEMBER = LkRelationshipToCaregiver(5, "Other Family Member")
    SERVICE_MEMBER = LkRelationshipToCaregiver(6, "Service Member")
    INLAW = LkRelationshipToCaregiver(7, "Inlaw")
    SIBLING = LkRelationshipToCaregiver(8, "Sibling - Brother/Sister")
    OTHER = LkRelationshipToCaregiver(9, "Other")
    EMPLOYEE = LkRelationshipToCaregiver(10, "Employee")
    SPOUSE = LkRelationshipToCaregiver(11, "Spouse")


class RelationshipQualifier(LookupTable):
    model = LkRelationshipQualifier
    column_names = ("relationship_qualifier_id", "relationship_qualifier_description")

    ADOPTED = LkRelationshipQualifier(1, "Adopted")
    BIOLOGICAL = LkRelationshipQualifier(2, "Biological")
    FOSTER = LkRelationshipQualifier(3, "Foster")
    CUSTODIAL_PARENT = LkRelationshipQualifier(4, "Custodial Parent")
    LEGAL_GAURDIAN = LkRelationshipQualifier(5, "Legal Guardian")
    STEP_PARENT = LkRelationshipQualifier(6, "Step Parent")
    LEGALLY_MARRIED = LkRelationshipQualifier(7, "Legally Married")
    UNDISCLOSED = LkRelationshipQualifier(8, "Undisclosed")
    PARENT_IN_LAW = LkRelationshipQualifier(9, "Parent-In-Law")


class NotificationMethod(LookupTable):
    model = LkNotificationMethod
    column_names = ("notification_method_id", "notification_method_description")

    IN_WRITING = LkNotificationMethod(1, "In Writing")
    IN_PERSON = LkNotificationMethod(2, "In Person")
    BY_TELEPHONE = LkNotificationMethod(3, "By Telephone")
    OTHER = LkNotificationMethod(4, "Other")


class FrequencyOrDuration(LookupTable):
    model = LkFrequencyOrDuration
    column_names = ("frequency_or_duration_id", "frequency_or_duration_description")

    DAYS = LkFrequencyOrDuration(1, "Days")
    WEEKS = LkFrequencyOrDuration(2, "Weeks")
    MONTHS = LkFrequencyOrDuration(3, "Months")
    MINUTES = LkFrequencyOrDuration(4, "Minutes")
    HOURS = LkFrequencyOrDuration(5, "Hours")


class EmploymentStatus(LookupTable):
    model = LkEmploymentStatus
    column_names = ("employment_status_id", "employment_status_description", "fineos_label")

    EMPLOYED = LkEmploymentStatus(1, "Employed", "Active")
    UNEMPLOYED = LkEmploymentStatus(2, "Unemployed", "Terminated")
    SELF_EMPLOYED = LkEmploymentStatus(3, "Self-Employed", "Self-Employed")


class AmountFrequency(LookupTable):
    model = LkAmountFrequency
    column_names = ("amount_frequency_id", "amount_frequency_description")

    PER_DAY = LkAmountFrequency(1, "Per Day")
    PER_WEEK = LkAmountFrequency(2, "Per Week")
    PER_MONTH = LkAmountFrequency(3, "Per Month")
    ALL_AT_ONCE = LkAmountFrequency(4, "In Total")


class EmployerBenefitType(LookupTable):
    model = LkEmployerBenefitType
    column_names = ("employer_benefit_type_id", "employer_benefit_type_description")

    ACCRUED_PAID_LEAVE = LkEmployerBenefitType(1, "Accrued paid leave")
    SHORT_TERM_DISABILITY = LkEmployerBenefitType(2, "Short-term disability insurance")
    PERMANENT_DISABILITY_INSURANCE = LkEmployerBenefitType(3, "Permanent disability insurance")
    FAMILY_OR_MEDICAL_LEAVE_INSURANCE = LkEmployerBenefitType(
        4, "Family or medical leave insurance"
    )
    UNKNOWN = LkEmployerBenefitType(5, "Unknown")


class OtherIncomeType(LookupTable):
    model = LkOtherIncomeType
    column_names = ("other_income_type_id", "other_income_type_description")

    WORKERS_COMP = LkOtherIncomeType(1, "Workers Compensation")
    UNEMPLOYMENT = LkOtherIncomeType(2, "Unemployment Insurance")
    SSDI = LkOtherIncomeType(3, "SSDI")
    RETIREMENT_DISABILITY = LkOtherIncomeType(4, "Disability benefits under Gov't retirement plan")
    JONES_ACT = LkOtherIncomeType(5, "Jones Act benefits")
    RAILROAD_RETIREMENT = LkOtherIncomeType(6, "Railroad Retirement benefits")
    OTHER_EMPLOYER = LkOtherIncomeType(7, "Earnings from another employment/self-employment")


class FINEOSWebIdExt(Base, TimestampMixin):
    __tablename__ = "link_fineos_web_id_ext"
    employee_tax_identifier = Column(Text, primary_key=True)
    employer_fein = Column(Text, primary_key=True)
    fineos_web_id = Column(Text)


class LkDocumentType(Base):
    __tablename__ = "lk_document_type"
    document_type_id = Column(Integer, primary_key=True, autoincrement=True)
    document_type_description = Column(Text, nullable=False)

    def __init__(self, document_type_id, document_type_description):
        self.document_type_id = document_type_id
        self.document_type_description = document_type_description


class DocumentType(LookupTable):
    model = LkDocumentType
    column_names = ("document_type_id", "document_type_description")

    PASSPORT = LkDocumentType(1, "Passport")
    DRIVERS_LICENSE_MASS = LkDocumentType(2, "Driver's License Mass")
    DRIVERS_LICENSE_OTHER_STATE = LkDocumentType(3, "Driver's License Other State")
    IDENTIFICATION_PROOF = LkDocumentType(4, "Identification Proof")
    STATE_MANAGED_PAID_LEAVE_CONFIRMATION = LkDocumentType(
        5, "State managed Paid Leave Confirmation"
    )
    APPROVAL_NOTICE = LkDocumentType(6, "Approval Notice")
    REQUEST_FOR_MORE_INFORMATION = LkDocumentType(7, "Request for More Information")
    DENIAL_NOTICE = LkDocumentType(8, "Denial Notice")
    OWN_SERIOUS_HEALTH_CONDITION_FORM = LkDocumentType(9, "Own serious health condition form")
    PREGNANCY_MATERNITY_FORM = LkDocumentType(10, "Pregnancy/Maternity form")
    CHILD_BONDING_EVIDENCE_FORM = LkDocumentType(11, "Child bonding evidence form")
    CARE_FOR_A_FAMILY_MEMBER_FORM = LkDocumentType(12, "Care for a family member form")
    MILITARY_EXIGENCY_FORM = LkDocumentType(13, "Military exigency form")
    WITHDRAWAL_NOTICE = LkDocumentType(14, "Pending Application Withdrawn")
    APPEAL_ACKNOWLEDGMENT = LkDocumentType(15, "Appeal Acknowledgment")
    MAXIMUM_WEEKLY_BENEFIT_CHANGE_NOTICE = LkDocumentType(
        16, "Maximum Weekly Benefit Change Notice"
    )
    BENEFIT_AMOUNT_CHANGE_NOTICE = LkDocumentType(17, "Benefit Amount Change Notice")
    LEAVE_ALLOTMENT_CHANGE_NOTICE = LkDocumentType(18, "Leave Allotment Change Notice")
    APPROVED_TIME_CANCELLED = LkDocumentType(19, "Approved Time Cancelled")
    CHANGE_REQUEST_APPROVED = LkDocumentType(20, "Change Request Approved")
    CHANGE_REQUEST_DENIED = LkDocumentType(21, "Change Request Denied")
    IRS_1099G_TAX_FORM_FOR_CLAIMANTS = LkDocumentType(22, "1099G Tax Form for Claimants")


class Document(Base, TimestampMixin):
    __tablename__ = "document"
    document_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    user_id = Column(PostgreSQLUUID, ForeignKey("user.user_id"), nullable=False, index=True)
    application_id = Column(
        PostgreSQLUUID, ForeignKey("application.application_id"), nullable=False, index=True
    )
    document_type_id = Column(
        Integer, ForeignKey("lk_document_type.document_type_id"), nullable=False
    )
    size_bytes = Column(Integer, nullable=False)
    fineos_id = Column(Text, nullable=True)
    is_stored_in_s3 = Column(Boolean, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    document_type_instance = relationship(LkDocumentType)


class RMVCheckApiErrorCode(Enum):
    FAILED_TO_BUILD_REQUEST = "FAILED_TO_BUILD_REQUEST"
    NETWORKING_ISSUES = "NETWORKING_ISSUES"
    FAILED_TO_PARSE_RESPONSE = "FAILED_TO_PARSE_RESPONSE"
    UNKNOWN_RMV_ISSUE = "UNKNOWN_RMV_ISSUE"


class RMVCheck(Base, TimestampMixin):
    __tablename__ = "rmv_check"
    rmv_check_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    request_to_rmv_started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    request_to_rmv_completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    check_expiration = Column(Boolean, nullable=False, default=False, server_default="FALSE")
    check_customer_inactive = Column(Boolean, nullable=False, default=False, server_default="FALSE")
    check_active_fraudulent_activity = Column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    check_mass_id_number = Column(Boolean, nullable=False, default=False, server_default="FALSE")
    check_residential_address_line_1 = Column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    check_residential_address_line_2 = Column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    check_residential_city = Column(Boolean, nullable=False, default=False, server_default="FALSE")
    check_residential_zip_code = Column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )

    has_passed_required_checks = Column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )

    rmv_error_code = Column(StrEnum(RmvAcknowledgement), nullable=True)
    api_error_code = Column(StrEnum(RMVCheckApiErrorCode), nullable=True)

    absence_case_id = Column(Text, nullable=False, index=True)
    rmv_customer_key = Column(Text, nullable=True)


class UnemploymentMetric(Base, TimestampMixin):
    __tablename__ = "unemployment_metric"
    effective_date = Column(Date, primary_key=True, nullable=False)
    unemployment_minimum_earnings = Column(Numeric, nullable=False)

    def __init__(self, effective_date: datetime.date, unemployment_minimum_earnings: str):
        """Constructor that takes metric values as strings.

        This ensures that the decimals are precise. For example compare Decimal(1431.66) to
        Decimal("1431.66").
        """
        self.effective_date = effective_date
        self.unemployment_minimum_earnings = Decimal(unemployment_minimum_earnings)

    def __repr__(self):
        return "UnemploymentMetric(%s, %s)" % (
            self.effective_date,
            self.unemployment_minimum_earnings,
        )


class BenefitsMetrics(Base, TimestampMixin):
    __tablename__ = "benefits_metrics"
    effective_date = Column(Date, primary_key=True, nullable=False)
    average_weekly_wage = Column(Numeric, nullable=False)
    maximum_weekly_benefit_amount = Column(Numeric, nullable=False)

    def __init__(
        self,
        effective_date: datetime.date,
        average_weekly_wage: str,
        maximum_weekly_benefit_amount: Optional[str] = None,
    ):
        """Constructor that takes metric values as strings.

        This ensures that the decimals are precise. For example compare Decimal(1431.66) to
        Decimal("1431.66").
        """
        self.effective_date = effective_date
        self.average_weekly_wage = Decimal(average_weekly_wage)

        # When the maximum weekly benefit is not manually set, it will be calculated based on
        # the average weekly wage, as per the regulation:
        # https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXXII/Chapter175M/Section3
        if maximum_weekly_benefit_amount is None:
            self.maximum_weekly_benefit_amount = round_nearest_hundredth(
                self.average_weekly_wage * Decimal(".64")
            )
        else:
            self.maximum_weekly_benefit_amount = Decimal(maximum_weekly_benefit_amount)

    def __repr__(self):
        return "BenefitsMetrics(%s, %s, %s)" % (
            self.effective_date,
            self.average_weekly_wage,
            self.maximum_weekly_benefit_amount,
        )


def sync_state_metrics(db_session):
    # For the first year of the program, the maximum weekly benefit is $850, which needs to
    # be set directly. Beyond that, we should only directly set the unempleoyment minimum
    # earnings and the average weekly wage. The maximum weekly benefit amount will then be
    # calculated based on the average weekly wage.

    state_metrics = [
        BenefitsMetrics(
            effective_date=datetime.date(2020, 10, 1),
            average_weekly_wage="1431.66",
            maximum_weekly_benefit_amount="850.00",
        ),
        UnemploymentMetric(
            effective_date=datetime.date(2020, 10, 1), unemployment_minimum_earnings="5100.00"
        ),
        BenefitsMetrics(
            effective_date=datetime.date(2021, 1, 1),
            average_weekly_wage="1487.78",
            maximum_weekly_benefit_amount="850.00",
        ),
        UnemploymentMetric(
            effective_date=datetime.date(2021, 1, 1), unemployment_minimum_earnings="5400.00"
        ),
        BenefitsMetrics(effective_date=datetime.date(2022, 1, 2), average_weekly_wage="1694.24"),
        UnemploymentMetric(
            effective_date=datetime.date(2022, 1, 2), unemployment_minimum_earnings="5700.00"
        ),
    ]

    for metric in state_metrics:
        instance = db_session.merge(metric)
        if db_session.is_modified(instance):
            logger.info("updating metric %r", instance)

    db_session.commit()


class Notification(Base, TimestampMixin):
    __tablename__ = "notification"
    notification_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    request_json = Column(JSONB, nullable=False)
    fineos_absence_id = Column(Text, index=True)


class PhoneType(LookupTable):
    model = LkPhoneType
    column_names = ("phone_type_id", "phone_type_description")

    CELL = LkPhoneType(1, "Cell")
    FAX = LkPhoneType(2, "Fax")
    PHONE = LkPhoneType(3, "Phone")


# TODO (CP-1554): investigate whether this model can be merged with LeaveReason
class PreviousLeaveQualifyingReason(LookupTable):
    model = LkPreviousLeaveQualifyingReason
    column_names = (
        "previous_leave_qualifying_reason_id",
        "previous_leave_qualifying_reason_description",
    )

    PREGNANCY_MATERNITY = LkPreviousLeaveQualifyingReason(1, "Pregnancy")
    AN_ILLNESS_OR_INJURY = LkPreviousLeaveQualifyingReason(2, "An illness or injury")
    CARE_FOR_A_FAMILY_MEMBER = LkPreviousLeaveQualifyingReason(
        3, "Caring for a family member with a serious health condition"
    )
    CHILD_BONDING = LkPreviousLeaveQualifyingReason(
        4, "Bonding with my child after birth or placement"
    )
    MILITARY_CAREGIVER = LkPreviousLeaveQualifyingReason(
        5, "Caring for a family member who serves in the armed forces"
    )
    MILITARY_EXIGENCY_FAMILY = LkPreviousLeaveQualifyingReason(
        6, "Managing family affairs while a family member is on active duty in the armed forces"
    )


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    LeaveReason.sync_to_database(db_session)
    LeaveReasonQualifier.sync_to_database(db_session)
    RelationshipToCaregiver.sync_to_database(db_session)
    RelationshipQualifier.sync_to_database(db_session)
    NotificationMethod.sync_to_database(db_session)
    FrequencyOrDuration.sync_to_database(db_session)
    EmploymentStatus.sync_to_database(db_session)
    AmountFrequency.sync_to_database(db_session)
    EmployerBenefitType.sync_to_database(db_session)
    OtherIncomeType.sync_to_database(db_session)
    DocumentType.sync_to_database(db_session)
    DayOfWeek.sync_to_database(db_session)
    WorkPatternType.sync_to_database(db_session)
    PhoneType.sync_to_database(db_session)
    PreviousLeaveQualifyingReason.sync_to_database(db_session)
    db_session.commit()
