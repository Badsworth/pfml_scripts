from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from massgov.pfml.db.models.employees import (
    Address,
    Employee,
    Employer,
    LkOccupation,
    LkPaymentType,
    TaxIdentifier,
    User,
)
from massgov.pfml.rmv.models import RmvAcknowledgement

from ..lookup import LookupTable
from .base import Base, utc_timestamp_gen, uuid_gen
from .common import StrEnum


class LkEmploymentStatus(Base):
    __tablename__ = "lk_employment_status"
    employment_status_id = Column(Integer, primary_key=True, autoincrement=True)
    employment_status_description = Column(Text)

    def __init__(self, employment_status_id, employment_status_description):
        self.employment_status_id = employment_status_id
        self.employment_status_description = employment_status_description


class LkLeaveReason(Base):
    __tablename__ = "lk_leave_reason"
    leave_reason_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_reason_description = Column(Text)

    def __init__(self, leave_reason_id, leave_reason_description):
        self.leave_reason_id = leave_reason_id
        self.leave_reason_description = leave_reason_description


class LkLeaveReasonQualifier(Base):
    __tablename__ = "lk_leave_reason_qualifier"
    leave_reason_qualifier_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_reason_qualifier_description = Column(Text)

    def __init__(self, leave_reason_qualifier_id, leave_reason_qualifier_description):
        self.leave_reason_qualifier_id = leave_reason_qualifier_id
        self.leave_reason_qualifier_description = leave_reason_qualifier_description


class LkLeaveType(Base):
    __tablename__ = "lk_leave_type"
    leave_type_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_type_description = Column(Text)

    def __init__(self, leave_type_id, leave_type_description):
        self.leave_type_id = leave_type_id
        self.leave_type_description = leave_type_description


class LkRelationshipToCareGiver(Base):
    __tablename__ = "lk_relationship_to_caregiver"
    relationship_to_caregiver_id = Column(Integer, primary_key=True, autoincrement=True)
    relationship_to_caregiver_description = Column(Text)

    def __init__(self, relationship_to_caregiver_id, relationship_to_caregiver_description):
        self.relationship_to_caregiver_id = relationship_to_caregiver_id
        self.relationship_to_caregiver_description = relationship_to_caregiver_description


class LkRelationshipQualifier(Base):
    __tablename__ = "lk_relationship_qualifier"
    relationship_qualifier_id = Column(Integer, primary_key=True, autoincrement=True)
    relationship_qualifier_description = Column(Text)

    def __init__(self, relationship_qualifier_id, relationship_qualifier_description):
        self.relationship_qualifier_id = relationship_qualifier_id
        self.relationship_qualifier_description = relationship_qualifier_description


class LkNotificationMethod(Base):
    __tablename__ = "lk_notification_method"
    notification_method_id = Column(Integer, primary_key=True, autoincrement=True)
    notification_method_description = Column(Text)

    def __init__(self, notification_method_id, notification_method_description):
        self.notification_method_id = notification_method_id
        self.notification_method_description = notification_method_description


class LkFrequencyOrDuration(Base):
    __tablename__ = "lk_frequency_or_duration"
    frequency_or_duration_id = Column(Integer, primary_key=True, autoincrement=True)
    frequency_or_duration_description = Column(Text)

    def __init__(self, frequency_or_duration_id, frequency_or_duration_description):
        self.frequency_or_duration_id = frequency_or_duration_id
        self.frequency_or_duration_description = frequency_or_duration_description


class LkWorkPatternType(Base):
    __tablename__ = "lk_work_pattern_type"
    work_pattern_type_id = Column(Integer, primary_key=True, autoincrement=True)
    work_pattern_type_description = Column(Text)

    def __init__(self, work_pattern_type_id, work_pattern_type_description):
        self.work_pattern_type_id = work_pattern_type_id
        self.work_pattern_type_description = work_pattern_type_description


class LkDayOfWeek(Base):
    __tablename__ = "lk_day_of_week"
    day_of_week_id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week_description = Column(Text)

    def __init__(self, day_of_week_id, day_of_week_description):
        self.day_of_week_id = day_of_week_id
        self.day_of_week_description = day_of_week_description


