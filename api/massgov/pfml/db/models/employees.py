# ORM and serialization models for our employee data and API layers.
#
# A model's ORM representation should always match the database so we can
# properly read and write data. If you make a change, follow the instructions
# in the API README to generate an associated table migration.
#
# Generally, a model factory should be provided in the associated factories.py file.
# This allows us to build mock data and insert them easily in the database for tests
# and seeding.
#
from typing import TYPE_CHECKING, Optional, cast

from sqlalchemy import TIMESTAMP, Boolean, Column, Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Query, dynamic_loader, relationship
from sqlalchemy.sql.expression import func

from ..lookup import LookupTable
from .base import Base, utc_timestamp_gen, uuid_gen

# https://github.com/dropbox/sqlalchemy-stubs/issues/98
if TYPE_CHECKING:
    # Use this to make hybrid_property's have the same typing as a normal property until stubs are improved.
    typed_hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property as typed_hybrid_property


class LkAddressType(Base):
    __tablename__ = "lk_address_type"
    address_type_id = Column(Integer, primary_key=True, autoincrement=True)
    address_description = Column(Text)

    def __init__(self, address_type_id, address_description):
        self.address_type_id = address_type_id
        self.address_description = address_description


class LkGeoState(Base):
    __tablename__ = "lk_geo_state"
    geo_state_id = Column(Integer, primary_key=True, autoincrement=True)
    geo_state_description = Column(Text)

    def __init__(self, geo_state_id, geo_state_description):
        self.geo_state_id = geo_state_id
        self.geo_state_description = geo_state_description


class LkCountry(Base):
    __tablename__ = "lk_country"
    country_id = Column(Integer, primary_key=True, autoincrement=True)
    country_description = Column(Text)

    def __init__(self, country_id, country_description):
        self.country_id = country_id
        self.country_description = country_description


class LkClaimType(Base):
    __tablename__ = "lk_claim_type"
    claim_type_id = Column(Integer, primary_key=True, autoincrement=True)
    claim_type_description = Column(Text)

    def __init__(self, claim_type_id, claim_type_description):
        self.claim_type_id = claim_type_id
        self.claim_type_description = claim_type_description


class LkRace(Base):
    __tablename__ = "lk_race"
    race_id = Column(Integer, primary_key=True)
    race_description = Column(Text)

    def __init__(self, race_id, race_description):
        self.race_id = race_id
        self.race_description = race_description


class LkMaritalStatus(Base):
    __tablename__ = "lk_marital_status"
    marital_status_id = Column(Integer, primary_key=True, autoincrement=True)
    marital_status_description = Column(Text)

    def __init__(self, marital_status_id, marital_status_description):
        self.marital_status_id = marital_status_id
        self.marital_status_description = marital_status_description


class LkGender(Base):
    __tablename__ = "lk_gender"
    gender_id = Column(Integer, primary_key=True, autoincrement=True)
    gender_description = Column(Text)

    def __init__(self, gender_id, gender_description):
        self.gender_id = gender_id
        self.gender_description = gender_description


class LkOccupation(Base):
    __tablename__ = "lk_occupation"
    occupation_id = Column(Integer, primary_key=True)
    occupation_description = Column(Text)

    def __init__(self, occupation_id, occupation_description):
        self.occupation_id = occupation_id
        self.occupation_description = occupation_description


class LkEducationLevel(Base):
    __tablename__ = "lk_education_level"
    education_level_id = Column(Integer, primary_key=True, autoincrement=True)
    education_level_description = Column(Text)

    def __init__(self, education_level_id, education_level_description):
        self.education_level_id = education_level_id
        self.education_level_description = education_level_description


class LkRole(Base):
    __tablename__ = "lk_role"
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_description = Column(Text)

    def __init__(self, role_id, role_description):
        self.role_id = role_id
        self.role_description = role_description


class LkPaymentType(Base):
    __tablename__ = "lk_payment_type"
    payment_type_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_type_description = Column(Text)

    def __init__(self, payment_type_id, payment_type_description):
        self.payment_type_id = payment_type_id
        self.payment_type_description = payment_type_description


class AuthorizedRepresentative(Base):
    __tablename__ = "authorized_representative"
    authorized_representative_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    first_name = Column(Text)
    last_name = Column(Text)

    employees = relationship("AuthorizedRepEmployee", back_populates="authorized_rep")


class HealthCareProvider(Base):
    __tablename__ = "health_care_provider"
    health_care_provider_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    provider_name = Column(Text)

    addresses = relationship("HealthCareProviderAddress", back_populates="health_care_provider")


