from sqlalchemy import Column, Integer, Text

from ..lookup import LookupTable
from .base import Base


class LkAbsencePeriodType(Base):
    __tablename__ = "lk_absence_period_type"
    absence_period_type_id = Column(Integer, primary_key=True, autoincrement=True)
    absence_period_type_description = Column(Text, nullable=False)

    def __init__(self, absence_period_type_id, absence_period_type_description):
        self.absence_period_type_id = absence_period_type_id
        self.absence_period_type_description = absence_period_type_description


class LkAbsenceReason(Base):
    __tablename__ = "lk_absence_reason"
    absence_reason_id = Column(Integer, primary_key=True, autoincrement=True)
    absence_reason_description = Column(Text, nullable=False)

    def __init__(self, absence_reason_id, absence_reason_description):
        self.absence_reason_id = absence_reason_id
        self.absence_reason_description = absence_reason_description


class LkAbsenceReasonQualifierOne(Base):
    __tablename__ = "lk_absence_reason_qualifier_one"
    absence_reason_qualifier_one_id = Column(Integer, primary_key=True, autoincrement=True)
    absence_reason_qualifier_one_description = Column(Text, nullable=False)

    def __init__(self, absence_reason_qualifier_one_id, absence_reason_qualifier_one_description):
        self.absence_reason_qualifier_one_id = absence_reason_qualifier_one_id
        self.absence_reason_qualifier_one_description = absence_reason_qualifier_one_description


class LkAbsenceReasonQualifierTwo(Base):
    __tablename__ = "lk_absence_reason_qualifier_two"
    absence_reason_qualifier_two_id = Column(Integer, primary_key=True, autoincrement=True)
    absence_reason_qualifier_two_description = Column(Text, nullable=False)

    def __init__(self, absence_reason_qualifier_two_id, absence_reason_qualifier_two_description):
        self.absence_reason_qualifier_two_id = absence_reason_qualifier_two_id
        self.absence_reason_qualifier_two_description = absence_reason_qualifier_two_description


class LkAbsenceStatus(Base):
    __tablename__ = "lk_absence_status"
    absence_status_id = Column(Integer, primary_key=True, autoincrement=True)
    absence_status_description = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # use to set order when sorting (non alphabetic) by absence status

    def __init__(self, absence_status_id, absence_status_description, sort_order):
        self.absence_status_id = absence_status_id
        self.absence_status_description = absence_status_description
        self.sort_order = sort_order


class AbsenceStatus(LookupTable):
    model = LkAbsenceStatus
    column_names = ("absence_status_id", "absence_status_description", "sort_order")

    ADJUDICATION = LkAbsenceStatus(1, "Adjudication", 2)
    APPROVED = LkAbsenceStatus(2, "Approved", 5)
    CLOSED = LkAbsenceStatus(3, "Closed", 7)
    COMPLETED = LkAbsenceStatus(4, "Completed", 6)
    DECLINED = LkAbsenceStatus(5, "Declined", 4)
    IN_REVIEW = LkAbsenceStatus(6, "In Review", 3)
    INTAKE_IN_PROGRESS = LkAbsenceStatus(7, "Intake In Progress", 1)


class AbsencePeriodType(LookupTable):
    model = LkAbsencePeriodType
    column_names = ("absence_period_type_id", "absence_period_type_description")

    TIME_OFF_PERIOD = LkAbsencePeriodType(1, "Time off period")
    REDUCED_SCHEDULE = LkAbsencePeriodType(2, "Reduced Schedule")
    EPISODIC = LkAbsencePeriodType(3, "Episodic")
    OFFICE_VISIT = LkAbsencePeriodType(4, "Office Visit")
    INCAPACITY = LkAbsencePeriodType(5, "Incapacity")
    OFFICE_VISIT_EPISODIC = LkAbsencePeriodType(6, "Office Visit Episodic")
    INCAPACITY_EPISODIC = LkAbsencePeriodType(7, "Incapacity Episodic")
    BLACKOUT_PERIOD = LkAbsencePeriodType(8, "Blackout Period")
    UNSPECIFIED = LkAbsencePeriodType(9, "Unspecified")
    CONTINUOUS = LkAbsencePeriodType(10, "Continuous")
    INTERMITTENT = LkAbsencePeriodType(11, "Intermittent")


class AbsenceReason(LookupTable):
    model = LkAbsenceReason
    column_names = ("absence_reason_id", "absence_reason_description")

    SERIOUS_HEALTH_CONDITION_EMPLOYEE = LkAbsenceReason(1, "Serious Health Condition - Employee")
    MEDICAL_DONATION_EMPLOYEE = LkAbsenceReason(2, "Medical Donation - Employee")
    PREVENTATIVE_CARE_EMPLOYEE = LkAbsenceReason(3, "Preventative Care - Employee")
    SICKENESS_NON_SERIOUS_HEALTH_CONDITION_EMPLOYEE = LkAbsenceReason(
        4, "Sickness - Non-Serious Health Condition - Employee"
    )
    PREGNANCY_MATERNITY = LkAbsenceReason(5, "Pregnancy/Maternity")
    CHILD_BONDING = LkAbsenceReason(6, "Child Bonding")
    CARE_OF_A_FAMILY_MEMBER = LkAbsenceReason(7, "Care for a Family Member")
    BEREAVEMENT = LkAbsenceReason(8, "Bereavement")
    EDUCATIONAL_ACTIVITY_FAMILY = LkAbsenceReason(9, "Educational Activity - Family")
    MEDICAL_DONATION_FAMILY = LkAbsenceReason(10, "Medical Donation - Family")
    MILITARY_CAREGIVER = LkAbsenceReason(11, "Military Caregiver")
    MILITARY_EXIGENCY_FAMILY = LkAbsenceReason(12, "Military Exigency Family")
    PREVENTATIVE_CARE_FAMILY_MEMBER = LkAbsenceReason(13, "Preventative Care - Family Member")
    PUBLIC_HEALTH_EMERGENCY_FAMILY = LkAbsenceReason(14, "Public Health Emergency - Family")
    MILITARY_EMPLOYEE = LkAbsenceReason(15, "Military - Employee")
    PERSONAL_EMPLOYEE = LkAbsenceReason(16, "Personal - Employee")