class Application(Base):
    __tablename__ = "application"
    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False, index=True)
    tax_identifier_id = Column(UUID(as_uuid=True), ForeignKey("tax_identifier.tax_identifier_id"))
    nickname = Column(Text)
    requestor = Column(Integer)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), index=True)
    has_mailing_address = Column(Boolean)
    mailing_address_id = Column(UUID(as_uuid=True), ForeignKey("address.address_id"), nullable=True)
    residential_address_id = Column(
        UUID(as_uuid=True), ForeignKey("address.address_id"), nullable=True
    )
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
    employment_status_id = Column(Integer, ForeignKey("lk_employment_status.employment_status_id"))
    work_pattern_id = Column(UUID(as_uuid=True), ForeignKey("work_pattern.work_pattern_id"))
    start_time = Column(TIMESTAMP(timezone=True))
    updated_time = Column(TIMESTAMP(timezone=True))
    completed_time = Column(TIMESTAMP(timezone=True))
    submitted_time = Column(TIMESTAMP(timezone=True))
    fineos_absence_id = Column(Text, index=True)
    fineos_notification_case_id = Column(Text, index=True)

    user = relationship(User)
    employer = relationship(Employer)
    employee = relationship(Employee)
    occupation = relationship(LkOccupation)
    leave_type = relationship(LkLeaveType)
    leave_reason = relationship(LkLeaveReason)
    leave_reason_qualifier = relationship(LkLeaveReasonQualifier)
    employment_status = relationship(LkEmploymentStatus)
    relationship_to_caregiver = relationship(LkRelationshipToCareGiver)
    relationship_qualifier = relationship(LkRelationshipQualifier)
    employer_notification_method = relationship(LkNotificationMethod)
    tax_identifier = relationship(TaxIdentifier)
    mailing_address = relationship(Address, foreign_keys=[mailing_address_id])
    residential_address = relationship(Address, foreign_keys=[residential_address_id])

    work_pattern = relationship("WorkPattern", back_populates="applications", uselist=False)

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
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.application_id"), index=True
    )
    description = Column(Text)
    payment_type_id = Column(Integer, ForeignKey("lk_payment_type.payment_type_id"))
    is_default = Column(Boolean)
    account_name = Column(Text)
    account_number = Column(Text)
    routing_number = Column(Text)
    type_of_account = Column(Text)
    name_in_check = Column(Text)

    application = relationship(Application, back_populates="payment_preferences")
    payment_type = relationship(LkPaymentType)


class ContinuousLeavePeriod(Base):
    __tablename__ = "continuous_leave_period"
    leave_period_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.application_id"), index=True
    )
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
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.application_id"), index=True
    )
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
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.application_id"), index=True
    )
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


class WorkPattern(Base):
    __tablename__ = "work_pattern"
    work_pattern_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    work_pattern_type_id = Column(Integer, ForeignKey("lk_work_pattern_type.work_pattern_type_id"))
    work_week_starts_id = Column(Integer, ForeignKey("lk_day_of_week.day_of_week_id"))
    pattern_start_date = Column(Date)

    applications = relationship("Application", back_populates="work_pattern", uselist=True)
    work_pattern_type = relationship(LkWorkPatternType)
    work_week_starts = relationship(LkDayOfWeek)
    work_pattern_days = relationship("WorkPatternDay", back_populates="work_pattern", uselist=True)


class WorkPatternDay(Base):
    __tablename__ = "work_pattern_day"
    work_pattern_id = Column(
        UUID(as_uuid=True), ForeignKey("work_pattern.work_pattern_id"), primary_key=True
    )
    day_of_week_id = Column(Integer, ForeignKey("lk_day_of_week.day_of_week_id"), primary_key=True)
    week_number = Column(Integer, nullable=False, primary_key=True)
    hours = Column(Integer)
    minutes = Column(Integer)

    work_pattern = relationship("WorkPattern", back_populates="work_pattern_days", uselist=False)
    day_of_week = relationship(LkDayOfWeek)
    relationship(WorkPattern, back_populates="work_pattern_days")


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

    # This reason is not currently being used. See API-389 & PR #1280.
    CARE_FOR_A_FAMILY_MEMBER = LkLeaveReason(1, "Care For A Family Member")
    PREGNANCY_MATERNITY = LkLeaveReason(2, "Pregnancy/Maternity")
    CHILD_BONDING = LkLeaveReason(3, "Child Bonding")
    SERIOUS_HEALTH_CONDITION_EMPLOYEE = LkLeaveReason(4, "Serious Health Condition - Employee")