class Employer(Base):
    __tablename__ = "employer"
    employer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    account_key = Column(Text)
    employer_fein = Column(Text, nullable=False)
    employer_name = Column(Text)
    employer_dba = Column(Text, nullable=False)
    family_exemption = Column(Boolean)
    medical_exemption = Column(Boolean)
    exemption_commence_date = Column(Date)
    exemption_cease_date = Column(Date)
    dor_updated_date = Column(TIMESTAMP(timezone=True))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"))
    fineos_customer_nbr = Column(Text)
    fineos_employer_id = Column(Integer)

    wages_and_contributions: "Query[WagesAndContributions]" = dynamic_loader(
        "WagesAndContributions", back_populates="employer"
    )
    addresses: "Query[EmployerAddress]" = dynamic_loader(
        "EmployerAddress", back_populates="employer"
    )


class EmployerLog(Base):
    __tablename__ = "employer_log"
    employer_log_id = Column(UUID(as_uuid=True), primary_key=True)
    employer_id = Column(UUID(as_uuid=True), index=True)
    action = Column(Text, index=True)
    modified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)


class PaymentInformation(Base):
    __tablename__ = "payment_information"
    payment_info_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    payment_type_id = Column(Integer, ForeignKey("lk_payment_type.payment_type_id"))
    bank_routing_nbr = Column(Integer)
    bank_account_nbr = Column(Integer)
    gift_card_nbr = Column(Integer)


class TaxIdentifier(Base):
    __tablename__ = "tax_identifier"
    tax_identifier_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    tax_identifier = Column(Text, nullable=False, unique=True)

    employee = relationship("Employee", back_populates="tax_identifier")

    @typed_hybrid_property
    def tax_identifier_last4(self) -> str:
        return self.tax_identifier[-4:]

    @tax_identifier_last4.expression
    def tax_identifier_last4(self):
        return func.right(TaxIdentifier.tax_identifier, 4)


class Employee(Base):
    __tablename__ = "employee"
    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    tax_identifier_id = Column(UUID(as_uuid=True), ForeignKey("tax_identifier.tax_identifier_id"))
    first_name = Column(Text, nullable=False)
    middle_name = Column(Text)
    last_name = Column(Text, nullable=False)
    other_name = Column(Text)
    email_address = Column(Text)
    phone_number = Column(Text)
    preferred_comm_method_type = Column(Text)
    payment_info_id = Column(UUID(as_uuid=True), ForeignKey("payment_information.payment_info_id"))
    date_of_birth = Column(Date)
    race_id = Column(Integer, ForeignKey("lk_race.race_id"))
    marital_status_id = Column(Integer, ForeignKey("lk_marital_status.marital_status_id"))
    gender_id = Column(Integer, ForeignKey("lk_gender.gender_id"))
    occupation_id = Column(Integer, ForeignKey("lk_occupation.occupation_id"))
    education_level_id = Column(Integer, ForeignKey("lk_education_level.education_level_id"))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"))

    payment_info = relationship(PaymentInformation)
    race = relationship(LkRace)
    marital_status = relationship(LkMaritalStatus)
    gender = relationship(LkGender)
    occupation = relationship(LkOccupation)
    education_level = relationship(LkEducationLevel)
    latest_import_log = relationship("ImportLog")
    tax_identifier = cast(
        Optional[TaxIdentifier], relationship("TaxIdentifier", back_populates="employee")
    )

    authorized_reps: "Query[AuthorizedRepEmployee]" = dynamic_loader(
        "AuthorizedRepEmployee", back_populates="employee"
    )
    wages_and_contributions: "Query[WagesAndContributions]" = dynamic_loader(
        "WagesAndContributions", back_populates="employee"
    )
    addresses: "Query[EmployeeAddress]" = dynamic_loader(
        "EmployeeAddress", back_populates="employee"
    )


class EmployeeLog(Base):
    __tablename__ = "employee_log"
    employee_log_id = Column(UUID(as_uuid=True), primary_key=True)
    employee_id = Column(UUID(as_uuid=True), index=True)
    action = Column(Text, index=True)
    modified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)


class Claim(Base):
    __tablename__ = "claim"
    claim_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    employer_id = Column(UUID(as_uuid=True))
    authorized_representative_id = Column(UUID(as_uuid=True))
    claim_type_id = Column(UUID(as_uuid=True))
    benefit_amount = Column(Numeric(asdecimal=True))
    benefit_days = Column(Integer)


class AuthorizedRepEmployee(Base):
    __tablename__ = "link_authorized_rep_employee"
    authorized_representative_id = Column(
        UUID(as_uuid=True),
        ForeignKey("authorized_representative.authorized_representative_id"),
        primary_key=True,
    )
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), primary_key=True)

    authorized_rep = relationship("AuthorizedRepresentative", back_populates="employees")
    employee = relationship("Employee", back_populates="authorized_reps")