class AbsenceReasonQualifierOne(LookupTable):
    model = LkAbsenceReasonQualifierOne
    column_names = ("absence_reason_qualifier_one_id", "absence_reason_qualifier_one_description")

    NOT_WORK_RELATED = LkAbsenceReasonQualifierOne(1, "Not Work Related")
    WORK_RELATED = LkAbsenceReasonQualifierOne(2, "Work Related")
    BLOOD = LkAbsenceReasonQualifierOne(3, "Blood")
    BLOOD_STEM_CELL = LkAbsenceReasonQualifierOne(4, "Blood Stem Cell")
    BONE_MARROW = LkAbsenceReasonQualifierOne(5, "Bone Marrow")
    ORGAN = LkAbsenceReasonQualifierOne(6, "Organ")
    OTHER = LkAbsenceReasonQualifierOne(7, "Other")
    POSTNATAL_DISABILITY = LkAbsenceReasonQualifierOne(8, "Postnatal Disability")
    PRENATAL_CARE = LkAbsenceReasonQualifierOne(9, "Prenatal Care")
    PRENATAL_DISABILITY = LkAbsenceReasonQualifierOne(10, "Prenatal Disability")
    ADOPTION = LkAbsenceReasonQualifierOne(11, "Adoption")
    FOSTER_CARE = LkAbsenceReasonQualifierOne(12, "Foster Care")
    NEWBORN = LkAbsenceReasonQualifierOne(13, "Newborn")
    PREGNANCY_RELATED = LkAbsenceReasonQualifierOne(14, "Pregnancy Related")
    RIGHT_TO_LEAVE = LkAbsenceReasonQualifierOne(15, "Right to Leave")
    SERIOUS_HEALTH_CONDITION = LkAbsenceReasonQualifierOne(16, "Serious Health Condition")
    SICKNESS_NON_SERIOUS_HEALTH_CONDITION = LkAbsenceReasonQualifierOne(
        17, "Sickness - Non-Serious Health Condition"
    )
    CHILDCARE = LkAbsenceReasonQualifierOne(18, "Childcare")
    COUNSELING = LkAbsenceReasonQualifierOne(19, "Counseling")
    FINANCIAL_AND_LEGAL_ARRANGEMENTS = LkAbsenceReasonQualifierOne(
        20, "Financial & Legal Arrangements"
    )
    MILITARY_EVENTS_AND_RELATED_ACTIVITIES = LkAbsenceReasonQualifierOne(
        21, "Military Events & Related Activities"
    )
    OTHER_ADDITIONAL_ACTIVITIES = LkAbsenceReasonQualifierOne(22, "Other Additional Activities")
    PRENATAL_CARE = LkAbsenceReasonQualifierOne(23, "Prenatal Care")
    POST_DEPLOYMENT_ACTIVITES_INCLUDING_BEREAVEMENT = LkAbsenceReasonQualifierOne(
        24, "Post Deployment Activities - Including Bereavement"
    )
    REST_AND_RECUPERATION = LkAbsenceReasonQualifierOne(25, "Rest & Recuperation")
    SHORT_NOTICE_DEPLOYMENT = LkAbsenceReasonQualifierOne(26, "Short Notice Deployment")
    CLOSURE_OF_SCHOOL_CHILDCARE = LkAbsenceReasonQualifierOne(27, "Closure of School/Childcare")
    QUARANTINE_ISOLATION_NON_SICK = LkAbsenceReasonQualifierOne(
        28, "Quarantine/Isolation - Not Sick"
    )
    BIRTH_DISABILITY = LkAbsenceReasonQualifierOne(29, "Birth Disability")
    CHILDCARE_AND_SCHOOL_ACTIVITIES = LkAbsenceReasonQualifierOne(
        30, "Childcare and School Activities"
    )


class AbsenceReasonQualifierTwo(LookupTable):
    model = LkAbsenceReasonQualifierTwo
    column_names = ("absence_reason_qualifier_two_id", "absence_reason_qualifier_two_description")

    ACCIDENT_INJURY = LkAbsenceReasonQualifierTwo(1, "Accident / Injury")
    MEDICAL_RELATED = LkAbsenceReasonQualifierTwo(2, "Medical Related")
    NON_MEDICAL = LkAbsenceReasonQualifierTwo(3, "Non Medical")
    SICKNESS = LkAbsenceReasonQualifierTwo(4, "Sickness")


def sync_lookup_tables(db_session):
    AbsencePeriodType.sync_to_database(db_session)
    AbsenceReason.sync_to_database(db_session)
    AbsenceReasonQualifierOne.sync_to_database(db_session)
    AbsenceReasonQualifierTwo.sync_to_database(db_session)
    AbsenceStatus.sync_to_database(db_session)