class LeaveReasonQualifier(LookupTable):
    model = LkLeaveReasonQualifier
    column_names = ("leave_reason_qualifier_id", "leave_reason_qualifier_description")

    NEWBORN = LkLeaveReasonQualifier(1, "Newborn")
    # This reason qualifier is not currently being used. See API-389 & PR #1280.
    SERIOUS_HEALTH_CONDITION = LkLeaveReasonQualifier(2, "Serious Health Condition")
    # This reason qualifier is not currently being used. See API-389 & PR #1280.
    WORK_RELATED_ACCIDENT_INJURY = LkLeaveReasonQualifier(3, "Work Related Accident/Injury")
    ADOPTION = LkLeaveReasonQualifier(4, "Adoption")
    FOSTER_CARE = LkLeaveReasonQualifier(5, "Foster Care")
    NOT_WORK_RELATED = LkLeaveReasonQualifier(6, "Not Work Related")
    SICKNESS = LkLeaveReasonQualifier(7, "Sickness")
    POSTNATAL_DISABILITY = LkLeaveReasonQualifier(8, "Postnatal Disability")


class LeaveType(LookupTable):
    model = LkLeaveType
    column_names = ("leave_type_id", "leave_type_description")

    BONDING_LEAVE = LkLeaveType(1, "Bonding Leave")
    MEDICAL_LEAVE = LkLeaveType(2, "Medical Leave")
    ACCIDENT = LkLeaveType(3, "Accident")
    MILITARY = LkLeaveType(4, "Military")


class RelationshipToCareGiver(LookupTable):
    model = LkRelationshipToCareGiver
    column_names = ("relationship_to_caregiver_id", "relationship_to_caregiver_description")

    PARENT = LkRelationshipToCareGiver(1, "Parent")
    CHILD = LkRelationshipToCareGiver(2, "Child")
    GRANDPARENT = LkRelationshipToCareGiver(3, "Grandparent")
    GRANDCHILD = LkRelationshipToCareGiver(4, "Grandchild")
    OTHER_FAMILY_MEMBER = LkRelationshipToCareGiver(5, "Other Family Member")
    SERVICE_MEMBER = LkRelationshipToCareGiver(6, "Service Member")
    INLAW = LkRelationshipToCareGiver(7, "Inlaw")
    SIBLING = LkRelationshipToCareGiver(8, "Sibling")
    OTHER = LkRelationshipToCareGiver(9, "Other")


class RelationshipQualifier(LookupTable):
    model = LkRelationshipQualifier
    column_names = ("relationship_qualifier_id", "relationship_qualifier_description")

    ADOPTIVE = LkRelationshipQualifier(1, "Adoptive")
    BIOLGICAL = LkRelationshipQualifier(2, "Biological")
    FOSTER = LkRelationshipQualifier(3, "Foster")
    CUSTODIAL_PARENT = LkRelationshipQualifier(4, "Custodial Parent")
    LEGAL_GAURDIAN = LkRelationshipQualifier(5, "Legal Guardian")
    STEP_PARENT = LkRelationshipQualifier(6, "Step Parent")


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
    column_names = ("employment_status_id", "employment_status_description")

    EMPLOYED = LkEmploymentStatus(1, "Employed")
    UNEMPLOYED = LkEmploymentStatus(2, "Unemployed")
    SELF_EMPLOYED = LkEmploymentStatus(3, "Self-Employed")


class FINEOSWebIdExt(Base):
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