class Address(Base):
    __tablename__ = "address"
    address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    address_type_id = Column(Integer, ForeignKey("lk_address_type.address_type_id"))
    address_line_one = Column(Text)
    address_line_two = Column(Text)
    city = Column(Text)
    geo_state_id = Column(Integer, ForeignKey("lk_geo_state.geo_state_id"))
    zip_code = Column(Text)
    country_id = Column(Integer, ForeignKey("lk_country.country_id"))

    address_type = relationship(LkAddressType)
    geo_state = relationship(LkGeoState)
    country = relationship(LkCountry)
    employees: "Query[EmployeeAddress]" = dynamic_loader(
        "EmployeeAddress", back_populates="address"
    )
    employers: "Query[EmployerAddress]" = dynamic_loader(
        "EmployerAddress", back_populates="address"
    )
    health_care_providers: "Query[HealthCareProviderAddress]" = dynamic_loader(
        "HealthCareProviderAddress", back_populates="address"
    )


class EmployeeAddress(Base):
    __tablename__ = "link_employee_address"
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), primary_key=True)
    address_id = Column(UUID(as_uuid=True), ForeignKey("address.address_id"), primary_key=True)

    employee = relationship("Employee", back_populates="addresses")
    address = relationship("Address", back_populates="employees")


class EmployerAddress(Base):
    __tablename__ = "link_employer_address"
    employer_id = Column(
        UUID(as_uuid=True), ForeignKey("employer.employer_id"), primary_key=True, unique=True
    )
    address_id = Column(
        UUID(as_uuid=True), ForeignKey("address.address_id"), primary_key=True, unique=True
    )

    employer = relationship("Employer", back_populates="addresses")
    address = relationship("Address", back_populates="employers")


class HealthCareProviderAddress(Base):
    __tablename__ = "link_health_care_provider_address"
    health_care_provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("health_care_provider.health_care_provider_id"),
        primary_key=True,
    )
    address_id = Column(UUID(as_uuid=True), ForeignKey("address.address_id"), primary_key=True)

    health_care_provider = relationship("HealthCareProvider", back_populates="addresses")
    address = relationship("Address", back_populates="health_care_providers")


class User(Base):
    __tablename__ = "user"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    active_directory_id = Column(Text)
    email_address = Column(Text)
    consented_to_data_sharing = Column(Boolean, default=False, nullable=False)

    roles = relationship("UserRole", back_populates="user", uselist=True)


class UserRole(Base):
    __tablename__ = "link_user_role"
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("lk_role.role_id"), primary_key=True)

    user = relationship(User)
    role = relationship(LkRole)


class UserLeaveAdministrator(Base):
    __tablename__ = "link_user_leave_administrator"
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), primary_key=True)

    user = relationship(User)
    employer = relationship(Employer)


class WagesAndContributions(Base):
    __tablename__ = "wages_and_contributions"
    wage_and_contribution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    account_key = Column(Text, nullable=False)
    filing_period = Column(Date, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), nullable=False)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=False)
    is_independent_contractor = Column(Boolean, nullable=False)
    is_opted_in = Column(Boolean, nullable=False)
    employee_ytd_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_qtr_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employee_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"))

    employee = relationship("Employee", back_populates="wages_and_contributions")
    employer = relationship("Employer", back_populates="wages_and_contributions")


class ImportLog(Base):
    __tablename__ = "import_log"
    import_log_id = Column(Integer, primary_key=True)
    source = Column(Text)
    import_type = Column(Text)
    status = Column(Text)
    report = Column(Text)
    start = Column(TIMESTAMP(timezone=True))
    end = Column(TIMESTAMP(timezone=True))


class AddressType(LookupTable):
    model = LkAddressType
    column_names = ("address_type_id", "address_description")

    HOME = LkAddressType(1, "Home")
    BUSINESS = LkAddressType(2, "Business")
    MAILING = LkAddressType(3, "Mailing")
    RESIDENTIAL = LkAddressType(4, "Residential")


