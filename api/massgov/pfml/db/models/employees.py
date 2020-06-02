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
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, uuid_gen


class AddressType(Base):
    __tablename__ = "lk_address_type"
    address_type = Column(Integer, primary_key=True, autoincrement=True)
    address_description = Column(Text)


class GeoState(Base):
    __tablename__ = "lk_geo_state"
    state_type = Column(Integer, primary_key=True, autoincrement=True)
    state_description = Column(Text)


class Country(Base):
    __tablename__ = "lk_country"
    country_type = Column(Integer, primary_key=True, autoincrement=True)
    country_description = Column(Text)


class ClaimType(Base):
    __tablename__ = "lk_claim_type"
    claim_type = Column(Integer, primary_key=True, autoincrement=True)
    claim_type_description = Column(Text)


class Race(Base):
    __tablename__ = "lk_race"
    race_type = Column(Integer, primary_key=True)
    race_description = Column(Text)


class MaritalStatus(Base):
    __tablename__ = "lk_marital_status"
    marital_status_type = Column(Integer, primary_key=True, autoincrement=True)
    marital_status_description = Column(Text)


class Gender(Base):
    __tablename__ = "lk_gender"
    gender_type = Column(Integer, primary_key=True, autoincrement=True)
    gender_description = Column(Text)


class Occupation(Base):
    __tablename__ = "lk_occupation"
    occupation_type = Column(Integer, primary_key=True)
    occupation_description = Column(Text)


class EducationLevel(Base):
    __tablename__ = "lk_education_level"
    education_level_type = Column(Integer, primary_key=True, autoincrement=True)
    education_level_description = Column(Text)


class Role(Base):
    __tablename__ = "lk_role"
    role_type = Column(Integer, primary_key=True, autoincrement=True)
    role_description = Column(Text)


class PaymentType(Base):
    __tablename__ = "lk_payment_type"
    payment_type = Column(Integer, primary_key=True, autoincrement=True)
    payment_type_description = Column(Text)


class Status(Base):
    __tablename__ = "lk_status"
    status_type = Column(Integer, primary_key=True, autoincrement=True)
    status_description = Column(Text)


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
    dor_updated_date = Column(DateTime)
    wages_and_contributions = relationship(
        "WagesAndContributions", back_populates="employer", lazy="dynamic"
    )
    addresses = relationship("EmployerAddress", back_populates="employers", lazy="dynamic")


class PaymentInformation(Base):
    __tablename__ = "payment_information"
    payment_info_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    payment_type = Column(Integer, ForeignKey("lk_payment_type.payment_type"))
    bank_routing_nbr = Column(Integer)
    bank_account_nbr = Column(Integer)
    gift_card_nbr = Column(Integer)


class Employee(Base):
    __tablename__ = "employee"
    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    tax_identifier = Column(Text)
    first_name = Column(Text, nullable=False)
    middle_name = Column(Text)
    last_name = Column(Text, nullable=False)
    other_name = Column(Text)
    email_address = Column(Text)
    phone_number = Column(Text)
    preferred_comm_method_type = Column(Text)
    payment_info_id = Column(UUID(as_uuid=True), ForeignKey("payment_information.payment_info_id"))
    date_of_birth = Column(Date)
    race_type = Column(Integer, ForeignKey("lk_race.race_type"))
    marital_status_type = Column(Integer, ForeignKey("lk_marital_status.marital_status_type"))
    gender_type = Column(Integer, ForeignKey("lk_gender.gender_type"))
    occupation_type = Column(Integer, ForeignKey("lk_occupation.occupation_type"))
    education_level_type = Column(Integer, ForeignKey("lk_education_level.education_level_type"))
    authorized_reps = relationship(
        "AuthorizedRepEmployee", back_populates="employee", lazy="dynamic"
    )
    wages_and_contributions = relationship(
        "WagesAndContributions", back_populates="employee", lazy="dynamic"
    )
    addresses = relationship("EmployeeAddress", back_populates="employees", lazy="dynamic")


class Claim(Base):
    __tablename__ = "claim"
    claim_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    employer_id = Column(UUID(as_uuid=True))
    authorized_representative_id = Column(UUID(as_uuid=True))
    claim_type = Column(UUID(as_uuid=True))
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
    address_type = Column(Integer, ForeignKey("lk_address_type.address_type"))
    address_line_one = Column(Text)
    address_line_two = Column(Text)
    city = Column(Text)
    state_type = Column(Integer, ForeignKey("lk_geo_state.state_type"))
    zip_code = Column(Text)
    country_type = Column(Integer, ForeignKey("lk_country.country_type"))
    employees = relationship("EmployeeAddress", back_populates="addresses", lazy="dynamic")
    employers = relationship("EmployerAddress", back_populates="addresses", lazy="dynamic")
    health_care_providers = relationship("HealthCareProviderAddress", back_populates="address")


class EmployeeAddress(Base):
    __tablename__ = "link_employee_address"
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), primary_key=True)
    address_id = Column(UUID(as_uuid=True), ForeignKey("address.address_id"), primary_key=True)
    employees = relationship("Employee", back_populates="addresses")
    addresses = relationship("Address", back_populates="employees")


class EmployerAddress(Base):
    __tablename__ = "link_employer_address"
    employer_id = Column(
        UUID(as_uuid=True), ForeignKey("employer.employer_id"), primary_key=True, unique=True
    )
    address_id = Column(
        UUID(as_uuid=True), ForeignKey("address.address_id"), primary_key=True, unique=True
    )
    employers = relationship("Employer", back_populates="addresses")
    addresses = relationship("Address", back_populates="employers")


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
    status_type = Column(Integer, ForeignKey("lk_status.status_type"))
    status = relationship("Status", backref="users")
    consented_to_data_sharing = Column(Boolean, default=False, nullable=False)


class UserRole(Base):
    __tablename__ = "link_user_role"
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True)
    role_type = Column(Integer, ForeignKey("lk_role.role_type"), primary_key=True)
    related_role_id = Column(UUID(as_uuid=True))


class WagesAndContributions(Base):
    __tablename__ = "wages_and_contributions"
    wage_and_contribution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    account_key = Column(Text, nullable=False)
    filing_period = Column(Date, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), nullable=False)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=False)
    employee = relationship("Employee", back_populates="wages_and_contributions")
    employer = relationship("Employer", back_populates="wages_and_contributions")
    is_independent_contractor = Column(Boolean, nullable=False)
    is_opted_in = Column(Boolean, nullable=False)
    employee_ytd_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_qtr_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employee_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)


class ImportLog(Base):
    __tablename__ = "import_log"
    import_log_id = Column(Integer, primary_key=True)
    source = Column(Text)
    import_type = Column(Text)
    status = Column(Text)
    report = Column(Text)
    start = Column(DateTime)
    end = Column(DateTime)
