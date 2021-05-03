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
import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional, cast

from dateutil.relativedelta import relativedelta
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import Query, deferred, dynamic_loader, relationship
from sqlalchemy.schema import Sequence
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.functions import now as sqlnow
from sqlalchemy.types import JSON, TypeEngine

from ..lookup import LookupTable
from .base import Base, utc_timestamp_gen, uuid_gen
from .verifications import Verification

# (typed_hybrid_property) https://github.com/dropbox/sqlalchemy-stubs/issues/98
if TYPE_CHECKING:
    # Use this to make hybrid_property's have the same typing as a normal property until stubs are improved.
    typed_hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property as typed_hybrid_property


# (PostgreSQLUUID) https://github.com/dropbox/sqlalchemy-stubs/issues/94
if TYPE_CHECKING:
    PostgreSQLUUID = TypeEngine[uuid.UUID]
else:
    PostgreSQLUUID = UUID(as_uuid=True)


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
    occupation_id = Column(Integer, primary_key=True, autoincrement=True)
    occupation_description = Column(Text)
    occupation_code = Column(Integer, unique=True)
    

    def __init__(self, occupation_id, occupation_description, occupation_code):
        self.occupation_id = occupation_id
        self.occupation_description = occupation_description
        self.occupation_code = occupation_code
        

class LkOccupationTitle(Base):
    __tablename__ = "lk_occupation_title"
    occupation_title_id = Column(Integer, primary_key=True, autoincrement=True)
    occupation_title_description = Column(Text)
    occupation_code = Column(Integer, ForeignKey("lk_occupation.occupation_code"))
    occupation_title_code = Column(Integer) 
    

    def __init__(self, occupation_title_id, occupation_title_description, occupation_code, occupation_title_code):
        self.occupation_title_id = occupation_title_id
        self.occupation_title_description = occupation_title_description
        self.occupation_code = occupation_code
        self.occupation_title_code = occupation_title_code
        


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


class LkPrenoteState(Base):
    __tablename__ = "lk_prenote_state"
    prenote_state_id = Column(Integer, primary_key=True, autoincrement=True)
    prenote_state_description = Column(Text)

    def __init__(self, prenote_state_id, prenote_state_description):
        self.prenote_state_id = prenote_state_id
        self.prenote_state_description = prenote_state_description


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


class LkPaymentTransactionType(Base):
    __tablename__ = "lk_payment_transaction_type"
    payment_transaction_type_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_transaction_type_description = Column(Text)

    def __init__(self, payment_transaction_type_id, payment_transaction_type_description):
        self.payment_transaction_type_id = payment_transaction_type_id
        self.payment_transaction_type_description = payment_transaction_type_description


class LkPaymentCheckStatus(Base):
    __tablename__ = "lk_payment_check_status"
    payment_check_status_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_check_status_description = Column(Text)

    def __init__(self, payment_check_status_id, payment_check_status_description):
        self.payment_check_status_id = payment_check_status_id
        self.payment_check_status_description = payment_check_status_description


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

    claims = cast(Optional[List["Claim"]], relationship("Claim", back_populates="employer"))
    wages_and_contributions: "Query[WagesAndContributions]" = dynamic_loader(
        "WagesAndContributions", back_populates="employer"
    )
    addresses: "Query[EmployerAddress]" = dynamic_loader(
        "EmployerAddress", back_populates="employer"
    )
    employer_occupations: "Query[EmployeeOccupation]" = dynamic_loader(
        "EmployeeOccupation", back_populates="employer"
    )
    employer_quarterly_contribution: "Query[EmployerQuarterlyContribution]" = dynamic_loader(
        "EmployerQuarterlyContribution", back_populates="employer"
    )

    @typed_hybrid_property
    def has_verification_data(self) -> bool:
        current_date = date.today()
        last_years_date = current_date - relativedelta(years=1)
        return any(
            quarter.employer_total_pfml_contribution > 0
            and quarter.filing_period >= last_years_date
            and quarter.filing_period < current_date
            for quarter in self.employer_quarterly_contribution
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

    employer = relationship("Employer", back_populates="employer_quarterly_contribution")


class EmployerLog(Base):
    __tablename__ = "employer_log"
    employer_log_id = Column(UUID(as_uuid=True), primary_key=True)
    employer_id = Column(UUID(as_uuid=True), index=True)
    action = Column(Text, index=True)
    modified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)
    process_id = Column(Integer, index=True)


class EFT(Base):
    __tablename__ = "eft"
    eft_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    routing_nbr = Column(Text, nullable=False)
    account_nbr = Column(Text, nullable=False)
    bank_account_type_id = Column(
        Integer, ForeignKey("lk_bank_account_type.bank_account_type_id"), nullable=False
    )
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)

    bank_account_type = relationship(LkBankAccountType)
    employee = relationship("Employee", back_populates="eft")


class PubEft(Base):
    __tablename__ = "pub_eft"
    pub_eft_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    routing_nbr = Column(Text, nullable=False)
    account_nbr = Column(Text, nullable=False)
    bank_account_type_id = Column(
        Integer, ForeignKey("lk_bank_account_type.bank_account_type_id"), nullable=False
    )
    prenote_state_id = Column(
        Integer, ForeignKey("lk_prenote_state.prenote_state_id"), nullable=False
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )
    prenote_response_at = Column(TIMESTAMP(timezone=True))
    prenote_sent_at = Column(TIMESTAMP(timezone=True))
    prenote_response_reason_code = Column(Text)
    pub_eft_individual_id_seq: Sequence = Sequence("pub_eft_individual_id_seq")
    pub_individual_id = Column(
        Integer,
        pub_eft_individual_id_seq,
        index=True,
        server_default=pub_eft_individual_id_seq.next_value(),
    )

    bank_account_type = relationship(LkBankAccountType)
    prenote_state = relationship(LkPrenoteState)

    employees = relationship("EmployeePubEftPair", back_populates="pub_eft")


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


class CtrAddressPair(Base):
    __tablename__ = "link_ctr_address_pair"
    fineos_address_id = Column(
        UUID(as_uuid=True), ForeignKey("address.address_id"), primary_key=True, unique=True
    )
    ctr_address_id = Column(
        UUID(as_uuid=True), ForeignKey("address.address_id"), nullable=True, index=True
    )

    fineos_address = relationship("Address", foreign_keys=fineos_address_id)
    ctr_address = cast("Optional[Address]", relationship("Address", foreign_keys=ctr_address_id))


class ExperianAddressPair(Base):
    __tablename__ = "link_experian_address_pair"
    fineos_address_id = Column(
        UUID(as_uuid=True), ForeignKey("address.address_id"), primary_key=True, unique=True
    )
    experian_address_id = Column(
        UUID(as_uuid=True), ForeignKey("address.address_id"), nullable=True, index=True
    )

    fineos_address = relationship("Address", foreign_keys=fineos_address_id)
    experian_address = cast(
        "Optional[Address]", relationship("Address", foreign_keys=experian_address_id)
    )


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
    occupation_title_id = Column(Integer, ForeignKey("lk_occupation_title.occupation_title_id"))
    education_level_id = Column(Integer, ForeignKey("lk_education_level.education_level_id"))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)
    mailing_address_id = Column(UUID(as_uuid=True), ForeignKey("address.address_id"), index=True)
    payment_method_id = Column(Integer, ForeignKey("lk_payment_method.payment_method_id"))
    ctr_vendor_customer_code = Column(Text)
    ctr_address_pair_id = Column(
        UUID(as_uuid=True), ForeignKey("link_ctr_address_pair.fineos_address_id"), index=True
    )
    experian_address_pair_id = deferred(
        Column(
            UUID(as_uuid=True).evaluates_none(),
            ForeignKey("link_experian_address_pair.fineos_address_id"),
            index=True,
        )
    )

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
    claims = cast(Optional[List["Claim"]], relationship("Claim", back_populates="employee"))
    state_logs = relationship("StateLog", back_populates="employee")
    eft = relationship("EFT", back_populates="employee", uselist=False)
    pub_efts: "Query[EmployeePubEftPair]" = dynamic_loader(
        "EmployeePubEftPair", back_populates="employee"
    )
    reference_files = relationship("EmployeeReferenceFile", back_populates="employee")
    payment_method = relationship(LkPaymentMethod, foreign_keys=payment_method_id)
    tax_identifier = cast(
        Optional[TaxIdentifier], relationship("TaxIdentifier", back_populates="employee")
    )
    ctr_address_pair = cast(Optional[CtrAddressPair], relationship("CtrAddressPair"))
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
    employer_id = Column(UUID(as_uuid=True), index=True)


class EmployeePubEftPair(Base):
    __tablename__ = "link_employee_pub_eft_pair"
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), primary_key=True)
    pub_eft_id = Column(PostgreSQLUUID, ForeignKey("pub_eft.pub_eft_id"), primary_key=True)

    employee = relationship("Employee", back_populates="pub_efts")
    pub_eft = relationship("PubEft", back_populates="employees")


class Claim(Base):
    __tablename__ = "claim"
    claim_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    claim_type_id = Column(Integer, ForeignKey("lk_claim_type.claim_type_id"))
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)
    fineos_absence_id = Column(Text, index=True, unique=True)
    fineos_absence_status_id = Column(Integer, ForeignKey("lk_absence_status.absence_status_id"))
    absence_period_start_date = Column(Date)
    absence_period_end_date = Column(Date)
    fineos_notification_id = Column(Text)
    is_id_proofed = Column(Boolean)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    # Not sure if these are currently used.
    authorized_representative_id = Column(UUID(as_uuid=True))
    benefit_amount = Column(Numeric(asdecimal=True))
    benefit_days = Column(Integer)

    claim_type = relationship(LkClaimType)
    fineos_absence_status = relationship(LkAbsenceStatus)
    employee = relationship("Employee", back_populates="claims")
    employer = relationship("Employer", back_populates="claims")


class Payment(Base):
    __tablename__ = "payment"
    payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True)
    payment_transaction_type_id = Column(
        Integer, ForeignKey("lk_payment_transaction_type.payment_transaction_type_id")
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
    leave_request_decision = Column(Text)
    experian_address_pair_id = Column(
        UUID(as_uuid=True), ForeignKey("link_experian_address_pair.fineos_address_id"), index=True
    )
    has_address_update = Column(Boolean, default=False, server_default="FALSE", nullable=False)
    has_eft_update = Column(Boolean, default=False, server_default="FALSE", nullable=False)
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )
    pub_eft_id = Column(UUID(as_uuid=True), ForeignKey("pub_eft.pub_eft_id"))
    payment_individual_id_seq: Sequence = Sequence("payment_individual_id_seq")
    pub_individual_id = Column(
        Integer,
        payment_individual_id_seq,
        index=True,
        server_default=payment_individual_id_seq.next_value(),
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    claim = relationship(Claim)
    payment_transaction_type = relationship(LkPaymentTransactionType)
    disb_method = relationship(LkPaymentMethod, foreign_keys=disb_method_id)
    pub_eft = relationship(PubEft)
    experian_address_pair = relationship(ExperianAddressPair, foreign_keys=experian_address_pair_id)
    fineos_extract_import_log = relationship("ImportLog")
    reference_files = relationship("PaymentReferenceFile", back_populates="payment")
    state_logs = relationship("StateLog", back_populates="payment")

    check = relationship("PaymentCheck", backref="payment", uselist=False)


class PaymentCheck(Base):
    __tablename__ = "payment_check"
    payment_id = Column(PostgreSQLUUID, ForeignKey(Payment.payment_id), primary_key=True)
    check_number = Column(Integer, nullable=False, index=True, unique=True)
    check_posted_date = Column(Date)
    payment_check_status_id = Column(
        Integer, ForeignKey("lk_payment_check_status.payment_check_status_id")
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    payment_check_status = relationship(LkPaymentCheckStatus)


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
    address_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
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
    ctr_document_identifier_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    ctr_document_identifier = Column(Text, unique=True, index=True)
    document_date = Column(Date, nullable=False, index=True)
    document_counter = Column(Integer, nullable=False, index=True)

    payment_reference_files = relationship(
        "PaymentReferenceFile", back_populates="ctr_document_identifier"
    )
    employee_reference_files = relationship(
        "EmployeeReferenceFile", back_populates="ctr_document_identifier"
    )


class CtrBatchIdentifier(Base):
    __tablename__ = "ctr_batch_identifier"
    ctr_batch_identifier_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
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

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    roles = relationship("LkRole", secondary="link_user_role", uselist=True)
    user_leave_administrators = relationship(
        "UserLeaveAdministrator", back_populates="user", uselist=True
    )
    employers = relationship("Employer", secondary="link_user_leave_administrator", uselist=True)

    @hybrid_method
    def get_user_leave_admin_for_employer(
        self, employer: Employer
    ) -> Optional["UserLeaveAdministrator"]:
        # Return the UserLeaveAdministrator record associated with the Employer
        for user_leave_administrator in self.user_leave_administrators:
            if user_leave_administrator.employer == employer:
                return user_leave_administrator
        return None

    @hybrid_method
    def verified_employer(self, employer: Employer) -> bool:
        # Return the `verified` state of the Employer (from the UserLeaveAdministrator record)
        user_leave_administrator = self.get_user_leave_admin_for_employer(employer=employer)
        return user_leave_administrator.verified if user_leave_administrator else False


class UserRole(Base):
    __tablename__ = "link_user_role"
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("lk_role.role_id"), primary_key=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    user = relationship(User)
    role = relationship(LkRole)


class UserLeaveAdministrator(Base):
    __tablename__ = "link_user_leave_administrator"
    __table_args__ = (UniqueConstraint("user_id", "employer_id"),)
    user_leave_administrator_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=False)
    fineos_web_id = Column(Text)
    verification_id = Column(
        UUID(as_uuid=True), ForeignKey("verification.verification_id"), nullable=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    user = relationship(User)
    employer = relationship(Employer)
    verification = relationship(Verification)

    @typed_hybrid_property
    def verified(self) -> bool:
        return self.verification_id is not None


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


class ReferenceFile(Base):
    __tablename__ = "reference_file"
    reference_file_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    file_location = Column(Text, index=True, unique=True, nullable=False)
    reference_file_type_id = Column(
        Integer, ForeignKey("lk_reference_file_type.reference_file_type_id"), nullable=True
    )
    ctr_batch_identifier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ctr_batch_identifier.ctr_batch_identifier_id"),
        nullable=True,
        index=True,
    )

    reference_file_type = relationship(LkReferenceFileType)
    payments = relationship("PaymentReferenceFile", back_populates="reference_file")
    employees = relationship("EmployeeReferenceFile", back_populates="reference_file")
    state_logs = relationship("StateLog", back_populates="reference_file")
    ctr_batch_identifier = relationship("CtrBatchIdentifier", back_populates="reference_files")
    dia_reduction_payment = relationship(
        "DiaReductionPaymentReferenceFile", back_populates="reference_file"
    )
    dua_reduction_payment = relationship(
        "DuaReductionPaymentReferenceFile", back_populates="reference_file"
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
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
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), primary_key=True
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

    def __iter__(self):
        return self


class DuaReductionPaymentReferenceFile(Base):
    __tablename__ = "link_dua_reduction_payment_reference_file"
    dua_reduction_payment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dua_reduction_payment.dua_reduction_payment_id"),
        primary_key=True,
    )
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), primary_key=True
    )

    dua_reduction_payment = relationship("DuaReductionPayment")
    reference_file = relationship("ReferenceFile")


class DiaReductionPaymentReferenceFile(Base):
    __tablename__ = "link_dia_reduction_payment_reference_file"
    dia_reduction_payment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dia_reduction_payment.dia_reduction_payment_id"),
        primary_key=True,
    )
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), primary_key=True
    )

    dia_reduction_payment = relationship("DiaReductionPayment")
    reference_file = relationship("ReferenceFile")


class StateLog(Base):
    __tablename__ = "state_log"
    state_log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
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
    associated_type = Column(Text, index=True)

    import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True, nullable=True,
    )
    end_state = cast("Optional[LkState]", relationship(LkState, foreign_keys=[end_state_id]))
    payment = relationship("Payment", back_populates="state_logs")
    reference_file = relationship("ReferenceFile", back_populates="state_logs")
    employee = relationship("Employee", back_populates="state_logs")
    prev_state_log = relationship("StateLog", uselist=False, remote_side=state_log_id)
    import_log = cast("Optional[ImportLog]", relationship(ImportLog, foreign_keys=[import_log_id]))


class LatestStateLog(Base):
    __tablename__ = "latest_state_log"
    latest_state_log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    state_log_id = Column(
        UUID(as_uuid=True), ForeignKey("state_log.state_log_id"), index=True, nullable=False
    )
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payment.payment_id"), index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee.employee_id"), index=True)
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), index=True
    )

    state_log = relationship("StateLog")
    payment = relationship("Payment")
    employee = relationship("Employee")
    reference_file = relationship("ReferenceFile")


class DuaReductionPayment(Base):
    __tablename__ = "dua_reduction_payment"
    dua_reduction_payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    absence_case_id = Column(Text, nullable=False)
    employer_fein = Column(Text)
    payment_date = Column(Date)
    request_week_begin_date = Column(Date)
    gross_payment_amount_cents = Column(Integer)
    payment_amount_cents = Column(Integer)
    fraud_indicator = Column(Text)
    benefit_year_begin_date = Column(Date)
    benefit_year_end_date = Column(Date)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    # Each row should be unique. This enables us to load only new rows from a CSV and ensures that
    # we don't include payments twice as two different rows. Almost all fields are nullable so we
    # have to coalesce those null values to empty strings. We've manually adjusted the migration
    # that adds this unique constraint to coalesce those nullable fields.
    # See: 2021_01_29_15_51_16_14155f78d8e6_create_dua_reduction_payment_table.py


class DiaReductionPayment(Base):
    __tablename__ = "dia_reduction_payment"
    dia_reduction_payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    fineos_customer_number = Column(Text, nullable=False)
    board_no = Column(Text)
    event_id = Column(Text)
    event_description = Column(Text)
    eve_created_date = Column(Date)
    event_occurrence_date = Column(Date)
    award_id = Column(Text)
    award_code = Column(Text)
    award_amount = Column(Numeric(asdecimal=True))
    award_date = Column(Date)
    start_date = Column(Date)
    end_date = Column(Date)
    weekly_amount = Column(Numeric(asdecimal=True))
    award_created_date = Column(Date)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    # Each row should be unique.


class PubError(Base):
    __tablename__ = "pub_error"
    pub_error_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    pub_error_type_id = Column(
        Integer, ForeignKey("lk_pub_error_type.pub_error_type_id"), nullable=False
    )

    message = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=False)
    type_code = Column(Integer)
    raw_data = Column(Text, nullable=False)
    details = Column(JSON)

    payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"))
    pub_eft_id = Column(PostgreSQLUUID, ForeignKey("pub_eft.pub_eft_id"))

    import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True, nullable=False
    )
    reference_file_id = Column(
        PostgreSQLUUID,
        ForeignKey("reference_file.reference_file_id"),
        primary_key=True,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        onupdate=utc_timestamp_gen,
        server_default=sqlnow(),
    )

    pub_error_type = relationship("LkPubErrorType")
    payment = relationship("Payment")
    pub_eft = relationship("PubEft")
    import_log = relationship("ImportLog")
    reference_file = relationship("ReferenceFile")


class LkPubErrorType(Base):
    __tablename__ = "lk_pub_error_type"
    pub_error_type_id = Column(Integer, primary_key=True, autoincrement=True)
    pub_error_type_description = Column(Text)

    def __init__(self, pub_error_type_id, pub_error_type_description):
        self.pub_error_type_id = pub_error_type_id
        self.pub_error_type_description = pub_error_type_description


class PubErrorType(LookupTable):
    model = LkPubErrorType
    column_names = ("pub_error_type_id", "pub_error_type_description")

    ACH_WARNING = LkPubErrorType(1, "ACH Warning")
    ACH_RETURN = LkPubErrorType(2, "ACH Return")
    ACH_PRENOTE = LkPubErrorType(3, "ACH Prenote")
    ACH_NOTIFICATION = LkPubErrorType(4, "ACH Notification")
    ACH_SUCCESS_WITH_NOTIFICATION = LkPubErrorType(5, "ACH Success with Notification")
    CHECK_PAYMENT_LINE_ERROR = LkPubErrorType(6, "Check payment line error")
    CHECK_PAYMENT_ERROR = LkPubErrorType(7, "Check payment error")
    CHECK_PAYMENT_FAILED = LkPubErrorType(8, "Check payment failed")


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
    MILITARY_LEAVE = LkClaimType(3, "Military Leave")


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
    column_names = ("occupation_id", "occupation_description", "occupation_code",)

    # HEALTH_CARE = LkOccupation(1, "Health Care")
    # SALES_CLERK = LkOccupation(2, "Sales Clerk")
    # ADMINISTRATIVE = LkOccupation(3, "Administrative")
    # ENGINEER = LkOccupation(4, "Engineer")

    # NAICS Occupations -> https://www.naics.com/search/
    AGRICULTURE_FORESTRY_FISHING_HUNTING = LkOccupation(
        1, "Agriculture, Forestry, Fishing and Hunting", 11
    )
    MINING = LkOccupation(2, "Mining", 21)
    UTILITIES = LkOccupation(3, "Utilities", 22)
    CONSTRUCTION = LkOccupation(4, "Construction", 23)
    MANUFACTURING = LkOccupation(5, "Manufacturing", 31)  # -33
    WHOLESALE_TRADE = LkOccupation(6, "Wholesale Trade", 42)
    RETAIL_TRADE = LkOccupation(7, "Retail Trade", 44)  # -45
    TRANSPORTATION_WAREHOUSING = LkOccupation(8, "Transportation and Warehousing", 48)  # -49
    INFORMATION = LkOccupation(9, "Information", 51)
    FINANCE_INSURANCE = LkOccupation(10, "Finance and Insurance", 52)
    REAL_ESTATE_RENTAL_LEASING = LkOccupation(11, "Real Estate Rental and Leasing", 53)
    PROFESSIONAL_SCIENTIFIC_TECHNICAL = LkOccupation(
        12, "Professional, Scientific, and Technical Services", 54
    )
    MANAGEMENT_COMPANIES_ENTERPRISES = LkOccupation(13, "Management of Companies and Enterprises", 55)
    ADMINISTRATIVE_SUPPORT_WASTE_MANAGEMENT_REMEDIATION = LkOccupation(
        14, "Administrative and Support and Waste Management and Remediation Services", 56
    )
    EDUCATIONAL = LkOccupation(15, "Educational Services", 61)
    HEALTH_CARE_SOCIAL_ASSISTANCE = LkOccupation(16, "Health Care and Social Assistance", 62)
    ARTS_ENTERTAINMENT_RECREATION = LkOccupation(17, "Arts, Entertainment, and Recreation", 71)
    ACCOMMODATION_FOOD_SERVICES = LkOccupation(18, "Accommodation and Food Services", 72)
    OTHER_SERVICES = LkOccupation(19, "Other Services (except Public Administration)", 81)
    PUBLIC_ADMINISTRATION = LkOccupation(20, "Public Administration", 92)

