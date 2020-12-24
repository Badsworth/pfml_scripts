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

from sqlalchemy import TIMESTAMP, Boolean, Column, Date, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Query, dynamic_loader, relationship
from sqlalchemy.sql.expression import func
from sqlalchemy.types import JSON

from ..lookup import LookupTable
from .base import Base, utc_timestamp_gen, uuid_gen

# https://github.com/dropbox/sqlalchemy-stubs/issues/98
if TYPE_CHECKING:
    # Use this to make hybrid_property's have the same typing as a normal property until stubs are improved.
    typed_hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property as typed_hybrid_property


class LkAbsenceStatus(Base):
    __tablename__ = "lk_absence_status"
    absence_status_id = Column(Integer, primary_key=True, autoincrement=True)
    absence_status_description = Column(Text)

    def __init__(self, absence_status_id, absence_status_description):
        self.absence_status_id = absence_status_id
        self.absence_status_description = absence_status_description


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


class LkPaymentMethod(Base):
    __tablename__ = "lk_payment_method"
    payment_method_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_method_description = Column(Text)

    def __init__(self, payment_method_id, payment_method_description):
        self.payment_method_id = payment_method_id
        self.payment_method_description = payment_method_description


class LkBankAccountType(Base):
    __tablename__ = "lk_bank_account_type"
    bank_account_type_id = Column(Integer, primary_key=True, autoincrement=True)
    bank_account_type_description = Column(Text)

    def __init__(self, bank_account_type_id, bank_account_type_description):
        self.bank_account_type_id = bank_account_type_id
        self.bank_account_type_description = bank_account_type_description


class LkFlow(Base):
    __tablename__ = "lk_flow"
    flow_id = Column(Integer, primary_key=True, autoincrement=True)
    flow_description = Column(Text)

    def __init__(self, flow_id, flow_description):
        self.flow_id = flow_id
        self.flow_description = flow_description


class LkState(Base):
    __tablename__ = "lk_state"
    state_id = Column(Integer, primary_key=True, autoincrement=True)
    state_description = Column(Text)
    flow_id = Column(Integer, ForeignKey("lk_flow.flow_id"))

    def __init__(self, state_id, state_description, flow_id):
        self.state_id = state_id
        self.state_description = state_description
        self.flow_id = flow_id


class LkReferenceFileType(Base):
    __tablename__ = "lk_reference_file_type"
    reference_file_type_id = Column(Integer, primary_key=True, autoincrement=True)
    reference_file_type_description = Column(Text)
    num_files_in_set = Column(Integer)

    def __init__(self, reference_file_type_id, reference_file_type_description, num_files_in_set):
        self.reference_file_type_id = reference_file_type_id
        self.reference_file_type_description = reference_file_type_description
        self.num_files_in_set = num_files_in_set


class LkTitle(Base):
    __tablename__ = "lk_title"
    title_id = Column(Integer, primary_key=True, autoincrement=True)
    title_description = Column(Text)

    def __init__(self, title_id, title_description):
        self.title_id = title_id
        self.title_description = title_description


class LkAgency(Base):
    __tablename__ = "lk_agency"
    agency_id = Column(Integer, primary_key=True, autoincrement=True)
    agency_description = Column(Text)

    def __init__(self, agency_id, agency_description):
        self.agency_id = agency_id
        self.agency_description = agency_description


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
    account_key = Column(Text, index=True)
    employer_fein = Column(Text, nullable=False, index=True)
    employer_name = Column(Text)
    employer_dba = Column(Text, nullable=False)
    family_exemption = Column(Boolean)
    medical_exemption = Column(Boolean)
    exemption_commence_date = Column(Date)
    exemption_cease_date = Column(Date)
    dor_updated_date = Column(TIMESTAMP(timezone=True))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)
    fineos_employer_id = Column(Integer, index=True)

    wages_and_contributions: "Query[WagesAndContributions]" = dynamic_loader(
        "WagesAndContributions", back_populates="employer"
    )
    addresses: "Query[EmployerAddress]" = dynamic_loader(
        "EmployerAddress", back_populates="employer"
    )
    employer_occupations: "Query[EmployeeOccupation]" = dynamic_loader(
        "EmployeeOccupation", back_populates="employer"
    )


class EmployerQuarterlyContribution(Base):
    __tablename__ = "employer_quarterly_contribution"
    employer_id = Column(
        UUID(as_uuid=True), ForeignKey("employer.employer_id"), index=True, primary_key=True
    )
    filing_period = Column(Date, primary_key=True)
    employer_total_pfml_contribution = Column(Numeric(asdecimal=True), nullable=False)
    pfm_account_id = Column(Text, nullable=False, index=True)
    dor_received_date = Column(TIMESTAMP(timezone=True))
    dor_updated_date = Column(TIMESTAMP(timezone=True))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)


class EmployerLog(Base):
    __tablename__ = "employer_log"
    employer_log_id = Column(UUID(as_uuid=True), primary_key=True)
    employer_id = Column(UUID(as_uuid=True), index=True)
    action = Column(Text, index=True)
    modified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)
    process_id = Column(Integer, index=True)