class LkContentType(Base):
    __tablename__ = "lk_content_type"
    content_type_id = Column(Integer, primary_key=True, autoincrement=True)
    content_type_description = Column(Text, nullable=False)

    def __init__(self, content_type_id, content_type_description):
        self.content_type_id = content_type_id
        self.content_type_description = content_type_description


class DocumentType(LookupTable):
    model = LkDocumentType
    column_names = ("document_type_id", "document_type_description")

    PASSPORT = LkDocumentType(1, "Passport")
    DRIVERS_LICENSE_MASS = LkDocumentType(2, "Driver's License Mass")
    DRIVERS_LICENSE_OTHER_STATE = LkDocumentType(3, "Driver's License Other State")
    IDENTIFICATION_PROOF = LkDocumentType(4, "Identification Proof")
    STATE_MANAGED_PAID_LEAVE_CONFIRMATION = LkDocumentType(
        5, "State Managed Paid Leave Confirmation"
    )


class ContentType(LookupTable):
    model = LkContentType
    column_names = ("content_type_id", "content_type_description")

    PDF = LkContentType(1, "application/pdf")
    JPEG = LkContentType(2, "image/jpeg")
    PNG = LkContentType(3, "image/png")
    TIFF = LkContentType(4, "image/tiff")
    HEIC = LkContentType(5, "image/heic")


class Document(Base):
    __tablename__ = "document"
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False, index=True)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("application.application_id"), nullable=False, index=True
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    document_type_id = Column(
        Integer, ForeignKey("lk_document_type.document_type_id"), nullable=False
    )
    content_type_id = Column(Integer, ForeignKey("lk_content_type.content_type_id"), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    fineos_id = Column(Text, nullable=True)
    is_stored_in_s3 = Column(Boolean, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    document_type_instance = relationship(LkDocumentType)
    content_type_instance = relationship(LkContentType)


class RMVCheckApiErrorCode(Enum):
    FAILED_TO_BUILD_REQUEST = "FAILED_TO_BUILD_REQUEST"
    NETWORKING_ISSUES = "NETWORKING_ISSUES"
    FAILED_TO_PARSE_RESPONSE = "FAILED_TO_PARSE_RESPONSE"
    UNKNOWN_RMV_ISSUE = "UNKNOWN_RMV_ISSUE"


class RMVCheck(Base):
    __tablename__ = "rmv_check"
    rmv_check_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=utc_timestamp_gen)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
    )

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

    rmv_error_code = Column(StrEnum(RmvAcknowledgement), nullable=True)
    api_error_code = Column(StrEnum(RMVCheckApiErrorCode), nullable=True)

    absence_case_id = Column(Text, nullable=False, index=True)
    rmv_customer_key = Column(Text, nullable=True)


class StateMetric(Base):
    __tablename__ = "state_metric"
    state_metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    effective_date = Column(Date, unique=True, nullable=False)
    unemployment_minimum_earnings = Column(Numeric, nullable=False)
    average_weekly_wage = Column(Numeric, nullable=False)


def sync_state_metrics(db_session):
    state_metrics = [
        StateMetric(
            effective_date=datetime(2020, 10, 1),
            unemployment_minimum_earnings=Decimal(5100),
            average_weekly_wage=Decimal(1431.66),
        )
    ]

    for metric in state_metrics:
        existing = (
            db_session.query(StateMetric)
            .filter(StateMetric.effective_date == metric.effective_date)
            .one_or_none()
        )

        if existing is None:
            db_session.add(metric)

    db_session.commit()


class Notification(Base):
    __tablename__ = "notification"
    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    request_json = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    LeaveReason.sync_to_database(db_session)
    LeaveReasonQualifier.sync_to_database(db_session)
    LeaveType.sync_to_database(db_session)
    RelationshipToCareGiver.sync_to_database(db_session)
    RelationshipQualifier.sync_to_database(db_session)
    NotificationMethod.sync_to_database(db_session)
    FrequencyOrDuration.sync_to_database(db_session)
    EmploymentStatus.sync_to_database(db_session)
    DocumentType.sync_to_database(db_session)
    ContentType.sync_to_database(db_session)
    DayOfWeek.sync_to_database(db_session)
    WorkPatternType.sync_to_database(db_session)
    db_session.commit()