class OccupationTitle(LookupTable):
    model = LkOccupationTitle
    column_names = ("occupation_title_id", "occupation_title_description", "occupation_code", "occupation_title_code")
    OILSEED_AND_GRAIN_FARMING = LkOccupationTitle(1, "Oilseed and Grain Farming", 11, 1111)
    SOYBEAN_FARMING = LkOccupationTitle(1, "Soybean Farming", 11, 111110)
    OILSEED_EXCEPT_SOYBEAN_FARMING = LkOccupationTitle(1, "Oilseed (except Soybean) Farming", 11, 111120)
    DRY_PEA_AND_BEAN_FARMING = LkOccupationTitle(1, "Dry Pea and Bean Farming", 11, 111130)
    WHEAT_FARMING = LkOccupationTitle(1, "Wheat Farming", 11, 111140)
    CORN_FARMING = LkOccupationTitle(1, "Corn Farming", 11, 111150)
    RICE_FARMING = LkOccupationTitle(1, "Rice Farming", 11, 111160)
    OILSEED_AND_GRAIN_COMBINATION_FARMING = LkOccupationTitle(1, "Oilseed and Grain Combination Farming", 11, 111191)
    ALL_OTHER_GRAIN_FARMING = LkOccupationTitle(1, "All Other Grain Farming", 11, 111199)
    VEGETABLE_AND_MELON_FARMING = LkOccupationTitle(1, "Vegetable and Melon Farming", 11, 1112)
    POTATO_FARMING = LkOccupationTitle(1, "Potato Farming", 11, 111211)
    OTHER_VEGETABLE_EXCEPT_POTATO_AND_MELON_FARMING = LkOccupationTitle(1, "Other Vegetable (except Potato) and Melon Farming", 11, 111219)
    FRUIT_AND_TREE_NUT_FARMING = LkOccupationTitle(1, "Fruit and Tree Nut Farming", 11, 1113)
    ORANGE_GROVES = LkOccupationTitle(1, "Orange Groves", 11, 111310)
    CITRUS_EXCEPT_ORANGE_GROVES = LkOccupationTitle(1, "Citrus (except Orange) Groves", 11, 111320)
    APPLE_ORCHARDS = LkOccupationTitle(1, "Apple Orchards", 11, 111331)
    GRAPE_VINEYARDS = LkOccupationTitle(1, "Grape Vineyards", 11, 111332)
    STRAWBERRY_FARMING = LkOccupationTitle(1, "Strawberry Farming", 11, 111333)
    BERRY_EXCEPT_STRAWBERRY_FARMING = LkOccupationTitle(1, "Berry (except Strawberry) Farming", 11, 111334)
    TREE_NUT_FARMING = LkOccupationTitle(1, "Tree Nut Farming", 11, 111335)
    FRUIT_AND_TREE_NUT_COMBINATION_FARMING = LkOccupationTitle(1, "Fruit and Tree Nut Combination Farming", 11, 111336)
    OTHER_NONCITRUS_FRUIT_FARMING = LkOccupationTitle(1, "Other Noncitrus Fruit Farming", 11, 111339)
    GREENHOUSE_NURSERY_AND_FLORICULTURE_PRODUCTION = LkOccupationTitle(1, "Greenhouse, Nursery, and Floriculture Production", 11, 1114)
    MUSHROOM_PRODUCTION = LkOccupationTitle(1, "Mushroom Production", 11, 111411)
    OTHER_FOOD_CROPS_GROWN_UNDER_COVER = LkOccupationTitle(1, "Other Food Crops Grown Under Cover", 11, 111419)
    NURSERY_AND_TREE_PRODUCTION = LkOccupationTitle(1, "Nursery and Tree Production", 11, 111421)
    FLORICULTURE_PRODUCTION = LkOccupationTitle(1, "Floriculture Production", 11, 111422)
    OTHER_CROP_FARMING = LkOccupationTitle(1, "Other Crop Farming", 11, 1119)
    TOBACCO_FARMING = LkOccupationTitle(1, "Tobacco Farming", 11, 111910)
    COTTON_FARMING = LkOccupationTitle(1, "Cotton Farming", 11, 111920)
    SUGARCANE_FARMING = LkOccupationTitle(1, "Sugarcane Farming", 11, 111930)
    HAY_FARMING = LkOccupationTitle(1, "Hay Farming", 11, 111940)
    SUGAR_BEET_FARMING = LkOccupationTitle(1, "Sugar Beet Farming", 11, 111991)
    PEANUT_FARMING = LkOccupationTitle(1, "Peanut Farming", 11, 111992)
    ALL_OTHER_MISCELLANEOUS_CROP_FARMING = LkOccupationTitle(1, "All Other Miscellaneous Crop Farming", 11, 111998)
    CATTLE_RANCHING_AND_FARMING = LkOccupationTitle(1, "Cattle Ranching and Farming", 11, 1121)
    BEEF_CATTLE_RANCHING_AND_FARMING = LkOccupationTitle(1, "Beef Cattle Ranching and Farming", 11, 112111)
    CATTLE_FEEDLOTS = LkOccupationTitle(1, "Cattle Feedlots", 11, 112112)
    DAIRY_CATTLE_AND_MILK_PRODUCTION = LkOccupationTitle(1, "Dairy Cattle and Milk Production", 11, 112120)
    DUALPURPOSE_CATTLE_RANCHING_AND_FARMING = LkOccupationTitle(1, "Dual-Purpose Cattle Ranching and Farming", 11, 112130)
    HOG_AND_PIG_FARMING = LkOccupationTitle(1, "Hog and Pig Farming", 11, 1122)
    HOG_AND_PIG_FARMING = LkOccupationTitle(1, "Hog and Pig Farming", 11, 112210)
    POULTRY_AND_EGG_PRODUCTION = LkOccupationTitle(1, "Poultry and Egg Production", 11, 1123)
    CHICKEN_EGG_PRODUCTION = LkOccupationTitle(1, "Chicken Egg Production", 11, 112310)
    BROILERS_AND_OTHER_MEAT_TYPE_CHICKEN_PRODUCTION = LkOccupationTitle(1, "Broilers and Other Meat Type Chicken Production", 11, 112320)
    TURKEY_PRODUCTION = LkOccupationTitle(1, "Turkey Production", 11, 112330)
    POULTRY_HATCHERIES = LkOccupationTitle(1, "Poultry Hatcheries", 11, 112340)
    OTHER_POULTRY_PRODUCTION = LkOccupationTitle(1, "Other Poultry Production", 11, 112390)
    SHEEP_AND_GOAT_FARMING = LkOccupationTitle(1, "Sheep and Goat Farming", 11, 1124)
    SHEEP_FARMING = LkOccupationTitle(1, "Sheep Farming", 11, 112410)
    GOAT_FARMING = LkOccupationTitle(1, "Goat Farming", 11, 112420)
    AQUACULTURE = LkOccupationTitle(1, "Aquaculture", 11, 1125)
    FINFISH_FARMING_AND_FISH_HATCHERIES = LkOccupationTitle(1, "Finfish Farming and Fish Hatcheries", 11, 112511)
    SHELLFISH_FARMING = LkOccupationTitle(1, "Shellfish Farming", 11, 112512)
    OTHER_AQUACULTURE = LkOccupationTitle(1, "Other Aquaculture", 11, 112519)
    OTHER_ANIMAL_PRODUCTION = LkOccupationTitle(1, "Other Animal Production", 11, 1129)
    APICULTURE = LkOccupationTitle(1, "Apiculture", 11, 112910)
    HORSES_AND_OTHER_EQUINE_PRODUCTION = LkOccupationTitle(1, "Horses and Other Equine Production", 11, 112920)
    FURBEARING_ANIMAL_AND_RABBIT_PRODUCTION = LkOccupationTitle(1, "Fur-Bearing Animal and Rabbit Production", 11, 112930)
    ALL_OTHER_ANIMAL_PRODUCTION = LkOccupationTitle(1, "All Other Animal Production", 11, 112990)
    TIMBER_TRACT_OPERATIONS = LkOccupationTitle(1, "Timber Tract Operations", 11, 1131)
    TIMBER_TRACT_OPERATIONS = LkOccupationTitle(1, "Timber Tract Operations", 11, 113110)
    FOREST_NURSERIES_AND_GATHERING_OF_FOREST_PRODUCTS = LkOccupationTitle(1, "Forest Nurseries and Gathering of Forest Products", 11, 1132)
    FOREST_NURSERIES_AND_GATHERING_OF_FOREST_PRODUCTS = LkOccupationTitle(1, "Forest Nurseries and Gathering of Forest Products", 11, 113210)
    LOGGING = LkOccupationTitle(1, "Logging", 11, 1133)
    LOGGING = LkOccupationTitle(1, "Logging", 11, 113310)
    FISHING = LkOccupationTitle(1, "Fishing", 11, 1141)
    FINFISH_FISHING = LkOccupationTitle(1, "Finfish Fishing", 11, 114111)
    SHELLFISH_FISHING = LkOccupationTitle(1, "Shellfish Fishing", 11, 114112)
    OTHER_MARINE_FISHING = LkOccupationTitle(1, "Other Marine Fishing", 11, 114119)
    HUNTING_AND_TRAPPING = LkOccupationTitle(1, "Hunting and Trapping", 11, 1142)
    HUNTING_AND_TRAPPING = LkOccupationTitle(1, "Hunting and Trapping", 11, 114210)
    SUPPORT_ACTIVITIES_FOR_CROP_PRODUCTION = LkOccupationTitle(1, "Support Activities for Crop Production", 11, 1151)
    COTTON_GINNING = LkOccupationTitle(1, "Cotton Ginning", 11, 115111)
    SOIL_PREPARATION_PLANTING_AND_CULTIVATING = LkOccupationTitle(1, "Soil Preparation, Planting, and Cultivating", 11, 115112)
    CROP_HARVESTING_PRIMARILY_BY_MACHINE = LkOccupationTitle(1, "Crop Harvesting, Primarily by Machine", 11, 115113)
    POSTHARVEST_CROP_ACTIVITIES_EXCEPT_COTTON_GINNING = LkOccupationTitle(1, "Postharvest Crop Activities (except Cotton Ginning)", 11, 115114)
    FARM_LABOR_CONTRACTORS_AND_CREW_LEADERS = LkOccupationTitle(1, "Farm Labor Contractors and Crew Leaders", 11, 115115)
    FARM_MANAGEMENT_SERVICES = LkOccupationTitle(1, "Farm Management Services", 11, 115116)
    SUPPORT_ACTIVITIES_FOR_ANIMAL_PRODUCTION = LkOccupationTitle(1, "Support Activities for Animal Production", 11, 1152)
    SUPPORT_ACTIVITIES_FOR_ANIMAL_PRODUCTION = LkOccupationTitle(1, "Support Activities for Animal Production", 11, 115210)
    SUPPORT_ACTIVITIES_FOR_FORESTRY = LkOccupationTitle(1, "Support Activities for Forestry", 11, 1153)
    SUPPORT_ACTIVITIES_FOR_FORESTRY = LkOccupationTitle(1, "Support Activities for Forestry", 11, 115310)
    OIL_AND_GAS_EXTRACTION = LkOccupationTitle(1, "Oil and Gas Extraction", 21, 2111)
    CRUDE_PETROLEUM_EXTRACTION = LkOccupationTitle(1, "Crude Petroleum Extraction", 21, 211120)
    NATURAL_GAS_EXTRACTION = LkOccupationTitle(1, "Natural Gas Extraction", 21, 211130)
    COAL_MINING = LkOccupationTitle(1, "Coal Mining", 21, 2121)
    BITUMINOUS_COAL_AND_LIGNITE_SURFACE_MINING = LkOccupationTitle(1, "Bituminous Coal and Lignite Surface Mining", 21, 212111)
    BITUMINOUS_COAL_UNDERGROUND_MINING = LkOccupationTitle(1, "Bituminous Coal Underground Mining", 21, 212112)
    ANTHRACITE_MINING = LkOccupationTitle(1, "Anthracite Mining", 21, 212113)
    METAL_ORE_MINING = LkOccupationTitle(1, "Metal Ore Mining", 21, 2122)
    IRON_ORE_MINING = LkOccupationTitle(1, "Iron Ore Mining", 21, 212210)
    GOLD_ORE_MINING = LkOccupationTitle(1, "Gold Ore Mining", 21, 212221)
    SILVER_ORE_MINING = LkOccupationTitle(1, "Silver Ore Mining", 21, 212222)
    COPPER_NICKEL_LEAD_AND_ZINC_MINING = LkOccupationTitle(1, "Copper, Nickel, Lead, and Zinc Mining", 21, 212230)
    URANIUMRADIUMVANADIUM_ORE_MINING = LkOccupationTitle(1, "Uranium-Radium-Vanadium Ore Mining", 21, 212291)
    ALL_OTHER_METAL_ORE_MINING = LkOccupationTitle(1, "All Other Metal Ore Mining", 21, 212299)
    NONMETALLIC_MINERAL_MINING_AND_QUARRYING = LkOccupationTitle(1, "Nonmetallic Mineral Mining and Quarrying", 21, 2123)
    DIMENSION_STONE_MINING_AND_QUARRYING = LkOccupationTitle(1, "Dimension Stone Mining and Quarrying", 21, 212311)
    CRUSHED_AND_BROKEN_LIMESTONE_MINING_AND_QUARRYING = LkOccupationTitle(1, "Crushed and Broken Limestone Mining and Quarrying", 21, 212312)
    CRUSHED_AND_BROKEN_GRANITE_MINING_AND_QUARRYING = LkOccupationTitle(1, "Crushed and Broken Granite Mining and Quarrying", 21, 212313)
    OTHER_CRUSHED_AND_BROKEN_STONE_MINING_AND_QUARRYING = LkOccupationTitle(1, "Other Crushed and Broken Stone Mining and Quarrying", 21, 212319)
    CONSTRUCTION_SAND_AND_GRAVEL_MINING = LkOccupationTitle(1, "Construction Sand and Gravel Mining", 21, 212321)
    INDUSTRIAL_SAND_MINING = LkOccupationTitle(1, "Industrial Sand Mining", 21, 212322)
    KAOLIN_AND_BALL_CLAY_MINING = LkOccupationTitle(1, "Kaolin and Ball Clay Mining", 21, 212324)
    CLAY_AND_CERAMIC_AND_REFRACTORY_MINERALS_MINING = LkOccupationTitle(1, "Clay and Ceramic and Refractory Minerals Mining", 21, 212325)
    POTASH_SODA_AND_BORATE_MINERAL_MINING = LkOccupationTitle(1, "Potash, Soda, and Borate Mineral Mining", 21, 212391)
    PHOSPHATE_ROCK_MINING = LkOccupationTitle(1, "Phosphate Rock Mining", 21, 212392)
    OTHER_CHEMICAL_AND_FERTILIZER_MINERAL_MINING = LkOccupationTitle(1, "Other Chemical and Fertilizer Mineral Mining", 21, 212393)
    ALL_OTHER_NONMETALLIC_MINERAL_MINING = LkOccupationTitle(1, "All Other Nonmetallic Mineral Mining", 21, 212399)
    SUPPORT_ACTIVITIES_FOR_MINING = LkOccupationTitle(1, "Support Activities for Mining", 21, 2131)
    DRILLING_OIL_AND_GAS_WELLS = LkOccupationTitle(1, "Drilling Oil and Gas Wells", 21, 213111)
    SUPPORT_ACTIVITIES_FOR_OIL_AND_GAS_OPERATIONS = LkOccupationTitle(1, "Support Activities for Oil and Gas Operations", 21, 213112)
    SUPPORT_ACTIVITIES_FOR_COAL_MINING = LkOccupationTitle(1, "Support Activities for Coal Mining", 21, 213113)
    SUPPORT_ACTIVITIES_FOR_METAL_MINING = LkOccupationTitle(1, "Support Activities for Metal Mining", 21, 213114)
    SUPPORT_ACTIVITIES_FOR_NONMETALLIC_MINERALS_EXCEPT_FUELS_MINING = LkOccupationTitle(1, "Support Activities for Nonmetallic Minerals (except Fuels) Mining", 21, 213115)
    ELECTRIC_POWER_GENERATION_TRANSMISSION_AND_DISTRIBUTION = LkOccupationTitle(1, "Electric Power Generation, Transmission and Distribution", 22, 2211)
    HYDROELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Hydroelectric Power Generation", 22, 221111)
    FOSSIL_FUEL_ELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Fossil Fuel Electric Power Generation", 22, 221112)
    NUCLEAR_ELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Nuclear Electric Power Generation", 22, 221113)
    SOLAR_ELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Solar Electric Power Generation", 22, 221114)
    WIND_ELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Wind Electric Power Generation", 22, 221115)
    GEOTHERMAL_ELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Geothermal Electric Power Generation", 22, 221116)
    BIOMASS_ELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Biomass Electric Power Generation", 22, 221117)
    OTHER_ELECTRIC_POWER_GENERATION = LkOccupationTitle(1, "Other Electric Power Generation", 22, 221118)
    ELECTRIC_BULK_POWER_TRANSMISSION_AND_CONTROL = LkOccupationTitle(1, "Electric Bulk Power Transmission and Control", 22, 221121)
    ELECTRIC_POWER_DISTRIBUTION = LkOccupationTitle(1, "Electric Power Distribution", 22, 221122)
    NATURAL_GAS_DISTRIBUTION = LkOccupationTitle(1, "Natural Gas Distribution", 22, 2212)
    NATURAL_GAS_DISTRIBUTION = LkOccupationTitle(1, "Natural Gas Distribution", 22, 221210)
    WATER_SEWAGE_AND_OTHER_SYSTEMS = LkOccupationTitle(1, "Water, Sewage and Other Systems", 22, 2213)
    WATER_SUPPLY_AND_IRRIGATION_SYSTEMS = LkOccupationTitle(1, "Water Supply and Irrigation Systems", 22, 221310)
    SEWAGE_TREATMENT_FACILITIES = LkOccupationTitle(1, "Sewage Treatment Facilities", 22, 221320)
    STEAM_AND_AIRCONDITIONING_SUPPLY = LkOccupationTitle(1, "Steam and Air-Conditioning Supply", 22, 221330)
    RESIDENTIAL_BUILDING_CONSTRUCTION = LkOccupationTitle(1, "Residential Building Construction", 23, 2361)
    NEW_SINGLEFAMILY_HOUSING_CONSTRUCTION_EXCEPT_FORSALE_BUILDERS = LkOccupationTitle(1, "New Single-Family Housing Construction (except For-Sale Builders)", 23, 236115)
    NEW_MULTIFAMILY_HOUSING_CONSTRUCTION_EXCEPT_FORSALE_BUILDERS = LkOccupationTitle(1, "New Multifamily Housing Construction (except For-Sale Builders)", 23, 236116)
    NEW_HOUSING_FORSALE_BUILDERS = LkOccupationTitle(1, "New Housing For-Sale Builders", 23, 236117)
    RESIDENTIAL_REMODELERS = LkOccupationTitle(1, "Residential Remodelers", 23, 236118)
    NONRESIDENTIAL_BUILDING_CONSTRUCTION = LkOccupationTitle(1, "Nonresidential Building Construction", 23, 2362)
    INDUSTRIAL_BUILDING_CONSTRUCTION = LkOccupationTitle(1, "Industrial Building Construction", 23, 236210)
    COMMERCIAL_AND_INSTITUTIONAL_BUILDING_CONSTRUCTION = LkOccupationTitle(1, "Commercial and Institutional Building Construction", 23, 236220)
    UTILITY_SYSTEM_CONSTRUCTION = LkOccupationTitle(1, "Utility System Construction", 23, 2371)
    WATER_AND_SEWER_LINE_AND_RELATED_STRUCTURES_CONSTRUCTION = LkOccupationTitle(1, "Water and Sewer Line and Related Structures Construction", 23, 237110)
    OIL_AND_GAS_PIPELINE_AND_RELATED_STRUCTURES_CONSTRUCTION = LkOccupationTitle(1, "Oil and Gas Pipeline and Related Structures Construction", 23, 237120)
    POWER_AND_COMMUNICATION_LINE_AND_RELATED_STRUCTURES_CONSTRUCTION = LkOccupationTitle(1, "Power and Communication Line and Related Structures Construction", 23, 237130)
    LAND_SUBDIVISION = LkOccupationTitle(1, "Land Subdivision", 23, 2372)
    LAND_SUBDIVISION = LkOccupationTitle(1, "Land Subdivision", 23, 237210)
    HIGHWAY_STREET_AND_BRIDGE_CONSTRUCTION = LkOccupationTitle(1, "Highway, Street, and Bridge Construction", 23, 2373)
    HIGHWAY_STREET_AND_BRIDGE_CONSTRUCTION = LkOccupationTitle(1, "Highway, Street, and Bridge Construction", 23, 237310)
    OTHER_HEAVY_AND_CIVIL_ENGINEERING_CONSTRUCTION = LkOccupationTitle(1, "Other Heavy and Civil Engineering Construction", 23, 2379)
    OTHER_HEAVY_AND_CIVIL_ENGINEERING_CONSTRUCTION = LkOccupationTitle(1, "Other Heavy and Civil Engineering Construction", 23, 237990)
    FOUNDATION_STRUCTURE_AND_BUILDING_EXTERIOR_CONTRACTORS = LkOccupationTitle(1, "Foundation, Structure, and Building Exterior Contractors", 23, 2381)
    POURED_CONCRETE_FOUNDATION_AND_STRUCTURE_CONTRACTORS = LkOccupationTitle(1, "Poured Concrete Foundation and Structure Contractors", 23, 238110)
    STRUCTURAL_STEEL_AND_PRECAST_CONCRETE_CONTRACTORS = LkOccupationTitle(1, "Structural Steel and Precast Concrete Contractors", 23, 238120)
    FRAMING_CONTRACTORS = LkOccupationTitle(1, "Framing Contractors", 23, 238130)
    MASONRY_CONTRACTORS = LkOccupationTitle(1, "Masonry Contractors", 23, 238140)
    GLASS_AND_GLAZING_CONTRACTORS = LkOccupationTitle(1, "Glass and Glazing Contractors", 23, 238150)
    ROOFING_CONTRACTORS = LkOccupationTitle(1, "Roofing Contractors", 23, 238160)
    SIDING_CONTRACTORS = LkOccupationTitle(1, "Siding Contractors", 23, 238170)
    OTHER_FOUNDATION_STRUCTURE_AND_BUILDING_EXTERIOR_CONTRACTORS = LkOccupationTitle(1, "Other Foundation, Structure, and Building Exterior Contractors", 23, 238190)
    BUILDING_EQUIPMENT_CONTRACTORS = LkOccupationTitle(1, "Building Equipment Contractors", 23, 2382)
    ELECTRICAL_CONTRACTORS_AND_OTHER_WIRING_INSTALLATION_CONTRACTORS = LkOccupationTitle(1, "Electrical Contractors and Other Wiring Installation Contractors", 23, 238210)
    PLUMBING_HEATING_AND_AIRCONDITIONING_CONTRACTORS = LkOccupationTitle(1, "Plumbing, Heating, and Air-Conditioning Contractors", 23, 238220)
    OTHER_BUILDING_EQUIPMENT_CONTRACTORS = LkOccupationTitle(1, "Other Building Equipment Contractors", 23, 238290)
    BUILDING_FINISHING_CONTRACTORS = LkOccupationTitle(1, "Building Finishing Contractors", 23, 2383)
    DRYWALL_AND_INSULATION_CONTRACTORS = LkOccupationTitle(1, "Drywall and Insulation Contractors", 23, 238310)
    PAINTING_AND_WALL_COVERING_CONTRACTORS = LkOccupationTitle(1, "Painting and Wall Covering Contractors", 23, 238320)
    FLOORING_CONTRACTORS = LkOccupationTitle(1, "Flooring Contractors", 23, 238330)
    TILE_AND_TERRAZZO_CONTRACTORS = LkOccupationTitle(1, "Tile and Terrazzo Contractors", 23, 238340)
    FINISH_CARPENTRY_CONTRACTORS = LkOccupationTitle(1, "Finish Carpentry Contractors", 23, 238350)
    OTHER_BUILDING_FINISHING_CONTRACTORS = LkOccupationTitle(1, "Other Building Finishing Contractors", 23, 238390)
    OTHER_SPECIALTY_TRADE_CONTRACTORS = LkOccupationTitle(1, "Other Specialty Trade Contractors", 23, 2389)
    SITE_PREPARATION_CONTRACTORS = LkOccupationTitle(1, "Site Preparation Contractors", 23, 238910)
    ALL_OTHER_SPECIALTY_TRADE_CONTRACTORS = LkOccupationTitle(1, "All Other Specialty Trade Contractors", 23, 238990)
    MANUFACTURING = LkOccupationTitle(1, "Manufacturing", 31, 31-33)
    ANIMAL_FOOD_MANUFACTURING = LkOccupationTitle(1, "Animal Food Manufacturing", 31, 3111)
    DOG_AND_CAT_FOOD_MANUFACTURING = LkOccupationTitle(1, "Dog and Cat Food Manufacturing", 31, 311111)
    OTHER_ANIMAL_FOOD_MANUFACTURING = LkOccupationTitle(1, "Other Animal Food Manufacturing", 31, 311119)
    GRAIN_AND_OILSEED_MILLING = LkOccupationTitle(1, "Grain and Oilseed Milling", 31, 3112)
    FLOUR_MILLING = LkOccupationTitle(1, "Flour Milling", 31, 311211)
    RICE_MILLING = LkOccupationTitle(1, "Rice Milling", 31, 311212)
    MALT_MANUFACTURING = LkOccupationTitle(1, "Malt Manufacturing", 31, 311213)
    WET_CORN_MILLING = LkOccupationTitle(1, "Wet Corn Milling", 31, 311221)
    SOYBEAN_AND_OTHER_OILSEED_PROCESSING = LkOccupationTitle(1, "Soybean and Other Oilseed Processing", 31, 311224)
    FATS_AND_OILS_REFINING_AND_BLENDING = LkOccupationTitle(1, "Fats and Oils Refining and Blending", 31, 311225)
    BREAKFAST_CEREAL_MANUFACTURING = LkOccupationTitle(1, "Breakfast Cereal Manufacturing", 31, 311230)
    SUGAR_AND_CONFECTIONERY_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Sugar and Confectionery Product Manufacturing", 31, 3113)
    BEET_SUGAR_MANUFACTURING = LkOccupationTitle(1, "Beet Sugar Manufacturing", 31, 311313)
    CANE_SUGAR_MANUFACTURING = LkOccupationTitle(1, "Cane Sugar Manufacturing", 31, 311314)
    NONCHOCOLATE_CONFECTIONERY_MANUFACTURING = LkOccupationTitle(1, "Nonchocolate Confectionery Manufacturing", 31, 311340)
    CHOCOLATE_AND_CONFECTIONERY_MANUFACTURING_FROM_CACAO_BEANS = LkOccupationTitle(1, "Chocolate and Confectionery Manufacturing from Cacao Beans", 31, 311351)
    CONFECTIONERY_MANUFACTURING_FROM_PURCHASED_CHOCOLATE = LkOccupationTitle(1, "Confectionery Manufacturing from Purchased Chocolate", 31, 311352)
    FRUIT_AND_VEGETABLE_PRESERVING_AND_SPECIALTY_FOOD_MANUFACTURING = LkOccupationTitle(1, "Fruit and Vegetable Preserving and Specialty Food Manufacturing", 31, 3114)
    FROZEN_FRUIT_JUICE_AND_VEGETABLE_MANUFACTURING = LkOccupationTitle(1, "Frozen Fruit, Juice, and Vegetable Manufacturing", 31, 311411)
    FROZEN_SPECIALTY_FOOD_MANUFACTURING = LkOccupationTitle(1, "Frozen Specialty Food Manufacturing", 31, 311412)
    FRUIT_AND_VEGETABLE_CANNING = LkOccupationTitle(1, "Fruit and Vegetable Canning", 31, 311421)
    SPECIALTY_CANNING = LkOccupationTitle(1, "Specialty Canning", 31, 311422)
    DRIED_AND_DEHYDRATED_FOOD_MANUFACTURING = LkOccupationTitle(1, "Dried and Dehydrated Food Manufacturing", 31, 311423)
    DAIRY_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Dairy Product Manufacturing", 31, 3115)
    FLUID_MILK_MANUFACTURING = LkOccupationTitle(1, "Fluid Milk Manufacturing", 31, 311511)
    CREAMERY_BUTTER_MANUFACTURING = LkOccupationTitle(1, "Creamery Butter Manufacturing", 31, 311512)
    CHEESE_MANUFACTURING = LkOccupationTitle(1, "Cheese Manufacturing", 31, 311513)
    DRY_CONDENSED_AND_EVAPORATED_DAIRY_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Dry, Condensed, and Evaporated Dairy Product Manufacturing", 31, 311514)
    ICE_CREAM_AND_FROZEN_DESSERT_MANUFACTURING = LkOccupationTitle(1, "Ice Cream and Frozen Dessert Manufacturing", 31, 311520)
    ANIMAL_SLAUGHTERING_AND_PROCESSING = LkOccupationTitle(1, "Animal Slaughtering and Processing", 31, 3116)
    ANIMAL_EXCEPT_POULTRY_SLAUGHTERING = LkOccupationTitle(1, "Animal (except Poultry) Slaughtering", 31, 311611)
    MEAT_PROCESSED_FROM_CARCASSES = LkOccupationTitle(1, "Meat Processed from Carcasses", 31, 311612)
    RENDERING_AND_MEAT_BYPRODUCT_PROCESSING = LkOccupationTitle(1, "Rendering and Meat Byproduct Processing", 31, 311613)
    POULTRY_PROCESSING = LkOccupationTitle(1, "Poultry Processing", 31, 311615)
    SEAFOOD_PRODUCT_PREPARATION_AND_PACKAGING = LkOccupationTitle(1, "Seafood Product Preparation and Packaging", 31, 3117)
    SEAFOOD_PRODUCT_PREPARATION_AND_PACKAGING = LkOccupationTitle(1, "Seafood Product Preparation and Packaging", 31, 311710)
    BAKERIES_AND_TORTILLA_MANUFACTURING = LkOccupationTitle(1, "Bakeries and Tortilla Manufacturing", 31, 3118)
    RETAIL_BAKERIES = LkOccupationTitle(1, "Retail Bakeries", 31, 311811)
    COMMERCIAL_BAKERIES = LkOccupationTitle(1, "Commercial Bakeries", 31, 311812)
    FROZEN_CAKES_PIES_AND_OTHER_PASTRIES_MANUFACTURING = LkOccupationTitle(1, "Frozen Cakes, Pies, and Other Pastries Manufacturing", 31, 311813)
    COOKIE_AND_CRACKER_MANUFACTURING = LkOccupationTitle(1, "Cookie and Cracker Manufacturing", 31, 311821)
    DRY_PASTA_DOUGH_AND_FLOUR_MIXES_MANUFACTURING_FROM_PURCHASED_FLOUR = LkOccupationTitle(1, "Dry Pasta, Dough, and Flour Mixes Manufacturing from Purchased Flour", 31, 311824)
    TORTILLA_MANUFACTURING = LkOccupationTitle(1, "Tortilla Manufacturing", 31, 311830)
    OTHER_FOOD_MANUFACTURING = LkOccupationTitle(1, "Other Food Manufacturing", 31, 3119)
    ROASTED_NUTS_AND_PEANUT_BUTTER_MANUFACTURING = LkOccupationTitle(1, "Roasted Nuts and Peanut Butter Manufacturing", 31, 311911)
    OTHER_SNACK_FOOD_MANUFACTURING = LkOccupationTitle(1, "Other Snack Food Manufacturing", 31, 311919)
    COFFEE_AND_TEA_MANUFACTURING = LkOccupationTitle(1, "Coffee and Tea Manufacturing", 31, 311920)
    FLAVORING_SYRUP_AND_CONCENTRATE_MANUFACTURING = LkOccupationTitle(1, "Flavoring Syrup and Concentrate Manufacturing", 31, 311930)
    MAYONNAISE_DRESSING_AND_OTHER_PREPARED_SAUCE_MANUFACTURING = LkOccupationTitle(1, "Mayonnaise, Dressing, and Other Prepared Sauce Manufacturing", 31, 311941)
    SPICE_AND_EXTRACT_MANUFACTURING = LkOccupationTitle(1, "Spice and Extract Manufacturing", 31, 311942)
    PERISHABLE_PREPARED_FOOD_MANUFACTURING = LkOccupationTitle(1, "Perishable Prepared Food Manufacturing", 31, 311991)
    ALL_OTHER_MISCELLANEOUS_FOOD_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous Food Manufacturing", 31, 311999)
    BEVERAGE_MANUFACTURING = LkOccupationTitle(1, "Beverage Manufacturing", 31, 3121)
    SOFT_DRINK_MANUFACTURING = LkOccupationTitle(1, "Soft Drink Manufacturing", 31, 312111)
    BOTTLED_WATER_MANUFACTURING = LkOccupationTitle(1, "Bottled Water Manufacturing", 31, 312112)
    ICE_MANUFACTURING = LkOccupationTitle(1, "Ice Manufacturing", 31, 312113)
    BREWERIES = LkOccupationTitle(1, "Breweries", 31, 312120)
    WINERIES = LkOccupationTitle(1, "Wineries", 31, 312130)
    DISTILLERIES = LkOccupationTitle(1, "Distilleries", 31, 312140)
    TOBACCO_MANUFACTURING = LkOccupationTitle(1, "Tobacco Manufacturing", 31, 3122)
    TOBACCO_MANUFACTURING = LkOccupationTitle(1, "Tobacco Manufacturing", 31, 312230)
    FIBER_YARN_AND_THREAD_MILLS = LkOccupationTitle(1, "Fiber, Yarn, and Thread Mills", 31, 3131)
    FIBER_YARN_AND_THREAD_MILLS = LkOccupationTitle(1, "Fiber, Yarn, and Thread Mills", 31, 313110)
    FABRIC_MILLS = LkOccupationTitle(1, "Fabric Mills", 31, 3132)
    BROADWOVEN_FABRIC_MILLS = LkOccupationTitle(1, "Broadwoven Fabric Mills", 31, 313210)
    NARROW_FABRIC_MILLS_AND_SCHIFFLI_MACHINE_EMBROIDERY = LkOccupationTitle(1, "Narrow Fabric Mills and Schiffli Machine Embroidery", 31, 313220)
    NONWOVEN_FABRIC_MILLS = LkOccupationTitle(1, "Nonwoven Fabric Mills", 31, 313230)
    KNIT_FABRIC_MILLS = LkOccupationTitle(1, "Knit Fabric Mills", 31, 313240)
    TEXTILE_AND_FABRIC_FINISHING_AND_FABRIC_COATING_MILLS = LkOccupationTitle(1, "Textile and Fabric Finishing and Fabric Coating Mills", 31, 3133)
    TEXTILE_AND_FABRIC_FINISHING_MILLS = LkOccupationTitle(1, "Textile and Fabric Finishing Mills", 31, 313310)
    FABRIC_COATING_MILLS = LkOccupationTitle(1, "Fabric Coating Mills", 31, 313320)
    TEXTILE_FURNISHINGS_MILLS = LkOccupationTitle(1, "Textile Furnishings Mills", 31, 3141)
    CARPET_AND_RUG_MILLS = LkOccupationTitle(1, "Carpet and Rug Mills", 31, 314110)
    CURTAIN_AND_LINEN_MILLS = LkOccupationTitle(1, "Curtain and Linen Mills", 31, 314120)
    OTHER_TEXTILE_PRODUCT_MILLS = LkOccupationTitle(1, "Other Textile Product Mills", 31, 3149)
    TEXTILE_BAG_AND_CANVAS_MILLS = LkOccupationTitle(1, "Textile Bag and Canvas Mills", 31, 314910)
    ROPE_CORDAGE_TWINE_TIRE_CORD_AND_TIRE_FABRIC_MILLS = LkOccupationTitle(1, "Rope, Cordage, Twine, Tire Cord, and Tire Fabric Mills", 31, 314994)
    ALL_OTHER_MISCELLANEOUS_TEXTILE_PRODUCT_MILLS = LkOccupationTitle(1, "All Other Miscellaneous Textile Product Mills", 31, 314999)
    APPAREL_KNITTING_MILLS = LkOccupationTitle(1, "Apparel Knitting Mills", 31, 3151)
    HOSIERY_AND_SOCK_MILLS = LkOccupationTitle(1, "Hosiery and Sock Mills", 31, 315110)
    OTHER_APPAREL_KNITTING_MILLS = LkOccupationTitle(1, "Other Apparel Knitting Mills", 31, 315190)
    CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(1, "Cut and Sew Apparel Manufacturing", 31, 3152)
    CUT_AND_SEW_APPAREL_CONTRACTORS = LkOccupationTitle(1, "Cut and Sew Apparel Contractors", 31, 315210)
    MENS_AND_BOYS_CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(1, "Men's and Boys' Cut and Sew Apparel Manufacturing", 31, 315220)
    WOMENS_GIRLS_AND_INFANTS_CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(1, "Women's, Girls', and Infants' Cut and Sew Apparel Manufacturing", 31, 315240)
    OTHER_CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(1, "Other Cut and Sew Apparel Manufacturing", 31, 315280)
    APPAREL_ACCESSORIES_AND_OTHER_APPAREL_MANUFACTURING = LkOccupationTitle(1, "Apparel Accessories and Other Apparel Manufacturing", 31, 3159)
    APPAREL_ACCESSORIES_AND_OTHER_APPAREL_MANUFACTURING = LkOccupationTitle(1, "Apparel Accessories and Other Apparel Manufacturing", 31, 315990)
    LEATHER_AND_HIDE_TANNING_AND_FINISHING = LkOccupationTitle(1, "Leather and Hide Tanning and Finishing", 31, 3161)
    LEATHER_AND_HIDE_TANNING_AND_FINISHING = LkOccupationTitle(1, "Leather and Hide Tanning and Finishing", 31, 316110)
    FOOTWEAR_MANUFACTURING = LkOccupationTitle(1, "Footwear Manufacturing", 31, 3162)
    FOOTWEAR_MANUFACTURING = LkOccupationTitle(1, "Footwear Manufacturing", 31, 316210)
    OTHER_LEATHER_AND_ALLIED_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Other Leather and Allied Product Manufacturing", 31, 3169)
    WOMENS_HANDBAG_AND_PURSE_MANUFACTURING = LkOccupationTitle(1, "Women's Handbag and Purse Manufacturing", 31, 316992)
    ALL_OTHER_LEATHER_GOOD_AND_ALLIED_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "All Other Leather Good and Allied Product Manufacturing", 31, 316998)
    SAWMILLS_AND_WOOD_PRESERVATION = LkOccupationTitle(1, "Sawmills and Wood Preservation", 32, 3211)
    SAWMILLS = LkOccupationTitle(1, "Sawmills", 32, 321113)
    WOOD_PRESERVATION = LkOccupationTitle(1, "Wood Preservation", 32, 321114)
    VENEER_PLYWOOD_AND_ENGINEERED_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Veneer, Plywood, and Engineered Wood Product Manufacturing", 32, 3212)
    HARDWOOD_VENEER_AND_PLYWOOD_MANUFACTURING = LkOccupationTitle(1, "Hardwood Veneer and Plywood Manufacturing", 32, 321211)
    SOFTWOOD_VENEER_AND_PLYWOOD_MANUFACTURING = LkOccupationTitle(1, "Softwood Veneer and Plywood Manufacturing", 32, 321212)
    ENGINEERED_WOOD_MEMBER_EXCEPT_TRUSS_MANUFACTURING = LkOccupationTitle(1, "Engineered Wood Member (except Truss) Manufacturing", 32, 321213)
    TRUSS_MANUFACTURING = LkOccupationTitle(1, "Truss Manufacturing", 32, 321214)
    RECONSTITUTED_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Reconstituted Wood Product Manufacturing", 32, 321219)
    OTHER_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Other Wood Product Manufacturing", 32, 3219)
    WOOD_WINDOW_AND_DOOR_MANUFACTURING = LkOccupationTitle(1, "Wood Window and Door Manufacturing", 32, 321911)
    CUT_STOCK_RESAWING_LUMBER_AND_PLANING = LkOccupationTitle(1, "Cut Stock, Resawing Lumber, and Planing", 32, 321912)
    OTHER_MILLWORK_INCLUDING_FLOORING = LkOccupationTitle(1, "Other Millwork (including Flooring)", 32, 321918)
    WOOD_CONTAINER_AND_PALLET_MANUFACTURING = LkOccupationTitle(1, "Wood Container and Pallet Manufacturing", 32, 321920)
    MANUFACTURED_HOME_MOBILE_HOME_MANUFACTURING = LkOccupationTitle(1, "Manufactured Home (Mobile Home) Manufacturing", 32, 321991)
    PREFABRICATED_WOOD_BUILDING_MANUFACTURING = LkOccupationTitle(1, "Prefabricated Wood Building Manufacturing", 32, 321992)
    ALL_OTHER_MISCELLANEOUS_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous Wood Product Manufacturing", 32, 321999)
    PULP_PAPER_AND_PAPERBOARD_MILLS = LkOccupationTitle(1, "Pulp, Paper, and Paperboard Mills", 32, 3221)
    PULP_MILLS = LkOccupationTitle(1, "Pulp Mills", 32, 322110)
    PAPER_EXCEPT_NEWSPRINT_MILLS = LkOccupationTitle(1, "Paper (except Newsprint) Mills", 32, 322121)
    NEWSPRINT_MILLS = LkOccupationTitle(1, "Newsprint Mills", 32, 322122)
    PAPERBOARD_MILLS = LkOccupationTitle(1, "Paperboard Mills", 32, 322130)
    CONVERTED_PAPER_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Converted Paper Product Manufacturing", 32, 3222)
    CORRUGATED_AND_SOLID_FIBER_BOX_MANUFACTURING = LkOccupationTitle(1, "Corrugated and Solid Fiber Box Manufacturing", 32, 322211)
    FOLDING_PAPERBOARD_BOX_MANUFACTURING = LkOccupationTitle(1, "Folding Paperboard Box Manufacturing", 32, 322212)
    OTHER_PAPERBOARD_CONTAINER_MANUFACTURING = LkOccupationTitle(1, "Other Paperboard Container Manufacturing", 32, 322219)
    PAPER_BAG_AND_COATED_AND_TREATED_PAPER_MANUFACTURING = LkOccupationTitle(1, "Paper Bag and Coated and Treated Paper Manufacturing", 32, 322220)
    STATIONERY_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Stationery Product Manufacturing", 32, 322230)
    SANITARY_PAPER_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Sanitary Paper Product Manufacturing", 32, 322291)
    ALL_OTHER_CONVERTED_PAPER_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "All Other Converted Paper Product Manufacturing", 32, 322299)
    PRINTING_AND_RELATED_SUPPORT_ACTIVITIES = LkOccupationTitle(1, "Printing and Related Support Activities", 32, 3231)
    COMMERCIAL_PRINTING_EXCEPT_SCREEN_AND_BOOKS = LkOccupationTitle(1, "Commercial Printing (except Screen and Books)", 32, 323111)
    COMMERCIAL_SCREEN_PRINTING = LkOccupationTitle(1, "Commercial Screen Printing", 32, 323113)
    BOOKS_PRINTING = LkOccupationTitle(1, "Books Printing", 32, 323117)
    SUPPORT_ACTIVITIES_FOR_PRINTING = LkOccupationTitle(1, "Support Activities for Printing", 32, 323120)
    PETROLEUM_AND_COAL_PRODUCTS_MANUFACTURING = LkOccupationTitle(1, "Petroleum and Coal Products Manufacturing", 32, 3241)
    PETROLEUM_REFINERIES = LkOccupationTitle(1, "Petroleum Refineries", 32, 324110)
    ASPHALT_PAVING_MIXTURE_AND_BLOCK_MANUFACTURING = LkOccupationTitle(1, "Asphalt Paving Mixture and Block Manufacturing", 32, 324121)
    ASPHALT_SHINGLE_AND_COATING_MATERIALS_MANUFACTURING = LkOccupationTitle(1, "Asphalt Shingle and Coating Materials Manufacturing", 32, 324122)
    PETROLEUM_LUBRICATING_OIL_AND_GREASE_MANUFACTURING = LkOccupationTitle(1, "Petroleum Lubricating Oil and Grease Manufacturing", 32, 324191)
    ALL_OTHER_PETROLEUM_AND_COAL_PRODUCTS_MANUFACTURING = LkOccupationTitle(1, "All Other Petroleum and Coal Products Manufacturing", 32, 324199)
    BASIC_CHEMICAL_MANUFACTURING = LkOccupationTitle(1, "Basic Chemical Manufacturing", 32, 3251)
    PETROCHEMICAL_MANUFACTURING = LkOccupationTitle(1, "Petrochemical Manufacturing", 32, 325110)
    INDUSTRIAL_GAS_MANUFACTURING = LkOccupationTitle(1, "Industrial Gas Manufacturing", 32, 325120)
    SYNTHETIC_DYE_AND_PIGMENT_MANUFACTURING = LkOccupationTitle(1, "Synthetic Dye and Pigment Manufacturing", 32, 325130)
    OTHER_BASIC_INORGANIC_CHEMICAL_MANUFACTURING = LkOccupationTitle(1, "Other Basic Inorganic Chemical Manufacturing", 32, 325180)
    ETHYL_ALCOHOL_MANUFACTURING = LkOccupationTitle(1, "Ethyl Alcohol Manufacturing", 32, 325193)
    CYCLIC_CRUDE_INTERMEDIATE_AND_GUM_AND_WOOD_CHEMICAL_MANUFACTURING = LkOccupationTitle(1, "Cyclic Crude, Intermediate, and Gum and Wood Chemical Manufacturing", 32, 325194)
    ALL_OTHER_BASIC_ORGANIC_CHEMICAL_MANUFACTURING = LkOccupationTitle(1, "All Other Basic Organic Chemical Manufacturing", 32, 325199)
    RESIN_SYNTHETIC_RUBBER_AND_ARTIFICIAL_AND_SYNTHETIC_FIBERS_AND_FILAMENTS_MANUFACTURING = LkOccupationTitle(1, "Resin, Synthetic Rubber, and Artificial and Synthetic Fibers and Filaments Manufacturing", 32, 3252)
    PLASTICS_MATERIAL_AND_RESIN_MANUFACTURING = LkOccupationTitle(1, "Plastics Material and Resin Manufacturing", 32, 325211)
    SYNTHETIC_RUBBER_MANUFACTURING = LkOccupationTitle(1, "Synthetic Rubber Manufacturing", 32, 325212)
    ARTIFICIAL_AND_SYNTHETIC_FIBERS_AND_FILAMENTS_MANUFACTURING = LkOccupationTitle(1, "Artificial and Synthetic Fibers and Filaments Manufacturing", 32, 325220)
    PESTICIDE_FERTILIZER_AND_OTHER_AGRICULTURAL_CHEMICAL_MANUFACTURING = LkOccupationTitle(1, "Pesticide, Fertilizer, and Other Agricultural Chemical Manufacturing", 32, 3253)
    NITROGENOUS_FERTILIZER_MANUFACTURING = LkOccupationTitle(1, "Nitrogenous Fertilizer Manufacturing", 32, 325311)
    PHOSPHATIC_FERTILIZER_MANUFACTURING = LkOccupationTitle(1, "Phosphatic Fertilizer Manufacturing", 32, 325312)
    FERTILIZER_MIXING_ONLY_MANUFACTURING = LkOccupationTitle(1, "Fertilizer (Mixing Only) Manufacturing", 32, 325314)
    PESTICIDE_AND_OTHER_AGRICULTURAL_CHEMICAL_MANUFACTURING = LkOccupationTitle(1, "Pesticide and Other Agricultural Chemical Manufacturing", 32, 325320)
    PHARMACEUTICAL_AND_MEDICINE_MANUFACTURING = LkOccupationTitle(1, "Pharmaceutical and Medicine Manufacturing", 32, 3254)
    MEDICINAL_AND_BOTANICAL_MANUFACTURING = LkOccupationTitle(1, "Medicinal and Botanical Manufacturing", 32, 325411)
    PHARMACEUTICAL_PREPARATION_MANUFACTURING = LkOccupationTitle(1, "Pharmaceutical Preparation Manufacturing", 32, 325412)
    INVITRO_DIAGNOSTIC_SUBSTANCE_MANUFACTURING = LkOccupationTitle(1, "In-Vitro Diagnostic Substance Manufacturing", 32, 325413)
    BIOLOGICAL_PRODUCT_EXCEPT_DIAGNOSTIC_MANUFACTURING = LkOccupationTitle(1, "Biological Product (except Diagnostic) Manufacturing", 32, 325414)
    PAINT_COATING_AND_ADHESIVE_MANUFACTURING = LkOccupationTitle(1, "Paint, Coating, and Adhesive Manufacturing", 32, 3255)
    PAINT_AND_COATING_MANUFACTURING = LkOccupationTitle(1, "Paint and Coating Manufacturing", 32, 325510)
    ADHESIVE_MANUFACTURING = LkOccupationTitle(1, "Adhesive Manufacturing", 32, 325520)
    SOAP_CLEANING_COMPOUND_AND_TOILET_PREPARATION_MANUFACTURING = LkOccupationTitle(1, "Soap, Cleaning Compound, and Toilet Preparation Manufacturing", 32, 3256)
    SOAP_AND_OTHER_DETERGENT_MANUFACTURING = LkOccupationTitle(1, "Soap and Other Detergent Manufacturing", 32, 325611)
    POLISH_AND_OTHER_SANITATION_GOOD_MANUFACTURING = LkOccupationTitle(1, "Polish and Other Sanitation Good Manufacturing", 32, 325612)
    SURFACE_ACTIVE_AGENT_MANUFACTURING = LkOccupationTitle(1, "Surface Active Agent Manufacturing", 32, 325613)
    TOILET_PREPARATION_MANUFACTURING = LkOccupationTitle(1, "Toilet Preparation Manufacturing", 32, 325620)
    OTHER_CHEMICAL_PRODUCT_AND_PREPARATION_MANUFACTURING = LkOccupationTitle(1, "Other Chemical Product and Preparation Manufacturing", 32, 3259)
    PRINTING_INK_MANUFACTURING = LkOccupationTitle(1, "Printing Ink Manufacturing", 32, 325910)
    EXPLOSIVES_MANUFACTURING = LkOccupationTitle(1, "Explosives Manufacturing", 32, 325920)
    CUSTOM_COMPOUNDING_OF_PURCHASED_RESINS = LkOccupationTitle(1, "Custom Compounding of Purchased Resins", 32, 325991)
    PHOTOGRAPHIC_FILM_PAPER_PLATE_AND_CHEMICAL_MANUFACTURING = LkOccupationTitle(1, "Photographic Film, Paper, Plate, and Chemical Manufacturing", 32, 325992)
    ALL_OTHER_MISCELLANEOUS_CHEMICAL_PRODUCT_AND_PREPARATION_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous Chemical Product and Preparation Manufacturing", 32, 325998)
    PLASTICS_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Plastics Product Manufacturing", 32, 3261)
    PLASTICS_BAG_AND_POUCH_MANUFACTURING = LkOccupationTitle(1, "Plastics Bag and Pouch Manufacturing", 32, 326111)
    PLASTICS_PACKAGING_FILM_AND_SHEET_INCLUDING_LAMINATED_MANUFACTURING = LkOccupationTitle(1, "Plastics Packaging Film and Sheet (including Laminated) Manufacturing", 32, 326112)
    UNLAMINATED_PLASTICS_FILM_AND_SHEET_EXCEPT_PACKAGING_MANUFACTURING = LkOccupationTitle(1, "Unlaminated Plastics Film and Sheet (except Packaging) Manufacturing", 32, 326113)
    UNLAMINATED_PLASTICS_PROFILE_SHAPE_MANUFACTURING = LkOccupationTitle(1, "Unlaminated Plastics Profile Shape Manufacturing", 32, 326121)
    PLASTICS_PIPE_AND_PIPE_FITTING_MANUFACTURING = LkOccupationTitle(1, "Plastics Pipe and Pipe Fitting Manufacturing", 32, 326122)
    LAMINATED_PLASTICS_PLATE_SHEET_EXCEPT_PACKAGING_AND_SHAPE_MANUFACTURING = LkOccupationTitle(1, "Laminated Plastics Plate, Sheet (except Packaging), and Shape Manufacturing", 32, 326130)
    POLYSTYRENE_FOAM_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Polystyrene Foam Product Manufacturing", 32, 326140)
    URETHANE_AND_OTHER_FOAM_PRODUCT_EXCEPT_POLYSTYRENE_MANUFACTURING = LkOccupationTitle(1, "Urethane and Other Foam Product (except Polystyrene) Manufacturing", 32, 326150)
    PLASTICS_BOTTLE_MANUFACTURING = LkOccupationTitle(1, "Plastics Bottle Manufacturing", 32, 326160)
    PLASTICS_PLUMBING_FIXTURE_MANUFACTURING = LkOccupationTitle(1, "Plastics Plumbing Fixture Manufacturing", 32, 326191)
    ALL_OTHER_PLASTICS_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "All Other Plastics Product Manufacturing", 32, 326199)
    RUBBER_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Rubber Product Manufacturing", 32, 3262)
    TIRE_MANUFACTURING_EXCEPT_RETREADING = LkOccupationTitle(1, "Tire Manufacturing (except Retreading)", 32, 326211)
    TIRE_RETREADING = LkOccupationTitle(1, "Tire Retreading", 32, 326212)
    RUBBER_AND_PLASTICS_HOSES_AND_BELTING_MANUFACTURING = LkOccupationTitle(1, "Rubber and Plastics Hoses and Belting Manufacturing", 32, 326220)
    RUBBER_PRODUCT_MANUFACTURING_FOR_MECHANICAL_USE = LkOccupationTitle(1, "Rubber Product Manufacturing for Mechanical Use", 32, 326291)
    ALL_OTHER_RUBBER_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "All Other Rubber Product Manufacturing", 32, 326299)
    CLAY_PRODUCT_AND_REFRACTORY_MANUFACTURING = LkOccupationTitle(1, "Clay Product and Refractory Manufacturing", 32, 3271)
    POTTERY_CERAMICS_AND_PLUMBING_FIXTURE_MANUFACTURING = LkOccupationTitle(1, "Pottery, Ceramics, and Plumbing Fixture Manufacturing", 32, 327110)
    CLAY_BUILDING_MATERIAL_AND_REFRACTORIES_MANUFACTURING = LkOccupationTitle(1, "Clay Building Material and Refractories Manufacturing", 32, 327120)
    GLASS_AND_GLASS_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Glass and Glass Product Manufacturing", 32, 3272)
    FLAT_GLASS_MANUFACTURING = LkOccupationTitle(1, "Flat Glass Manufacturing", 32, 327211)
    OTHER_PRESSED_AND_BLOWN_GLASS_AND_GLASSWARE_MANUFACTURING = LkOccupationTitle(1, "Other Pressed and Blown Glass and Glassware Manufacturing", 32, 327212)
    GLASS_CONTAINER_MANUFACTURING = LkOccupationTitle(1, "Glass Container Manufacturing", 32, 327213)
    GLASS_PRODUCT_MANUFACTURING_MADE_OF_PURCHASED_GLASS = LkOccupationTitle(1, "Glass Product Manufacturing Made of Purchased Glass", 32, 327215)
    CEMENT_AND_CONCRETE_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Cement and Concrete Product Manufacturing", 32, 3273)
    CEMENT_MANUFACTURING = LkOccupationTitle(1, "Cement Manufacturing", 32, 327310)
    READYMIX_CONCRETE_MANUFACTURING = LkOccupationTitle(1, "Ready-Mix Concrete Manufacturing", 32, 327320)
    CONCRETE_BLOCK_AND_BRICK_MANUFACTURING = LkOccupationTitle(1, "Concrete Block and Brick Manufacturing", 32, 327331)
    CONCRETE_PIPE_MANUFACTURING = LkOccupationTitle(1, "Concrete Pipe Manufacturing", 32, 327332)
    OTHER_CONCRETE_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Other Concrete Product Manufacturing", 32, 327390)
    LIME_AND_GYPSUM_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Lime and Gypsum Product Manufacturing", 32, 3274)
    LIME_MANUFACTURING = LkOccupationTitle(1, "Lime Manufacturing", 32, 327410)
    GYPSUM_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Gypsum Product Manufacturing", 32, 327420)
    OTHER_NONMETALLIC_MINERAL_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Other Nonmetallic Mineral Product Manufacturing", 32, 3279)
    ABRASIVE_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Abrasive Product Manufacturing", 32, 327910)
    CUT_STONE_AND_STONE_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Cut Stone and Stone Product Manufacturing", 32, 327991)
    GROUND_OR_TREATED_MINERAL_AND_EARTH_MANUFACTURING = LkOccupationTitle(1, "Ground or Treated Mineral and Earth Manufacturing", 32, 327992)
    MINERAL_WOOL_MANUFACTURING = LkOccupationTitle(1, "Mineral Wool Manufacturing", 32, 327993)
    ALL_OTHER_MISCELLANEOUS_NONMETALLIC_MINERAL_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous Nonmetallic Mineral Product Manufacturing", 32, 327999)
    IRON_AND_STEEL_MILLS_AND_FERROALLOY_MANUFACTURING = LkOccupationTitle(1, "Iron and Steel Mills and Ferroalloy Manufacturing", 33, 3311)
    IRON_AND_STEEL_MILLS_AND_FERROALLOY_MANUFACTURING = LkOccupationTitle(1, "Iron and Steel Mills and Ferroalloy Manufacturing", 33, 331110)
    STEEL_PRODUCT_MANUFACTURING_FROM_PURCHASED_STEEL = LkOccupationTitle(1, "Steel Product Manufacturing from Purchased Steel", 33, 3312)
    IRON_AND_STEEL_PIPE_AND_TUBE_MANUFACTURING_FROM_PURCHASED_STEEL = LkOccupationTitle(1, "Iron and Steel Pipe and Tube Manufacturing from Purchased Steel", 33, 331210)
    ROLLED_STEEL_SHAPE_MANUFACTURING = LkOccupationTitle(1, "Rolled Steel Shape Manufacturing", 33, 331221)
    STEEL_WIRE_DRAWING = LkOccupationTitle(1, "Steel Wire Drawing", 33, 331222)
    ALUMINA_AND_ALUMINUM_PRODUCTION_AND_PROCESSING = LkOccupationTitle(1, "Alumina and Aluminum Production and Processing", 33, 3313)
    ALUMINA_REFINING_AND_PRIMARY_ALUMINUM_PRODUCTION = LkOccupationTitle(1, "Alumina Refining and Primary Aluminum Production", 33, 331313)
    SECONDARY_SMELTING_AND_ALLOYING_OF_ALUMINUM = LkOccupationTitle(1, "Secondary Smelting and Alloying of Aluminum", 33, 331314)
    ALUMINUM_SHEET_PLATE_AND_FOIL_MANUFACTURING = LkOccupationTitle(1, "Aluminum Sheet, Plate, and Foil Manufacturing", 33, 331315)
    OTHER_ALUMINUM_ROLLING_DRAWING_AND_EXTRUDING = LkOccupationTitle(1, "Other Aluminum Rolling, Drawing, and Extruding", 33, 331318)
    NONFERROUS_METAL_EXCEPT_ALUMINUM_PRODUCTION_AND_PROCESSING = LkOccupationTitle(1, "Nonferrous Metal (except Aluminum) Production and Processing", 33, 3314)
    NONFERROUS_METAL_EXCEPT_ALUMINUM_SMELTING_AND_REFINING = LkOccupationTitle(1, "Nonferrous Metal (except Aluminum) Smelting and Refining", 33, 331410)
    COPPER_ROLLING_DRAWING_EXTRUDING_AND_ALLOYING = LkOccupationTitle(1, "Copper Rolling, Drawing, Extruding, and Alloying", 33, 331420)
    NONFERROUS_METAL_EXCEPT_COPPER_AND_ALUMINUM_ROLLING_DRAWING_AND_EXTRUDING = LkOccupationTitle(1, "Nonferrous Metal (except Copper and Aluminum) Rolling, Drawing, and Extruding", 33, 331491)
    SECONDARY_SMELTING_REFINING_AND_ALLOYING_OF_NONFERROUS_METAL_EXCEPT_COPPER_AND_ALUMINUM = LkOccupationTitle(1, "Secondary Smelting, Refining, and Alloying of Nonferrous Metal (except Copper and Aluminum)", 33, 331492)
    FOUNDRIES = LkOccupationTitle(1, "Foundries", 33, 3315)
    IRON_FOUNDRIES = LkOccupationTitle(1, "Iron Foundries", 33, 331511)
    STEEL_INVESTMENT_FOUNDRIES = LkOccupationTitle(1, "Steel Investment Foundries", 33, 331512)
    STEEL_FOUNDRIES_EXCEPT_INVESTMENT = LkOccupationTitle(1, "Steel Foundries (except Investment)", 33, 331513)
    NONFERROUS_METAL_DIECASTING_FOUNDRIES = LkOccupationTitle(1, "Nonferrous Metal Die-Casting Foundries", 33, 331523)
    ALUMINUM_FOUNDRIES_EXCEPT_DIECASTING = LkOccupationTitle(1, "Aluminum Foundries (except Die-Casting)", 33, 331524)
    OTHER_NONFERROUS_METAL_FOUNDRIES_EXCEPT_DIECASTING = LkOccupationTitle(1, "Other Nonferrous Metal Foundries (except Die-Casting)", 33, 331529)
    FORGING_AND_STAMPING = LkOccupationTitle(1, "Forging and Stamping", 33, 3321)
    IRON_AND_STEEL_FORGING = LkOccupationTitle(1, "Iron and Steel Forging", 33, 332111)
    NONFERROUS_FORGING = LkOccupationTitle(1, "Nonferrous Forging", 33, 332112)
    CUSTOM_ROLL_FORMING = LkOccupationTitle(1, "Custom Roll Forming", 33, 332114)
    POWDER_METALLURGY_PART_MANUFACTURING = LkOccupationTitle(1, "Powder Metallurgy Part Manufacturing", 33, 332117)
    METAL_CROWN_CLOSURE_AND_OTHER_METAL_STAMPING_EXCEPT_AUTOMOTIVE = LkOccupationTitle(1, "Metal Crown, Closure, and Other Metal Stamping (except Automotive)", 33, 332119)
    CUTLERY_AND_HANDTOOL_MANUFACTURING = LkOccupationTitle(1, "Cutlery and Handtool Manufacturing", 33, 3322)
    METAL_KITCHEN_COOKWARE_UTENSIL_CUTLERY_AND_FLATWARE_EXCEPT_PRECIOUS_MANUFACTURING = LkOccupationTitle(1, "Metal Kitchen Cookware, Utensil, Cutlery, and Flatware (except Precious) Manufacturing273", 33, 332215)
    SAW_BLADE_AND_HANDTOOL_MANUFACTURING = LkOccupationTitle(1, "Saw Blade and Handtool Manufacturing", 33, 332216)
    ARCHITECTURAL_AND_STRUCTURAL_METALS_MANUFACTURING = LkOccupationTitle(1, "Architectural and Structural Metals Manufacturing", 33, 3323)
    PREFABRICATED_METAL_BUILDING_AND_COMPONENT_MANUFACTURING = LkOccupationTitle(1, "Prefabricated Metal Building and Component Manufacturing", 33, 332311)
    FABRICATED_STRUCTURAL_METAL_MANUFACTURING = LkOccupationTitle(1, "Fabricated Structural Metal Manufacturing", 33, 332312)
    PLATE_WORK_MANUFACTURING = LkOccupationTitle(1, "Plate Work Manufacturing", 33, 332313)
    METAL_WINDOW_AND_DOOR_MANUFACTURING = LkOccupationTitle(1, "Metal Window and Door Manufacturing", 33, 332321)
    SHEET_METAL_WORK_MANUFACTURING = LkOccupationTitle(1, "Sheet Metal Work Manufacturing", 33, 332322)
    ORNAMENTAL_AND_ARCHITECTURAL_METAL_WORK_MANUFACTURING = LkOccupationTitle(1, "Ornamental and Architectural Metal Work Manufacturing", 33, 332323)
    BOILER_TANK_AND_SHIPPING_CONTAINER_MANUFACTURING = LkOccupationTitle(1, "Boiler, Tank, and Shipping Container Manufacturing", 33, 3324)
    POWER_BOILER_AND_HEAT_EXCHANGER_MANUFACTURING = LkOccupationTitle(1, "Power Boiler and Heat Exchanger Manufacturing", 33, 332410)
    METAL_TANK_HEAVY_GAUGE_MANUFACTURING = LkOccupationTitle(1, "Metal Tank (Heavy Gauge) Manufacturing", 33, 332420)
    METAL_CAN_MANUFACTURING = LkOccupationTitle(1, "Metal Can Manufacturing", 33, 332431)
    OTHER_METAL_CONTAINER_MANUFACTURING = LkOccupationTitle(1, "Other Metal Container Manufacturing", 33, 332439)
    HARDWARE_MANUFACTURING = LkOccupationTitle(1, "Hardware Manufacturing", 33, 3325)
    HARDWARE_MANUFACTURING = LkOccupationTitle(1, "Hardware Manufacturing", 33, 332510)
    SPRING_AND_WIRE_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Spring and Wire Product Manufacturing", 33, 3326)
    SPRING_MANUFACTURING = LkOccupationTitle(1, "Spring Manufacturing", 33, 332613)
    OTHER_FABRICATED_WIRE_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Other Fabricated Wire Product Manufacturing", 33, 332618)
    MACHINE_SHOPS_TURNED_PRODUCT_AND_SCREW_NUT_AND_BOLT_MANUFACTURING = LkOccupationTitle(1, "Machine Shops; Turned Product; and Screw, Nut, and Bolt Manufacturing", 33, 3327)
    MACHINE_SHOPS = LkOccupationTitle(1, "Machine Shops", 33, 332710)
    PRECISION_TURNED_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Precision Turned Product Manufacturing", 33, 332721)
    BOLT_NUT_SCREW_RIVET_AND_WASHER_MANUFACTURING = LkOccupationTitle(1, "Bolt, Nut, Screw, Rivet, and Washer Manufacturing", 33, 332722)
    COATING_ENGRAVING_HEAT_TREATING_AND_ALLIED_ACTIVITIES = LkOccupationTitle(1, "Coating, Engraving, Heat Treating, and Allied Activities", 33, 3328)
    METAL_HEAT_TREATING = LkOccupationTitle(1, "Metal Heat Treating", 33, 332811)
    METAL_COATING_ENGRAVING_EXCEPT_JEWELRY_AND_SILVERWARE_AND_ALLIED_SERVICES_TO_MANUFACTURERS = LkOccupationTitle(1, "Metal Coating, Engraving (except Jewelry and Silverware), and Allied Services to Manufacturers", 33, 332812)
    ELECTROPLATING_PLATING_POLISHING_ANODIZING_AND_COLORING = LkOccupationTitle(1, "Electroplating, Plating, Polishing, Anodizing, and Coloring", 33, 332813)
    OTHER_FABRICATED_METAL_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Other Fabricated Metal Product Manufacturing", 33, 3329)
    INDUSTRIAL_VALVE_MANUFACTURING = LkOccupationTitle(1, "Industrial Valve Manufacturing", 33, 332911)
    FLUID_POWER_VALVE_AND_HOSE_FITTING_MANUFACTURING = LkOccupationTitle(1, "Fluid Power Valve and Hose Fitting Manufacturing", 33, 332912)
    PLUMBING_FIXTURE_FITTING_AND_TRIM_MANUFACTURING = LkOccupationTitle(1, "Plumbing Fixture Fitting and Trim Manufacturing", 33, 332913)
    OTHER_METAL_VALVE_AND_PIPE_FITTING_MANUFACTURING = LkOccupationTitle(1, "Other Metal Valve and Pipe Fitting Manufacturing", 33, 332919)
    BALL_AND_ROLLER_BEARING_MANUFACTURING = LkOccupationTitle(1, "Ball and Roller Bearing Manufacturing", 33, 332991)
    SMALL_ARMS_AMMUNITION_MANUFACTURING = LkOccupationTitle(1, "Small Arms Ammunition Manufacturing", 33, 332992)
    AMMUNITION_EXCEPT_SMALL_ARMS_MANUFACTURING = LkOccupationTitle(1, "Ammunition (except Small Arms) Manufacturing", 33, 332993)
    SMALL_ARMS_ORDNANCE_AND_ORDNANCE_ACCESSORIES_MANUFACTURING = LkOccupationTitle(1, "Small Arms, Ordnance, and Ordnance Accessories Manufacturing", 33, 332994)
    FABRICATED_PIPE_AND_PIPE_FITTING_MANUFACTURING = LkOccupationTitle(1, "Fabricated Pipe and Pipe Fitting Manufacturing", 33, 332996)
    ALL_OTHER_MISCELLANEOUS_FABRICATED_METAL_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous Fabricated Metal Product Manufacturing", 33, 332999)
    AGRICULTURE_CONSTRUCTION_AND_MINING_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Agriculture, Construction, and Mining Machinery Manufacturing", 33, 3331)
    FARM_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Farm Machinery and Equipment Manufacturing", 33, 333111)
    LAWN_AND_GARDEN_TRACTOR_AND_HOME_LAWN_AND_GARDEN_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Lawn and Garden Tractor and Home Lawn and Garden Equipment Manufacturing", 33, 333112)
    CONSTRUCTION_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Construction Machinery Manufacturing", 33, 333120)
    MINING_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Mining Machinery and Equipment Manufacturing", 33, 333131)
    OIL_AND_GAS_FIELD_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Oil and Gas Field Machinery and Equipment Manufacturing", 33, 333132)
    INDUSTRIAL_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Industrial Machinery Manufacturing", 33, 3332)
    FOOD_PRODUCT_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Food Product Machinery Manufacturing", 33, 333241)
    SEMICONDUCTOR_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Semiconductor Machinery Manufacturing", 33, 333242)
    SAWMILL_WOODWORKING_AND_PAPER_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Sawmill, Woodworking, and Paper Machinery Manufacturing", 33, 333243)
    PRINTING_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Printing Machinery and Equipment Manufacturing", 33, 333244)
    OTHER_INDUSTRIAL_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Other Industrial Machinery Manufacturing", 33, 333249)
    COMMERCIAL_AND_SERVICE_INDUSTRY_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Commercial and Service Industry Machinery Manufacturing", 33, 3333)
    OPTICAL_INSTRUMENT_AND_LENS_MANUFACTURING = LkOccupationTitle(1, "Optical Instrument and Lens Manufacturing", 33, 333314)
    PHOTOGRAPHIC_AND_PHOTOCOPYING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Photographic and Photocopying Equipment Manufacturing", 33, 333316)
    OTHER_COMMERCIAL_AND_SERVICE_INDUSTRY_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Other Commercial and Service Industry Machinery Manufacturing", 33, 333318)
    VENTILATION_HEATING_AIRCONDITIONING_AND_COMMERCIAL_REFRIGERATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Ventilation, Heating, Air-Conditioning, and Commercial Refrigeration Equipment Manufacturing", 33, 3334)
    INDUSTRIAL_AND_COMMERCIAL_FAN_AND_BLOWER_AND_AIR_PURIFICATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Industrial and Commercial Fan and Blower and Air Purification Equipment Manufacturing123", 33, 333413)
    HEATING_EQUIPMENT_EXCEPT_WARM_AIR_FURNACES_MANUFACTURING = LkOccupationTitle(1, "Heating Equipment (except Warm Air Furnaces) Manufacturing", 33, 333414)
    AIRCONDITIONING_AND_WARM_AIR_HEATING_EQUIPMENT_AND_COMMERCIAL_AND_INDUSTRIAL_REFRIGERATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Air-Conditioning and Warm Air Heating Equipment and Commercial and Industrial Refrigeration Equipment Manufacturing", 33, 333415)
    METALWORKING_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Metalworking Machinery Manufacturing", 33, 3335)
    INDUSTRIAL_MOLD_MANUFACTURING = LkOccupationTitle(1, "Industrial Mold Manufacturing", 33, 333511)
    SPECIAL_DIE_AND_TOOL_DIE_SET_JIG_AND_FIXTURE_MANUFACTURING = LkOccupationTitle(1, "Special Die and Tool, Die Set, Jig, and Fixture Manufacturing", 33, 333514)
    CUTTING_TOOL_AND_MACHINE_TOOL_ACCESSORY_MANUFACTURING = LkOccupationTitle(1, "Cutting Tool and Machine Tool Accessory Manufacturing", 33, 333515)
    MACHINE_TOOL_MANUFACTURING = LkOccupationTitle(1, "Machine Tool Manufacturing", 33, 333517)
    ROLLING_MILL_AND_OTHER_METALWORKING_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Rolling Mill and Other Metalworking Machinery Manufacturing", 33, 333519)
    ENGINE_TURBINE_AND_POWER_TRANSMISSION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Engine, Turbine, and Power Transmission Equipment Manufacturing", 33, 3336)
    TURBINE_AND_TURBINE_GENERATOR_SET_UNITS_MANUFACTURING = LkOccupationTitle(1, "Turbine and Turbine Generator Set Units Manufacturing", 33, 333611)
    SPEED_CHANGER_INDUSTRIAL_HIGHSPEED_DRIVE_AND_GEAR_MANUFACTURING = LkOccupationTitle(1, "Speed Changer, Industrial High-Speed Drive, and Gear Manufacturing", 33, 333612)
    MECHANICAL_POWER_TRANSMISSION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Mechanical Power Transmission Equipment Manufacturing", 33, 333613)
    OTHER_ENGINE_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Other Engine Equipment Manufacturing", 33, 333618)
    OTHER_GENERAL_PURPOSE_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Other General Purpose Machinery Manufacturing", 33, 3339)
    AIR_AND_GAS_COMPRESSOR_MANUFACTURING = LkOccupationTitle(1, "Air and Gas Compressor Manufacturing", 33, 333912)
    MEASURING_DISPENSING_AND_OTHER_PUMPING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Measuring, Dispensing, and Other Pumping Equipment Manufacturing", 33, 333914)
    ELEVATOR_AND_MOVING_STAIRWAY_MANUFACTURING = LkOccupationTitle(1, "Elevator and Moving Stairway Manufacturing", 33, 333921)
    CONVEYOR_AND_CONVEYING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Conveyor and Conveying Equipment Manufacturing", 33, 333922)
    OVERHEAD_TRAVELING_CRANE_HOIST_AND_MONORAIL_SYSTEM_MANUFACTURING = LkOccupationTitle(1, "Overhead Traveling Crane, Hoist, and Monorail System Manufacturing", 33, 333923)
    INDUSTRIAL_TRUCK_TRACTOR_TRAILER_AND_STACKER_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Industrial Truck, Tractor, Trailer, and Stacker Machinery Manufacturing", 33, 333924)
    POWERDRIVEN_HANDTOOL_MANUFACTURING = LkOccupationTitle(1, "Power-Driven Handtool Manufacturing", 33, 333991)
    WELDING_AND_SOLDERING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Welding and Soldering Equipment Manufacturing", 33, 333992)
    PACKAGING_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "Packaging Machinery Manufacturing", 33, 333993)
    INDUSTRIAL_PROCESS_FURNACE_AND_OVEN_MANUFACTURING = LkOccupationTitle(1, "Industrial Process Furnace and Oven Manufacturing", 33, 333994)
    FLUID_POWER_CYLINDER_AND_ACTUATOR_MANUFACTURING = LkOccupationTitle(1, "Fluid Power Cylinder and Actuator Manufacturing", 33, 333995)
    FLUID_POWER_PUMP_AND_MOTOR_MANUFACTURING = LkOccupationTitle(1, "Fluid Power Pump and Motor Manufacturing", 33, 333996)
    SCALE_AND_BALANCE_MANUFACTURING = LkOccupationTitle(1, "Scale and Balance Manufacturing", 33, 333997)
    ALL_OTHER_MISCELLANEOUS_GENERAL_PURPOSE_MACHINERY_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous General Purpose Machinery Manufacturing", 33, 333999)
    COMPUTER_AND_PERIPHERAL_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Computer and Peripheral Equipment Manufacturing", 33, 3341)
    ELECTRONIC_COMPUTER_MANUFACTURING = LkOccupationTitle(1, "Electronic Computer Manufacturing", 33, 334111)
    COMPUTER_STORAGE_DEVICE_MANUFACTURING = LkOccupationTitle(1, "Computer Storage Device Manufacturing", 33, 334112)
    COMPUTER_TERMINAL_AND_OTHER_COMPUTER_PERIPHERAL_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Computer Terminal and Other Computer Peripheral Equipment Manufacturing", 33, 334118)
    COMMUNICATIONS_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Communications Equipment Manufacturing", 33, 3342)
    TELEPHONE_APPARATUS_MANUFACTURING = LkOccupationTitle(1, "Telephone Apparatus Manufacturing", 33, 334210)
    RADIO_AND_TELEVISION_BROADCASTING_AND_WIRELESS_COMMUNICATIONS_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Radio and Television Broadcasting and Wireless Communications Equipment Manufacturing163", 33, 334220)
    OTHER_COMMUNICATIONS_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Other Communications Equipment Manufacturing", 33, 334290)
    AUDIO_AND_VIDEO_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Audio and Video Equipment Manufacturing", 33, 3343)
    AUDIO_AND_VIDEO_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Audio and Video Equipment Manufacturing", 33, 334310)
    SEMICONDUCTOR_AND_OTHER_ELECTRONIC_COMPONENT_MANUFACTURING = LkOccupationTitle(1, "Semiconductor and Other Electronic Component Manufacturing", 33, 3344)
    BARE_PRINTED_CIRCUIT_BOARD_MANUFACTURING = LkOccupationTitle(1, "Bare Printed Circuit Board Manufacturing", 33, 334412)
    SEMICONDUCTOR_AND_RELATED_DEVICE_MANUFACTURING = LkOccupationTitle(1, "Semiconductor and Related Device Manufacturing", 33, 334413)
    CAPACITOR_RESISTOR_COIL_TRANSFORMER_AND_OTHER_INDUCTOR_MANUFACTURING = LkOccupationTitle(1, "Capacitor, Resistor, Coil, Transformer, and Other Inductor Manufacturing", 33, 334416)
    ELECTRONIC_CONNECTOR_MANUFACTURING = LkOccupationTitle(1, "Electronic Connector Manufacturing", 33, 334417)
    PRINTED_CIRCUIT_ASSEMBLY_ELECTRONIC_ASSEMBLY_MANUFACTURING = LkOccupationTitle(1, "Printed Circuit Assembly (Electronic Assembly) Manufacturing", 33, 334418)
    OTHER_ELECTRONIC_COMPONENT_MANUFACTURING = LkOccupationTitle(1, "Other Electronic Component Manufacturing", 33, 334419)
    NAVIGATIONAL_MEASURING_ELECTROMEDICAL_AND_CONTROL_INSTRUMENTS_MANUFACTURING = LkOccupationTitle(1, "Navigational, Measuring, Electromedical, and Control Instruments Manufacturing", 33, 3345)
    ELECTROMEDICAL_AND_ELECTROTHERAPEUTIC_APPARATUS_MANUFACTURING = LkOccupationTitle(1, "Electromedical and Electrotherapeutic Apparatus Manufacturing", 33, 334510)
    SEARCH_DETECTION_NAVIGATION_GUIDANCE_AERONAUTICAL_AND_NAUTICAL_SYSTEM_AND_INSTRUMENT_MANUFACTURING = LkOccupationTitle(1, "Search, Detection, Navigation, Guidance, Aeronautical, and Nautical System and Instrument Manufacturing", 33, 334511)
    AUTOMATIC_ENVIRONMENTAL_CONTROL_MANUFACTURING_FOR_RESIDENTIAL_COMMERCIAL_AND_APPLIANCE_USE = LkOccupationTitle(1, "Automatic Environmental Control Manufacturing for Residential, Commercial, and Appliance Use", 33, 334512)
    INSTRUMENTS_AND_RELATED_PRODUCTS_MANUFACTURING_FOR_MEASURING_DISPLAYING_AND_CONTROLLING_INDUSTRIAL_PROCESS_VARIABLES = LkOccupationTitle(1, "Instruments and Related Products Manufacturing for Measuring, Displaying, and Controlling Industrial Process Variables", 33, 334513)
    TOTALIZING_FLUID_METER_AND_COUNTING_DEVICE_MANUFACTURING = LkOccupationTitle(1, "Totalizing Fluid Meter and Counting Device Manufacturing", 33, 334514)
    INSTRUMENT_MANUFACTURING_FOR_MEASURING_AND_TESTING_ELECTRICITY_AND_ELECTRICAL_SIGNALS = LkOccupationTitle(1, "Instrument Manufacturing for Measuring and Testing Electricity and Electrical Signals832", 33, 334515)
    ANALYTICAL_LABORATORY_INSTRUMENT_MANUFACTURING = LkOccupationTitle(1, "Analytical Laboratory Instrument Manufacturing", 33, 334516)
    IRRADIATION_APPARATUS_MANUFACTURING = LkOccupationTitle(1, "Irradiation Apparatus Manufacturing", 33, 334517)
    OTHER_MEASURING_AND_CONTROLLING_DEVICE_MANUFACTURING = LkOccupationTitle(1, "Other Measuring and Controlling Device Manufacturing", 33, 334519)
    MANUFACTURING_AND_REPRODUCING_MAGNETIC_AND_OPTICAL_MEDIA = LkOccupationTitle(1, "Manufacturing and Reproducing Magnetic and Optical Media", 33, 3346)
    BLANK_MAGNETIC_AND_OPTICAL_RECORDING_MEDIA_MANUFACTURING = LkOccupationTitle(1, "Blank Magnetic and Optical Recording Media Manufacturing", 33, 334613)
    SOFTWARE_AND_OTHER_PRERECORDED_COMPACT_DISC_TAPE_AND_RECORD_REPRODUCING = LkOccupationTitle(1, "Software and Other Prerecorded Compact Disc, Tape, and Record Reproducing", 33, 334614)
    ELECTRIC_LIGHTING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Electric Lighting Equipment Manufacturing", 33, 3351)
    ELECTRIC_LAMP_BULB_AND_PART_MANUFACTURING = LkOccupationTitle(1, "Electric Lamp Bulb and Part Manufacturing", 33, 335110)
    RESIDENTIAL_ELECTRIC_LIGHTING_FIXTURE_MANUFACTURING = LkOccupationTitle(1, "Residential Electric Lighting Fixture Manufacturing", 33, 335121)
    COMMERCIAL_INDUSTRIAL_AND_INSTITUTIONAL_ELECTRIC_LIGHTING_FIXTURE_MANUFACTURING = LkOccupationTitle(1, "Commercial, Industrial, and Institutional Electric Lighting Fixture Manufacturing", 33, 335122)
    OTHER_LIGHTING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Other Lighting Equipment Manufacturing", 33, 335129)
    HOUSEHOLD_APPLIANCE_MANUFACTURING = LkOccupationTitle(1, "Household Appliance Manufacturing", 33, 3352)
    SMALL_ELECTRICAL_APPLIANCE_MANUFACTURING = LkOccupationTitle(1, "Small Electrical Appliance Manufacturing", 33, 335210)
    MAJOR_HOUSEHOLD_APPLIANCE_MANUFACTURING = LkOccupationTitle(1, "Major Household Appliance Manufacturing", 33, 335220)
    ELECTRICAL_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Electrical Equipment Manufacturing", 33, 3353)
    POWER_DISTRIBUTION_AND_SPECIALTY_TRANSFORMER_MANUFACTURING = LkOccupationTitle(1, "Power, Distribution, and Specialty Transformer Manufacturing", 33, 335311)
    MOTOR_AND_GENERATOR_MANUFACTURING = LkOccupationTitle(1, "Motor and Generator Manufacturing", 33, 335312)
    SWITCHGEAR_AND_SWITCHBOARD_APPARATUS_MANUFACTURING = LkOccupationTitle(1, "Switchgear and Switchboard Apparatus Manufacturing", 33, 335313)
    RELAY_AND_INDUSTRIAL_CONTROL_MANUFACTURING = LkOccupationTitle(1, "Relay and Industrial Control Manufacturing", 33, 335314)
    OTHER_ELECTRICAL_EQUIPMENT_AND_COMPONENT_MANUFACTURING = LkOccupationTitle(1, "Other Electrical Equipment and Component Manufacturing", 33, 3359)
    STORAGE_BATTERY_MANUFACTURING = LkOccupationTitle(1, "Storage Battery Manufacturing", 33, 335911)
    PRIMARY_BATTERY_MANUFACTURING = LkOccupationTitle(1, "Primary Battery Manufacturing", 33, 335912)
    FIBER_OPTIC_CABLE_MANUFACTURING = LkOccupationTitle(1, "Fiber Optic Cable Manufacturing", 33, 335921)
    OTHER_COMMUNICATION_AND_ENERGY_WIRE_MANUFACTURING = LkOccupationTitle(1, "Other Communication and Energy Wire Manufacturing", 33, 335929)
    CURRENTCARRYING_WIRING_DEVICE_MANUFACTURING = LkOccupationTitle(1, "Current-Carrying Wiring Device Manufacturing", 33, 335931)
    NONCURRENTCARRYING_WIRING_DEVICE_MANUFACTURING = LkOccupationTitle(1, "Noncurrent-Carrying Wiring Device Manufacturing", 33, 335932)
    CARBON_AND_GRAPHITE_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Carbon and Graphite Product Manufacturing", 33, 335991)
    ALL_OTHER_MISCELLANEOUS_ELECTRICAL_EQUIPMENT_AND_COMPONENT_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous Electrical Equipment and Component Manufacturing", 33, 335999)
    MOTOR_VEHICLE_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Manufacturing", 33, 3361)
    AUTOMOBILE_MANUFACTURING = LkOccupationTitle(1, "Automobile Manufacturing", 33, 336111)
    LIGHT_TRUCK_AND_UTILITY_VEHICLE_MANUFACTURING = LkOccupationTitle(1, "Light Truck and Utility Vehicle Manufacturing", 33, 336112)
    HEAVY_DUTY_TRUCK_MANUFACTURING = LkOccupationTitle(1, "Heavy Duty Truck Manufacturing", 33, 336120)
    MOTOR_VEHICLE_BODY_AND_TRAILER_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Body and Trailer Manufacturing", 33, 3362)
    MOTOR_VEHICLE_BODY_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Body Manufacturing", 33, 336211)
    TRUCK_TRAILER_MANUFACTURING = LkOccupationTitle(1, "Truck Trailer Manufacturing", 33, 336212)
    MOTOR_HOME_MANUFACTURING = LkOccupationTitle(1, "Motor Home Manufacturing", 33, 336213)
    TRAVEL_TRAILER_AND_CAMPER_MANUFACTURING = LkOccupationTitle(1, "Travel Trailer and Camper Manufacturing", 33, 336214)
    MOTOR_VEHICLE_PARTS_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Parts Manufacturing", 33, 3363)
    MOTOR_VEHICLE_GASOLINE_ENGINE_AND_ENGINE_PARTS_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Gasoline Engine and Engine Parts Manufacturing", 33, 336310)
    MOTOR_VEHICLE_ELECTRICAL_AND_ELECTRONIC_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Electrical and Electronic Equipment Manufacturing", 33, 336320)
    MOTOR_VEHICLE_STEERING_AND_SUSPENSION_COMPONENTS_EXCEPT_SPRING_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Steering and Suspension Components (except Spring) Manufacturing", 33, 336330)
    MOTOR_VEHICLE_BRAKE_SYSTEM_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Brake System Manufacturing", 33, 336340)
    MOTOR_VEHICLE_TRANSMISSION_AND_POWER_TRAIN_PARTS_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Transmission and Power Train Parts Manufacturing", 33, 336350)
    MOTOR_VEHICLE_SEATING_AND_INTERIOR_TRIM_MANUFACTURING = LkOccupationTitle(1, "Motor Vehicle Seating and Interior Trim Manufacturing", 33, 336360)
    MOTOR_VEHICLE_METAL_STAMPING = LkOccupationTitle(1, "Motor Vehicle Metal Stamping", 33, 336370)
    OTHER_MOTOR_VEHICLE_PARTS_MANUFACTURING = LkOccupationTitle(1, "Other Motor Vehicle Parts Manufacturing", 33, 336390)
    AEROSPACE_PRODUCT_AND_PARTS_MANUFACTURING = LkOccupationTitle(1, "Aerospace Product and Parts Manufacturing", 33, 3364)
    AIRCRAFT_MANUFACTURING = LkOccupationTitle(1, "Aircraft Manufacturing", 33, 336411)
    AIRCRAFT_ENGINE_AND_ENGINE_PARTS_MANUFACTURING = LkOccupationTitle(1, "Aircraft Engine and Engine Parts Manufacturing", 33, 336412)
    OTHER_AIRCRAFT_PARTS_AND_AUXILIARY_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Other Aircraft Parts and Auxiliary Equipment Manufacturing", 33, 336413)
    GUIDED_MISSILE_AND_SPACE_VEHICLE_MANUFACTURING = LkOccupationTitle(1, "Guided Missile and Space Vehicle Manufacturing", 33, 336414)
    GUIDED_MISSILE_AND_SPACE_VEHICLE_PROPULSION_UNIT_AND_PROPULSION_UNIT_PARTS_MANUFACTURING = LkOccupationTitle(1, "Guided Missile and Space Vehicle Propulsion Unit and Propulsion Unit Parts Manufacturing", 33, 336415)
    OTHER_GUIDED_MISSILE_AND_SPACE_VEHICLE_PARTS_AND_AUXILIARY_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Other Guided Missile and Space Vehicle Parts and Auxiliary Equipment Manufacturing", 33, 336419)
    RAILROAD_ROLLING_STOCK_MANUFACTURING = LkOccupationTitle(1, "Railroad Rolling Stock Manufacturing", 33, 3365)
    RAILROAD_ROLLING_STOCK_MANUFACTURING = LkOccupationTitle(1, "Railroad Rolling Stock Manufacturing", 33, 336510)
    SHIP_AND_BOAT_BUILDING = LkOccupationTitle(1, "Ship and Boat Building", 33, 3366)
    SHIP_BUILDING_AND_REPAIRING = LkOccupationTitle(1, "Ship Building and Repairing", 33, 336611)
    BOAT_BUILDING = LkOccupationTitle(1, "Boat Building", 33, 336612)
    OTHER_TRANSPORTATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "Other Transportation Equipment Manufacturing", 33, 3369)
    MOTORCYCLE_BICYCLE_AND_PARTS_MANUFACTURING = LkOccupationTitle(1, "Motorcycle, Bicycle, and Parts Manufacturing", 33, 336991)
    MILITARY_ARMORED_VEHICLE_TANK_AND_TANK_COMPONENT_MANUFACTURING = LkOccupationTitle(1, "Military Armored Vehicle, Tank, and Tank Component Manufacturing", 33, 336992)
    ALL_OTHER_TRANSPORTATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(1, "All Other Transportation Equipment Manufacturing", 33, 336999)
    HOUSEHOLD_AND_INSTITUTIONAL_FURNITURE_AND_KITCHEN_CABINET_MANUFACTURING = LkOccupationTitle(1, "Household and Institutional Furniture and Kitchen Cabinet Manufacturing", 33, 3371)
    WOOD_KITCHEN_CABINET_AND_COUNTERTOP_MANUFACTURING = LkOccupationTitle(1, "Wood Kitchen Cabinet and Countertop Manufacturing", 33, 337110)
    UPHOLSTERED_HOUSEHOLD_FURNITURE_MANUFACTURING = LkOccupationTitle(1, "Upholstered Household Furniture Manufacturing", 33, 337121)
    NONUPHOLSTERED_WOOD_HOUSEHOLD_FURNITURE_MANUFACTURING = LkOccupationTitle(1, "Nonupholstered Wood Household Furniture Manufacturing", 33, 337122)
    METAL_HOUSEHOLD_FURNITURE_MANUFACTURING = LkOccupationTitle(1, "Metal Household Furniture Manufacturing", 33, 337124)
    HOUSEHOLD_FURNITURE_EXCEPT_WOOD_AND_METAL_MANUFACTURING = LkOccupationTitle(1, "Household Furniture (except Wood and Metal) Manufacturing", 33, 337125)
    INSTITUTIONAL_FURNITURE_MANUFACTURING = LkOccupationTitle(1, "Institutional Furniture Manufacturing", 33, 337127)
    OFFICE_FURNITURE_INCLUDING_FIXTURES_MANUFACTURING = LkOccupationTitle(1, "Office Furniture (including Fixtures) Manufacturing", 33, 3372)
    WOOD_OFFICE_FURNITURE_MANUFACTURING = LkOccupationTitle(1, "Wood Office Furniture Manufacturing", 33, 337211)
    CUSTOM_ARCHITECTURAL_WOODWORK_AND_MILLWORK_MANUFACTURING = LkOccupationTitle(1, "Custom Architectural Woodwork and Millwork Manufacturing", 33, 337212)
    OFFICE_FURNITURE_EXCEPT_WOOD_MANUFACTURING = LkOccupationTitle(1, "Office Furniture (except Wood) Manufacturing", 33, 337214)
    SHOWCASE_PARTITION_SHELVING_AND_LOCKER_MANUFACTURING = LkOccupationTitle(1, "Showcase, Partition, Shelving, and Locker Manufacturing", 33, 337215)
    OTHER_FURNITURE_RELATED_PRODUCT_MANUFACTURING = LkOccupationTitle(1, "Other Furniture Related Product Manufacturing", 33, 3379)
    MATTRESS_MANUFACTURING = LkOccupationTitle(1, "Mattress Manufacturing", 33, 337910)
    BLIND_AND_SHADE_MANUFACTURING = LkOccupationTitle(1, "Blind and Shade Manufacturing", 33, 337920)
    MEDICAL_EQUIPMENT_AND_SUPPLIES_MANUFACTURING = LkOccupationTitle(1, "Medical Equipment and Supplies Manufacturing", 33, 3391)
    SURGICAL_AND_MEDICAL_INSTRUMENT_MANUFACTURING = LkOccupationTitle(1, "Surgical and Medical Instrument Manufacturing", 33, 339112)
    SURGICAL_APPLIANCE_AND_SUPPLIES_MANUFACTURING = LkOccupationTitle(1, "Surgical Appliance and Supplies Manufacturing", 33, 339113)
    DENTAL_EQUIPMENT_AND_SUPPLIES_MANUFACTURING = LkOccupationTitle(1, "Dental Equipment and Supplies Manufacturing", 33, 339114)
    OPHTHALMIC_GOODS_MANUFACTURING = LkOccupationTitle(1, "Ophthalmic Goods Manufacturing", 33, 339115)
    DENTAL_LABORATORIES = LkOccupationTitle(1, "Dental Laboratories", 33, 339116)
    OTHER_MISCELLANEOUS_MANUFACTURING = LkOccupationTitle(1, "Other Miscellaneous Manufacturing", 33, 3399)
    JEWELRY_AND_SILVERWARE_MANUFACTURING = LkOccupationTitle(1, "Jewelry and Silverware Manufacturing", 33, 339910)
    SPORTING_AND_ATHLETIC_GOODS_MANUFACTURING = LkOccupationTitle(1, "Sporting and Athletic Goods Manufacturing", 33, 339920)
    DOLL_TOY_AND_GAME_MANUFACTURING = LkOccupationTitle(1, "Doll, Toy, and Game Manufacturing", 33, 339930)
    OFFICE_SUPPLIES_EXCEPT_PAPER_MANUFACTURING = LkOccupationTitle(1, "Office Supplies (except Paper) Manufacturing", 33, 339940)
    SIGN_MANUFACTURING = LkOccupationTitle(1, "Sign Manufacturing", 33, 339950)
    GASKET_PACKING_AND_SEALING_DEVICE_MANUFACTURING = LkOccupationTitle(1, "Gasket, Packing, and Sealing Device Manufacturing", 33, 339991)
    MUSICAL_INSTRUMENT_MANUFACTURING = LkOccupationTitle(1, "Musical Instrument Manufacturing", 33, 339992)
    FASTENER_BUTTON_NEEDLE_AND_PIN_MANUFACTURING = LkOccupationTitle(1, "Fastener, Button, Needle, and Pin Manufacturing", 33, 339993)
    BROOM_BRUSH_AND_MOP_MANUFACTURING = LkOccupationTitle(1, "Broom, Brush, and Mop Manufacturing", 33, 339994)
    BURIAL_CASKET_MANUFACTURING = LkOccupationTitle(1, "Burial Casket Manufacturing", 33, 339995)
    ALL_OTHER_MISCELLANEOUS_MANUFACTURING = LkOccupationTitle(1, "All Other Miscellaneous Manufacturing", 33, 339999)
    MOTOR_VEHICLE_AND_MOTOR_VEHICLE_PARTS_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Motor Vehicle and Motor Vehicle Parts and Supplies Merchant Wholesalers", 42, 4231)
    AUTOMOBILE_AND_OTHER_MOTOR_VEHICLE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Automobile and Other Motor Vehicle Merchant Wholesalers", 42, 423110)
    MOTOR_VEHICLE_SUPPLIES_AND_NEW_PARTS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Motor Vehicle Supplies and New Parts Merchant Wholesalers", 42, 423120)
    TIRE_AND_TUBE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Tire and Tube Merchant Wholesalers", 42, 423130)
    MOTOR_VEHICLE_PARTS_USED_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Motor Vehicle Parts (Used) Merchant Wholesalers", 42, 423140)
    FURNITURE_AND_HOME_FURNISHING_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Furniture and Home Furnishing Merchant Wholesalers", 42, 4232)
    FURNITURE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Furniture Merchant Wholesalers", 42, 423210)
    HOME_FURNISHING_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Home Furnishing Merchant Wholesalers", 42, 423220)
    LUMBER_AND_OTHER_CONSTRUCTION_MATERIALS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Lumber and Other Construction Materials Merchant Wholesalers", 42, 4233)
    LUMBER_PLYWOOD_MILLWORK_AND_WOOD_PANEL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Lumber, Plywood, Millwork, and Wood Panel Merchant Wholesalers", 42, 423310)
    BRICK_STONE_AND_RELATED_CONSTRUCTION_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Brick, Stone, and Related Construction Material Merchant Wholesalers", 42, 423320)
    ROOFING_SIDING_AND_INSULATION_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Roofing, Siding, and Insulation Material Merchant Wholesalers", 42, 423330)
    OTHER_CONSTRUCTION_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Construction Material Merchant Wholesalers", 42, 423390)
    PROFESSIONAL_AND_COMMERCIAL_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Professional and Commercial Equipment and Supplies Merchant Wholesalers", 42, 4234)
    PHOTOGRAPHIC_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Photographic Equipment and Supplies Merchant Wholesalers", 42, 423410)
    OFFICE_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Office Equipment Merchant Wholesalers", 42, 423420)
    COMPUTER_AND_COMPUTER_PERIPHERAL_EQUIPMENT_AND_SOFTWARE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Computer and Computer Peripheral Equipment and Software Merchant Wholesalers", 42, 423430)
    OTHER_COMMERCIAL_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Commercial Equipment Merchant Wholesalers", 42, 423440)
    MEDICAL_DENTAL_AND_HOSPITAL_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Medical, Dental, and Hospital Equipment and Supplies Merchant Wholesalers", 42, 423450)
    OPHTHALMIC_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Ophthalmic Goods Merchant Wholesalers", 42, 423460)
    OTHER_PROFESSIONAL_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Professional Equipment and Supplies Merchant Wholesalers", 42, 423490)
    METAL_AND_MINERAL_EXCEPT_PETROLEUM_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Metal and Mineral (except Petroleum) Merchant Wholesalers", 42, 4235)
    METAL_SERVICE_CENTERS_AND_OTHER_METAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Metal Service Centers and Other Metal Merchant Wholesalers", 42, 423510)
    COAL_AND_OTHER_MINERAL_AND_ORE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Coal and Other Mineral and Ore Merchant Wholesalers", 42, 423520)
    HOUSEHOLD_APPLIANCES_AND_ELECTRICAL_AND_ELECTRONIC_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Household Appliances and Electrical and Electronic Goods Merchant Wholesalers", 42, 4236)
    ELECTRICAL_APPARATUS_AND_EQUIPMENT_WIRING_SUPPLIES_AND_RELATED_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Electrical Apparatus and Equipment, Wiring Supplies, and Related Equipment Merchant Wholesalers", 42, 423610)
    HOUSEHOLD_APPLIANCES_ELECTRIC_HOUSEWARES_AND_CONSUMER_ELECTRONICS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Household Appliances, Electric Housewares, and Consumer Electronics Merchant Wholesalers", 42, 423620)
    OTHER_ELECTRONIC_PARTS_AND_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Electronic Parts and Equipment Merchant Wholesalers", 42, 423690)
    HARDWARE_AND_PLUMBING_AND_HEATING_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Hardware, and Plumbing and Heating Equipment and Supplies Merchant Wholesalers", 42, 4237)
    HARDWARE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Hardware Merchant Wholesalers", 42, 423710)
    PLUMBING_AND_HEATING_EQUIPMENT_AND_SUPPLIES_HYDRONICS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Plumbing and Heating Equipment and Supplies (Hydronics) Merchant Wholesalers", 42, 423720)
    WARM_AIR_HEATING_AND_AIRCONDITIONING_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Warm Air Heating and Air-Conditioning Equipment and Supplies Merchant Wholesalers", 42, 423730)
    REFRIGERATION_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Refrigeration Equipment and Supplies Merchant Wholesalers", 42, 423740)
    MACHINERY_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Machinery, Equipment, and Supplies Merchant Wholesalers", 42, 4238)
    CONSTRUCTION_AND_MINING_EXCEPT_OIL_WELL_MACHINERY_AND_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Construction and Mining (except Oil Well) Machinery and Equipment Merchant Wholesalers220", 42, 423810)
    FARM_AND_GARDEN_MACHINERY_AND_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Farm and Garden Machinery and Equipment Merchant Wholesalers", 42, 423820)
    INDUSTRIAL_MACHINERY_AND_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Industrial Machinery and Equipment Merchant Wholesalers", 42, 423830)
    INDUSTRIAL_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Industrial Supplies Merchant Wholesalers", 42, 423840)
    SERVICE_ESTABLISHMENT_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Service Establishment Equipment and Supplies Merchant Wholesalers", 42, 423850)
    TRANSPORTATION_EQUIPMENT_AND_SUPPLIES_EXCEPT_MOTOR_VEHICLE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Transportation Equipment and Supplies (except Motor Vehicle) Merchant Wholesalers", 42, 423860)
    MISCELLANEOUS_DURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Miscellaneous Durable Goods Merchant Wholesalers", 42, 4239)
    SPORTING_AND_RECREATIONAL_GOODS_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Sporting and Recreational Goods and Supplies Merchant Wholesalers", 42, 423910)
    TOY_AND_HOBBY_GOODS_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Toy and Hobby Goods and Supplies Merchant Wholesalers", 42, 423920)
    RECYCLABLE_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Recyclable Material Merchant Wholesalers", 42, 423930)
    JEWELRY_WATCH_PRECIOUS_STONE_AND_PRECIOUS_METAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Jewelry, Watch, Precious Stone, and Precious Metal Merchant Wholesalers", 42, 423940)
    OTHER_MISCELLANEOUS_DURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Miscellaneous Durable Goods Merchant Wholesalers", 42, 423990)
    PAPER_AND_PAPER_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Paper and Paper Product Merchant Wholesalers", 42, 4241)
    PRINTING_AND_WRITING_PAPER_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Printing and Writing Paper Merchant Wholesalers", 42, 424110)
    STATIONERY_AND_OFFICE_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Stationery and Office Supplies Merchant Wholesalers", 42, 424120)
    INDUSTRIAL_AND_PERSONAL_SERVICE_PAPER_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Industrial and Personal Service Paper Merchant Wholesalers", 42, 424130)
    DRUGS_AND_DRUGGISTS_SUNDRIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Drugs and Druggists' Sundries Merchant Wholesalers", 42, 4242)
    DRUGS_AND_DRUGGISTS_SUNDRIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Drugs and Druggists' Sundries Merchant Wholesalers", 42, 424210)
    APPAREL_PIECE_GOODS_AND_NOTIONS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Apparel, Piece Goods, and Notions Merchant Wholesalers", 42, 4243)
    PIECE_GOODS_NOTIONS_AND_OTHER_DRY_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Piece Goods, Notions, and Other Dry Goods Merchant Wholesalers", 42, 424310)
    MENS_AND_BOYS_CLOTHING_AND_FURNISHINGS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Men's and Boys' Clothing and Furnishings Merchant Wholesalers", 42, 424320)
    WOMENS_CHILDRENS_AND_INFANTS_CLOTHING_AND_ACCESSORIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Women's, Children's, and Infants' Clothing and Accessories Merchant Wholesalers", 42, 424330)
    FOOTWEAR_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Footwear Merchant Wholesalers", 42, 424340)
    GROCERY_AND_RELATED_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Grocery and Related Product Merchant Wholesalers", 42, 4244)
    GENERAL_LINE_GROCERY_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "General Line Grocery Merchant Wholesalers", 42, 424410)
    PACKAGED_FROZEN_FOOD_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Packaged Frozen Food Merchant Wholesalers", 42, 424420)
    DAIRY_PRODUCT_EXCEPT_DRIED_OR_CANNED_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Dairy Product (except Dried or Canned) Merchant Wholesalers", 42, 424430)
    POULTRY_AND_POULTRY_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Poultry and Poultry Product Merchant Wholesalers", 42, 424440)
    CONFECTIONERY_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Confectionery Merchant Wholesalers", 42, 424450)
    FISH_AND_SEAFOOD_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Fish and Seafood Merchant Wholesalers", 42, 424460)
    MEAT_AND_MEAT_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Meat and Meat Product Merchant Wholesalers", 42, 424470)
    FRESH_FRUIT_AND_VEGETABLE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Fresh Fruit and Vegetable Merchant Wholesalers", 42, 424480)
    OTHER_GROCERY_AND_RELATED_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Grocery and Related Products Merchant Wholesalers", 42, 424490)
    FARM_PRODUCT_RAW_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Farm Product Raw Material Merchant Wholesalers", 42, 4245)
    GRAIN_AND_FIELD_BEAN_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Grain and Field Bean Merchant Wholesalers", 42, 424510)
    LIVESTOCK_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Livestock Merchant Wholesalers", 42, 424520)
    OTHER_FARM_PRODUCT_RAW_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Farm Product Raw Material Merchant Wholesalers", 42, 424590)
    CHEMICAL_AND_ALLIED_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Chemical and Allied Products Merchant Wholesalers", 42, 4246)
    PLASTICS_MATERIALS_AND_BASIC_FORMS_AND_SHAPES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Plastics Materials and Basic Forms and Shapes Merchant Wholesalers", 42, 424610)
    OTHER_CHEMICAL_AND_ALLIED_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Chemical and Allied Products Merchant Wholesalers", 42, 424690)
    PETROLEUM_AND_PETROLEUM_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Petroleum and Petroleum Products Merchant Wholesalers", 42, 4247)
    PETROLEUM_BULK_STATIONS_AND_TERMINALS = LkOccupationTitle(1, "Petroleum Bulk Stations and Terminals", 42, 424710)
    PETROLEUM_AND_PETROLEUM_PRODUCTS_MERCHANT_WHOLESALERS_EXCEPT_BULK_STATIONS_AND_TERMINALS = LkOccupationTitle(1, "Petroleum and Petroleum Products Merchant Wholesalers (except Bulk Stations and Terminals)", 42, 424720)
    BEER_WINE_AND_DISTILLED_ALCOHOLIC_BEVERAGE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Beer, Wine, and Distilled Alcoholic Beverage Merchant Wholesalers", 42, 4248)
    BEER_AND_ALE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Beer and Ale Merchant Wholesalers", 42, 424810)
    WINE_AND_DISTILLED_ALCOHOLIC_BEVERAGE_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Wine and Distilled Alcoholic Beverage Merchant Wholesalers", 42, 424820)
    MISCELLANEOUS_NONDURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Miscellaneous Nondurable Goods Merchant Wholesalers", 42, 4249)
    FARM_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Farm Supplies Merchant Wholesalers", 42, 424910)
    BOOK_PERIODICAL_AND_NEWSPAPER_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Book, Periodical, and Newspaper Merchant Wholesalers", 42, 424920)
    FLOWER_NURSERY_STOCK_AND_FLORISTS_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Flower, Nursery Stock, and Florists' Supplies Merchant Wholesalers", 42, 424930)
    TOBACCO_AND_TOBACCO_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Tobacco and Tobacco Product Merchant Wholesalers", 42, 424940)
    PAINT_VARNISH_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Paint, Varnish, and Supplies Merchant Wholesalers", 42, 424950)
    OTHER_MISCELLANEOUS_NONDURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(1, "Other Miscellaneous Nondurable Goods Merchant Wholesalers", 42, 424990)
    WHOLESALE_ELECTRONIC_MARKETS_AND_AGENTS_AND_BROKERS = LkOccupationTitle(1, "Wholesale Electronic Markets and Agents and Brokers", 42, 4251)
    BUSINESS_TO_BUSINESS_ELECTRONIC_MARKETS = LkOccupationTitle(1, "Business to Business Electronic Markets", 42, 425110)
    WHOLESALE_TRADE_AGENTS_AND_BROKERS = LkOccupationTitle(1, "Wholesale Trade Agents and Brokers", 42, 425120)
    RETAIL_TRADE = LkOccupationTitle(1, "Retail Trade", 44, 44-45)
    AUTOMOBILE_DEALERS = LkOccupationTitle(1, "Automobile Dealers", 44, 4411)
    NEW_CAR_DEALERS = LkOccupationTitle(1, "New Car Dealers", 44, 441110)
    USED_CAR_DEALERS = LkOccupationTitle(1, "Used Car Dealers", 44, 441120)
    OTHER_MOTOR_VEHICLE_DEALERS = LkOccupationTitle(1, "Other Motor Vehicle Dealers", 44, 4412)
    RECREATIONAL_VEHICLE_DEALERS = LkOccupationTitle(1, "Recreational Vehicle Dealers", 44, 441210)
    BOAT_DEALERS = LkOccupationTitle(1, "Boat Dealers", 44, 441222)
    MOTORCYCLE_ATV_AND_ALL_OTHER_MOTOR_VEHICLE_DEALERS = LkOccupationTitle(1, "Motorcycle, ATV, and All Other Motor Vehicle Dealers", 44, 441228)
    AUTOMOTIVE_PARTS_ACCESSORIES_AND_TIRE_STORES = LkOccupationTitle(1, "Automotive Parts, Accessories, and Tire Stores", 44, 4413)
    AUTOMOTIVE_PARTS_AND_ACCESSORIES_STORES = LkOccupationTitle(1, "Automotive Parts and Accessories Stores", 44, 441310)
    TIRE_DEALERS = LkOccupationTitle(1, "Tire Dealers", 44, 441320)
    FURNITURE_STORES = LkOccupationTitle(1, "Furniture Stores", 44, 4421)
    FURNITURE_STORES = LkOccupationTitle(1, "Furniture Stores", 44, 442110)
    HOME_FURNISHINGS_STORES = LkOccupationTitle(1, "Home Furnishings Stores", 44, 4422)
    FLOOR_COVERING_STORES = LkOccupationTitle(1, "Floor Covering Stores", 44, 442210)
    WINDOW_TREATMENT_STORES = LkOccupationTitle(1, "Window Treatment Stores", 44, 442291)
    ALL_OTHER_HOME_FURNISHINGS_STORES = LkOccupationTitle(1, "All Other Home Furnishings Stores", 44, 442299)
    ELECTRONICS_AND_APPLIANCE_STORES = LkOccupationTitle(1, "Electronics and Appliance Stores", 44, 4431)
    HOUSEHOLD_APPLIANCE_STORES = LkOccupationTitle(1, "Household Appliance Stores", 44, 443141)
    ELECTRONICS_STORES = LkOccupationTitle(1, "Electronics Stores", 44, 443142)
    BUILDING_MATERIAL_AND_SUPPLIES_DEALERS = LkOccupationTitle(1, "Building Material and Supplies Dealers", 44, 4441)
    HOME_CENTERS = LkOccupationTitle(1, "Home Centers", 44, 444110)
    PAINT_AND_WALLPAPER_STORES = LkOccupationTitle(1, "Paint and Wallpaper Stores", 44, 444120)
    HARDWARE_STORES = LkOccupationTitle(1, "Hardware Stores", 44, 444130)
    OTHER_BUILDING_MATERIAL_DEALERS = LkOccupationTitle(1, "Other Building Material Dealers", 44, 444190)
    LAWN_AND_GARDEN_EQUIPMENT_AND_SUPPLIES_STORES = LkOccupationTitle(1, "Lawn and Garden Equipment and Supplies Stores", 44, 4442)
    OUTDOOR_POWER_EQUIPMENT_STORES = LkOccupationTitle(1, "Outdoor Power Equipment Stores", 44, 444210)
    NURSERY_GARDEN_CENTER_AND_FARM_SUPPLY_STORES = LkOccupationTitle(1, "Nursery, Garden Center, and Farm Supply Stores", 44, 444220)
    GROCERY_STORES = LkOccupationTitle(1, "Grocery Stores", 44, 4451)
    SUPERMARKETS_AND_OTHER_GROCERY_EXCEPT_CONVENIENCE_STORES = LkOccupationTitle(1, "Supermarkets and Other Grocery (except Convenience) Stores", 44, 445110)
    CONVENIENCE_STORES = LkOccupationTitle(1, "Convenience Stores", 44, 445120)
    SPECIALTY_FOOD_STORES = LkOccupationTitle(1, "Specialty Food Stores", 44, 4452)
    MEAT_MARKETS = LkOccupationTitle(1, "Meat Markets", 44, 445210)
    FISH_AND_SEAFOOD_MARKETS = LkOccupationTitle(1, "Fish and Seafood Markets", 44, 445220)
    FRUIT_AND_VEGETABLE_MARKETS = LkOccupationTitle(1, "Fruit and Vegetable Markets", 44, 445230)
    BAKED_GOODS_STORES = LkOccupationTitle(1, "Baked Goods Stores", 44, 445291)
    CONFECTIONERY_AND_NUT_STORES = LkOccupationTitle(1, "Confectionery and Nut Stores", 44, 445292)
    ALL_OTHER_SPECIALTY_FOOD_STORES = LkOccupationTitle(1, "All Other Specialty Food Stores", 44, 445299)
    BEER_WINE_AND_LIQUOR_STORES = LkOccupationTitle(1, "Beer, Wine, and Liquor Stores", 44, 4453)
    BEER_WINE_AND_LIQUOR_STORES = LkOccupationTitle(1, "Beer, Wine, and Liquor Stores", 44, 445310)
    HEALTH_AND_PERSONAL_CARE_STORES = LkOccupationTitle(1, "Health and Personal Care Stores", 44, 4461)
    PHARMACIES_AND_DRUG_STORES = LkOccupationTitle(1, "Pharmacies and Drug Stores", 44, 446110)
    COSMETICS_BEAUTY_SUPPLIES_AND_PERFUME_STORES = LkOccupationTitle(1, "Cosmetics, Beauty Supplies, and Perfume Stores", 44, 446120)
    OPTICAL_GOODS_STORES = LkOccupationTitle(1, "Optical Goods Stores", 44, 446130)
    FOOD_HEALTH_SUPPLEMENT_STORES = LkOccupationTitle(1, "Food (Health) Supplement Stores", 44, 446191)
    ALL_OTHER_HEALTH_AND_PERSONAL_CARE_STORES = LkOccupationTitle(1, "All Other Health and Personal Care Stores", 44, 446199)
    GASOLINE_STATIONS = LkOccupationTitle(1, "Gasoline Stations", 44, 4471)
    GASOLINE_STATIONS_WITH_CONVENIENCE_STORES = LkOccupationTitle(1, "Gasoline Stations with Convenience Stores", 44, 447110)
    OTHER_GASOLINE_STATIONS = LkOccupationTitle(1, "Other Gasoline Stations", 44, 447190)
    CLOTHING_STORES = LkOccupationTitle(1, "Clothing Stores", 44, 4481)
    MENS_CLOTHING_STORES = LkOccupationTitle(1, "Men's Clothing Stores", 44, 448110)
    WOMENS_CLOTHING_STORES = LkOccupationTitle(1, "Women's Clothing Stores", 44, 448120)
    CHILDRENS_AND_INFANTS_CLOTHING_STORES = LkOccupationTitle(1, "Children's and Infants' Clothing Stores", 44, 448130)
    FAMILY_CLOTHING_STORES = LkOccupationTitle(1, "Family Clothing Stores", 44, 448140)
    CLOTHING_ACCESSORIES_STORES = LkOccupationTitle(1, "Clothing Accessories Stores", 44, 448150)
    OTHER_CLOTHING_STORES = LkOccupationTitle(1, "Other Clothing Stores", 44, 448190)
    SHOE_STORES = LkOccupationTitle(1, "Shoe Stores", 44, 4482)
    SHOE_STORES = LkOccupationTitle(1, "Shoe Stores", 44, 448210)
    JEWELRY_LUGGAGE_AND_LEATHER_GOODS_STORES = LkOccupationTitle(1, "Jewelry, Luggage, and Leather Goods Stores", 44, 4483)
    JEWELRY_STORES = LkOccupationTitle(1, "Jewelry Stores", 44, 448310)
    LUGGAGE_AND_LEATHER_GOODS_STORES = LkOccupationTitle(1, "Luggage and Leather Goods Stores", 44, 448320)
    SPORTING_GOODS_HOBBY_AND_MUSICAL_INSTRUMENT_STORES = LkOccupationTitle(1, "Sporting Goods, Hobby, and Musical Instrument Stores", 45, 4511)
    SPORTING_GOODS_STORES = LkOccupationTitle(1, "Sporting Goods Stores", 45, 451110)
    HOBBY_TOY_AND_GAME_STORES = LkOccupationTitle(1, "Hobby, Toy, and Game Stores", 45, 451120)
    SEWING_NEEDLEWORK_AND_PIECE_GOODS_STORES = LkOccupationTitle(1, "Sewing, Needlework, and Piece Goods Stores", 45, 451130)
    MUSICAL_INSTRUMENT_AND_SUPPLIES_STORES = LkOccupationTitle(1, "Musical Instrument and Supplies Stores", 45, 451140)
    BOOK_STORES_AND_NEWS_DEALERS = LkOccupationTitle(1, "Book Stores and News Dealers", 45, 4512)
    BOOK_STORES = LkOccupationTitle(1, "Book Stores", 45, 451211)
    NEWS_DEALERS_AND_NEWSSTANDS = LkOccupationTitle(1, "News Dealers and Newsstands", 45, 451212)
    DEPARTMENT_STORES = LkOccupationTitle(1, "Department Stores", 45, 4522)
    DEPARTMENT_STORES = LkOccupationTitle(1, "Department Stores", 45, 452210)
    GENERAL_MERCHANDISE_STORES_INCLUDING_WAREHOUSE_CLUBS_AND_SUPERCENTERS = LkOccupationTitle(1, "General Merchandise Stores, including Warehouse Clubs and Supercenters", 45, 4523)
    WAREHOUSE_CLUBS_AND_SUPERCENTERS = LkOccupationTitle(1, "Warehouse Clubs and Supercenters", 45, 452311)
    ALL_OTHER_GENERAL_MERCHANDISE_STORES = LkOccupationTitle(1, "All Other General Merchandise Stores", 45, 452319)
    FLORISTS = LkOccupationTitle(1, "Florists", 45, 4531)
    FLORISTS = LkOccupationTitle(1, "Florists", 45, 453110)
    OFFICE_SUPPLIES_STATIONERY_AND_GIFT_STORES = LkOccupationTitle(1, "Office Supplies, Stationery, and Gift Stores", 45, 4532)
    OFFICE_SUPPLIES_AND_STATIONERY_STORES = LkOccupationTitle(1, "Office Supplies and Stationery Stores", 45, 453210)
    GIFT_NOVELTY_AND_SOUVENIR_STORES = LkOccupationTitle(1, "Gift, Novelty, and Souvenir Stores", 45, 453220)
    USED_MERCHANDISE_STORES = LkOccupationTitle(1, "Used Merchandise Stores", 45, 4533)
    USED_MERCHANDISE_STORES = LkOccupationTitle(1, "Used Merchandise Stores", 45, 453310)
    OTHER_MISCELLANEOUS_STORE_RETAILERS = LkOccupationTitle(1, "Other Miscellaneous Store Retailers", 45, 4539)
    PET_AND_PET_SUPPLIES_STORES = LkOccupationTitle(1, "Pet and Pet Supplies Stores", 45, 453910)
    ART_DEALERS = LkOccupationTitle(1, "Art Dealers", 45, 453920)
    MANUFACTURED_MOBILE_HOME_DEALERS = LkOccupationTitle(1, "Manufactured (Mobile) Home Dealers", 45, 453930)
    TOBACCO_STORES = LkOccupationTitle(1, "Tobacco Stores", 45, 453991)
    ALL_OTHER_MISCELLANEOUS_STORE_RETAILERS_EXCEPT_TOBACCO_STORES = LkOccupationTitle(1, "All Other Miscellaneous Store Retailers (except Tobacco Stores)", 45, 453998)
    ELECTRONIC_SHOPPING_AND_MAILORDER_HOUSES = LkOccupationTitle(1, "Electronic Shopping and Mail-Order Houses", 45, 4541)
    ELECTRONIC_SHOPPING_AND_MAILORDER_HOUSES = LkOccupationTitle(1, "Electronic Shopping and Mail-Order Houses", 45, 454110)
    VENDING_MACHINE_OPERATORS = LkOccupationTitle(1, "Vending Machine Operators", 45, 4542)
    VENDING_MACHINE_OPERATORS = LkOccupationTitle(1, "Vending Machine Operators", 45, 454210)
    DIRECT_SELLING_ESTABLISHMENTS = LkOccupationTitle(1, "Direct Selling Establishments", 45, 4543)
    FUEL_DEALERS = LkOccupationTitle(1, "Fuel Dealers", 45, 454310)
    OTHER_DIRECT_SELLING_ESTABLISHMENTS = LkOccupationTitle(1, "Other Direct Selling Establishments", 45, 454390)
    TRANSPORTATION_AND_WAREHOUSING = LkOccupationTitle(1, "Transportation and Warehousing", 48, 48-49)
    SCHEDULED_AIR_TRANSPORTATION = LkOccupationTitle(1, "Scheduled Air Transportation", 48, 4811)
    SCHEDULED_PASSENGER_AIR_TRANSPORTATION = LkOccupationTitle(1, "Scheduled Passenger Air Transportation", 48, 481111)
    SCHEDULED_FREIGHT_AIR_TRANSPORTATION = LkOccupationTitle(1, "Scheduled Freight Air Transportation", 48, 481112)
    NONSCHEDULED_AIR_TRANSPORTATION = LkOccupationTitle(1, "Nonscheduled Air Transportation", 48, 4812)
    NONSCHEDULED_CHARTERED_PASSENGER_AIR_TRANSPORTATION = LkOccupationTitle(1, "Nonscheduled Chartered Passenger Air Transportation", 48, 481211)
    NONSCHEDULED_CHARTERED_FREIGHT_AIR_TRANSPORTATION = LkOccupationTitle(1, "Nonscheduled Chartered Freight Air Transportation", 48, 481212)
    OTHER_NONSCHEDULED_AIR_TRANSPORTATION = LkOccupationTitle(1, "Other Nonscheduled Air Transportation", 48, 481219)
    RAIL_TRANSPORTATION = LkOccupationTitle(1, "Rail Transportation", 48, 4821)
    LINEHAUL_RAILROADS = LkOccupationTitle(1, "Line-Haul Railroads", 48, 482111)
    SHORT_LINE_RAILROADS = LkOccupationTitle(1, "Short Line Railroads", 48, 482112)
    DEEP_SEA_COASTAL_AND_GREAT_LAKES_WATER_TRANSPORTATION = LkOccupationTitle(1, "Deep Sea, Coastal, and Great Lakes Water Transportation", 48, 4831)
    DEEP_SEA_FREIGHT_TRANSPORTATION = LkOccupationTitle(1, "Deep Sea Freight Transportation", 48, 483111)
    DEEP_SEA_PASSENGER_TRANSPORTATION = LkOccupationTitle(1, "Deep Sea Passenger Transportation", 48, 483112)
    COASTAL_AND_GREAT_LAKES_FREIGHT_TRANSPORTATION = LkOccupationTitle(1, "Coastal and Great Lakes Freight Transportation", 48, 483113)
    COASTAL_AND_GREAT_LAKES_PASSENGER_TRANSPORTATION = LkOccupationTitle(1, "Coastal and Great Lakes Passenger Transportation", 48, 483114)
    INLAND_WATER_TRANSPORTATION = LkOccupationTitle(1, "Inland Water Transportation", 48, 4832)
    INLAND_WATER_FREIGHT_TRANSPORTATION = LkOccupationTitle(1, "Inland Water Freight Transportation", 48, 483211)
    INLAND_WATER_PASSENGER_TRANSPORTATION = LkOccupationTitle(1, "Inland Water Passenger Transportation", 48, 483212)
    GENERAL_FREIGHT_TRUCKING = LkOccupationTitle(1, "General Freight Trucking", 48, 4841)
    GENERAL_FREIGHT_TRUCKING_LOCAL = LkOccupationTitle(1, "General Freight Trucking, Local", 48, 484110)
    GENERAL_FREIGHT_TRUCKING_LONGDISTANCE_TRUCKLOAD = LkOccupationTitle(1, "General Freight Trucking, Long-Distance, Truckload", 48, 484121)
    GENERAL_FREIGHT_TRUCKING_LONGDISTANCE_LESS_THAN_TRUCKLOAD = LkOccupationTitle(1, "General Freight Trucking, Long-Distance, Less Than Truckload", 48, 484122)
    SPECIALIZED_FREIGHT_TRUCKING = LkOccupationTitle(1, "Specialized Freight Trucking", 48, 4842)
    USED_HOUSEHOLD_AND_OFFICE_GOODS_MOVING = LkOccupationTitle(1, "Used Household and Office Goods Moving", 48, 484210)
    SPECIALIZED_FREIGHT_EXCEPT_USED_GOODS_TRUCKING_LOCAL = LkOccupationTitle(1, "Specialized Freight (except Used Goods) Trucking, Local", 48, 484220)
    SPECIALIZED_FREIGHT_EXCEPT_USED_GOODS_TRUCKING_LONGDISTANCE = LkOccupationTitle(1, "Specialized Freight (except Used Goods) Trucking, Long-Distance", 48, 484230)
    URBAN_TRANSIT_SYSTEMS = LkOccupationTitle(1, "Urban Transit Systems", 48, 4851)
    MIXED_MODE_TRANSIT_SYSTEMS = LkOccupationTitle(1, "Mixed Mode Transit Systems", 48, 485111)
    COMMUTER_RAIL_SYSTEMS = LkOccupationTitle(1, "Commuter Rail Systems", 48, 485112)
    BUS_AND_OTHER_MOTOR_VEHICLE_TRANSIT_SYSTEMS = LkOccupationTitle(1, "Bus and Other Motor Vehicle Transit Systems", 48, 485113)
    OTHER_URBAN_TRANSIT_SYSTEMS = LkOccupationTitle(1, "Other Urban Transit Systems", 48, 485119)
    INTERURBAN_AND_RURAL_BUS_TRANSPORTATION = LkOccupationTitle(1, "Interurban and Rural Bus Transportation", 48, 4852)
    INTERURBAN_AND_RURAL_BUS_TRANSPORTATION = LkOccupationTitle(1, "Interurban and Rural Bus Transportation", 48, 485210)
    TAXI_AND_LIMOUSINE_SERVICE = LkOccupationTitle(1, "Taxi and Limousine Service", 48, 4853)
    TAXI_SERVICE = LkOccupationTitle(1, "Taxi Service", 48, 485310)
    LIMOUSINE_SERVICE = LkOccupationTitle(1, "Limousine Service", 48, 485320)
    SCHOOL_AND_EMPLOYEE_BUS_TRANSPORTATION = LkOccupationTitle(1, "School and Employee Bus Transportation", 48, 4854)
    SCHOOL_AND_EMPLOYEE_BUS_TRANSPORTATION = LkOccupationTitle(1, "School and Employee Bus Transportation", 48, 485410)
    CHARTER_BUS_INDUSTRY = LkOccupationTitle(1, "Charter Bus Industry", 48, 4855)
    CHARTER_BUS_INDUSTRY = LkOccupationTitle(1, "Charter Bus Industry", 48, 485510)
    OTHER_TRANSIT_AND_GROUND_PASSENGER_TRANSPORTATION = LkOccupationTitle(1, "Other Transit and Ground Passenger Transportation", 48, 4859)
    SPECIAL_NEEDS_TRANSPORTATION = LkOccupationTitle(1, "Special Needs Transportation", 48, 485991)
    ALL_OTHER_TRANSIT_AND_GROUND_PASSENGER_TRANSPORTATION = LkOccupationTitle(1, "All Other Transit and Ground Passenger Transportation", 48, 485999)
    PIPELINE_TRANSPORTATION_OF_CRUDE_OIL = LkOccupationTitle(1, "Pipeline Transportation of Crude Oil", 48, 4861)
    PIPELINE_TRANSPORTATION_OF_CRUDE_OIL = LkOccupationTitle(1, "Pipeline Transportation of Crude Oil", 48, 486110)
    PIPELINE_TRANSPORTATION_OF_NATURAL_GAS = LkOccupationTitle(1, "Pipeline Transportation of Natural Gas", 48, 4862)
    PIPELINE_TRANSPORTATION_OF_NATURAL_GAS = LkOccupationTitle(1, "Pipeline Transportation of Natural Gas", 48, 486210)
    OTHER_PIPELINE_TRANSPORTATION = LkOccupationTitle(1, "Other Pipeline Transportation", 48, 4869)
    PIPELINE_TRANSPORTATION_OF_REFINED_PETROLEUM_PRODUCTS = LkOccupationTitle(1, "Pipeline Transportation of Refined Petroleum Products", 48, 486910)
    ALL_OTHER_PIPELINE_TRANSPORTATION = LkOccupationTitle(1, "All Other Pipeline Transportation", 48, 486990)
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_LAND = LkOccupationTitle(1, "Scenic and Sightseeing Transportation, Land", 48, 4871)
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_LAND = LkOccupationTitle(1, "Scenic and Sightseeing Transportation, Land", 48, 487110)
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_WATER = LkOccupationTitle(1, "Scenic and Sightseeing Transportation, Water", 48, 4872)
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_WATER = LkOccupationTitle(1, "Scenic and Sightseeing Transportation, Water", 48, 487210)
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_OTHER = LkOccupationTitle(1, "Scenic and Sightseeing Transportation, Other", 48, 4879)
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_OTHER = LkOccupationTitle(1, "Scenic and Sightseeing Transportation, Other", 48, 487990)
    SUPPORT_ACTIVITIES_FOR_AIR_TRANSPORTATION = LkOccupationTitle(1, "Support Activities for Air Transportation", 48, 4881)
    AIR_TRAFFIC_CONTROL = LkOccupationTitle(1, "Air Traffic Control", 48, 488111)
    OTHER_AIRPORT_OPERATIONS = LkOccupationTitle(1, "Other Airport Operations", 48, 488119)
    OTHER_SUPPORT_ACTIVITIES_FOR_AIR_TRANSPORTATION = LkOccupationTitle(1, "Other Support Activities for Air Transportation", 48, 488190)
    SUPPORT_ACTIVITIES_FOR_RAIL_TRANSPORTATION = LkOccupationTitle(1, "Support Activities for Rail Transportation", 48, 4882)
    SUPPORT_ACTIVITIES_FOR_RAIL_TRANSPORTATION = LkOccupationTitle(1, "Support Activities for Rail Transportation", 48, 488210)
    SUPPORT_ACTIVITIES_FOR_WATER_TRANSPORTATION = LkOccupationTitle(1, "Support Activities for Water Transportation", 48, 4883)
    PORT_AND_HARBOR_OPERATIONS = LkOccupationTitle(1, "Port and Harbor Operations", 48, 488310)
    MARINE_CARGO_HANDLING = LkOccupationTitle(1, "Marine Cargo Handling", 48, 488320)
    NAVIGATIONAL_SERVICES_TO_SHIPPING = LkOccupationTitle(1, "Navigational Services to Shipping", 48, 488330)
    OTHER_SUPPORT_ACTIVITIES_FOR_WATER_TRANSPORTATION = LkOccupationTitle(1, "Other Support Activities for Water Transportation", 48, 488390)
    SUPPORT_ACTIVITIES_FOR_ROAD_TRANSPORTATION = LkOccupationTitle(1, "Support Activities for Road Transportation", 48, 4884)
    MOTOR_VEHICLE_TOWING = LkOccupationTitle(1, "Motor Vehicle Towing", 48, 488410)
    OTHER_SUPPORT_ACTIVITIES_FOR_ROAD_TRANSPORTATION = LkOccupationTitle(1, "Other Support Activities for Road Transportation", 48, 488490)
    FREIGHT_TRANSPORTATION_ARRANGEMENT = LkOccupationTitle(1, "Freight Transportation Arrangement", 48, 4885)
    FREIGHT_TRANSPORTATION_ARRANGEMENT = LkOccupationTitle(1, "Freight Transportation Arrangement", 48, 488510)
    OTHER_SUPPORT_ACTIVITIES_FOR_TRANSPORTATION = LkOccupationTitle(1, "Other Support Activities for Transportation", 48, 4889)
    PACKING_AND_CRATING = LkOccupationTitle(1, "Packing and Crating", 48, 488991)
    ALL_OTHER_SUPPORT_ACTIVITIES_FOR_TRANSPORTATION = LkOccupationTitle(1, "All Other Support Activities for Transportation", 48, 488999)
    POSTAL_SERVICE = LkOccupationTitle(1, "Postal Service", 49, 4911)
    POSTAL_SERVICE = LkOccupationTitle(1, "Postal Service", 49, 491110)
    COURIERS_AND_EXPRESS_DELIVERY_SERVICES = LkOccupationTitle(1, "Couriers and Express Delivery Services", 49, 4921)
    COURIERS_AND_EXPRESS_DELIVERY_SERVICES = LkOccupationTitle(1, "Couriers and Express Delivery Services", 49, 492110)
    LOCAL_MESSENGERS_AND_LOCAL_DELIVERY = LkOccupationTitle(1, "Local Messengers and Local Delivery", 49, 4922)
    LOCAL_MESSENGERS_AND_LOCAL_DELIVERY = LkOccupationTitle(1, "Local Messengers and Local Delivery", 49, 492210)
    WAREHOUSING_AND_STORAGE = LkOccupationTitle(1, "Warehousing and Storage", 49, 4931)
    GENERAL_WAREHOUSING_AND_STORAGE = LkOccupationTitle(1, "General Warehousing and Storage", 49, 493110)
    REFRIGERATED_WAREHOUSING_AND_STORAGE = LkOccupationTitle(1, "Refrigerated Warehousing and Storage", 49, 493120)
    FARM_PRODUCT_WAREHOUSING_AND_STORAGE = LkOccupationTitle(1, "Farm Product Warehousing and Storage", 49, 493130)
    OTHER_WAREHOUSING_AND_STORAGE = LkOccupationTitle(1, "Other Warehousing and Storage", 49, 493190)
    NEWSPAPER_PERIODICAL_BOOK_AND_DIRECTORY_PUBLISHERS = LkOccupationTitle(1, "Newspaper, Periodical, Book, and Directory Publishers", 51, 5111)
    NEWSPAPER_PUBLISHERS = LkOccupationTitle(1, "Newspaper Publishers", 51, 511110)
    PERIODICAL_PUBLISHERS = LkOccupationTitle(1, "Periodical Publishers", 51, 511120)
    BOOK_PUBLISHERS = LkOccupationTitle(1, "Book Publishers", 51, 511130)
    DIRECTORY_AND_MAILING_LIST_PUBLISHERS = LkOccupationTitle(1, "Directory and Mailing List Publishers", 51, 511140)
    GREETING_CARD_PUBLISHERS = LkOccupationTitle(1, "Greeting Card Publishers", 51, 511191)
    ALL_OTHER_PUBLISHERS = LkOccupationTitle(1, "All Other Publishers", 51, 511199)
    SOFTWARE_PUBLISHERS = LkOccupationTitle(1, "Software Publishers", 51, 5112)
    SOFTWARE_PUBLISHERS = LkOccupationTitle(1, "Software Publishers", 51, 511210)
    MOTION_PICTURE_AND_VIDEO_INDUSTRIES = LkOccupationTitle(1, "Motion Picture and Video Industries", 51, 5121)
    MOTION_PICTURE_AND_VIDEO_PRODUCTION = LkOccupationTitle(1, "Motion Picture and Video Production", 51, 512110)
    MOTION_PICTURE_AND_VIDEO_DISTRIBUTION = LkOccupationTitle(1, "Motion Picture and Video Distribution", 51, 512120)
    MOTION_PICTURE_THEATERS_EXCEPT_DRIVEINS = LkOccupationTitle(1, "Motion Picture Theaters (except Drive-Ins)", 51, 512131)
    DRIVEIN_MOTION_PICTURE_THEATERS = LkOccupationTitle(1, "Drive-In Motion Picture Theaters", 51, 512132)
    TELEPRODUCTION_AND_OTHER_POSTPRODUCTION_SERVICES = LkOccupationTitle(1, "Teleproduction and Other Postproduction Services", 51, 512191)
    OTHER_MOTION_PICTURE_AND_VIDEO_INDUSTRIES = LkOccupationTitle(1, "Other Motion Picture and Video Industries", 51, 512199)
    SOUND_RECORDING_INDUSTRIES = LkOccupationTitle(1, "Sound Recording Industries", 51, 5122)
    MUSIC_PUBLISHERS = LkOccupationTitle(1, "Music Publishers", 51, 512230)
    SOUND_RECORDING_STUDIOS = LkOccupationTitle(1, "Sound Recording Studios", 51, 512240)
    RECORD_PRODUCTION_AND_DISTRIBUTION = LkOccupationTitle(1, "Record Production and Distribution", 51, 512250)
    OTHER_SOUND_RECORDING_INDUSTRIES = LkOccupationTitle(1, "Other Sound Recording Industries", 51, 512290)
    RADIO_AND_TELEVISION_BROADCASTING = LkOccupationTitle(1, "Radio and Television Broadcasting", 51, 5151)
    RADIO_NETWORKS = LkOccupationTitle(1, "Radio Networks", 51, 515111)
    RADIO_STATIONS = LkOccupationTitle(1, "Radio Stations", 51, 515112)
    TELEVISION_BROADCASTING = LkOccupationTitle(1, "Television Broadcasting", 51, 515120)
    CABLE_AND_OTHER_SUBSCRIPTION_PROGRAMMING = LkOccupationTitle(1, "Cable and Other Subscription Programming", 51, 5152)
    CABLE_AND_OTHER_SUBSCRIPTION_PROGRAMMING = LkOccupationTitle(1, "Cable and Other Subscription Programming", 51, 515210)
    WIRED_AND_WIRELESS_TELECOMMUNICATIONS_CARRIERS = LkOccupationTitle(1, "Wired and Wireless Telecommunications Carriers", 51, 5173)
    WIRED_TELECOMMUNICATIONS_CARRIERS = LkOccupationTitle(1, "Wired Telecommunications Carriers", 51, 517311)
    WIRELESS_TELECOMMUNICATIONS_CARRIERS_EXCEPT_SATELLITE = LkOccupationTitle(1, "Wireless Telecommunications Carriers (except Satellite)", 51, 517312)
    SATELLITE_TELECOMMUNICATIONS = LkOccupationTitle(1, "Satellite Telecommunications", 51, 5174)
    SATELLITE_TELECOMMUNICATIONS = LkOccupationTitle(1, "Satellite Telecommunications", 51, 517410)
    OTHER_TELECOMMUNICATIONS = LkOccupationTitle(1, "Other Telecommunications", 51, 5179)
    TELECOMMUNICATIONS_RESELLERS = LkOccupationTitle(1, "Telecommunications Resellers", 51, 517911)
    ALL_OTHER_TELECOMMUNICATIONS = LkOccupationTitle(1, "All Other Telecommunications", 51, 517919)
    DATA_PROCESSING_HOSTING_AND_RELATED_SERVICES = LkOccupationTitle(1, "Data Processing, Hosting, and Related Services", 51, 5182)
    DATA_PROCESSING_HOSTING_AND_RELATED_SERVICES = LkOccupationTitle(1, "Data Processing, Hosting, and Related Services", 51, 518210)
    OTHER_INFORMATION_SERVICES = LkOccupationTitle(1, "Other Information Services", 51, 5191)
    NEWS_SYNDICATES = LkOccupationTitle(1, "News Syndicates", 51, 519110)
    LIBRARIES_AND_ARCHIVES = LkOccupationTitle(1, "Libraries and Archives", 51, 519120)
    INTERNET_PUBLISHING_AND_BROADCASTING_AND_WEB_SEARCH_PORTALS = LkOccupationTitle(1, "Internet Publishing and Broadcasting and Web Search Portals", 51, 519130)
    ALL_OTHER_INFORMATION_SERVICES = LkOccupationTitle(1, "All Other Information Services", 51, 519190)
    MONETARY_AUTHORITIESCENTRAL_BANK = LkOccupationTitle(1, "Monetary Authorities-Central Bank", 52, 5211)
    MONETARY_AUTHORITIESCENTRAL_BANK = LkOccupationTitle(1, "Monetary Authorities-Central Bank", 52, 521110)
    DEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(1, "Depository Credit Intermediation", 52, 5221)
    COMMERCIAL_BANKING = LkOccupationTitle(1, "Commercial Banking", 52, 522110)
    SAVINGS_INSTITUTIONS = LkOccupationTitle(1, "Savings Institutions", 52, 522120)
    CREDIT_UNIONS = LkOccupationTitle(1, "Credit Unions", 52, 522130)
    OTHER_DEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(1, "Other Depository Credit Intermediation", 52, 522190)
    NONDEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(1, "Nondepository Credit Intermediation", 52, 5222)
    CREDIT_CARD_ISSUING = LkOccupationTitle(1, "Credit Card Issuing", 52, 522210)
    SALES_FINANCING = LkOccupationTitle(1, "Sales Financing", 52, 522220)
    CONSUMER_LENDING = LkOccupationTitle(1, "Consumer Lending", 52, 522291)
    REAL_ESTATE_CREDIT = LkOccupationTitle(1, "Real Estate Credit", 52, 522292)
    INTERNATIONAL_TRADE_FINANCING = LkOccupationTitle(1, "International Trade Financing", 52, 522293)
    SECONDARY_MARKET_FINANCING = LkOccupationTitle(1, "Secondary Market Financing", 52, 522294)
    ALL_OTHER_NONDEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(1, "All Other Nondepository Credit Intermediation", 52, 522298)
    ACTIVITIES_RELATED_TO_CREDIT_INTERMEDIATION = LkOccupationTitle(1, "Activities Related to Credit Intermediation", 52, 5223)
    MORTGAGE_AND_NONMORTGAGE_LOAN_BROKERS = LkOccupationTitle(1, "Mortgage and Nonmortgage Loan Brokers", 52, 522310)
    FINANCIAL_TRANSACTIONS_PROCESSING_RESERVE_AND_CLEARINGHOUSE_ACTIVITIES = LkOccupationTitle(1, "Financial Transactions Processing, Reserve, and Clearinghouse Activities", 52, 522320)
    OTHER_ACTIVITIES_RELATED_TO_CREDIT_INTERMEDIATION = LkOccupationTitle(1, "Other Activities Related to Credit Intermediation", 52, 522390)
    SECURITIES_AND_COMMODITY_CONTRACTS_INTERMEDIATION_AND_BROKERAGE = LkOccupationTitle(1, "Securities and Commodity Contracts Intermediation and Brokerage", 52, 5231)
    INVESTMENT_BANKING_AND_SECURITIES_DEALING = LkOccupationTitle(1, "Investment Banking and Securities Dealing", 52, 523110)
    SECURITIES_BROKERAGE = LkOccupationTitle(1, "Securities Brokerage", 52, 523120)
    COMMODITY_CONTRACTS_DEALING = LkOccupationTitle(1, "Commodity Contracts Dealing", 52, 523130)
    COMMODITY_CONTRACTS_BROKERAGE = LkOccupationTitle(1, "Commodity Contracts Brokerage", 52, 523140)
    SECURITIES_AND_COMMODITY_EXCHANGES = LkOccupationTitle(1, "Securities and Commodity Exchanges", 52, 5232)
    SECURITIES_AND_COMMODITY_EXCHANGES = LkOccupationTitle(1, "Securities and Commodity Exchanges", 52, 523210)
    OTHER_FINANCIAL_INVESTMENT_ACTIVITIES = LkOccupationTitle(1, "Other Financial Investment Activities", 52, 5239)
    MISCELLANEOUS_INTERMEDIATION = LkOccupationTitle(1, "Miscellaneous Intermediation", 52, 523910)
    PORTFOLIO_MANAGEMENT = LkOccupationTitle(1, "Portfolio Management", 52, 523920)
    INVESTMENT_ADVICE = LkOccupationTitle(1, "Investment Advice", 52, 523930)
    TRUST_FIDUCIARY_AND_CUSTODY_ACTIVITIES = LkOccupationTitle(1, "Trust, Fiduciary, and Custody Activities", 52, 523991)
    MISCELLANEOUS_FINANCIAL_INVESTMENT_ACTIVITIES = LkOccupationTitle(1, "Miscellaneous Financial Investment Activities", 52, 523999)
    INSURANCE_CARRIERS = LkOccupationTitle(1, "Insurance Carriers", 52, 5241)
    DIRECT_LIFE_INSURANCE_CARRIERS = LkOccupationTitle(1, "Direct Life Insurance Carriers", 52, 524113)
    DIRECT_HEALTH_AND_MEDICAL_INSURANCE_CARRIERS = LkOccupationTitle(1, "Direct Health and Medical Insurance Carriers", 52, 524114)
    DIRECT_PROPERTY_AND_CASUALTY_INSURANCE_CARRIERS = LkOccupationTitle(1, "Direct Property and Casualty Insurance Carriers", 52, 524126)
    DIRECT_TITLE_INSURANCE_CARRIERS = LkOccupationTitle(1, "Direct Title Insurance Carriers", 52, 524127)
    OTHER_DIRECT_INSURANCE_EXCEPT_LIFE_HEALTH_AND_MEDICAL_CARRIERS = LkOccupationTitle(1, "Other Direct Insurance (except Life, Health, and Medical) Carriers", 52, 524128)
    REINSURANCE_CARRIERS = LkOccupationTitle(1, "Reinsurance Carriers", 52, 524130)
    AGENCIES_BROKERAGES_AND_OTHER_INSURANCE_RELATED_ACTIVITIES = LkOccupationTitle(1, "Agencies, Brokerages, and Other Insurance Related Activities", 52, 5242)
    INSURANCE_AGENCIES_AND_BROKERAGES = LkOccupationTitle(1, "Insurance Agencies and Brokerages", 52, 524210)
    CLAIMS_ADJUSTING = LkOccupationTitle(1, "Claims Adjusting", 52, 524291)
    THIRD_PARTY_ADMINISTRATION_OF_INSURANCE_AND_PENSION_FUNDS = LkOccupationTitle(1, "Third Party Administration of Insurance and Pension Funds", 52, 524292)
    ALL_OTHER_INSURANCE_RELATED_ACTIVITIES = LkOccupationTitle(1, "All Other Insurance Related Activities", 52, 524298)
    INSURANCE_AND_EMPLOYEE_BENEFIT_FUNDS = LkOccupationTitle(1, "Insurance and Employee Benefit Funds", 52, 5251)
    PENSION_FUNDS = LkOccupationTitle(1, "Pension Funds", 52, 525110)
    HEALTH_AND_WELFARE_FUNDS = LkOccupationTitle(1, "Health and Welfare Funds", 52, 525120)
    OTHER_INSURANCE_FUNDS = LkOccupationTitle(1, "Other Insurance Funds", 52, 525190)
    OTHER_INVESTMENT_POOLS_AND_FUNDS = LkOccupationTitle(1, "Other Investment Pools and Funds", 52, 5259)
    OPENEND_INVESTMENT_FUNDS = LkOccupationTitle(1, "Open-End Investment Funds", 52, 525910)
    TRUSTS_ESTATES_AND_AGENCY_ACCOUNTS = LkOccupationTitle(1, "Trusts, Estates, and Agency Accounts", 52, 525920)
    OTHER_FINANCIAL_VEHICLES = LkOccupationTitle(1, "Other Financial Vehicles", 52, 525990)
    LESSORS_OF_REAL_ESTATE = LkOccupationTitle(1, "Lessors of Real Estate", 53, 5311)
    LESSORS_OF_RESIDENTIAL_BUILDINGS_AND_DWELLINGS = LkOccupationTitle(1, "Lessors of Residential Buildings and Dwellings", 53, 531110)
    LESSORS_OF_NONRESIDENTIAL_BUILDINGS_EXCEPT_MINIWAREHOUSES = LkOccupationTitle(1, "Lessors of Nonresidential Buildings (except Miniwarehouses)", 53, 531120)
    LESSORS_OF_MINIWAREHOUSES_AND_SELFSTORAGE_UNITS = LkOccupationTitle(1, "Lessors of Miniwarehouses and Self-Storage Units", 53, 531130)
    LESSORS_OF_OTHER_REAL_ESTATE_PROPERTY = LkOccupationTitle(1, "Lessors of Other Real Estate Property", 53, 531190)
    OFFICES_OF_REAL_ESTATE_AGENTS_AND_BROKERS = LkOccupationTitle(1, "Offices of Real Estate Agents and Brokers", 53, 5312)
    OFFICES_OF_REAL_ESTATE_AGENTS_AND_BROKERS = LkOccupationTitle(1, "Offices of Real Estate Agents and Brokers", 53, 531210)
    ACTIVITIES_RELATED_TO_REAL_ESTATE = LkOccupationTitle(1, "Activities Related to Real Estate", 53, 5313)
    RESIDENTIAL_PROPERTY_MANAGERS = LkOccupationTitle(1, "Residential Property Managers", 53, 531311)
    NONRESIDENTIAL_PROPERTY_MANAGERS = LkOccupationTitle(1, "Nonresidential Property Managers", 53, 531312)
    OFFICES_OF_REAL_ESTATE_APPRAISERS = LkOccupationTitle(1, "Offices of Real Estate Appraisers", 53, 531320)
    OTHER_ACTIVITIES_RELATED_TO_REAL_ESTATE = LkOccupationTitle(1, "Other Activities Related to Real Estate", 53, 531390)
    AUTOMOTIVE_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(1, "Automotive Equipment Rental and Leasing", 53, 5321)
    PASSENGER_CAR_RENTAL = LkOccupationTitle(1, "Passenger Car Rental", 53, 532111)
    PASSENGER_CAR_LEASING = LkOccupationTitle(1, "Passenger Car Leasing", 53, 532112)
    TRUCK_UTILITY_TRAILER_AND_RV_RECREATIONAL_VEHICLE_RENTAL_AND_LEASING = LkOccupationTitle(1, "Truck, Utility Trailer, and RV (Recreational Vehicle) Rental and Leasing", 53, 532120)
    CONSUMER_GOODS_RENTAL = LkOccupationTitle(1, "Consumer Goods Rental", 53, 5322)
    CONSUMER_ELECTRONICS_AND_APPLIANCES_RENTAL = LkOccupationTitle(1, "Consumer Electronics and Appliances Rental", 53, 532210)
    FORMAL_WEAR_AND_COSTUME_RENTAL = LkOccupationTitle(1, "Formal Wear and Costume Rental", 53, 532281)
    VIDEO_TAPE_AND_DISC_RENTAL = LkOccupationTitle(1, "Video Tape and Disc Rental", 53, 532282)
    HOME_HEALTH_EQUIPMENT_RENTAL = LkOccupationTitle(1, "Home Health Equipment Rental", 53, 532283)
    RECREATIONAL_GOODS_RENTAL = LkOccupationTitle(1, "Recreational Goods Rental", 53, 532284)
    ALL_OTHER_CONSUMER_GOODS_RENTAL = LkOccupationTitle(1, "All Other Consumer Goods Rental", 53, 532289)
    GENERAL_RENTAL_CENTERS = LkOccupationTitle(1, "General Rental Centers", 53, 5323)
    GENERAL_RENTAL_CENTERS = LkOccupationTitle(1, "General Rental Centers", 53, 532310)
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(1, "Commercial and Industrial Machinery and Equipment Rental and Leasing", 53, 5324)
    COMMERCIAL_AIR_RAIL_AND_WATER_TRANSPORTATION_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(1, "Commercial Air, Rail, and Water Transportation Equipment Rental and Leasing", 53, 532411)
    CONSTRUCTION_MINING_AND_FORESTRY_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(1, "Construction, Mining, and Forestry Machinery and Equipment Rental and Leasing", 53, 532412)
    OFFICE_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(1, "Office Machinery and Equipment Rental and Leasing", 53, 532420)
    OTHER_COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(1, "Other Commercial and Industrial Machinery and Equipment Rental and Leasing", 53, 532490)
    LESSORS_OF_NONFINANCIAL_INTANGIBLE_ASSETS_EXCEPT_COPYRIGHTED_WORKS = LkOccupationTitle(1, "Lessors of Nonfinancial Intangible Assets (except Copyrighted Works)", 53, 5331)
    LESSORS_OF_NONFINANCIAL_INTANGIBLE_ASSETS_EXCEPT_COPYRIGHTED_WORKS = LkOccupationTitle(1, "Lessors of Nonfinancial Intangible Assets (except Copyrighted Works)", 53, 533110)
    LEGAL_SERVICES = LkOccupationTitle(1, "Legal Services", 54, 5411)
    OFFICES_OF_LAWYERS = LkOccupationTitle(1, "Offices of Lawyers", 54, 541110)
    OFFICES_OF_NOTARIES = LkOccupationTitle(1, "Offices of Notaries", 54, 541120)
    TITLE_ABSTRACT_AND_SETTLEMENT_OFFICES = LkOccupationTitle(1, "Title Abstract and Settlement Offices", 54, 541191)
    ALL_OTHER_LEGAL_SERVICES = LkOccupationTitle(1, "All Other Legal Services", 54, 541199)
    ACCOUNTING_TAX_PREPARATION_BOOKKEEPING_AND_PAYROLL_SERVICES = LkOccupationTitle(1, "Accounting, Tax Preparation, Bookkeeping, and Payroll Services", 54, 5412)
    OFFICES_OF_CERTIFIED_PUBLIC_ACCOUNTANTS = LkOccupationTitle(1, "Offices of Certified Public Accountants", 54, 541211)
    TAX_PREPARATION_SERVICES = LkOccupationTitle(1, "Tax Preparation Services", 54, 541213)
    PAYROLL_SERVICES = LkOccupationTitle(1, "Payroll Services", 54, 541214)
    OTHER_ACCOUNTING_SERVICES = LkOccupationTitle(1, "Other Accounting Services", 54, 541219)
    ARCHITECTURAL_ENGINEERING_AND_RELATED_SERVICES = LkOccupationTitle(1, "Architectural, Engineering, and Related Services", 54, 5413)
    ARCHITECTURAL_SERVICES = LkOccupationTitle(1, "Architectural Services", 54, 541310)
    LANDSCAPE_ARCHITECTURAL_SERVICES = LkOccupationTitle(1, "Landscape Architectural Services", 54, 541320)
    ENGINEERING_SERVICES = LkOccupationTitle(1, "Engineering Services", 54, 541330)
    DRAFTING_SERVICES = LkOccupationTitle(1, "Drafting Services", 54, 541340)
    BUILDING_INSPECTION_SERVICES = LkOccupationTitle(1, "Building Inspection Services", 54, 541350)
    GEOPHYSICAL_SURVEYING_AND_MAPPING_SERVICES = LkOccupationTitle(1, "Geophysical Surveying and Mapping Services", 54, 541360)
    SURVEYING_AND_MAPPING_EXCEPT_GEOPHYSICAL_SERVICES = LkOccupationTitle(1, "Surveying and Mapping (except Geophysical) Services", 54, 541370)
    TESTING_LABORATORIES = LkOccupationTitle(1, "Testing Laboratories", 54, 541380)
    SPECIALIZED_DESIGN_SERVICES = LkOccupationTitle(1, "Specialized Design Services", 54, 5414)
    INTERIOR_DESIGN_SERVICES = LkOccupationTitle(1, "Interior Design Services", 54, 541410)
    INDUSTRIAL_DESIGN_SERVICES = LkOccupationTitle(1, "Industrial Design Services", 54, 541420)
    GRAPHIC_DESIGN_SERVICES = LkOccupationTitle(1, "Graphic Design Services", 54, 541430)
    OTHER_SPECIALIZED_DESIGN_SERVICES = LkOccupationTitle(1, "Other Specialized Design Services", 54, 541490)
    COMPUTER_SYSTEMS_DESIGN_AND_RELATED_SERVICES = LkOccupationTitle(1, "Computer Systems Design and Related Services", 54, 5415)
    CUSTOM_COMPUTER_PROGRAMMING_SERVICES = LkOccupationTitle(1, "Custom Computer Programming Services", 54, 541511)
    COMPUTER_SYSTEMS_DESIGN_SERVICES = LkOccupationTitle(1, "Computer Systems Design Services", 54, 541512)
    COMPUTER_FACILITIES_MANAGEMENT_SERVICES = LkOccupationTitle(1, "Computer Facilities Management Services", 54, 541513)
    OTHER_COMPUTER_RELATED_SERVICES = LkOccupationTitle(1, "Other Computer Related Services", 54, 541519)
    MANAGEMENT_SCIENTIFIC_AND_TECHNICAL_CONSULTING_SERVICES = LkOccupationTitle(1, "Management, Scientific, and Technical Consulting Services", 54, 5416)
    ADMINISTRATIVE_MANAGEMENT_AND_GENERAL_MANAGEMENT_CONSULTING_SERVICES = LkOccupationTitle(1, "Administrative Management and General Management Consulting Services", 54, 541611)
    HUMAN_RESOURCES_CONSULTING_SERVICES = LkOccupationTitle(1, "Human Resources Consulting Services", 54, 541612)
    MARKETING_CONSULTING_SERVICES = LkOccupationTitle(1, "Marketing Consulting Services", 54, 541613)
    PROCESS_PHYSICAL_DISTRIBUTION_AND_LOGISTICS_CONSULTING_SERVICES = LkOccupationTitle(1, "Process, Physical Distribution, and Logistics Consulting Services", 54, 541614)
    OTHER_MANAGEMENT_CONSULTING_SERVICES = LkOccupationTitle(1, "Other Management Consulting Services", 54, 541618)
    ENVIRONMENTAL_CONSULTING_SERVICES = LkOccupationTitle(1, "Environmental Consulting Services", 54, 541620)
    OTHER_SCIENTIFIC_AND_TECHNICAL_CONSULTING_SERVICES = LkOccupationTitle(1, "Other Scientific and Technical Consulting Services", 54, 541690)
    SCIENTIFIC_RESEARCH_AND_DEVELOPMENT_SERVICES = LkOccupationTitle(1, "Scientific Research and Development Services", 54, 5417)
    RESEARCH_AND_DEVELOPMENT_IN_NANOTECHNOLOGY = LkOccupationTitle(1, "Research and Development in Nanotechnology", 54, 541713)
    RESEARCH_AND_DEVELOPMENT_IN_BIOTECHNOLOGY_EXCEPT_NANOBIOTECHNOLOGY = LkOccupationTitle(1, "Research and Development in Biotechnology (except Nanobiotechnology)", 54, 541714)
    RESEARCH_AND_DEVELOPMENT_IN_THE_PHYSICAL_ENGINEERING_AND_LIFE_SCIENCES_EXCEPT_NANOTECHNOLOGY_AND_BIOTECHNOLOGY = LkOccupationTitle(1, "Research and Development in the Physical, Engineering, and Life Sciences (except Nanotechnology and Biotechnology)", 54, 541715)
    RESEARCH_AND_DEVELOPMENT_IN_THE_SOCIAL_SCIENCES_AND_HUMANITIES = LkOccupationTitle(1, "Research and Development in the Social Sciences and Humanities", 54, 541720)
    ADVERTISING_PUBLIC_RELATIONS_AND_RELATED_SERVICES = LkOccupationTitle(1, "Advertising, Public Relations, and Related Services", 54, 5418)
    ADVERTISING_AGENCIES = LkOccupationTitle(1, "Advertising Agencies", 54, 541810)
    PUBLIC_RELATIONS_AGENCIES = LkOccupationTitle(1, "Public Relations Agencies", 54, 541820)
    MEDIA_BUYING_AGENCIES = LkOccupationTitle(1, "Media Buying Agencies", 54, 541830)
    MEDIA_REPRESENTATIVES = LkOccupationTitle(1, "Media Representatives", 54, 541840)
    OUTDOOR_ADVERTISING = LkOccupationTitle(1, "Outdoor Advertising", 54, 541850)
    DIRECT_MAIL_ADVERTISING = LkOccupationTitle(1, "Direct Mail Advertising", 54, 541860)
    ADVERTISING_MATERIAL_DISTRIBUTION_SERVICES = LkOccupationTitle(1, "Advertising Material Distribution Services", 54, 541870)
    OTHER_SERVICES_RELATED_TO_ADVERTISING = LkOccupationTitle(1, "Other Services Related to Advertising", 54, 541890)
    OTHER_PROFESSIONAL_SCIENTIFIC_AND_TECHNICAL_SERVICES = LkOccupationTitle(1, "Other Professional, Scientific, and Technical Services", 54, 5419)
    MARKETING_RESEARCH_AND_PUBLIC_OPINION_POLLING = LkOccupationTitle(1, "Marketing Research and Public Opinion Polling", 54, 541910)
    PHOTOGRAPHY_STUDIOS_PORTRAIT = LkOccupationTitle(1, "Photography Studios, Portrait", 54, 541921)
    COMMERCIAL_PHOTOGRAPHY = LkOccupationTitle(1, "Commercial Photography", 54, 541922)
    TRANSLATION_AND_INTERPRETATION_SERVICES = LkOccupationTitle(1, "Translation and Interpretation Services", 54, 541930)
    VETERINARY_SERVICES = LkOccupationTitle(1, "Veterinary Services", 54, 541940)
    ALL_OTHER_PROFESSIONAL_SCIENTIFIC_AND_TECHNICAL_SERVICES = LkOccupationTitle(1, "All Other Professional, Scientific, and Technical Services", 54, 541990)
    MANAGEMENT_OF_COMPANIES_AND_ENTERPRISES = LkOccupationTitle(1, "Management of Companies and Enterprises", 55, 5511)
    OFFICES_OF_BANK_HOLDING_COMPANIES = LkOccupationTitle(1, "Offices of Bank Holding Companies", 55, 551111)
    OFFICES_OF_OTHER_HOLDING_COMPANIES = LkOccupationTitle(1, "Offices of Other Holding Companies", 55, 551112)
    CORPORATE_SUBSIDIARY_AND_REGIONAL_MANAGING_OFFICES = LkOccupationTitle(1, "Corporate, Subsidiary, and Regional Managing Offices", 55, 551114)
    OFFICE_ADMINISTRATIVE_SERVICES = LkOccupationTitle(1, "Office Administrative Services", 56, 5611)
    OFFICE_ADMINISTRATIVE_SERVICES = LkOccupationTitle(1, "Office Administrative Services", 56, 561110)
    FACILITIES_SUPPORT_SERVICES = LkOccupationTitle(1, "Facilities Support Services", 56, 5612)
    FACILITIES_SUPPORT_SERVICES = LkOccupationTitle(1, "Facilities Support Services", 56, 561210)
    EMPLOYMENT_SERVICES = LkOccupationTitle(1, "Employment Services", 56, 5613)
    EMPLOYMENT_PLACEMENT_AGENCIES = LkOccupationTitle(1, "Employment Placement Agencies", 56, 561311)
    EXECUTIVE_SEARCH_SERVICES = LkOccupationTitle(1, "Executive Search Services", 56, 561312)
    TEMPORARY_HELP_SERVICES = LkOccupationTitle(1, "Temporary Help Services", 56, 561320)
    PROFESSIONAL_EMPLOYER_ORGANIZATIONS = LkOccupationTitle(1, "Professional Employer Organizations", 56, 561330)
    BUSINESS_SUPPORT_SERVICES = LkOccupationTitle(1, "Business Support Services", 56, 5614)
    DOCUMENT_PREPARATION_SERVICES = LkOccupationTitle(1, "Document Preparation Services", 56, 561410)
    TELEPHONE_ANSWERING_SERVICES = LkOccupationTitle(1, "Telephone Answering Services", 56, 561421)
    TELEMARKETING_BUREAUS_AND_OTHER_CONTACT_CENTERS = LkOccupationTitle(1, "Telemarketing Bureaus and Other Contact Centers", 56, 561422)
    PRIVATE_MAIL_CENTERS = LkOccupationTitle(1, "Private Mail Centers", 56, 561431)
    OTHER_BUSINESS_SERVICE_CENTERS_INCLUDING_COPY_SHOPS = LkOccupationTitle(1, "Other Business Service Centers (including Copy Shops)", 56, 561439)
    COLLECTION_AGENCIES = LkOccupationTitle(1, "Collection Agencies", 56, 561440)
    CREDIT_BUREAUS = LkOccupationTitle(1, "Credit Bureaus", 56, 561450)
    REPOSSESSION_SERVICES = LkOccupationTitle(1, "Repossession Services", 56, 561491)
    COURT_REPORTING_AND_STENOTYPE_SERVICES = LkOccupationTitle(1, "Court Reporting and Stenotype Services", 56, 561492)
    ALL_OTHER_BUSINESS_SUPPORT_SERVICES = LkOccupationTitle(1, "All Other Business Support Services", 56, 561499)
    TRAVEL_ARRANGEMENT_AND_RESERVATION_SERVICES = LkOccupationTitle(1, "Travel Arrangement and Reservation Services", 56, 5615)
    TRAVEL_AGENCIES = LkOccupationTitle(1, "Travel Agencies", 56, 561510)
    TOUR_OPERATORS = LkOccupationTitle(1, "Tour Operators", 56, 561520)
    CONVENTION_AND_VISITORS_BUREAUS = LkOccupationTitle(1, "Convention and Visitors Bureaus", 56, 561591)
    ALL_OTHER_TRAVEL_ARRANGEMENT_AND_RESERVATION_SERVICES = LkOccupationTitle(1, "All Other Travel Arrangement and Reservation Services", 56, 561599)
    INVESTIGATION_AND_SECURITY_SERVICES = LkOccupationTitle(1, "Investigation and Security Services", 56, 5616)
    INVESTIGATION_SERVICES = LkOccupationTitle(1, "Investigation Services", 56, 561611)
    SECURITY_GUARDS_AND_PATROL_SERVICES = LkOccupationTitle(1, "Security Guards and Patrol Services", 56, 561612)
    ARMORED_CAR_SERVICES = LkOccupationTitle(1, "Armored Car Services", 56, 561613)
    SECURITY_SYSTEMS_SERVICES_EXCEPT_LOCKSMITHS = LkOccupationTitle(1, "Security Systems Services (except Locksmiths)", 56, 561621)
    LOCKSMITHS = LkOccupationTitle(1, "Locksmiths", 56, 561622)
    SERVICES_TO_BUILDINGS_AND_DWELLINGS = LkOccupationTitle(1, "Services to Buildings and Dwellings", 56, 5617)
    EXTERMINATING_AND_PEST_CONTROL_SERVICES = LkOccupationTitle(1, "Exterminating and Pest Control Services", 56, 561710)
    JANITORIAL_SERVICES = LkOccupationTitle(1, "Janitorial Services", 56, 561720)
    LANDSCAPING_SERVICES = LkOccupationTitle(1, "Landscaping Services", 56, 561730)
    CARPET_AND_UPHOLSTERY_CLEANING_SERVICES = LkOccupationTitle(1, "Carpet and Upholstery Cleaning Services", 56, 561740)
    OTHER_SERVICES_TO_BUILDINGS_AND_DWELLINGS = LkOccupationTitle(1, "Other Services to Buildings and Dwellings", 56, 561790)
    OTHER_SUPPORT_SERVICES = LkOccupationTitle(1, "Other Support Services", 56, 5619)
    PACKAGING_AND_LABELING_SERVICES = LkOccupationTitle(1, "Packaging and Labeling Services", 56, 561910)
    CONVENTION_AND_TRADE_SHOW_ORGANIZERS = LkOccupationTitle(1, "Convention and Trade Show Organizers", 56, 561920)
    ALL_OTHER_SUPPORT_SERVICES = LkOccupationTitle(1, "All Other Support Services", 56, 561990)
    WASTE_COLLECTION = LkOccupationTitle(1, "Waste Collection", 56, 5621)
    SOLID_WASTE_COLLECTION = LkOccupationTitle(1, "Solid Waste Collection", 56, 562111)
    HAZARDOUS_WASTE_COLLECTION = LkOccupationTitle(1, "Hazardous Waste Collection", 56, 562112)
    OTHER_WASTE_COLLECTION = LkOccupationTitle(1, "Other Waste Collection", 56, 562119)
    WASTE_TREATMENT_AND_DISPOSAL = LkOccupationTitle(1, "Waste Treatment and Disposal", 56, 5622)
    HAZARDOUS_WASTE_TREATMENT_AND_DISPOSAL = LkOccupationTitle(1, "Hazardous Waste Treatment and Disposal", 56, 562211)
    SOLID_WASTE_LANDFILL = LkOccupationTitle(1, "Solid Waste Landfill", 56, 562212)
    SOLID_WASTE_COMBUSTORS_AND_INCINERATORS = LkOccupationTitle(1, "Solid Waste Combustors and Incinerators", 56, 562213)
    OTHER_NONHAZARDOUS_WASTE_TREATMENT_AND_DISPOSAL = LkOccupationTitle(1, "Other Nonhazardous Waste Treatment and Disposal", 56, 562219)
    REMEDIATION_AND_OTHER_WASTE_MANAGEMENT_SERVICES = LkOccupationTitle(1, "Remediation and Other Waste Management Services", 56, 5629)
    REMEDIATION_SERVICES = LkOccupationTitle(1, "Remediation Services", 56, 562910)
    MATERIALS_RECOVERY_FACILITIES = LkOccupationTitle(1, "Materials Recovery Facilities", 56, 562920)
    SEPTIC_TANK_AND_RELATED_SERVICES = LkOccupationTitle(1, "Septic Tank and Related Services", 56, 562991)
    ALL_OTHER_MISCELLANEOUS_WASTE_MANAGEMENT_SERVICES = LkOccupationTitle(1, "All Other Miscellaneous Waste Management Services", 56, 562998)
    ELEMENTARY_AND_SECONDARY_SCHOOLS = LkOccupationTitle(1, "Elementary and Secondary Schools", 61, 6111)
    ELEMENTARY_AND_SECONDARY_SCHOOLS = LkOccupationTitle(1, "Elementary and Secondary Schools", 61, 611110)
    JUNIOR_COLLEGES = LkOccupationTitle(1, "Junior Colleges", 61, 6112)
    JUNIOR_COLLEGES = LkOccupationTitle(1, "Junior Colleges", 61, 611210)
    COLLEGES_UNIVERSITIES_AND_PROFESSIONAL_SCHOOLS = LkOccupationTitle(1, "Colleges, Universities, and Professional Schools", 61, 6113)
    COLLEGES_UNIVERSITIES_AND_PROFESSIONAL_SCHOOLS = LkOccupationTitle(1, "Colleges, Universities, and Professional Schools", 61, 611310)
    BUSINESS_SCHOOLS_AND_COMPUTER_AND_MANAGEMENT_TRAINING = LkOccupationTitle(1, "Business Schools and Computer and Management Training", 61, 6114)
    BUSINESS_AND_SECRETARIAL_SCHOOLS = LkOccupationTitle(1, "Business and Secretarial Schools", 61, 611410)
    COMPUTER_TRAINING = LkOccupationTitle(1, "Computer Training", 61, 611420)
    PROFESSIONAL_AND_MANAGEMENT_DEVELOPMENT_TRAINING = LkOccupationTitle(1, "Professional and Management Development Training", 61, 611430)
    TECHNICAL_AND_TRADE_SCHOOLS = LkOccupationTitle(1, "Technical and Trade Schools", 61, 6115)
    COSMETOLOGY_AND_BARBER_SCHOOLS = LkOccupationTitle(1, "Cosmetology and Barber Schools", 61, 611511)
    FLIGHT_TRAINING = LkOccupationTitle(1, "Flight Training", 61, 611512)
    APPRENTICESHIP_TRAINING = LkOccupationTitle(1, "Apprenticeship Training", 61, 611513)
    OTHER_TECHNICAL_AND_TRADE_SCHOOLS = LkOccupationTitle(1, "Other Technical and Trade Schools", 61, 611519)
    OTHER_SCHOOLS_AND_INSTRUCTION = LkOccupationTitle(1, "Other Schools and Instruction", 61, 6116)
    FINE_ARTS_SCHOOLS = LkOccupationTitle(1, "Fine Arts Schools", 61, 611610)
    SPORTS_AND_RECREATION_INSTRUCTION = LkOccupationTitle(1, "Sports and Recreation Instruction", 61, 611620)
    LANGUAGE_SCHOOLS = LkOccupationTitle(1, "Language Schools", 61, 611630)
    EXAM_PREPARATION_AND_TUTORING = LkOccupationTitle(1, "Exam Preparation and Tutoring", 61, 611691)
    AUTOMOBILE_DRIVING_SCHOOLS = LkOccupationTitle(1, "Automobile Driving Schools", 61, 611692)
    ALL_OTHER_MISCELLANEOUS_SCHOOLS_AND_INSTRUCTION = LkOccupationTitle(1, "All Other Miscellaneous Schools and Instruction", 61, 611699)
    EDUCATIONAL_SUPPORT_SERVICES = LkOccupationTitle(1, "Educational Support Services", 61, 6117)
    EDUCATIONAL_SUPPORT_SERVICES = LkOccupationTitle(1, "Educational Support Services", 61, 611710)
    OFFICES_OF_PHYSICIANS = LkOccupationTitle(1, "Offices of Physicians", 62, 6211)
    OFFICES_OF_PHYSICIANS_EXCEPT_MENTAL_HEALTH_SPECIALISTS = LkOccupationTitle(1, "Offices of Physicians (except Mental Health Specialists)", 62, 621111)
    OFFICES_OF_PHYSICIANS_MENTAL_HEALTH_SPECIALISTS = LkOccupationTitle(1, "Offices of Physicians, Mental Health Specialists", 62, 621112)
    OFFICES_OF_DENTISTS = LkOccupationTitle(1, "Offices of Dentists", 62, 6212)
    OFFICES_OF_DENTISTS = LkOccupationTitle(1, "Offices of Dentists", 62, 621210)
    OFFICES_OF_OTHER_HEALTH_PRACTITIONERS = LkOccupationTitle(1, "Offices of Other Health Practitioners", 62, 6213)
    OFFICES_OF_CHIROPRACTORS = LkOccupationTitle(1, "Offices of Chiropractors", 62, 621310)
    OFFICES_OF_OPTOMETRISTS = LkOccupationTitle(1, "Offices of Optometrists", 62, 621320)
    OFFICES_OF_MENTAL_HEALTH_PRACTITIONERS_EXCEPT_PHYSICIANS = LkOccupationTitle(1, "Offices of Mental Health Practitioners (except Physicians)", 62, 621330)
    OFFICES_OF_PHYSICAL_OCCUPATIONAL_AND_SPEECH_THERAPISTS_AND_AUDIOLOGISTS = LkOccupationTitle(1, "Offices of Physical, Occupational and Speech Therapists, and Audiologists", 62, 621340)
    OFFICES_OF_PODIATRISTS = LkOccupationTitle(1, "Offices of Podiatrists", 62, 621391)
    OFFICES_OF_ALL_OTHER_MISCELLANEOUS_HEALTH_PRACTITIONERS = LkOccupationTitle(1, "Offices of All Other Miscellaneous Health Practitioners", 62, 621399)
    OUTPATIENT_CARE_CENTERS = LkOccupationTitle(1, "Outpatient Care Centers", 62, 6214)
    FAMILY_PLANNING_CENTERS = LkOccupationTitle(1, "Family Planning Centers", 62, 621410)
    OUTPATIENT_MENTAL_HEALTH_AND_SUBSTANCE_ABUSE_CENTERS = LkOccupationTitle(1, "Outpatient Mental Health and Substance Abuse Centers", 62, 621420)
    HMO_MEDICAL_CENTERS = LkOccupationTitle(1, "HMO Medical Centers", 62, 621491)
    KIDNEY_DIALYSIS_CENTERS = LkOccupationTitle(1, "Kidney Dialysis Centers", 62, 621492)
    FREESTANDING_AMBULATORY_SURGICAL_AND_EMERGENCY_CENTERS = LkOccupationTitle(1, "Freestanding Ambulatory Surgical and Emergency Centers", 62, 621493)
    ALL_OTHER_OUTPATIENT_CARE_CENTERS = LkOccupationTitle(1, "All Other Outpatient Care Centers", 62, 621498)
    MEDICAL_AND_DIAGNOSTIC_LABORATORIES = LkOccupationTitle(1, "Medical and Diagnostic Laboratories", 62, 6215)
    MEDICAL_LABORATORIES = LkOccupationTitle(1, "Medical Laboratories", 62, 621511)
    DIAGNOSTIC_IMAGING_CENTERS = LkOccupationTitle(1, "Diagnostic Imaging Centers", 62, 621512)
    HOME_HEALTH_CARE_SERVICES = LkOccupationTitle(1, "Home Health Care Services", 62, 6216)
    HOME_HEALTH_CARE_SERVICES = LkOccupationTitle(1, "Home Health Care Services", 62, 621610)
    OTHER_AMBULATORY_HEALTH_CARE_SERVICES = LkOccupationTitle(1, "Other Ambulatory Health Care Services", 62, 6219)
    AMBULANCE_SERVICES = LkOccupationTitle(1, "Ambulance Services", 62, 621910)
    BLOOD_AND_ORGAN_BANKS = LkOccupationTitle(1, "Blood and Organ Banks", 62, 621991)
    ALL_OTHER_MISCELLANEOUS_AMBULATORY_HEALTH_CARE_SERVICES = LkOccupationTitle(1, "All Other Miscellaneous Ambulatory Health Care Services", 62, 621999)
    GENERAL_MEDICAL_AND_SURGICAL_HOSPITALS = LkOccupationTitle(1, "General Medical and Surgical Hospitals", 62, 6221)
    GENERAL_MEDICAL_AND_SURGICAL_HOSPITALS = LkOccupationTitle(1, "General Medical and Surgical Hospitals", 62, 622110)
    PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkOccupationTitle(1, "Psychiatric and Substance Abuse Hospitals", 62, 6222)
    PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkOccupationTitle(1, "Psychiatric and Substance Abuse Hospitals", 62, 622210)
    SPECIALTY_EXCEPT_PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkOccupationTitle(1, "Specialty (except Psychiatric and Substance Abuse) Hospitals", 62, 6223)
    SPECIALTY_EXCEPT_PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkOccupationTitle(1, "Specialty (except Psychiatric and Substance Abuse) Hospitals", 62, 622310)
    NURSING_CARE_FACILITIES_SKILLED_NURSING_FACILITIES = LkOccupationTitle(1, "Nursing Care Facilities (Skilled Nursing Facilities)", 62, 6231)
    NURSING_CARE_FACILITIES_SKILLED_NURSING_FACILITIES = LkOccupationTitle(1, "Nursing Care Facilities (Skilled Nursing Facilities)", 62, 623110)
    RESIDENTIAL_INTELLECTUAL_AND_DEVELOPMENTAL_DISABILITY_MENTAL_HEALTH_AND_SUBSTANCE_ABUSE_FACILITIES = LkOccupationTitle(1, "Residential Intellectual and Developmental Disability, Mental Health, and Substance Abuse Facilities", 62, 6232)
    RESIDENTIAL_INTELLECTUAL_AND_DEVELOPMENTAL_DISABILITY_FACILITIES = LkOccupationTitle(1, "Residential Intellectual and Developmental Disability Facilities", 62, 623210)
    RESIDENTIAL_MENTAL_HEALTH_AND_SUBSTANCE_ABUSE_FACILITIES = LkOccupationTitle(1, "Residential Mental Health and Substance Abuse Facilities", 62, 623220)
    CONTINUING_CARE_RETIREMENT_COMMUNITIES_AND_ASSISTED_LIVING_FACILITIES_FOR_THE_ELDERLY = LkOccupationTitle(1, "Continuing Care Retirement Communities and Assisted Living Facilities for the Elderly028", 62, 6233)
    CONTINUING_CARE_RETIREMENT_COMMUNITIES = LkOccupationTitle(1, "Continuing Care Retirement Communities", 62, 623311)
    ASSISTED_LIVING_FACILITIES_FOR_THE_ELDERLY = LkOccupationTitle(1, "Assisted Living Facilities for the Elderly", 62, 623312)
    OTHER_RESIDENTIAL_CARE_FACILITIES = LkOccupationTitle(1, "Other Residential Care Facilities", 62, 6239)
    OTHER_RESIDENTIAL_CARE_FACILITIES = LkOccupationTitle(1, "Other Residential Care Facilities", 62, 623990)
    INDIVIDUAL_AND_FAMILY_SERVICES = LkOccupationTitle(1, "Individual and Family Services", 62, 6241)
    CHILD_AND_YOUTH_SERVICES = LkOccupationTitle(1, "Child and Youth Services", 62, 624110)
    SERVICES_FOR_THE_ELDERLY_AND_PERSONS_WITH_DISABILITIES = LkOccupationTitle(1, "Services for the Elderly and Persons with Disabilities", 62, 624120)
    OTHER_INDIVIDUAL_AND_FAMILY_SERVICES = LkOccupationTitle(1, "Other Individual and Family Services", 62, 624190)
    COMMUNITY_FOOD_AND_HOUSING_AND_EMERGENCY_AND_OTHER_RELIEF_SERVICES = LkOccupationTitle(1, "Community Food and Housing, and Emergency and Other Relief Services", 62, 6242)
    COMMUNITY_FOOD_SERVICES = LkOccupationTitle(1, "Community Food Services", 62, 624210)
    TEMPORARY_SHELTERS = LkOccupationTitle(1, "Temporary Shelters", 62, 624221)
    OTHER_COMMUNITY_HOUSING_SERVICES = LkOccupationTitle(1, "Other Community Housing Services", 62, 624229)
    EMERGENCY_AND_OTHER_RELIEF_SERVICES = LkOccupationTitle(1, "Emergency and Other Relief Services", 62, 624230)
    VOCATIONAL_REHABILITATION_SERVICES = LkOccupationTitle(1, "Vocational Rehabilitation Services", 62, 6243)
    VOCATIONAL_REHABILITATION_SERVICES = LkOccupationTitle(1, "Vocational Rehabilitation Services", 62, 624310)
    CHILD_DAY_CARE_SERVICES = LkOccupationTitle(1, "Child Day Care Services", 62, 6244)
    CHILD_DAY_CARE_SERVICES = LkOccupationTitle(1, "Child Day Care Services", 62, 624410)
    PERFORMING_ARTS_COMPANIES = LkOccupationTitle(1, "Performing Arts Companies", 71, 7111)
    THEATER_COMPANIES_AND_DINNER_THEATERS = LkOccupationTitle(1, "Theater Companies and Dinner Theaters", 71, 711110)
    DANCE_COMPANIES = LkOccupationTitle(1, "Dance Companies", 71, 711120)
    MUSICAL_GROUPS_AND_ARTISTS = LkOccupationTitle(1, "Musical Groups and Artists", 71, 711130)
    OTHER_PERFORMING_ARTS_COMPANIES = LkOccupationTitle(1, "Other Performing Arts Companies", 71, 711190)
    SPECTATOR_SPORTS = LkOccupationTitle(1, "Spectator Sports", 71, 7112)
    SPORTS_TEAMS_AND_CLUBS = LkOccupationTitle(1, "Sports Teams and Clubs", 71, 711211)
    RACETRACKS = LkOccupationTitle(1, "Racetracks", 71, 711212)
    OTHER_SPECTATOR_SPORTS = LkOccupationTitle(1, "Other Spectator Sports", 71, 711219)
    PROMOTERS_OF_PERFORMING_ARTS_SPORTS_AND_SIMILAR_EVENTS = LkOccupationTitle(1, "Promoters of Performing Arts, Sports, and Similar Events", 71, 7113)
    PROMOTERS_OF_PERFORMING_ARTS_SPORTS_AND_SIMILAR_EVENTS_WITH_FACILITIES = LkOccupationTitle(1, "Promoters of Performing Arts, Sports, and Similar Events with Facilities", 71, 711310)
    PROMOTERS_OF_PERFORMING_ARTS_SPORTS_AND_SIMILAR_EVENTS_WITHOUT_FACILITIES = LkOccupationTitle(1, "Promoters of Performing Arts, Sports, and Similar Events without Facilities", 71, 711320)
    AGENTS_AND_MANAGERS_FOR_ARTISTS_ATHLETES_ENTERTAINERS_AND_OTHER_PUBLIC_FIGURES = LkOccupationTitle(1, "Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures", 71, 7114)
    AGENTS_AND_MANAGERS_FOR_ARTISTS_ATHLETES_ENTERTAINERS_AND_OTHER_PUBLIC_FIGURES = LkOccupationTitle(1, "Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures", 71, 711410)
    INDEPENDENT_ARTISTS_WRITERS_AND_PERFORMERS = LkOccupationTitle(1, "Independent Artists, Writers, and Performers", 71, 7115)
    INDEPENDENT_ARTISTS_WRITERS_AND_PERFORMERS = LkOccupationTitle(1, "Independent Artists, Writers, and Performers", 71, 711510)
    MUSEUMS_HISTORICAL_SITES_AND_SIMILAR_INSTITUTIONS = LkOccupationTitle(1, "Museums, Historical Sites, and Similar Institutions", 71, 7121)
    MUSEUMS = LkOccupationTitle(1, "Museums", 71, 712110)
    HISTORICAL_SITES = LkOccupationTitle(1, "Historical Sites", 71, 712120)
    ZOOS_AND_BOTANICAL_GARDENS = LkOccupationTitle(1, "Zoos and Botanical Gardens", 71, 712130)
    NATURE_PARKS_AND_OTHER_SIMILAR_INSTITUTIONS = LkOccupationTitle(1, "Nature Parks and Other Similar Institutions", 71, 712190)
    AMUSEMENT_PARKS_AND_ARCADES = LkOccupationTitle(1, "Amusement Parks and Arcades", 71, 7131)
    AMUSEMENT_AND_THEME_PARKS = LkOccupationTitle(1, "Amusement and Theme Parks", 71, 713110)
    AMUSEMENT_ARCADES = LkOccupationTitle(1, "Amusement Arcades", 71, 713120)
    GAMBLING_INDUSTRIES = LkOccupationTitle(1, "Gambling Industries", 71, 7132)
    CASINOS_EXCEPT_CASINO_HOTELS = LkOccupationTitle(1, "Casinos (except Casino Hotels)", 71, 713210)
    OTHER_GAMBLING_INDUSTRIES = LkOccupationTitle(1, "Other Gambling Industries", 71, 713290)
    OTHER_AMUSEMENT_AND_RECREATION_INDUSTRIES = LkOccupationTitle(1, "Other Amusement and Recreation Industries", 71, 7139)
    GOLF_COURSES_AND_COUNTRY_CLUBS = LkOccupationTitle(1, "Golf Courses and Country Clubs", 71, 713910)
    SKIING_FACILITIES = LkOccupationTitle(1, "Skiing Facilities", 71, 713920)
    MARINAS = LkOccupationTitle(1, "Marinas", 71, 713930)
    FITNESS_AND_RECREATIONAL_SPORTS_CENTERS = LkOccupationTitle(1, "Fitness and Recreational Sports Centers", 71, 713940)
    BOWLING_CENTERS = LkOccupationTitle(1, "Bowling Centers", 71, 713950)
    ALL_OTHER_AMUSEMENT_AND_RECREATION_INDUSTRIES = LkOccupationTitle(1, "All Other Amusement and Recreation Industries", 71, 713990)
    TRAVELER_ACCOMMODATION = LkOccupationTitle(1, "Traveler Accommodation", 72, 7211)
    HOTELS_EXCEPT_CASINO_HOTELS_AND_MOTELS = LkOccupationTitle(1, "Hotels (except Casino Hotels) and Motels", 72, 721110)
    CASINO_HOTELS = LkOccupationTitle(1, "Casino Hotels", 72, 721120)
    BEDANDBREAKFAST_INNS = LkOccupationTitle(1, "Bed-and-Breakfast Inns", 72, 721191)
    ALL_OTHER_TRAVELER_ACCOMMODATION = LkOccupationTitle(1, "All Other Traveler Accommodation", 72, 721199)
    RV_RECREATIONAL_VEHICLE_PARKS_AND_RECREATIONAL_CAMPS = LkOccupationTitle(1, "RV (Recreational Vehicle) Parks and Recreational Camps", 72, 7212)
    RV_RECREATIONAL_VEHICLE_PARKS_AND_CAMPGROUNDS = LkOccupationTitle(1, "RV (Recreational Vehicle) Parks and Campgrounds", 72, 721211)
    RECREATIONAL_AND_VACATION_CAMPS_EXCEPT_CAMPGROUNDS = LkOccupationTitle(1, "Recreational and Vacation Camps (except Campgrounds)", 72, 721214)
    ROOMING_AND_BOARDING_HOUSES_DORMITORIES_AND_WORKERS_CAMPS = LkOccupationTitle(1, "Rooming and Boarding Houses, Dormitories, and Workers' Camps", 72, 7213)
    ROOMING_AND_BOARDING_HOUSES_DORMITORIES_AND_WORKERS_CAMPS = LkOccupationTitle(1, "Rooming and Boarding Houses, Dormitories, and Workers' Camps", 72, 721310)
    SPECIAL_FOOD_SERVICES = LkOccupationTitle(1, "Special Food Services", 72, 7223)
    FOOD_SERVICE_CONTRACTORS = LkOccupationTitle(1, "Food Service Contractors", 72, 722310)
    CATERERS = LkOccupationTitle(1, "Caterers", 72, 722320)
    MOBILE_FOOD_SERVICES = LkOccupationTitle(1, "Mobile Food Services", 72, 722330)
    DRINKING_PLACES_ALCOHOLIC_BEVERAGES = LkOccupationTitle(1, "Drinking Places (Alcoholic Beverages)", 72, 7224)
    DRINKING_PLACES_ALCOHOLIC_BEVERAGES = LkOccupationTitle(1, "Drinking Places (Alcoholic Beverages)", 72, 722410)
    RESTAURANTS_AND_OTHER_EATING_PLACES = LkOccupationTitle(1, "Restaurants and Other Eating Places", 72, 7225)
    FULLSERVICE_RESTAURANTS = LkOccupationTitle(1, "Full-Service Restaurants", 72, 722511)
    LIMITEDSERVICE_RESTAURANTS = LkOccupationTitle(1, "Limited-Service Restaurants", 72, 722513)
    CAFETERIAS_GRILL_BUFFETS_AND_BUFFETS = LkOccupationTitle(1, "Cafeterias, Grill Buffets, and Buffets", 72, 722514)
    SNACK_AND_NONALCOHOLIC_BEVERAGE_BARS = LkOccupationTitle(1, "Snack and Nonalcoholic Beverage Bars", 72, 722515)
    AUTOMOTIVE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Automotive Repair and Maintenance", 81, 8111)
    GENERAL_AUTOMOTIVE_REPAIR = LkOccupationTitle(1, "General Automotive Repair", 81, 811111)
    AUTOMOTIVE_EXHAUST_SYSTEM_REPAIR = LkOccupationTitle(1, "Automotive Exhaust System Repair", 81, 811112)
    AUTOMOTIVE_TRANSMISSION_REPAIR = LkOccupationTitle(1, "Automotive Transmission Repair", 81, 811113)
    OTHER_AUTOMOTIVE_MECHANICAL_AND_ELECTRICAL_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Other Automotive Mechanical and Electrical Repair and Maintenance", 81, 811118)
    AUTOMOTIVE_BODY_PAINT_AND_INTERIOR_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Automotive Body, Paint, and Interior Repair and Maintenance", 81, 811121)
    AUTOMOTIVE_GLASS_REPLACEMENT_SHOPS = LkOccupationTitle(1, "Automotive Glass Replacement Shops", 81, 811122)
    AUTOMOTIVE_OIL_CHANGE_AND_LUBRICATION_SHOPS = LkOccupationTitle(1, "Automotive Oil Change and Lubrication Shops", 81, 811191)
    CAR_WASHES = LkOccupationTitle(1, "Car Washes", 81, 811192)
    ALL_OTHER_AUTOMOTIVE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "All Other Automotive Repair and Maintenance", 81, 811198)
    ELECTRONIC_AND_PRECISION_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Electronic and Precision Equipment Repair and Maintenance", 81, 8112)
    CONSUMER_ELECTRONICS_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Consumer Electronics Repair and Maintenance", 81, 811211)
    COMPUTER_AND_OFFICE_MACHINE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Computer and Office Machine Repair and Maintenance", 81, 811212)
    COMMUNICATION_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Communication Equipment Repair and Maintenance", 81, 811213)
    OTHER_ELECTRONIC_AND_PRECISION_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Other Electronic and Precision Equipment Repair and Maintenance", 81, 811219)
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_EXCEPT_AUTOMOTIVE_AND_ELECTRONIC_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance", 81, 8113)
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_EXCEPT_AUTOMOTIVE_AND_ELECTRONIC_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance", 81, 811310)
    PERSONAL_AND_HOUSEHOLD_GOODS_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Personal and Household Goods Repair and Maintenance", 81, 8114)
    HOME_AND_GARDEN_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Home and Garden Equipment Repair and Maintenance", 81, 811411)
    APPLIANCE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Appliance Repair and Maintenance", 81, 811412)
    REUPHOLSTERY_AND_FURNITURE_REPAIR = LkOccupationTitle(1, "Reupholstery and Furniture Repair", 81, 811420)
    FOOTWEAR_AND_LEATHER_GOODS_REPAIR = LkOccupationTitle(1, "Footwear and Leather Goods Repair", 81, 811430)
    OTHER_PERSONAL_AND_HOUSEHOLD_GOODS_REPAIR_AND_MAINTENANCE = LkOccupationTitle(1, "Other Personal and Household Goods Repair and Maintenance", 81, 811490)
    PERSONAL_CARE_SERVICES = LkOccupationTitle(1, "Personal Care Services", 81, 8121)
    BARBER_SHOPS = LkOccupationTitle(1, "Barber Shops", 81, 812111)
    BEAUTY_SALONS = LkOccupationTitle(1, "Beauty Salons", 81, 812112)
    NAIL_SALONS = LkOccupationTitle(1, "Nail Salons", 81, 812113)
    DIET_AND_WEIGHT_REDUCING_CENTERS = LkOccupationTitle(1, "Diet and Weight Reducing Centers", 81, 812191)
    OTHER_PERSONAL_CARE_SERVICES = LkOccupationTitle(1, "Other Personal Care Services", 81, 812199)
    DEATH_CARE_SERVICES = LkOccupationTitle(1, "Death Care Services", 81, 8122)
    FUNERAL_HOMES_AND_FUNERAL_SERVICES = LkOccupationTitle(1, "Funeral Homes and Funeral Services", 81, 812210)
    CEMETERIES_AND_CREMATORIES = LkOccupationTitle(1, "Cemeteries and Crematories", 81, 812220)
    DRYCLEANING_AND_LAUNDRY_SERVICES = LkOccupationTitle(1, "Drycleaning and Laundry Services", 81, 8123)
    COINOPERATED_LAUNDRIES_AND_DRYCLEANERS = LkOccupationTitle(1, "Coin-Operated Laundries and Drycleaners", 81, 812310)
    DRYCLEANING_AND_LAUNDRY_SERVICES_EXCEPT_COINOPERATED = LkOccupationTitle(1, "Drycleaning and Laundry Services (except Coin-Operated)", 81, 812320)
    LINEN_SUPPLY = LkOccupationTitle(1, "Linen Supply", 81, 812331)
    INDUSTRIAL_LAUNDERERS = LkOccupationTitle(1, "Industrial Launderers", 81, 812332)
    OTHER_PERSONAL_SERVICES = LkOccupationTitle(1, "Other Personal Services", 81, 8129)
    PET_CARE_EXCEPT_VETERINARY_SERVICES = LkOccupationTitle(1, "Pet Care (except Veterinary) Services", 81, 812910)
    PHOTOFINISHING_LABORATORIES_EXCEPT_ONEHOUR = LkOccupationTitle(1, "Photofinishing Laboratories (except One-Hour)", 81, 812921)
    ONEHOUR_PHOTOFINISHING = LkOccupationTitle(1, "One-Hour Photofinishing", 81, 812922)
    PARKING_LOTS_AND_GARAGES = LkOccupationTitle(1, "Parking Lots and Garages", 81, 812930)
    ALL_OTHER_PERSONAL_SERVICES = LkOccupationTitle(1, "All Other Personal Services", 81, 812990)
    RELIGIOUS_ORGANIZATIONS = LkOccupationTitle(1, "Religious Organizations", 81, 8131)
    RELIGIOUS_ORGANIZATIONS = LkOccupationTitle(1, "Religious Organizations", 81, 813110)
    GRANTMAKING_AND_GIVING_SERVICES = LkOccupationTitle(1, "Grantmaking and Giving Services", 81, 8132)
    GRANTMAKING_FOUNDATIONS = LkOccupationTitle(1, "Grantmaking Foundations", 81, 813211)
    VOLUNTARY_HEALTH_ORGANIZATIONS = LkOccupationTitle(1, "Voluntary Health Organizations", 81, 813212)
    OTHER_GRANTMAKING_AND_GIVING_SERVICES = LkOccupationTitle(1, "Other Grantmaking and Giving Services", 81, 813219)
    SOCIAL_ADVOCACY_ORGANIZATIONS = LkOccupationTitle(1, "Social Advocacy Organizations", 81, 8133)
    HUMAN_RIGHTS_ORGANIZATIONS = LkOccupationTitle(1, "Human Rights Organizations", 81, 813311)
    ENVIRONMENT_CONSERVATION_AND_WILDLIFE_ORGANIZATIONS = LkOccupationTitle(1, "Environment, Conservation and Wildlife Organizations", 81, 813312)
    OTHER_SOCIAL_ADVOCACY_ORGANIZATIONS = LkOccupationTitle(1, "Other Social Advocacy Organizations", 81, 813319)
    CIVIC_AND_SOCIAL_ORGANIZATIONS = LkOccupationTitle(1, "Civic and Social Organizations", 81, 8134)
    CIVIC_AND_SOCIAL_ORGANIZATIONS = LkOccupationTitle(1, "Civic and Social Organizations", 81, 813410)
    BUSINESS_PROFESSIONAL_LABOR_POLITICAL_AND_SIMILAR_ORGANIZATIONS = LkOccupationTitle(1, "Business, Professional, Labor, Political, and Similar Organizations", 81, 8139)
    BUSINESS_ASSOCIATIONS = LkOccupationTitle(1, "Business Associations", 81, 813910)
    PROFESSIONAL_ORGANIZATIONS = LkOccupationTitle(1, "Professional Organizations", 81, 813920)
    LABOR_UNIONS_AND_SIMILAR_LABOR_ORGANIZATIONS = LkOccupationTitle(1, "Labor Unions and Similar Labor Organizations", 81, 813930)
    POLITICAL_ORGANIZATIONS = LkOccupationTitle(1, "Political Organizations", 81, 813940)
    OTHER_SIMILAR_ORGANIZATIONS_EXCEPT_BUSINESS_PROFESSIONAL_LABOR_AND_POLITICAL_ORGANIZATIONS = LkOccupationTitle(1, "Other Similar Organizations (except Business, Professional, Labor, and Political Organizations)", 81, 813990)
    PRIVATE_HOUSEHOLDS = LkOccupationTitle(1, "Private Households", 81, 8141)
    PRIVATE_HOUSEHOLDS = LkOccupationTitle(1, "Private Households", 81, 814110)
    EXECUTIVE_LEGISLATIVE_AND_OTHER_GENERAL_GOVERNMENT_SUPPORT = LkOccupationTitle(1, "Executive, Legislative, and Other General Government Support", 92, 9211)
    EXECUTIVE_OFFICES = LkOccupationTitle(1, "Executive Offices", 92, 921110)
    LEGISLATIVE_BODIES = LkOccupationTitle(1, "Legislative Bodies", 92, 921120)
    PUBLIC_FINANCE_ACTIVITIES = LkOccupationTitle(1, "Public Finance Activities", 92, 921130)
    EXECUTIVE_AND_LEGISLATIVE_OFFICES_COMBINED = LkOccupationTitle(1, "Executive and Legislative Offices, Combined", 92, 921140)
    AMERICAN_INDIAN_AND_ALASKA_NATIVE_TRIBAL_GOVERNMENTS = LkOccupationTitle(1, "American Indian and Alaska Native Tribal Governments", 92, 921150)
    OTHER_GENERAL_GOVERNMENT_SUPPORT = LkOccupationTitle(1, "Other General Government Support", 92, 921190)
    JUSTICE_PUBLIC_ORDER_AND_SAFETY_ACTIVITIES = LkOccupationTitle(1, "Justice, Public Order, and Safety Activities", 92, 9221)
    COURTS = LkOccupationTitle(1, "Courts", 92, 922110)
    POLICE_PROTECTION = LkOccupationTitle(1, "Police Protection", 92, 922120)
    LEGAL_COUNSEL_AND_PROSECUTION = LkOccupationTitle(1, "Legal Counsel and Prosecution", 92, 922130)
    CORRECTIONAL_INSTITUTIONS = LkOccupationTitle(1, "Correctional Institutions", 92, 922140)
    PAROLE_OFFICES_AND_PROBATION_OFFICES = LkOccupationTitle(1, "Parole Offices and Probation Offices", 92, 922150)
    FIRE_PROTECTION = LkOccupationTitle(1, "Fire Protection", 92, 922160)
    OTHER_JUSTICE_PUBLIC_ORDER_AND_SAFETY_ACTIVITIES = LkOccupationTitle(1, "Other Justice, Public Order, and Safety Activities", 92, 922190)
    ADMINISTRATION_OF_HUMAN_RESOURCE_PROGRAMS = LkOccupationTitle(1, "Administration of Human Resource Programs", 92, 9231)
    ADMINISTRATION_OF_EDUCATION_PROGRAMS = LkOccupationTitle(1, "Administration of Education Programs", 92, 923110)
    ADMINISTRATION_OF_PUBLIC_HEALTH_PROGRAMS = LkOccupationTitle(1, "Administration of Public Health Programs", 92, 923120)
    ADMINISTRATION_OF_HUMAN_RESOURCE_PROGRAMS_EXCEPT_EDUCATION_PUBLIC_HEALTH_AND_VETERANS_AFFAIRS_PROGRAMS = LkOccupationTitle(1, "Administration of Human Resource Programs (except Education, Public Health, and Veterans' Affairs Programs)", 92, 923130)
    ADMINISTRATION_OF_VETERANS_AFFAIRS = LkOccupationTitle(1, "Administration of Veterans' Affairs", 92, 923140)
    ADMINISTRATION_OF_ENVIRONMENTAL_QUALITY_PROGRAMS = LkOccupationTitle(1, "Administration of Environmental Quality Programs", 92, 9241)
    ADMINISTRATION_OF_AIR_AND_WATER_RESOURCE_AND_SOLID_WASTE_MANAGEMENT_PROGRAMS = LkOccupationTitle(1, "Administration of Air and Water Resource and Solid Waste Management Programs", 92, 924110)
    ADMINISTRATION_OF_CONSERVATION_PROGRAMS = LkOccupationTitle(1, "Administration of Conservation Programs", 92, 924120)
    ADMINISTRATION_OF_HOUSING_PROGRAMS_URBAN_PLANNING_AND_COMMUNITY_DEVELOPMENT = LkOccupationTitle(1, "Administration of Housing Programs, Urban Planning, and Community Development", 92, 9251)
    ADMINISTRATION_OF_HOUSING_PROGRAMS = LkOccupationTitle(1, "Administration of Housing Programs", 92, 925110)
    ADMINISTRATION_OF_URBAN_PLANNING_AND_COMMUNITY_AND_RURAL_DEVELOPMENT = LkOccupationTitle(1, "Administration of Urban Planning and Community and Rural Development", 92, 925120)
    ADMINISTRATION_OF_ECONOMIC_PROGRAMS = LkOccupationTitle(1, "Administration of Economic Programs", 92, 9261)
    ADMINISTRATION_OF_GENERAL_ECONOMIC_PROGRAMS = LkOccupationTitle(1, "Administration of General Economic Programs", 92, 926110)
    REGULATION_AND_ADMINISTRATION_OF_TRANSPORTATION_PROGRAMS = LkOccupationTitle(1, "Regulation and Administration of Transportation Programs", 92, 926120)
    REGULATION_AND_ADMINISTRATION_OF_COMMUNICATIONS_ELECTRIC_GAS_AND_OTHER_UTILITIES = LkOccupationTitle(1, "Regulation and Administration of Communications, Electric, Gas, and Other Utilities", 92, 926130)
    REGULATION_OF_AGRICULTURAL_MARKETING_AND_COMMODITIES = LkOccupationTitle(1, "Regulation of Agricultural Marketing and Commodities", 92, 926140)
    REGULATION_LICENSING_AND_INSPECTION_OF_MISCELLANEOUS_COMMERCIAL_SECTORS = LkOccupationTitle(1, "Regulation, Licensing, and Inspection of Miscellaneous Commercial Sectors", 92, 926150)
    SPACE_RESEARCH_AND_TECHNOLOGY = LkOccupationTitle(1, "Space Research and Technology", 92, 9271)
    SPACE_RESEARCH_AND_TECHNOLOGY = LkOccupationTitle(1, "Space Research and Technology", 92, 927110)
    NATIONAL_SECURITY_AND_INTERNATIONAL_AFFAIRS = LkOccupationTitle(1, "National Security and International Affairs", 92, 9281)
    NATIONAL_SECURITY = LkOccupationTitle(1, "National Security", 92, 928110)
    INTERNATIONAL_AFFAIRS = LkOccupationTitle(1, "International Affairs", 92, 928120)

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