class EFT(Base):
    __tablename__ = "eft"
    eft_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    routing_nbr = Column(Integer, nullable=False)
    account_nbr = Column(Integer, nullable=False)
    bank_account_type_id = Column(
        Integer, ForeignKey("lk_bank_account_type.bank_account_type_id"), nullable=False
    )
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)

    bank_account_type = relationship(LkBankAccountType)
    employee = relationship("Employee", back_populates="eft")


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
    tax_identifier_id = Column(
        UUID(as_uuid=True), ForeignKey("tax_identifier.tax_identifier_id"), index=True
    )
    title_id = Column(Integer, ForeignKey("lk_title.title_id"))
    first_name = Column(Text, nullable=False)
    middle_name = Column(Text)
    last_name = Column(Text, nullable=False)
    other_name = Column(Text)
    email_address = Column(Text)
    phone_number = Column(Text)  # Formatted in E.164
    cell_phone_number = Column(Text)  # Formatted in E.164
    preferred_comm_method_type = Column(Text)
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    fineos_customer_number = Column(Text, nullable=True)
    race_id = Column(Integer, ForeignKey("lk_race.race_id"))
    marital_status_id = Column(Integer, ForeignKey("lk_marital_status.marital_status_id"))
    gender_id = Column(Integer, ForeignKey("lk_gender.gender_id"))
    occupation_id = Column(Integer, ForeignKey("lk_occupation.occupation_id"))
    education_level_id = Column(Integer, ForeignKey("lk_education_level.education_level_id"))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)
    mailing_address_id = Column(UUID(as_uuid=True), ForeignKey("address.address_id"), index=True)
    payment_method_id = Column(Integer, ForeignKey("lk_payment_method.payment_method_id"))
    ctr_vendor_customer_code = Column(Text)

    title = relationship(LkTitle)
    race = relationship(LkRace)
    marital_status = relationship(LkMaritalStatus)
    gender = relationship(LkGender)
    # Note: We should move occupation to new EmployeeOccupation model
    # if this field relates to the function employee performs in a
    # specific employer. If it is a description of their profession
    # it should stay here.
    # Evaluate impact of change if it is appropriate to move.
    occupation = relationship(LkOccupation)
    education_level = relationship(LkEducationLevel)
    latest_import_log = relationship("ImportLog")
    claims = relationship("Claim", back_populates="employee")
    state_logs = relationship("StateLog", back_populates="employee")
    mailing_address = relationship("Address")
    eft = relationship("EFT", back_populates="employee", uselist=False)
    reference_files = relationship("EmployeeReferenceFile", back_populates="employee")
    payment_method = relationship(LkPaymentMethod, foreign_keys=payment_method_id)
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
    employee_occupations: "Query[EmployeeOccupation]" = dynamic_loader(
        "EmployeeOccupation", back_populates="employee"
    )


class EmployeeLog(Base):
    __tablename__ = "employee_log"
    employee_log_id = Column(UUID(as_uuid=True), primary_key=True)
    employee_id = Column(UUID(as_uuid=True), index=True)
    action = Column(Text, index=True)
    modified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)
    process_id = Column(Integer, index=True)


class Claim(Base):
    __tablename__ = "claim"
    claim_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    claim_type_id = Column(Integer, ForeignKey("lk_claim_type.claim_type_id"))
    employer_id = Column(UUID(as_uuid=True), index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)
    fineos_absence_id = Column(Text, index=True, unique=True)
    fineos_absence_status_id = Column(Integer, ForeignKey("lk_absence_status.absence_status_id"))
    absence_period_start_date = Column(Date)
    absence_period_end_date = Column(Date)
    fineos_notification_id = Column(Text)
    is_id_proofed = Column(Boolean)

    # Not sure if these are currently used.
    authorized_representative_id = Column(UUID(as_uuid=True))
    benefit_amount = Column(Numeric(asdecimal=True))
    benefit_days = Column(Integer)

    claim_type = relationship(LkClaimType)
    fineos_absence_status = relationship(LkAbsenceStatus)
    employee = relationship("Employee", back_populates="claims")


class Payment(Base):
    __tablename__ = "payment"
    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True, nullable=False)
    payment_method_id = Column(
        Integer, ForeignKey("lk_payment_method.payment_method_id"), nullable=False
    )
    period_start_date = Column(Date)
    period_end_date = Column(Date)
    payment_date = Column(Date)
    amount = Column(Numeric(asdecimal=True), nullable=False)
    fineos_pei_c_value = Column(Text, index=True)
    fineos_pei_i_value = Column(Text, index=True)
    fineos_extraction_date = Column(Date)
    disb_check_eft_number = Column(Text)
    disb_check_eft_issue_date = Column(Date)
    disb_method_id = Column(Integer, ForeignKey("lk_payment_method.payment_method_id"))
    disb_amount = Column(Numeric(asdecimal=True))

    claim = relationship(Claim)
    payment_method = relationship(LkPaymentMethod, foreign_keys=payment_method_id)
    disb_method = relationship(LkPaymentMethod, foreign_keys=disb_method_id)
    reference_files = relationship("PaymentReferenceFile", back_populates="payment")
    state_logs = relationship("StateLog", back_populates="payment")


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
    geo_state_text = Column(Text)
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


