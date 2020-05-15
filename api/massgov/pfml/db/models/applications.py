from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, uuid_gen


class LeaveReason(Base):
    __tablename__ = "lk_leave_reason"
    leave_reason = Column(Integer, primary_key=True, autoincrement=True)
    reason_description = Column(Text)


class LeaveReasonQualifier(Base):
    __tablename__ = "lk_leave_reason_qualifier"
    leave_reason_qualifier = Column(Integer, primary_key=True, autoincrement=True)
    reason_qualifier_description = Column(Text)


class LeaveType(Base):
    __tablename__ = "lk_leave_type"
    leave_type = Column(Integer, primary_key=True, autoincrement=True)
    leave_type_description = Column(Text)


class RelationshipToCareGiver(Base):
    __tablename__ = "lk_relationship_to_caregiver"
    relationship = Column(Integer, primary_key=True, autoincrement=True)
    relationship_description = Column(Text)


class NotificationMethod(Base):
    __tablename__ = "lk_notification_method"
    notification_method = Column(Integer, primary_key=True, autoincrement=True)
    notification_method_description = Column(Text)


class FrequencyOrDuration(Base):
    __tablename__ = "lk_frequency_or_duration"
    frequency_or_duration = Column(Integer, primary_key=True, autoincrement=True)
    frequency_duration_description = Column(Text)


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
    occupation_type = Column(Integer, ForeignKey("lk_occupation.occupation_type"))
    relationship_to_caregiver = Column(
        Integer, ForeignKey("lk_relationship_to_caregiver.relationship")
    )
    employer_notified = Column(Boolean)
    employer_notification_date = Column(Date)
    employer_notification_method = Column(
        Integer, ForeignKey("lk_notification_method.notification_method")
    )
    leave_type = Column(Integer, ForeignKey("lk_leave_type.leave_type"))
    leave_reason = Column(Integer, ForeignKey("lk_leave_reason.leave_reason"))
    leave_reason_qualifier = Column(
        Integer, ForeignKey("lk_leave_reason_qualifier.leave_reason_qualifier")
    )
    status = Column(Integer, ForeignKey("lk_status.status_type"))
    start_time = Column(DateTime)
    updated_time = Column(DateTime)
    completed_time = Column(DateTime)
    submitted_time = Column(DateTime)
    fineos_absence_id = Column(Text)
    fineos_notification_case_id = Column(Text)


class ApplicationPaymentPreference(Base):
    __tablename__ = "application_payment_preference"
    payment_pref_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application.application_id"))
    description = Column(Text)
    payment_type = Column(Integer, ForeignKey("lk_payment_type.payment_type"))
    is_default = Column(Boolean)
    account_name = Column(Text)
    account_number = Column(Text)
    routing_number = Column(Text)
    type_of_account = Column(Text)
    name_in_check = Column(Text)


class ContinuousLeavePeriod(Base):
    __tablename__ = "continuous_leave_period"
    leave_period_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application.application_id"))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Integer, ForeignKey("lk_status.status_type"))
    last_day_worked = Column(Date)
    expected_return_to_work_date = Column(Date)
    start_date_full_day = Column(Boolean)
    start_date_off_hours = Column(Integer)
    start_date_off_minutes = Column(Integer)
    end_date_full_day = Column(Boolean)
    end_date_off_hours = Column(Integer)
    end_date_off_minutes = Column(Integer)


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


class ReducedScheduleLeavePeriod(Base):
    __tablename__ = "reduced_schedule_leave_period"
    leave_period_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(UUID(as_uuid=True), ForeignKey("application.application_id"))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Integer, ForeignKey("lk_status.status_type"))
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
