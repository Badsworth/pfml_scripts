from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Text
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

from ..lookup import LookupTable
from .base import Base, uuid_gen


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


class Application(Base):
    __tablename__ = "application"
    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"))
    tax_identifier_id = Column(UUID(as_uuid=True), ForeignKey("tax_identifier.tax_identifier_id"))
    nickname = Column(Text)
    requestor = Column(Integer)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"))
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"))
    mailing_address_id = Column(UUID(as_uuid=True), ForeignKey("address.address_id"), nullable=True)
    employer_fein = Column(Text)
    first_name = Column(Text)
    last_name = Column(Text)
    middle_name = Column(Text, nullable=True)
    date_of_birth = Column(Date)
    has_state_id = Column(Boolean)
    mass_id = Column(Text)
    occupation_id = Column(Integer, ForeignKey("lk_occupation.occupation_id"))
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
    start_time = Column(DateTime)
    updated_time = Column(DateTime)
    completed_time = Column(DateTime)
    submitted_time = Column(DateTime)
    fineos_absence_id = Column(Text)
    fineos_notification_case_id = Column(Text)

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
    mailing_address = relationship(Address)

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
    payment_type = relationship(LkPaymentType)


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


class LeaveReasonQualifier(LookupTable):
    model = LkLeaveReasonQualifier
    column_names = ("leave_reason_qualifier_id", "leave_reason_qualifier_description")

    NEWBORN = LkLeaveReasonQualifier(1, "Newborn")
    SERIOUS_HEALTH_CONDITION = LkLeaveReasonQualifier(2, "Serious Health Condition")
    WORK_RELATED_ACCIDENT_INJURY = LkLeaveReasonQualifier(3, "Work Related Accident/Injury")
    ADOPTION = LkLeaveReasonQualifier(4, "Adoption")
    FOSTER_CARE = LkLeaveReasonQualifier(5, "Foster Care")


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


class LkDocumentCategory(Base):
    __tablename__ = "lk_document_category"
    document_category_id = Column(Integer, primary_key=True, autoincrement=True)
    document_category_description = Column(Text, nullable=False)

    def __init__(self, document_category_id, document_category_description):
        self.document_category_id = document_category_id
        self.document_category_description = document_category_description


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


class DocumentCategory(LookupTable):
    model = LkDocumentCategory
    column_names = ("document_category_id", "document_category_description")

    IDENTITY_PROOFING = LkDocumentCategory(1, "Identity Proofing")
    CERTIFICATION = LkDocumentCategory(2, "Certification")


class DocumentType(LookupTable):
    model = LkDocumentType
    column_names = ("document_type_id", "document_type_description")

    PASSPORT = LkDocumentType(1, "Passport")
    DRIVERS_LICENSE_MASS = LkDocumentType(2, "Driver's License Mass")
    DRIVERS_LICENSE_OTHER_STATE = LkDocumentType(3, "Driver's License Other State")


class ContentType(LookupTable):
    model = LkContentType
    column_names = ("content_type_id", "content_type_description")

    PDF = LkContentType(1, "application/pdf")
    JPEG = LkContentType(2, "image/jpeg")
    PNG = LkContentType(3, "image/png")
    WEBP = LkContentType(4, "image/webp")
    HEIC = LkContentType(5, "image/heic")


class Document(Base):
    __tablename__ = "document"
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    document_category_id = Column(
        Integer, ForeignKey("lk_document_category.document_category_id"), nullable=False
    )
    document_type_id = Column(
        Integer, ForeignKey("lk_document_type.document_type_id"), nullable=False
    )
    content_type_id = Column(Integer, ForeignKey("lk_content_type.content_type_id"), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    fineos_id = Column(Text, nullable=True)
    is_stored_in_s3 = Column(Boolean, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)


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
    DocumentCategory.sync_to_database(db_session)
    DocumentType.sync_to_database(db_session)
    ContentType.sync_to_database(db_session)
    db_session.commit()
