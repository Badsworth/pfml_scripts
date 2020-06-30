from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from massgov.pfml.db.models.employees import Employee, Employer, Occupation, PaymentType, User

from ..lookup import LookupTable
from .base import Base, uuid_gen


class LkLeaveReason(Base):
    __tablename__ = "lk_leave_reason"
    leave_reason_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_reason_description = Column(Text)

    def __init__(self, leave_reason_id, leave_reason_description):
        self.leave_reason_id = leave_reason_id
        self.leave_reason_description = leave_reason_description


class LeaveReasonQualifier(Base):
    __tablename__ = "lk_leave_reason_qualifier"
    leave_reason_qualifier_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_reason_qualifier_description = Column(Text)


class LeaveType(Base):
    __tablename__ = "lk_leave_type"
    leave_type_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_type_description = Column(Text)


class RelationshipToCareGiver(Base):
    __tablename__ = "lk_relationship_to_caregiver"
    relationship_to_caregiver_id = Column(Integer, primary_key=True, autoincrement=True)
    relationship_to_caregiver_description = Column(Text)


class RelationshipQualifier(Base):
    __tablename__ = "lk_relationship_qualifier"
    relationship_qualifier_id = Column(Integer, primary_key=True, autoincrement=True)
    relationship_qualifier_description = Column(Text)


class NotificationMethod(Base):
    __tablename__ = "lk_notification_method"
    notification_method_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_method_description = Column(Text)


class FrequencyOrDuration(Base):
    __tablename__ = "lk_frequency_or_duration"
    frequency_or_duration_id = Column(Integer, primary_key=True, autoincrement=True)
    frequency_or_duration_description = Column(Text)


class Application(Base):
    __tablename__ = "application"
    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"))
    nickname = Column(Text)
    requestor = Column(Integer)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"))
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"))
    first_name = Column(Text)
    last_name = Column(Text)
    middle_initial = Column(Text)
    occupation_id = Column(Integer, ForeignKey("lk_occupation.occupation_id"))
    relationship_to_caregiver_id = Column(
        Integer, ForeignKey("lk_relationship_to_caregiver.relationship_to_caregiver_id")
    )
    relationship_qualifier_id = Column(
        Integer, ForeignKey("lk_relationship_qualifier.relationship_qualifier_id")
    )
    employer_notified = Column(Boolean)
    employer_notification_date = Column(Date)
    employer_notification_method_id = Column(
        Integer, ForeignKey("lk_notification_method.notification_method_id")
    )
    leave_type_id = Column(Integer, ForeignKey("lk_leave_type.leave_type_id"))
    leave_reason_id = Column(Integer, ForeignKey("lk_leave_reason.leave_reason_id"))
    leave_reason_qualifier_id = Column(
        Integer, ForeignKey("lk_leave_reason_qualifier.leave_reason_qualifier_id")
    )
    start_time = Column(DateTime)
    updated_time = Column(DateTime)
    completed_time = Column(DateTime)
    submitted_time = Column(DateTime)
    fineos_absence_id = Column(Text)
    fineos_notification_case_id = Column(Text)

    user = relationship(User)
    employer = relationship(Employer)
    employee = relationship(Employee)
    occupation = relationship(Occupation)
    leave_type = relationship(LeaveType)
    leave_reason = relationship(LkLeaveReason)
    leave_reason_qualifier = relationship(LeaveReasonQualifier)
    relationship_to_caregiver = relationship(RelationshipToCareGiver)
    relationship_qualifier = relationship(RelationshipQualifier)
    employer_notification_method = relationship(NotificationMethod)

    # `uselist` default is True, but for mypy need to state it explicitly so it
    # detects the relationship as many-to-one
    #
    # https://github.com/dropbox/sqlalchemy-stubs/issues/152
    payment_preferences = relationship(
        "ApplicationPaymentPreference", back_populates="application", uselist=True
    )
    continuous_leave_periods = relationship(
        "ContinuousLeavePeriod", back_populates="application", uselist=True
    )
    intermittent_leave_periods = relationship(
        "IntermittentLeavePeriod", back_populates="application", uselist=True
    )
    reduced_schedule_leave_periods = relationship(
        "ReducedScheduleLeavePeriod", back_populates="application", uselist=True
    )


class ApplicationPaymentPreference(Base):
    __tablename__ = "application_payment_preference"
    payment_pref_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application.application_id"))
    description = Column(Text)
    payment_type_id = Column(Integer, ForeignKey("lk_payment_type.payment_type_id"))
    is_default = Column(Boolean)
    account_name = Column(Text)
    account_number = Column(Text)
    routing_number = Column(Text)
    type_of_account = Column(Text)
    name_in_check = Column(Text)

    application = relationship(Application, back_populates="payment_preferences")
    payment_type = relationship(PaymentType)


class ContinuousLeavePeriod(Base):
    __tablename__ = "continuous_leave_period"
    leave_period_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application.application_id"))
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


class IntermittentLeavePeriod(Base):
    __tablename__ = "intermittent_leave_period"
    leave_period_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application.application_id"))
    start_date = Column(Date)
    end_date = Column(Date)
    frequency = Column(Integer)
    frequency_interval = Column(Integer)
    frequency_interval_basis = Column(Text)
    duration = Column(Integer)
    duration_basis = Column(Text)

    application = relationship(Application, back_populates="intermittent_leave_periods")


class ReducedScheduleLeavePeriod(Base):
    __tablename__ = "reduced_schedule_leave_period"
    leave_period_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application.application_id"))
    start_date = Column(Date)
    end_date = Column(Date)
    is_estimated = Column(Boolean, default=True, nullable=False)
    thursday_off_hours = Column(Integer)
    thursday_off_minutes = Column(Integer)
    friday_off_hours = Column(Integer)
    friday_off_minutes = Column(Integer)
    saturday_off_hours = Column(Integer)
    saturday_off_minutes = Column(Integer)
    sunday_off_hours = Column(Integer)
    sunday_off_minutes = Column(Integer)
    monday_off_hours = Column(Integer)
    monday_off_minutes = Column(Integer)
    tuesday_off_hours = Column(Integer)
    tuesday_off_minutes = Column(Integer)
    wednesday_off_hours = Column(Integer)
    wednesday_off_minutes = Column(Integer)

    application = relationship(Application, back_populates="reduced_schedule_leave_periods")


class LeaveReason(LookupTable):
    model = LkLeaveReason
    column_names = ("leave_reason_id", "leave_reason_description")

    CARE_FOR_A_FAMILY_MEMBER = LkLeaveReason(1, "Care For A Family Member")
    PREGNANCY_MATERNITY = LkLeaveReason(2, "Pregnancy/Maternity")
    CHILD_BONDING = LkLeaveReason(3, "Child Bonding")
    SERIOUS_HEALTH_CONDITION_EMPLOYEE = LkLeaveReason(4, "Serious Health Condition - Employee")


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    LeaveReason.sync_to_database(db_session)
    db_session.commit()