class CtrDocumentIdentifier(Base):
    __tablename__ = "ctr_document_identifier"
    ctr_document_identifier_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    ctr_document_identifier = Column(Text, unique=True, index=True)

    payment_reference_files = relationship(
        "PaymentReferenceFile", back_populates="ctr_document_identifier"
    )
    employee_reference_files = relationship(
        "EmployeeReferenceFile", back_populates="ctr_document_identifier"
    )


class CtrBatchIdentifier(Base):
    __tablename__ = "ctr_batch_identifier"
    ctr_batch_identifier_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    ctr_batch_identifier = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    batch_date = Column(Date, nullable=False)
    batch_counter = Column(Integer, nullable=False)
    inf_data = Column(JSON)

    Index("ix_year_ctr_batch_identifier", year, ctr_batch_identifier, unique=True)

    reference_files = relationship("ReferenceFile", back_populates="ctr_batch_identifier")


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
    active_directory_id = Column(Text, index=True, unique=True)
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
    user_leave_administrator_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=False)
    fineos_web_id = Column(Text)

    user = relationship(User)
    employer = relationship(Employer)


class WagesAndContributions(Base):
    __tablename__ = "wages_and_contributions"
    wage_and_contribution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    account_key = Column(Text, nullable=False)
    filing_period = Column(Date, nullable=False, index=True)
    employee_id = Column(
        UUID(as_uuid=True), ForeignKey("employee.employee_id"), nullable=False, index=True
    )
    employer_id = Column(
        UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=False, index=True
    )
    is_independent_contractor = Column(Boolean, nullable=False)
    is_opted_in = Column(Boolean, nullable=False)
    employee_ytd_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_qtr_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employee_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)

    employee = relationship("Employee", back_populates="wages_and_contributions")
    employer = relationship("Employer", back_populates="wages_and_contributions")


class EmployeeOccupation(Base):
    __tablename__ = "employee_occupation"
    employee_occupation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    employee_id = Column(
        UUID(as_uuid=True), ForeignKey("employee.employee_id"), nullable=False, index=True
    )
    employer_id = Column(
        UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=False, index=True
    )
    job_title = Column(Text)
    date_of_hire = Column(Date)
    date_job_ended = Column(Date)
    employment_status = Column(Text)
    org_unit_name = Column(Text)
    hours_worked_per_week = Column(Numeric)
    days_worked_per_week = Column(Numeric)
    manager_id = Column(Text)
    worksite_id = Column(Text)
    occupation_qualifier = Column(Text)

    employee = relationship("Employee", back_populates="employee_occupations")
    employer = relationship("Employer", back_populates="employer_occupations")


class ImportLog(Base):
    __tablename__ = "import_log"
    import_log_id = Column(Integer, primary_key=True)
    source = Column(Text, index=True)
    import_type = Column(Text, index=True)
    status = Column(Text)
    report = Column(Text)
    start = Column(TIMESTAMP(timezone=True), index=True)
    end = Column(TIMESTAMP(timezone=True))


class AgencyReductionPayment(Base):
    __tablename__ = "agency_reduction_payment"
    agency_reduction_payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    absence_case_id = Column(Text, index=True)
    agency_id = Column(Integer, ForeignKey("lk_agency.agency_id"), nullable=False)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True, nullable=False)
    payment_issued_date = Column(TIMESTAMP(timezone=True), index=True)
    gross_benefit_amount_cents = Column(Numeric)
    net_benefit_amount_cents = Column(Numeric)
    has_fraud_indicator = Column(Boolean)
    benefit_week_start_date = Column(TIMESTAMP(timezone=True), index=True)
    benefit_week_end_date = Column(TIMESTAMP(timezone=True), index=True)
    benefit_year_start_date = Column(TIMESTAMP(timezone=True), index=True)
    benefit_year_end_date = Column(TIMESTAMP(timezone=True), index=True)
    created_at = Column(TIMESTAMP(timezone=True), index=True)

    agency = relationship(LkAgency)
    claim = relationship(Claim)
    reference_file = relationship(
        "AgencyReductionPaymentReferenceFile", back_populates="agency_reduction_payment"
    )


class ReferenceFile(Base):
    __tablename__ = "reference_file"
    reference_file_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    file_location = Column(Text, index=True, unique=True, nullable=False)
    reference_file_type_id = Column(
        Integer, ForeignKey("lk_reference_file_type.reference_file_type_id"), nullable=True
    )
    ctr_batch_identifier_id = Column(
        UUID(as_uuid=True), ForeignKey("ctr_batch_identifier"), nullable=True, index=True
    )

    reference_file_type = relationship(LkReferenceFileType)
    payments = relationship("PaymentReferenceFile", back_populates="reference_file")
    employees = relationship("EmployeeReferenceFile", back_populates="reference_file")
    state_logs = relationship("StateLog", back_populates="reference_file")
    ctr_batch_identifier = relationship("CtrBatchIdentifier", back_populates="reference_files")
    agency_reduction_payment = relationship(
        "AgencyReductionPaymentReferenceFile", back_populates="reference_file"
    )