class PrenoteState(LookupTable):
    model = LkPrenoteState
    column_names = ("prenote_state_id", "prenote_state_description")

    PENDING_PRE_PUB = LkPrenoteState(1, "Pending - Needs to be sent to PUB")
    PENDING_WITH_PUB = LkPrenoteState(2, "Pending - Was sent to PUB")
    APPROVED = LkPrenoteState(3, "Approved")
    REJECTED = LkPrenoteState(4, "Rejected")


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
    PEI_WRITEBACK_FILES = LkFlow(10, "PEI Writeback files")
    DFML_DUA_REDUCTION_REPORT = LkFlow(11, "DUA agency reduction report")
    DFML_DIA_REDUCTION_REPORT = LkFlow(12, "DIA agency reduction report")

    # ==============================
    # Delegated Payments Flows
    # ==============================
    DELEGATED_CLAIMANT = LkFlow(20, "Claimant")
    DELEGATED_PAYMENT = LkFlow(21, "Payment")
    DELEGATED_EFT = LkFlow(22, "EFT")


class State(LookupTable):
    model = LkState
    column_names = ("state_id", "state_description", "flow_id")

    VERIFY_VENDOR_STATUS = LkState(1, "Verify vendor status", Flow.UNUSED.flow_id)  # Not used
    DIA_CLAIMANT_LIST_CREATED = LkState(
        2, "Create claimant list for DIA", Flow.DIA_CLAIMANT_LIST.flow_id
    )
    DIA_CLAIMANT_LIST_SUBMITTED = LkState(
        3, "Submit claimant list to DIA", Flow.DIA_CLAIMANT_LIST.flow_id
    )
    PAYMENTS_RETRIEVED = LkState(4, "Payments retrieved", Flow.UNUSED.flow_id)  # Not used
    PAYMENTS_STORED_IN_DB = LkState(5, "Payments stored in db", Flow.UNUSED.flow_id)  # Not used
    DUA_REPORT_FOR_DFML_CREATED = LkState(
        6, "Create DUA report for DFML", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
    )
    DUA_REPORT_FOR_DFML_SUBMITTED = LkState(
        7, "Submit DUA report for DFML", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
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

    # State for sending the PEI writeback file to FINEOS.
    # https://app.lucidchart.com/lucidchart/3ad90c37-4cbb-467e-bfcf-bc98504c98f2/edit
    SEND_PEI_WRITEBACK = LkState(42, "Send PEI writeback", Flow.PEI_WRITEBACK_FILES.flow_id)
    PEI_WRITEBACK_SENT = LkState(
        43, "PEI writeback sent to FINEOS", Flow.PEI_WRITEBACK_FILES.flow_id
    )

    # DUA payment list retrieval.
    DUA_PAYMENT_LIST_SAVED_TO_S3 = LkState(
        44, "DUA payment list saved to S3", Flow.DUA_PAYMENT_LIST.flow_id
    )
    DUA_PAYMENT_LIST_SAVED_TO_DB = LkState(
        45, "New DUA payments stored in database", Flow.DUA_PAYMENT_LIST.flow_id
    )

    # DUA claimant list operations.
    DUA_CLAIMANT_LIST_CREATED = LkState(
        46, "Created claimant list for DUA", Flow.DUA_CLAIMANT_LIST.flow_id
    )
    DUA_CLAIMANT_LIST_SUBMITTED = LkState(
        47, "Submitted claimant list to DIA", Flow.DUA_CLAIMANT_LIST.flow_id
    )

    # DIA payment list retrieval.
    DIA_PAYMENT_LIST_SAVED_TO_S3 = LkState(
        48, "DIA payment list saved to S3", Flow.DIA_PAYMENT_LIST.flow_id
    )
    DIA_PAYMENT_LIST_SAVED_TO_DB = LkState(
        49, "New DIA payments stored in database", Flow.DIA_PAYMENT_LIST.flow_id
    )

    # State for sending new reductions payments to DFML
    DIA_REDUCTIONS_REPORT_SENT = LkState(
        50,
        "New DIA reductions payments report sent to DFML",
        Flow.DFML_DIA_REDUCTION_REPORT.flow_id,
    )
    DUA_REDUCTIONS_REPORT_SENT = LkState(
        51,
        "New DUA reductions payments report sent to DFML",
        Flow.DFML_DUA_REDUCTION_REPORT.flow_id,
    )

    # ==============================
    # Delegated Payments States
    # https://lucid.app/lucidchart/edf54a33-1a3f-432d-82b7-157cf02667a4/edit?useCachedRole=false&shared=true&page=NnnYFBRiym9J#
    # ==============================

    # == Claimant States

    DELEGATED_CLAIMANT_EXTRACTED_FROM_FINEOS = LkState(
        100, "Claimant extracted from FINEOS", Flow.DELEGATED_CLAIMANT.flow_id
    )
    DELEGATED_CLAIMANT_ADD_TO_CLAIMANT_EXTRACT_ERROR_REPORT = LkState(
        101, "Add to Claimant Extract Error Report", Flow.DELEGATED_CLAIMANT.flow_id
    )
    DEPRECATED_DELEGATED_CLAIMANT_EXTRACT_ERROR_REPORT_SENT = LkState(
        102,
        "DEPRECATED STATE - Claimant Extract Error Report sent",
        Flow.DELEGATED_CLAIMANT.flow_id,
    )

    # == EFT States

    DELEGATED_EFT_SEND_PRENOTE = LkState(110, "Send EFT Prenote", Flow.DELEGATED_EFT.flow_id)
    DELEGATED_EFT_PRENOTE_SENT = LkState(111, "EFT Prenote Sent", Flow.DELEGATED_EFT.flow_id)
    DEPRECATED_DELEGATED_EFT_ALLOWABLE_TIME_IN_PRENOTE_STATE_EXCEEDED = LkState(
        112,
        "DEPRECATED STATE - EFT alllowable time in Prenote state exceeded",
        Flow.DELEGATED_EFT.flow_id,
    )
    DEPRECATED_DELEGATED_EFT_ELIGIBLE = LkState(
        113, "DEPRECATED STATE - EFT eligible", Flow.DELEGATED_EFT.flow_id
    )
    DEPRECATED_DELEGATED_EFT_ADD_TO_ERROR_REPORT = LkState(
        114, "DEPRECATED STATE - Add to EFT Error Report", Flow.DELEGATED_EFT.flow_id
    )
    DEPRECATED_DELEGATED_EFT_ERROR_REPORT_SENT = LkState(
        115, "DEPRECATED STATE - EFT Error Report sent", Flow.DELEGATED_EFT.flow_id
    )

    # == Payment States

    # FINEOS Extract stage
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT = LkState(
        120, "Add to Payment Error Report", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ERROR_REPORT_SENT = LkState(
        121, "DEPRECATED STATE - Payment Error Report sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_ZERO_PAYMENT = LkState(
        122,
        "Waiting for Payment Audit Report response - $0 payment",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        123, "Add $0 payment to FINEOS Writeback", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_ZERO_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        124, "$0 payment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_OVERPAYMENT = LkState(
        125,
        "Waiting for Payment Audit Report response - overpayment",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK = LkState(
        126, "Add overpayment to FINEOS Writeback", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_OVERPAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        127, "Overpayment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING = LkState(
        128, "Staged for Payment Audit Report sampling", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_AUDIT_REPORT = LkState(
        129, "Add to Payment Audit Report", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_PAYMENT_AUDIT_REPORT_SENT = LkState(
        130, "Payment Audit Report sent", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_NOT_SAMPLED = LkState(
        131,
        "Waiting for Payment Audit Report response - not sampled",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    # Payment Rejects processing stage
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT = LkState(
        132, "Add to Payment Reject Report", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPRECATED_DELEGATED_PAYMENT_ADD_ACCEPTED_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        134,
        "DEPRECATED STATE - Add accepted payment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_ACCEPTED_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        135,
        "DEPRECATED STATE - Accepted payment FINEOS Writeback sent",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    DELEGATED_PAYMENT_VALIDATED = LkState(157, "Payment Validated", Flow.DELEGATED_PAYMENT.flow_id)

    DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK = LkState(
        136, "Add to PUB Transaction - Check", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT = LkState(
        137, "PUB Transaction sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT = LkState(
        138, "Add to PUB Transaction - EFT", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT = LkState(
        139, "PUB Transaction sent - EFT", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_FINEOS_WRITEBACK_CHECK_SENT = LkState(
        158, "FINEOS Writeback sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT = LkState(
        159, "FINEOS Writeback sent - EFT", Flow.DELEGATED_PAYMENT.flow_id
    )

    # PUB Status Return stage
    DEPRECATED_DELEGATED_PAYMENT_ADD_TO_PUB_ERROR_REPORT = LkState(
        140, "DEPRECATED STATE - Add to PUB Error Report", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_PUB_ERROR_REPORT_SENT = LkState(
        141, "DEPRECATED STATE - PUB Error Report sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPRECATED_DELEGATED_PAYMENT_ADD_TO_PUB_PAYMENT_FINEOS_WRITEBACK = LkState(
        142,
        "DEPRECATED STATE - Add to PUB payment FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_PUB_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        143, "DEPRECATED STATE - PUB payment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_COMPLETE = LkState(144, "Payment complete", Flow.DELEGATED_PAYMENT.flow_id)

    # Delegated payment states for cancellations (similar to 122-127)
    DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION = LkState(
        145,
        "Waiting for Payment Audit Report response - cancellation payment",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        146, "Add cancellation payment to FINEOS Writeback", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_CANCELLATION_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        147, "cancellation payment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    # Report states for employer reimbursement payment states
    DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_EMPLOYER_REIMBURSEMENT = LkState(
        148,
        "Waiting for Payment Audit Report response - employer reimbursement payment",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DELEGATED_PAYMENT_ADD_EMPLOYER_REIMBURSEMENT_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        149,
        "Add employer reimbursement payment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        150, "Employer reimbursement payment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    # PEI WRITE BACK ERROR TO FINEOS
    # These states are not retryable because this is erroring after we've sent a payment to PUB
    # If there was an error, it will require a manual effort to fix.
    ADD_TO_ERRORED_PEI_WRITEBACK = LkState(
        151, "Add to Errored PEI writeback", Flow.DELEGATED_PAYMENT.flow_id
    )

    ERRORED_PEI_WRITEBACK_SENT = LkState(
        152, "Errored PEI write back sent to FINEOS", Flow.DELEGATED_PAYMENT.flow_id
    )

    # Delegated payments address validation states.
    DEPRECATED_CLAIMANT_READY_FOR_ADDRESS_VALIDATION = LkState(
        153,
        "DEPRECATED STATE - Claimant ready for address validation",
        Flow.DELEGATED_CLAIMANT.flow_id,
    )
    DEPRECATED_CLAIMANT_FAILED_ADDRESS_VALIDATION = LkState(
        154,
        "DEPRECATED STATE - Claimant failed address validation",
        Flow.DELEGATED_CLAIMANT.flow_id,
    )
    PAYMENT_READY_FOR_ADDRESS_VALIDATION = LkState(
        155, "Payment ready for address validation", Flow.DELEGATED_PAYMENT.flow_id
    )
    PAYMENT_FAILED_ADDRESS_VALIDATION = LkState(
        156, "Payment failed address validation", Flow.DELEGATED_PAYMENT.flow_id,
    )

    # 2nd writeback to FINEOS for successful checks
    DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_ADD_CHECK = LkState(
        160, "Add to FINEOS Writeback #2 - Check", Flow.DELEGATED_PAYMENT.flow_id
    )
    DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_SENT_CHECK = LkState(
        161, "FINEOS Writeback #2 sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )


class PaymentTransactionType(LookupTable):
    model = LkPaymentTransactionType
    column_names = ("payment_transaction_type_id", "payment_transaction_type_description")

    STANDARD = LkPaymentTransactionType(1, "Standard")
    ZERO_DOLLAR = LkPaymentTransactionType(2, "Zero Dollar")
    OVERPAYMENT = LkPaymentTransactionType(3, "Overpayment")
    CANCELLATION = LkPaymentTransactionType(4, "Cancellation")
    UNKNOWN = LkPaymentTransactionType(5, "Unknown")
    EMPLOYER_REIMBURSEMENT = LkPaymentTransactionType(6, "Employer Reimbursement")


class PaymentCheckStatus(LookupTable):
    model = LkPaymentCheckStatus
    column_names = ("payment_check_status_id", "payment_check_status_description")

    PAID = LkPaymentCheckStatus(1, "Paid")
    OUTSTANDING = LkPaymentCheckStatus(2, "Outstanding")
    FUTURE = LkPaymentCheckStatus(3, "Future")
    VOID = LkPaymentCheckStatus(4, "Void")
    STALE = LkPaymentCheckStatus(5, "Stale")
    STOP = LkPaymentCheckStatus(6, "Stop")


class ReferenceFileType(LookupTable):
    model = LkReferenceFileType
    column_names = ("reference_file_type_id", "reference_file_type_description", "num_files_in_set")

    GAX = LkReferenceFileType(1, "GAX", 2)
    VCC = LkReferenceFileType(2, "VCC", 2)
    PAYMENT_EXTRACT = LkReferenceFileType(3, "Payment export", 3)
    VENDOR_CLAIM_EXTRACT = LkReferenceFileType(4, "Vendor export", 3)
    DUA_CLAIMANT_LIST = LkReferenceFileType(5, "DUA claimant list", 1)
    DIA_CLAIMANT_LIST = LkReferenceFileType(6, "DIA claimant list", 1)
    DUA_PAYMENT_LIST = LkReferenceFileType(7, "DUA payment list", 1)
    DIA_PAYMENT_LIST = LkReferenceFileType(8, "DIA payment list", 1)
    DUA_REDUCTION_REPORT_FOR_DFML = LkReferenceFileType(
        9, "DUA payments for DFML reduction report", 1
    )
    OUTBOUND_STATUS_RETURN = LkReferenceFileType(10, "Outbound Status Return", 1)
    OUTBOUND_VENDOR_CUSTOMER_RETURN = LkReferenceFileType(11, "Outbound Vendor Customer Return", 1)
    OUTBOUND_PAYMENT_RETURN = LkReferenceFileType(12, "Outbound Payment Return", 1)
    PEI_WRITEBACK = LkReferenceFileType(13, "PEI Writeback", 1)
    DIA_REDUCTION_REPORT_FOR_DFML = LkReferenceFileType(
        14, "DIA payments for DFML reduction report", 1
    )
    PUB_NACHA = LkReferenceFileType(15, "PUB NACHA file", 1)
    PUB_ACH_RETURN = LkReferenceFileType(16, "PUB ACH Return", 1)
    PUB_CHECK_RETURN = LkReferenceFileType(17, "PUB Check Return", 1)

    DELEGATED_PAYMENT_AUDIT_REPORT = LkReferenceFileType(20, "Payment Audit Report", 1)
    DELEGATED_PAYMENT_REJECTS = LkReferenceFileType(21, "Payment Rejects", 1)
    FINEOS_CLAIMANT_EXTRACT = LkReferenceFileType(24, "Claimant extract", 2)
    FINEOS_PAYMENT_EXTRACT = LkReferenceFileType(25, "Payment extract", 4)

    PUB_EZ_CHECK = LkReferenceFileType(26, "PUB EZ check file", 1)
    PUB_POSITIVE_PAYMENT = LkReferenceFileType(27, "PUB positive pay file", 1)

    DELEGATED_PAYMENT_REPORT_FILE = LkReferenceFileType(28, "SQL Report", 1)


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
    PaymentTransactionType.sync_to_database(db_session)
    PaymentCheckStatus.sync_to_database(db_session)
    PrenoteState.sync_to_database(db_session)
    PubErrorType.sync_to_database(db_session)
    db_session.commit()