class GeoState(LookupTable):
    model = LkGeoState
    column_names = ("geo_state_id", "geo_state_description")

    MA = LkGeoState(1, "MA")
    AL = LkGeoState(2, "AL")
    AS = LkGeoState(3, "AS")
    AZ = LkGeoState(4, "AZ")
    AR = LkGeoState(5, "AR")
    CA = LkGeoState(6, "CA")
    CO = LkGeoState(7, "CO")
    CT = LkGeoState(8, "CT")
    DE = LkGeoState(9, "DE")
    DC = LkGeoState(10, "DC")
    FM = LkGeoState(11, "FM")
    FL = LkGeoState(12, "FL")
    GA = LkGeoState(13, "GA")
    GU = LkGeoState(14, "GU")
    HI = LkGeoState(15, "HI")
    ID = LkGeoState(16, "ID")
    IL = LkGeoState(17, "IL")
    IN = LkGeoState(18, "IN")
    IA = LkGeoState(19, "IA")
    KS = LkGeoState(20, "KS")
    KY = LkGeoState(21, "KY")
    LA = LkGeoState(22, "LA")
    ME = LkGeoState(23, "ME")
    MH = LkGeoState(24, "MH")
    MD = LkGeoState(25, "MD")
    MI = LkGeoState(26, "MI")
    MN = LkGeoState(27, "MN")
    MS = LkGeoState(28, "MS")
    MO = LkGeoState(29, "MO")
    MT = LkGeoState(30, "MT")
    NE = LkGeoState(31, "NE")
    NV = LkGeoState(32, "NV")
    NH = LkGeoState(33, "NH")
    NJ = LkGeoState(34, "NJ")
    NM = LkGeoState(35, "NM")
    NY = LkGeoState(36, "NY")
    NC = LkGeoState(37, "NC")
    ND = LkGeoState(38, "ND")
    MP = LkGeoState(39, "MP")
    OH = LkGeoState(40, "OH")
    OK = LkGeoState(41, "OK")
    OR = LkGeoState(42, "OR")
    PW = LkGeoState(43, "PW")
    PA = LkGeoState(44, "PA")
    PR = LkGeoState(45, "PR")
    RI = LkGeoState(46, "RI")
    SC = LkGeoState(47, "SC")
    SD = LkGeoState(48, "SD")
    TN = LkGeoState(49, "TN")
    TX = LkGeoState(50, "TX")
    UT = LkGeoState(51, "UT")
    VT = LkGeoState(52, "VT")
    VA = LkGeoState(53, "VA")
    VI = LkGeoState(54, "VI")
    WA = LkGeoState(55, "WA")
    WV = LkGeoState(56, "WV")
    WI = LkGeoState(57, "WI")
    WY = LkGeoState(58, "WY")
    AK = LkGeoState(59, "AK")


class Country(LookupTable):
    model = LkCountry
    column_names = ("country_id", "country_description")

    US = LkCountry(1, "US")


class ClaimType(LookupTable):
    model = LkClaimType
    column_names = ("claim_type_id", "claim_type_description")

    FAMILY_LEAVE = LkClaimType(1, "Family Leave")


class Race(LookupTable):
    model = LkRace
    column_names = ("race_id", "race_description")

    BLACK = LkRace(1, "Black")
    HISPANIC = LkRace(2, "Hispanic")
    WHITE = LkRace(3, "White")


class MaritalStatus(LookupTable):
    model = LkMaritalStatus
    column_names = ("marital_status_id", "marital_status_description")

    SINGLE = LkMaritalStatus(1, "Single")
    MARRIED = LkMaritalStatus(2, "Married")
    DIVORCED = LkMaritalStatus(3, "Divorced")
    WIDOWED = LkMaritalStatus(4, "Widowed")


class Gender(LookupTable):
    model = LkGender
    column_names = ("gender_id", "gender_description")

    FEMALE = LkGender(1, "Female")
    MALE = LkGender(2, "Male")
    OTHER = LkGender(3, "Other")


class Occupation(LookupTable):
    model = LkOccupation
    column_names = ("occupation_id", "occupation_description")

    HEALTH_CARE = LkOccupation(1, "Health Care")
    SALES_CLERK = LkOccupation(2, "Sales Clerk")
    ADMINISTRATIVE = LkOccupation(3, "Administrative")
    ENGINEER = LkOccupation(4, "Engineer")


class EducationLevel(LookupTable):
    model = LkEducationLevel
    column_names = ("education_level_id", "education_level_description")


class Role(LookupTable):
    model = LkRole
    column_names = ("role_id", "role_description")

    USER = LkRole(1, "User")
    FINEOS = LkRole(2, "Fineos")
    EMPLOYER = LkRole(3, "Employer")


class PaymentType(LookupTable):
    model = LkPaymentType
    column_names = ("payment_type_id", "payment_type_description")

    ACH = LkPaymentType(1, "ACH")
    CHECK = LkPaymentType(2, "Check")
    DEBIT = LkPaymentType(3, "Debit")


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    AddressType.sync_to_database(db_session)
    GeoState.sync_to_database(db_session)
    Country.sync_to_database(db_session)
    ClaimType.sync_to_database(db_session)
    Race.sync_to_database(db_session)
    MaritalStatus.sync_to_database(db_session)
    Gender.sync_to_database(db_session)
    Occupation.sync_to_database(db_session)
    Role.sync_to_database(db_session)
    PaymentType.sync_to_database(db_session)
    db_session.commit()