class AgencyReductionPaymentReferenceFile(Base):
    __tablename__ = "link_agency_reduction_payment_reference_file"
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), primary_key=True
    )
    agency_reduction_payment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agency_reduction_payment.agency_reduction_payment_id"),
        primary_key=True,
    )

    reference_file = relationship("ReferenceFile", back_populates="agency_reduction_payment")
    agency_reduction_payment = relationship(
        "AgencyReductionPayment", back_populates="reference_file"
    )


class PaymentReferenceFile(Base):
    __tablename__ = "link_payment_reference_file"
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payment.payment_id"), primary_key=True)
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), primary_key=True
    )
    ctr_document_identifier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ctr_document_identifier.ctr_document_identifier_id"),
        index=True,
    )

    payment = relationship("Payment", back_populates="reference_files")
    reference_file = relationship("ReferenceFile", back_populates="payments")
    ctr_document_identifier = relationship(
        "CtrDocumentIdentifier", back_populates="payment_reference_files"
    )


class EmployeeReferenceFile(Base):
    __tablename__ = "link_employee_reference_file"
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), primary_key=True)
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), primary_key=True
    )
    ctr_document_identifier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ctr_document_identifier.ctr_document_identifier_id"),
        index=True,
    )

    employee = relationship("Employee", back_populates="reference_files")
    reference_file = relationship("ReferenceFile", back_populates="employees")
    ctr_document_identifier = relationship(
        "CtrDocumentIdentifier", back_populates="employee_reference_files"
    )


class StateLog(Base):
    __tablename__ = "state_log"
    state_log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    start_state_id = Column(Integer, ForeignKey("lk_state.state_id"), nullable=False)
    end_state_id = Column(Integer, ForeignKey("lk_state.state_id"))
    started_at = Column(TIMESTAMP(timezone=True))
    ended_at = Column(TIMESTAMP(timezone=True), index=True)
    outcome = Column(JSON)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payment.payment_id"), index=True)
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), index=True
    )
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)
    prev_state_log_id = Column(UUID(as_uuid=True), ForeignKey("state_log.state_log_id"))

    payment = relationship("Payment", back_populates="state_logs")
    reference_file = relationship("ReferenceFile", back_populates="state_logs")
    employee = relationship("Employee", back_populates="state_logs")
    prev_state_log = relationship("StateLog", uselist=False)


class LatestStateLog(Base):
    __tablename__ = "latest_state_log"
    latest_state_log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    state_log_id = Column(UUID(as_uuid=True), ForeignKey("state_log.state_log_id"), index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payment.payment_id"), index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), index=True
    )

    state_log = relationship("StateLog")
    payment = relationship("Payment")
    employee = relationship("Employee")
    reference_file = relationship("ReferenceFile")


class AbsenceStatus(LookupTable):
    model = LkAbsenceStatus
    column_names = ("absence_status_id", "absence_status_description")

    ADJUDICATION = LkAbsenceStatus(1, "Adjudication")
    APPROVED = LkAbsenceStatus(2, "Approved")
    CLOSED = LkAbsenceStatus(3, "Closed")
    COMPLETED = LkAbsenceStatus(4, "Completed")
    DECLINED = LkAbsenceStatus(5, "Declined")
    IN_REVIEW = LkAbsenceStatus(6, "In Review")
    INTAKE_IN_PROGRESS = LkAbsenceStatus(7, "Intake In Progress")


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

    ABW = LkCountry(2, "ABW")
    AFG = LkCountry(3, "AFG")
    AGO = LkCountry(4, "AGO")
    AIA = LkCountry(5, "AIA")
    ALB = LkCountry(6, "ALB")
    AND = LkCountry(7, "AND")
    ANT = LkCountry(8, "ANT")
    ARE = LkCountry(9, "ARE")
    ARG = LkCountry(10, "ARG")
    ARM = LkCountry(11, "ARM")
    ASM = LkCountry(12, "ASM")
    ATA = LkCountry(13, "ATA")
    ATF = LkCountry(14, "ATF")
    ATG = LkCountry(15, "ATG")
    AUS = LkCountry(16, "AUS")
    AUT = LkCountry(17, "AUT")
    AZE = LkCountry(18, "AZE")
    BDI = LkCountry(19, "BDI")
    BEL = LkCountry(20, "BEL")
    BEN = LkCountry(21, "BEN")
    BFA = LkCountry(22, "BFA")
    BGD = LkCountry(23, "BGD")
    BGR = LkCountry(24, "BGR")
    BHR = LkCountry(25, "BHR")
    BHS = LkCountry(26, "BHS")
    BIH = LkCountry(27, "BIH")
    BLM = LkCountry(28, "BLM")
    BLR = LkCountry(29, "BLR")
    BLZ = LkCountry(30, "BLZ")
    BMU = LkCountry(31, "BMU")
    BOL = LkCountry(32, "BOL")
    BRA = LkCountry(33, "BRA")
    BRB = LkCountry(34, "BRB")
    BRN = LkCountry(35, "BRN")
    BTN = LkCountry(36, "BTN")
    BVT = LkCountry(37, "BVT")
    BWA = LkCountry(38, "BWA")
    CAF = LkCountry(39, "CAF")
    CAN = LkCountry(40, "CAN")
    CCK = LkCountry(41, "CCK")
    CHE = LkCountry(42, "CHE")
    CHL = LkCountry(43, "CHL")
    CHN = LkCountry(44, "CHN")
    CIV = LkCountry(45, "CIV")
    CMR = LkCountry(46, "CMR")
    COD = LkCountry(47, "COD")
    COG = LkCountry(48, "COG")
    COK = LkCountry(49, "COK")
    COL = LkCountry(50, "COL")
    COM = LkCountry(51, "COM")
    CPV = LkCountry(52, "CPV")
    CRI = LkCountry(53, "CRI")
    CUB = LkCountry(54, "CUB")
    CXR = LkCountry(55, "CXR")
    CYM = LkCountry(56, "CYM")
    CYP = LkCountry(57, "CYP")
    CZE = LkCountry(58, "CZE")
    DEU = LkCountry(59, "DEU")
    DJI = LkCountry(60, "DJI")
    DMA = LkCountry(61, "DMA")
    DNK = LkCountry(62, "DNK")
    DOM = LkCountry(63, "DOM")
    DZA = LkCountry(64, "DZA")
    ECU = LkCountry(65, "ECU")
    EGY = LkCountry(66, "EGY")
    ERI = LkCountry(67, "ERI")
    ESH = LkCountry(68, "ESH")
    ESP = LkCountry(69, "ESP")
    EST = LkCountry(70, "EST")
    ETH = LkCountry(71, "ETH")
    FIN = LkCountry(72, "FIN")
    FJI = LkCountry(73, "FJI")
    FLK = LkCountry(74, "FLK")
    FRA = LkCountry(75, "FRA")
    FRO = LkCountry(76, "FRO")
    FSM = LkCountry(77, "FSM")
    GAB = LkCountry(78, "GAB")
    GBR = LkCountry(79, "GBR")
    GEO = LkCountry(80, "GEO")
    GGY = LkCountry(81, "GGY")
    GHA = LkCountry(82, "GHA")
    GIB = LkCountry(83, "GIB")
    GIN = LkCountry(84, "GIN")
    GLP = LkCountry(85, "GLP")
    GMB = LkCountry(86, "GMB")
    GNB = LkCountry(87, "GNB")
    GNQ = LkCountry(88, "GNQ")
    GRC = LkCountry(89, "GRC")
    GRD = LkCountry(90, "GRD")
    GRL = LkCountry(91, "GRL")
    GTM = LkCountry(92, "GTM")
    GUF = LkCountry(93, "GUF")
    GUM = LkCountry(94, "GUM")
    GUY = LkCountry(95, "GUY")
    HKG = LkCountry(96, "HKG")
    HMD = LkCountry(97, "HMD")
    HND = LkCountry(98, "HND")
    HRV = LkCountry(99, "HRV")
    HTI = LkCountry(100, "HTI")
    HUN = LkCountry(101, "HUN")
    IDN = LkCountry(102, "IDN")
    IMN = LkCountry(103, "IMN")
    IND = LkCountry(104, "IND")
    IOT = LkCountry(105, "IOT")
    IRL = LkCountry(106, "IRL")
    IRN = LkCountry(107, "IRN")
    IRQ = LkCountry(108, "IRQ")
    ISL = LkCountry(109, "ISL")
    ISR = LkCountry(110, "ISR")
    ITA = LkCountry(111, "ITA")
    JAM = LkCountry(112, "JAM")
    JEY = LkCountry(113, "JEY")
    JOR = LkCountry(114, "JOR")
    JPN = LkCountry(115, "JPN")
    KAZ = LkCountry(116, "KAZ")
    KEN = LkCountry(117, "KEN")
    KGZ = LkCountry(118, "KGZ")
    KHM = LkCountry(119, "KHM")
    KIR = LkCountry(120, "KIR")
    KNA = LkCountry(121, "KNA")
    KOR = LkCountry(122, "KOR")
    KWT = LkCountry(123, "KWT")
    LAO = LkCountry(124, "LAO")
    LBN = LkCountry(125, "LBN")
    LBR = LkCountry(126, "LBR")
    LBY = LkCountry(127, "LBY")
    LCA = LkCountry(128, "LCA")
    LIE = LkCountry(129, "LIE")
    LKA = LkCountry(130, "LKA")
    LSO = LkCountry(131, "LSO")
    LTU = LkCountry(132, "LTU")
    LUX = LkCountry(133, "LUX")
    LVA = LkCountry(134, "LVA")
    MAC = LkCountry(135, "MAC")
    MAF = LkCountry(136, "MAF")
    MAR = LkCountry(137, "MAR")
    MCO = LkCountry(138, "MCO")
    MDA = LkCountry(139, "MDA")
    MDG = LkCountry(140, "MDG")
    MDV = LkCountry(141, "MDV")
    MEX = LkCountry(142, "MEX")
    MHL = LkCountry(143, "MHL")
    MKD = LkCountry(144, "MKD")
    MLI = LkCountry(145, "MLI")
    MLT = LkCountry(146, "MLT")
    MMR = LkCountry(147, "MMR")
    MNE = LkCountry(148, "MNE")
    MNG = LkCountry(149, "MNG")
    MNP = LkCountry(150, "MNP")
    MOZ = LkCountry(151, "MOZ")
    MRT = LkCountry(152, "MRT")
    MSR = LkCountry(153, "MSR")
    MTQ = LkCountry(154, "MTQ")
    MUS = LkCountry(155, "MUS")
    MWI = LkCountry(156, "MWI")
    MYS = LkCountry(157, "MYS")
    MYT = LkCountry(158, "MYT")
    NAM = LkCountry(159, "NAM")
    NCL = LkCountry(160, "NCL")
    NER = LkCountry(161, "NER")
    NFK = LkCountry(162, "NFK")
    NGA = LkCountry(163, "NGA")
    NIC = LkCountry(164, "NIC")
    NIU = LkCountry(165, "NIU")
    NLD = LkCountry(166, "NLD")
    NOR = LkCountry(167, "NOR")
    NPL = LkCountry(168, "NPL")
    NRU = LkCountry(169, "NRU")
    NZL = LkCountry(170, "NZL")
    OMN = LkCountry(171, "OMN")
    PAK = LkCountry(172, "PAK")
    PAN = LkCountry(173, "PAN")
    PCN = LkCountry(174, "PCN")
    PER = LkCountry(175, "PER")
    PHL = LkCountry(176, "PHL")
    PLW = LkCountry(177, "PLW")
    PNG = LkCountry(178, "PNG")
    POL = LkCountry(179, "POL")
    PRI = LkCountry(180, "PRI")
    PRK = LkCountry(181, "PRK")
    PRT = LkCountry(182, "PRT")
    PRY = LkCountry(183, "PRY")
    PSE = LkCountry(184, "PSE")
    PYF = LkCountry(185, "PYF")
    QAT = LkCountry(186, "QAT")
    REU = LkCountry(187, "REU")
    ROU = LkCountry(188, "ROU")
    RUS = LkCountry(189, "RUS")
    RWA = LkCountry(190, "RWA")
    SAU = LkCountry(191, "SAU")
    SDN = LkCountry(192, "SDN")
    SEN = LkCountry(193, "SEN")
    SGP = LkCountry(194, "SGP")
    SGS = LkCountry(195, "SGS")
    SHN = LkCountry(196, "SHN")
    SJM = LkCountry(197, "SJM")
    SLB = LkCountry(198, "SLB")
    SLE = LkCountry(199, "SLE")
    SLV = LkCountry(200, "SLV")
    SMR = LkCountry(201, "SMR")
    SOM = LkCountry(202, "SOM")
    SPM = LkCountry(203, "SPM")
    SRB = LkCountry(204, "SRB")
    STP = LkCountry(205, "STP")
    SUR = LkCountry(206, "SUR")
    SVK = LkCountry(207, "SVK")
    SVN = LkCountry(208, "SVN")
    SWE = LkCountry(209, "SWE")
    SWZ = LkCountry(210, "SWZ")
    SYC = LkCountry(211, "SYC")
    SYR = LkCountry(212, "SYR")
    TCA = LkCountry(213, "TCA")
    TCD = LkCountry(214, "TCD")
    TGO = LkCountry(215, "TGO")
    THA = LkCountry(216, "THA")
    TJK = LkCountry(217, "TJK")
    TKL = LkCountry(218, "TKL")
    TKM = LkCountry(219, "TKM")
    TLS = LkCountry(220, "TLS")
    TON = LkCountry(221, "TON")
    TTO = LkCountry(222, "TTO")
    TUN = LkCountry(223, "TUN")
    TUR = LkCountry(224, "TUR")
    TUV = LkCountry(225, "TUV")
    TWN = LkCountry(226, "TWN")
    TZA = LkCountry(227, "TZA")
    UGA = LkCountry(228, "UGA")
    UKR = LkCountry(229, "UKR")
    UMI = LkCountry(230, "UMI")
    URY = LkCountry(231, "URY")
    USA = LkCountry(232, "USA")
    UZB = LkCountry(233, "UZB")
    VAT = LkCountry(234, "VAT")
    VCT = LkCountry(235, "VCT")
    VEN = LkCountry(236, "VEN")
    VGB = LkCountry(237, "VGB")
    VIR = LkCountry(238, "VIR")
    VNM = LkCountry(239, "VNM")
    VUT = LkCountry(240, "VUT")
    WLF = LkCountry(241, "WLF")
    WSM = LkCountry(242, "WSM")
    YEM = LkCountry(243, "YEM")
    ZAF = LkCountry(244, "ZAF")
    ZMB = LkCountry(245, "ZMB")
    ZWE = LkCountry(246, "ZWE")
    ALA = LkCountry(247, "ALA")


class ClaimType(LookupTable):
    model = LkClaimType
    column_names = ("claim_type_id", "claim_type_description")

    FAMILY_LEAVE = LkClaimType(1, "Family Leave")
    MEDICAL_LEAVE = LkClaimType(2, "Medical Leave")


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


class PaymentMethod(LookupTable):
    model = LkPaymentMethod
    column_names = ("payment_method_id", "payment_method_description")

    ACH = LkPaymentMethod(1, "Elec Funds Transfer")
    CHECK = LkPaymentMethod(2, "Check")
    DEBIT = LkPaymentMethod(3, "Debit")


class BankAccountType(LookupTable):
    model = LkBankAccountType
    column_names = ("bank_account_type_id", "bank_account_type_description")

    SAVINGS = LkBankAccountType(1, "Savings")
    CHECKING = LkBankAccountType(2, "Checking")


class Flow(LookupTable):
    model = LkFlow
    column_names = ("flow_id", "flow_description")

    PAYMENT = LkFlow(1, "Payment")
    DUA_CLAIMANT_LIST = LkFlow(2, "DUA claimant list")
    DIA_CLAIMANT_LIST = LkFlow(3, "DIA claimant list")
    DUA_PAYMENT_LIST = LkFlow(4, "DUA payment list")
    DIA_PAYMENT_LIST = LkFlow(5, "DIA payment list")
    DFML_AGENCY_REDUCTION_REPORT = LkFlow(6, "DFML agency reduction report")
    VENDOR_CHECK = LkFlow(7, "Vendor check")
    VENDOR_EFT = LkFlow(8, "Vendor EFT")
    UNUSED = LkFlow(9, "Unused flow")


class State(LookupTable):
    model = LkState
    column_names = ("state_id", "state_description", "flow_id")

    VERIFY_VENDOR_STATUS = LkState(1, "Verify vendor status", Flow.UNUSED.flow_id)  # Not used
    CLAIMANT_LIST_CREATED = LkState(
        2, "Create claimant list for DIA", Flow.DIA_CLAIMANT_LIST.flow_id
    )
    CLAIMANT_LIST_SUBMITTED = LkState(
        3, "Submit claimant list to DIA", Flow.DIA_CLAIMANT_LIST.flow_id
    )
    PAYMENTS_RETRIEVED = LkState(4, "Payments retrieved", Flow.UNUSED.flow_id)  # Not used
    PAYMENTS_STORED_IN_DB = LkState(5, "Payments stored in db", Flow.UNUSED.flow_id)  # Not used
    DFML_REPORT_CREATED = LkState(
        6, "Create DFML report", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
    )
    DFML_REPORT_SUBMITTED = LkState(
        7, "Submit DFML report", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
    )

    # Payments State Machine LucidChart: https://app.lucidchart.com/lucidchart/invitations/accept/8ae0d129-b21e-4678-8f98-0b0feafb9ace
    # States for Payment flow
    PAYMENT_PROCESS_INITIATED = LkState(8, "Payment process initiated", Flow.PAYMENT.flow_id)
    ADD_TO_PAYMENT_EXPORT_ERROR_REPORT = LkState(
        9, "Add to payment export error report", Flow.PAYMENT.flow_id
    )
    PAYMENT_EXPORT_ERROR_REPORT_SENT = LkState(
        10, "Payment export error report sent", Flow.PAYMENT.flow_id
    )
    MARK_AS_EXTRACTED_IN_FINEOS = LkState(11, "Mark as extracted in FINEOS", Flow.PAYMENT.flow_id)
    CONFIRM_VENDOR_STATUS_IN_MMARS = LkState(
        12, "Confirm vendor status in MMARS", Flow.PAYMENT.flow_id
    )
    PAYMENT_ALLOWABLE_TIME_IN_STATE_EXCEEDED = LkState(
        13, "Payment: allowable time in state exceeded", Flow.PAYMENT.flow_id
    )
    ADD_TO_GAX = LkState(14, "Add to GAX", Flow.PAYMENT.flow_id)
    GAX_SENT = LkState(15, "GAX sent", Flow.PAYMENT.flow_id)
    ADD_TO_GAX_ERROR_REPORT = LkState(16, "Add to GAX error report", Flow.PAYMENT.flow_id)
    GAX_ERROR_REPORT_SENT = LkState(17, "GAX error report sent", Flow.PAYMENT.flow_id)
    CONFIRM_PAYMENT = LkState(18, "Confirm payment", Flow.PAYMENT.flow_id)
    SEND_PAYMENT_DETAILS_TO_FINEOS = LkState(
        19, "Send payment details to FINEOS", Flow.PAYMENT.flow_id
    )
    PAYMENT_COMPLETE = LkState(20, "Payment complete", Flow.PAYMENT.flow_id)

    # States for Vendor Check flow
    VENDOR_CHECK_INITIATED_BY_VENDOR_EXPORT = LkState(
        21, "Vendor check initiated by vendor export", Flow.VENDOR_CHECK.flow_id
    )
    ADD_TO_VENDOR_EXPORT_ERROR_REPORT = LkState(
        22, "Add to vendor export error report", Flow.VENDOR_CHECK.flow_id
    )
    VENDOR_EXPORT_ERROR_REPORT_SENT = LkState(
        23, "Vendor export error report sent", Flow.VENDOR_CHECK.flow_id
    )
    VENDOR_CHECK_INITIATED_BY_PAYMENT_EXPORT = LkState(
        24, "Vendor check initiated by payment export", Flow.VENDOR_CHECK.flow_id
    )
    IDENTIFY_MMARS_STATUS = LkState(25, "Identify MMARS status", Flow.VENDOR_CHECK.flow_id)
    ADD_TO_VCM_REPORT = LkState(26, "Add to VCM report", Flow.VENDOR_CHECK.flow_id)
    VCM_REPORT_SENT = LkState(27, "VCM report sent", Flow.VENDOR_CHECK.flow_id)
    VENDOR_ALLOWABLE_TIME_IN_STATE_EXCEEDED = LkState(
        28, "Vendor: allowable time in state exceeded", Flow.VENDOR_CHECK.flow_id
    )
    ADD_TO_VCC = LkState(29, "Add to VCC", Flow.VENDOR_CHECK.flow_id)
    VCC_SENT = LkState(30, "VCC sent", Flow.VENDOR_CHECK.flow_id)
    ADD_TO_VCC_ERROR_REPORT = LkState(31, "Add to VCC error report", Flow.VENDOR_CHECK.flow_id)
    VCC_ERROR_REPORT_SENT = LkState(32, "VCC error report sent", Flow.VENDOR_CHECK.flow_id)
    MMARS_STATUS_CONFIRMED = LkState(33, "MMARS status confirmed", Flow.VENDOR_CHECK.flow_id)

    # States for Vendor EFT flow
    EFT_DETECTED_IN_VENDOR_EXPORT = LkState(
        34, "EFT detected in vendor export", Flow.VENDOR_EFT.flow_id
    )
    EFT_DETECTED_IN_PAYMENT_EXPORT = LkState(
        35, "EFT detected in payment export", Flow.VENDOR_EFT.flow_id
    )
    EFT_REQUEST_RECEIVED = LkState(36, "EFT request received", Flow.VENDOR_EFT.flow_id)
    EFT_PENDING = LkState(37, "EFT pending", Flow.VENDOR_EFT.flow_id)
    ADD_TO_EFT_ERROR_REPORT = LkState(38, "Add to EFT error report", Flow.VENDOR_EFT.flow_id)
    EFT_ERROR_REPORT_SENT = LkState(39, "EFT error report sent", Flow.VENDOR_EFT.flow_id)
    EFT_ALLOWABLE_TIME_IN_STATE_EXCEEDED = LkState(
        40, "EFT: allowable time in state exceeded", Flow.VENDOR_EFT.flow_id
    )
    EFT_ELIGIBLE = LkState(41, "EFT eligible", Flow.VENDOR_EFT.flow_id)


class ReferenceFileType(LookupTable):
    model = LkReferenceFileType
    column_names = ("reference_file_type_id", "reference_file_type_description", "num_files_in_set")

    GAX = LkReferenceFileType(1, "GAX", 2)
    VCC = LkReferenceFileType(2, "VCC", 2)
    PAYMENT_EXTRACT = LkReferenceFileType(3, "Payment extract", 3)
    VENDOR_CLAIM_EXTRACT = LkReferenceFileType(4, "Vendor claim extract", 3)
    DUA_CLAIMANT_LIST = LkReferenceFileType(5, "DUA claimant list", 1)
    DIA_CLAIMANT_LIST = LkReferenceFileType(6, "DIA claimant list", 1)
    DUA_PAYMENT_LIST = LkReferenceFileType(7, "DUA payment list", 1)
    DIA_PAYMENT_LIST = LkReferenceFileType(8, "DIA payment list", 1)
    DFML_AGENCY_REDUCTION_REPORT = LkReferenceFileType(9, "DFML agency reduction report", 1)
    OUTBOUND_STATUS_RETURN = LkReferenceFileType(10, "Outbound Status Return", 1)
    OUTBOUND_VENDOR_CUSTOMER_RETURN = LkReferenceFileType(11, "Outbound Vendor Customer Return", 1)
    OUTBOUND_PAYMENT_RETURN = LkReferenceFileType(12, "Outbound Payment Return", 1)
    PEI_WRITEBACK = LkReferenceFileType(13, "PEI Writeback", 1)


class Title(LookupTable):
    model = LkTitle
    column_names = ("title_id", "title_description")

    UNKNOWN = LkTitle(1, "Unknown")
    MR = LkTitle(2, "Mr")
    MRS = LkTitle(3, "Mrs")
    MISS = LkTitle(4, "Miss")
    MS = LkTitle(5, "Ms")
    DR = LkTitle(6, "Dr")
    MADAM = LkTitle(7, "Madam")
    SIR = LkTitle(8, "Sir")


class Agency(LookupTable):
    model = LkAgency
    column_names = ("agency_id", "agency_description")

    DIA = LkAgency(1, "Department of Industrial Accidents")
    DUA = LkAgency(2, "Department of Unemployment Assistance")


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    AbsenceStatus.sync_to_database(db_session)
    AddressType.sync_to_database(db_session)
    GeoState.sync_to_database(db_session)
    Country.sync_to_database(db_session)
    ClaimType.sync_to_database(db_session)
    Race.sync_to_database(db_session)
    MaritalStatus.sync_to_database(db_session)
    Gender.sync_to_database(db_session)
    Occupation.sync_to_database(db_session)
    Role.sync_to_database(db_session)
    PaymentMethod.sync_to_database(db_session)
    BankAccountType.sync_to_database(db_session)
    ReferenceFileType.sync_to_database(db_session)
    Title.sync_to_database(db_session)
    ReferenceFileType.sync_to_database(db_session)

    # Order of operations matters here:
    # Flow must be synced before State.
    Flow.sync_to_database(db_session)
    State.sync_to_database(db_session)
    db_session.commit()
