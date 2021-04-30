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
    occupation_code = Column(Integer, unique=True)
    occupation_description = Column(Text)

    def __init__(self, occupation_id, occupation_code, occupation_description):
        self.occupation_id = occupation_id
        self.occupation_description = occupation_description
        self.occupation_code = occupation_code


class LkOccupationTitle(Base):
    __tablename__ = "lk_occupation_title"
    occupation_title_id = Column(Integer, primary_key=True, autoincrement=True)
    occupation_id = Column(Integer, ForeignKey("lk_occupation.occupation_id"))
    occupation_title_code = Column(Integer)
    occupation_title_description = Column(Text)

    def __init__(
        self,
        occupation_title_id,
        occupation_id,
        occupation_title_code,
        occupation_title_description,
    ):
        self.occupation_title_id = occupation_title_id
        self.occupation_id = occupation_id
        self.occupation_title_code = occupation_title_code
        self.occupation_title_description = occupation_title_description


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
    # @todo: this broke dor imports, occupation_title_id = Column(Integer, ForeignKey("lk_occupation_title.occupation_title_id"), nullable=True)
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
    column_names = (
        "occupation_id",
        "occupation_code",
        "occupation_description",
    )

    # HEALTH_CARE = LkOccupation(1, "Health Care")
    # SALES_CLERK = LkOccupation(2, "Sales Clerk")
    # ADMINISTRATIVE = LkOccupation(3, "Administrative")
    # ENGINEER = LkOccupation(4, "Engineer")

    # NAICS Occupations -> https://www.naics.com/search/
    AGRICULTURE_FORESTRY_FISHING_HUNTING = LkOccupation(
        1, 11, "Agriculture, Forestry, Fishing and Hunting"
    )
    MINING = LkOccupation(2, 21, "Mining")
    UTILITIES = LkOccupation(3, 22, "Utilities")
    CONSTRUCTION = LkOccupation(4, 23, "Construction")
    MANUFACTURING = LkOccupation(5, 31, "Manufacturing")  # @todo: category code up to 33
    WHOLESALE_TRADE = LkOccupation(6, 42, "Wholesale Trade")
    RETAIL_TRADE = LkOccupation(7, 44, "Retail Trade")  # @todo: category code up to 45
    TRANSPORTATION_WAREHOUSING = LkOccupation(
        8, 48, "Transportation and Warehousing"
    )  # @todo: category code up to 49
    INFORMATION = LkOccupation(9, 51, "Information")
    FINANCE_INSURANCE = LkOccupation(10, 52, "Finance and Insurance")
    REAL_ESTATE_RENTAL_LEASING = LkOccupation(11, 53, "Real Estate Rental and Leasing")
    PROFESSIONAL_SCIENTIFIC_TECHNICAL = LkOccupation(
        12, 54, "Professional, Scientific, and Technical Services"
    )
    MANAGEMENT_COMPANIES_ENTERPRISES = LkOccupation(
        13, 55, "Management of Companies and Enterprises"
    )
    ADMINISTRATIVE_SUPPORT_WASTE_MANAGEMENT_REMEDIATION = LkOccupation(
        14, 56, "Administrative and Support and Waste Management and Remediation Services"
    )
    EDUCATIONAL = LkOccupation(15, 61, "Educational Services")
    HEALTH_CARE_SOCIAL_ASSISTANCE = LkOccupation(16, 62, "Health Care and Social Assistance")
    ARTS_ENTERTAINMENT_RECREATION = LkOccupation(17, 71, "Arts, Entertainment, and Recreation")
    ACCOMMODATION_FOOD_SERVICES = LkOccupation(18, 72, "Accommodation and Food Services")
    OTHER_SERVICES = LkOccupation(19, 81, "Other Services (except Public Administration)")
    PUBLIC_ADMINISTRATION = LkOccupation(20, 92, "Public Administration")


class OccupationTitle(LookupTable):
    model = LkOccupationTitle
    column_names = (
        "occupation_title_id",
        "occupation_id",
        "occupation_title_code",
        "occupation_title_description",
    )

    OILSEED_AND_GRAIN_FARMING = LkOccupationTitle(1, 1, 1111, "Oilseed and Grain Farming")
    SOYBEAN_FARMING = LkOccupationTitle(2, 1, 111110, "Soybean Farming")
    OILSEED_EXCEPT_SOYBEAN_FARMING = LkOccupationTitle(
        3, 1, 111120, "Oilseed (except Soybean) Farming"
    )

    DRY_PEA_AND_BEAN_FARMING = LkOccupationTitle(4, 1, 111130, "Dry Pea and Bean Farming")
    WHEAT_FARMING = LkOccupationTitle(5, 1, 111140, "Wheat Farming")
    CORN_FARMING = LkOccupationTitle(6, 1, 111150, "Corn Farming")
    RICE_FARMING = LkOccupationTitle(7, 1, 111160, "Rice Farming")
    OILSEED_AND_GRAIN_COMBINATION_FARMING = LkOccupationTitle(
        8, 1, 111191, "Oilseed and Grain Combination Farming"
    )
    ALL_OTHER_GRAIN_FARMING = LkOccupationTitle(9, 1, 111199, "All Other Grain Farming")
    VEGETABLE_AND_MELON_FARMING = LkOccupationTitle(10, 1, 1112, "Vegetable and Melon Farming")
    POTATO_FARMING = LkOccupationTitle(11, 1, 111211, "Potato Farming")
    OTHER_VEGETABLE_EXCEPT_POTATO_AND_MELON_FARMING = LkOccupationTitle(
        12, 1, 111219, "Other Vegetable (except Potato) and Melon Farming"
    )
    FRUIT_AND_TREE_NUT_FARMING = LkOccupationTitle(13, 1, 1113, "Fruit and Tree Nut Farming")
    ORANGE_GROVES = LkOccupationTitle(14, 1, 111310, "Orange Groves")
    CITRUS_EXCEPT_ORANGE_GROVES = LkOccupationTitle(15, 1, 111320, "Citrus (except Orange) Groves")
    APPLE_ORCHARDS = LkOccupationTitle(16, 1, 111331, "Apple Orchards")
    GRAPE_VINEYARDS = LkOccupationTitle(17, 1, 111332, "Grape Vineyards")
    STRAWBERRY_FARMING = LkOccupationTitle(18, 1, 111333, "Strawberry Farming")
    BERRY_EXCEPT_STRAWBERRY_FARMING = LkOccupationTitle(
        19, 1, 111334, "Berry (except Strawberry) Farming"
    )
    TREE_NUT_FARMING = LkOccupationTitle(20, 1, 111335, "Tree Nut Farming")
    FRUIT_AND_TREE_NUT_COMBINATION_FARMING = LkOccupationTitle(
        21, 1, 111336, "Fruit and Tree Nut Combination Farming"
    )
    OTHER_NONCITRUS_FRUIT_FARMING = LkOccupationTitle(
        22, 1, 111339, "Other Noncitrus Fruit Farming"
    )
    GREENHOUSE_NURSERY_AND_FLORICULTURE_PRODUCTION = LkOccupationTitle(
        23, 1, 1114, "Greenhouse, Nursery, and Floriculture Production"
    )
    MUSHROOM_PRODUCTION = LkOccupationTitle(24, 1, 111411, "Mushroom Production")
    OTHER_FOOD_CROPS_GROWN_UNDER_COVER = LkOccupationTitle(
        25, 1, 111419, "Other Food Crops Grown Under Cover"
    )
    NURSERY_AND_TREE_PRODUCTION = LkOccupationTitle(26, 1, 111421, "Nursery and Tree Production")
    FLORICULTURE_PRODUCTION = LkOccupationTitle(27, 1, 111422, "Floriculture Production")
    OTHER_CROP_FARMING = LkOccupationTitle(28, 1, 1119, "Other Crop Farming")
    TOBACCO_FARMING = LkOccupationTitle(29, 1, 111910, "Tobacco Farming")
    COTTON_FARMING = LkOccupationTitle(30, 1, 111920, "Cotton Farming")
    SUGARCANE_FARMING = LkOccupationTitle(31, 1, 111930, "Sugarcane Farming")
    HAY_FARMING = LkOccupationTitle(32, 1, 111940, "Hay Farming")
    SUGAR_BEET_FARMING = LkOccupationTitle(33, 1, 111991, "Sugar Beet Farming")
    PEANUT_FARMING = LkOccupationTitle(34, 1, 111992, "Peanut Farming")
    ALL_OTHER_MISCELLANEOUS_CROP_FARMING = LkOccupationTitle(
        35, 1, 111998, "All Other Miscellaneous Crop Farming"
    )
    CATTLE_RANCHING_AND_FARMING = LkOccupationTitle(36, 1, 1121, "Cattle Ranching and Farming")
    BEEF_CATTLE_RANCHING_AND_FARMING = LkOccupationTitle(
        37, 1, 112111, "Beef Cattle Ranching and Farming"
    )
    CATTLE_FEEDLOTS = LkOccupationTitle(38, 1, 112112, "Cattle Feedlots")
    DAIRY_CATTLE_AND_MILK_PRODUCTION = LkOccupationTitle(
        39, 1, 112120, "Dairy Cattle and Milk Production"
    )
    DUAL_PURPOSE_CATTLE_RANCHING_AND_FARMING = LkOccupationTitle(
        40, 1, 112130, "Dual-Purpose Cattle Ranching and Farming"
    )
    HOG_AND_PIG_FARMING_4 = LkOccupationTitle(41, 1, 1122, "Hog and Pig Farming")
    HOG_AND_PIG_FARMING = LkOccupationTitle(42, 1, 112210, "Hog and Pig Farming")
    POULTRY_AND_EGG_PRODUCTION = LkOccupationTitle(43, 1, 1123, "Poultry and Egg Production")
    CHICKEN_EGG_PRODUCTION = LkOccupationTitle(44, 1, 112310, "Chicken Egg Production")
    BROILERS_AND_OTHER_MEAT_TYPE_CHICKEN_PRODUCTION = LkOccupationTitle(
        45, 1, 112320, "Broilers and Other Meat Type Chicken Production"
    )
    TURKEY_PRODUCTION = LkOccupationTitle(46, 1, 112330, "Turkey Production")
    POULTRY_HATCHERIES = LkOccupationTitle(47, 1, 112340, "Poultry Hatcheries")
    OTHER_POULTRY_PRODUCTION = LkOccupationTitle(48, 1, 112390, "Other Poultry Production")
    SHEEP_AND_GOAT_FARMING = LkOccupationTitle(49, 1, 1124, "Sheep and Goat Farming")
    SHEEP_FARMING = LkOccupationTitle(50, 1, 112410, "Sheep Farming")
    GOAT_FARMING = LkOccupationTitle(51, 1, 112420, "Goat Farming")
    AQUACULTURE = LkOccupationTitle(52, 1, 1125, "Aquaculture")
    FINFISH_FARMING_AND_FISH_HATCHERIES = LkOccupationTitle(
        53, 1, 112511, "Finfish Farming and Fish Hatcheries"
    )
    SHELLFISH_FARMING = LkOccupationTitle(54, 1, 112512, "Shellfish Farming")
    OTHER_AQUACULTURE = LkOccupationTitle(55, 1, 112519, "Other Aquaculture")
    OTHER_ANIMAL_PRODUCTION = LkOccupationTitle(56, 1, 1129, "Other Animal Production")
    APICULTURE = LkOccupationTitle(57, 1, 112910, "Apiculture")
    HORSES_AND_OTHER_EQUINE_PRODUCTION = LkOccupationTitle(
        58, 1, 112920, "Horses and Other Equine Production"
    )
    FUR_BEARING_ANIMAL_AND_RABBIT_PRODUCTION = LkOccupationTitle(
        59, 1, 112930, "Fur-Bearing Animal and Rabbit Production"
    )
    ALL_OTHER_ANIMAL_PRODUCTION = LkOccupationTitle(60, 1, 112990, "All Other Animal Production")
    TIMBER_TRACT_OPERATIONS_4 = LkOccupationTitle(61, 1, 1131, "Timber Tract Operations")
    TIMBER_TRACT_OPERATIONS = LkOccupationTitle(62, 1, 113110, "Timber Tract Operations")
    FOREST_NURSERIES_AND_GATHERING_OF_FOREST_PRODUCTS_4 = LkOccupationTitle(
        63, 1, 1132, "Forest Nurseries and Gathering of Forest Products"
    )
    FOREST_NURSERIES_AND_GATHERING_OF_FOREST_PRODUCTS = LkOccupationTitle(
        64, 1, 113210, "Forest Nurseries and Gathering of Forest Products"
    )
    LOGGING_4 = LkOccupationTitle(65, 1, 1133, "Logging")
    LOGGING = LkOccupationTitle(66, 1, 113310, "Logging")
    FISHING = LkOccupationTitle(67, 1, 1141, "Fishing")
    FINFISH_FISHING = LkOccupationTitle(68, 1, 114111, "Finfish Fishing")
    SHELLFISH_FISHING = LkOccupationTitle(69, 1, 114112, "Shellfish Fishing")
    OTHER_MARINE_FISHING = LkOccupationTitle(70, 1, 114119, "Other Marine Fishing")
    HUNTING_AND_TRAPPING_4 = LkOccupationTitle(71, 1, 1142, "Hunting and Trapping")
    HUNTING_AND_TRAPPING = LkOccupationTitle(72, 1, 114210, "Hunting and Trapping")
    SUPPORT_ACTIVITIES_FOR_CROP_PRODUCTION = LkOccupationTitle(
        73, 1, 1151, "Support Activities for Crop Production"
    )
    COTTON_GINNING = LkOccupationTitle(74, 1, 115111, "Cotton Ginning")
    SOIL_PREPARATION_PLANTING_AND_CULTIVATING = LkOccupationTitle(
        75, 1, 115112, "Soil Preparation, Planting, and Cultivating"
    )
    CROP_HARVESTING_PRIMARILY_BY_MACHINE = LkOccupationTitle(
        76, 1, 115113, "Crop Harvesting, Primarily by Machine"
    )
    POSTHARVEST_CROP_ACTIVITIES_EXCEPT_COTTON_GINNING = LkOccupationTitle(
        77, 1, 115114, "Postharvest Crop Activities (except Cotton Ginning)"
    )
    FARM_LABOR_CONTRACTORS_AND_CREW_LEADERS = LkOccupationTitle(
        78, 1, 115115, "Farm Labor Contractors and Crew Leaders"
    )
    FARM_MANAGEMENT_SERVICES = LkOccupationTitle(79, 1, 115116, "Farm Management Services")
    SUPPORT_ACTIVITIES_FOR_ANIMAL_PRODUCTION_4 = LkOccupationTitle(
        80, 1, 1152, "Support Activities for Animal Production"
    )
    SUPPORT_ACTIVITIES_FOR_ANIMAL_PRODUCTION = LkOccupationTitle(
        81, 1, 115210, "Support Activities for Animal Production"
    )
    SUPPORT_ACTIVITIES_FOR_FORESTRY_4 = LkOccupationTitle(
        82, 1, 1153, "Support Activities for Forestry"
    )
    SUPPORT_ACTIVITIES_FOR_FORESTRY = LkOccupationTitle(
        83, 1, 115310, "Support Activities for Forestry"
    )
    OIL_AND_GAS_EXTRACTION = LkOccupationTitle(84, 2, 2111, "Oil and Gas Extraction")
    CRUDE_PETROLEUM_EXTRACTION = LkOccupationTitle(85, 2, 211120, "Crude Petroleum Extraction")
    NATURAL_GAS_EXTRACTION = LkOccupationTitle(86, 2, 211130, "Natural Gas Extraction")
    COAL_MINING = LkOccupationTitle(87, 2, 2121, "Coal Mining")
    BITUMINOUS_COAL_AND_LIGNITE_SURFACE_MINING = LkOccupationTitle(
        88, 2, 212111, "Bituminous Coal and Lignite Surface Mining"
    )
    BITUMINOUS_COAL_UNDERGROUND_MINING = LkOccupationTitle(
        89, 2, 212112, "Bituminous Coal Underground Mining"
    )
    ANTHRACITE_MINING = LkOccupationTitle(90, 2, 212113, "Anthracite Mining")
    METAL_ORE_MINING = LkOccupationTitle(91, 2, 2122, "Metal Ore Mining")
    IRON_ORE_MINING = LkOccupationTitle(92, 2, 212210, "Iron Ore Mining")
    GOLD_ORE_MINING = LkOccupationTitle(93, 2, 212221, "Gold Ore Mining")
    SILVER_ORE_MINING = LkOccupationTitle(94, 2, 212222, "Silver Ore Mining")
    COPPER_NICKEL_LEAD_AND_ZINC_MINING = LkOccupationTitle(
        95, 2, 212230, "Copper, Nickel, Lead, and Zinc Mining"
    )
    URANIUM_RADIUM_VANADIUM_ORE_MINING = LkOccupationTitle(
        96, 2, 212291, "Uranium-Radium-Vanadium Ore Mining"
    )
    ALL_OTHER_METAL_ORE_MINING = LkOccupationTitle(97, 2, 212299, "All Other Metal Ore Mining")
    NONMETALLIC_MINERAL_MINING_AND_QUARRYING = LkOccupationTitle(
        98, 2, 2123, "Nonmetallic Mineral Mining and Quarrying"
    )
    DIMENSION_STONE_MINING_AND_QUARRYING = LkOccupationTitle(
        99, 2, 212311, "Dimension Stone Mining and Quarrying"
    )
    CRUSHED_AND_BROKEN_LIMESTONE_MINING_AND_QUARRYING = LkOccupationTitle(
        100, 2, 212312, "Crushed and Broken Limestone Mining and Quarrying"
    )
    CRUSHED_AND_BROKEN_GRANITE_MINING_AND_QUARRYING = LkOccupationTitle(
        101, 2, 212313, "Crushed and Broken Granite Mining and Quarrying"
    )
    OTHER_CRUSHED_AND_BROKEN_STONE_MINING_AND_QUARRYING = LkOccupationTitle(
        102, 2, 212319, "Other Crushed and Broken Stone Mining and Quarrying"
    )
    CONSTRUCTION_SAND_AND_GRAVEL_MINING = LkOccupationTitle(
        103, 2, 212321, "Construction Sand and Gravel Mining"
    )
    INDUSTRIAL_SAND_MINING = LkOccupationTitle(104, 2, 212322, "Industrial Sand Mining")
    KAOLIN_AND_BALL_CLAY_MINING = LkOccupationTitle(105, 2, 212324, "Kaolin and Ball Clay Mining")
    CLAY_AND_CERAMIC_AND_REFRACTORY_MINERALS_MINING = LkOccupationTitle(
        106, 2, 212325, "Clay and Ceramic and Refractory Minerals Mining"
    )
    POTASH_SODA_AND_BORATE_MINERAL_MINING = LkOccupationTitle(
        107, 2, 212391, "Potash, Soda, and Borate Mineral Mining"
    )
    PHOSPHATE_ROCK_MINING = LkOccupationTitle(108, 2, 212392, "Phosphate Rock Mining")
    OTHER_CHEMICAL_AND_FERTILIZER_MINERAL_MINING = LkOccupationTitle(
        109, 2, 212393, "Other Chemical and Fertilizer Mineral Mining"
    )
    ALL_OTHER_NONMETALLIC_MINERAL_MINING = LkOccupationTitle(
        110, 2, 212399, "All Other Nonmetallic Mineral Mining"
    )
    SUPPORT_ACTIVITIES_FOR_MINING = LkOccupationTitle(111, 2, 2131, "Support Activities for Mining")
    DRILLING_OIL_AND_GAS_WELLS = LkOccupationTitle(112, 2, 213111, "Drilling Oil and Gas Wells")
    SUPPORT_ACTIVITIES_FOR_OIL_AND_GAS_OPERATIONS = LkOccupationTitle(
        113, 2, 213112, "Support Activities for Oil and Gas Operations"
    )
    SUPPORT_ACTIVITIES_FOR_COAL_MINING = LkOccupationTitle(
        114, 2, 213113, "Support Activities for Coal Mining"
    )
    SUPPORT_ACTIVITIES_FOR_METAL_MINING = LkOccupationTitle(
        115, 2, 213114, "Support Activities for Metal Mining"
    )
    SUPPORT_ACTIVITIES_FOR_NONMETALLIC_MINERALS_EXCEPT_FUELS_MINING = LkOccupationTitle(
        116, 2, 213115, "Support Activities for Nonmetallic Minerals (except Fuels) Mining"
    )
    ELECTRIC_POWER_GENERATION_TRANSMISSION_AND_DISTRIBUTION = LkOccupationTitle(
        117, 3, 2211, "Electric Power Generation, Transmission and Distribution"
    )
    HYDROELECTRIC_POWER_GENERATION = LkOccupationTitle(
        118, 3, 221111, "Hydroelectric Power Generation"
    )
    FOSSIL_FUEL_ELECTRIC_POWER_GENERATION = LkOccupationTitle(
        119, 3, 221112, "Fossil Fuel Electric Power Generation"
    )
    NUCLEAR_ELECTRIC_POWER_GENERATION = LkOccupationTitle(
        120, 3, 221113, "Nuclear Electric Power Generation"
    )
    SOLAR_ELECTRIC_POWER_GENERATION = LkOccupationTitle(
        121, 3, 221114, "Solar Electric Power Generation"
    )
    WIND_ELECTRIC_POWER_GENERATION = LkOccupationTitle(
        122, 3, 221115, "Wind Electric Power Generation"
    )
    GEOTHERMAL_ELECTRIC_POWER_GENERATION = LkOccupationTitle(
        123, 3, 221116, "Geothermal Electric Power Generation"
    )
    BIOMASS_ELECTRIC_POWER_GENERATION = LkOccupationTitle(
        124, 3, 221117, "Biomass Electric Power Generation"
    )
    OTHER_ELECTRIC_POWER_GENERATION = LkOccupationTitle(
        125, 3, 221118, "Other Electric Power Generation"
    )
    ELECTRIC_BULK_POWER_TRANSMISSION_AND_CONTROL = LkOccupationTitle(
        126, 3, 221121, "Electric Bulk Power Transmission and Control"
    )
    ELECTRIC_POWER_DISTRIBUTION = LkOccupationTitle(127, 3, 221122, "Electric Power Distribution")
    NATURAL_GAS_DISTRIBUTION_4 = LkOccupationTitle(128, 3, 2212, "Natural Gas Distribution")
    NATURAL_GAS_DISTRIBUTION = LkOccupationTitle(129, 3, 221210, "Natural Gas Distribution")
    WATER_SEWAGE_AND_OTHER_SYSTEMS = LkOccupationTitle(
        130, 3, 2213, "Water, Sewage and Other Systems"
    )
    WATER_SUPPLY_AND_IRRIGATION_SYSTEMS = LkOccupationTitle(
        131, 3, 221310, "Water Supply and Irrigation Systems"
    )
    SEWAGE_TREATMENT_FACILITIES = LkOccupationTitle(132, 3, 221320, "Sewage Treatment Facilities")
    STEAM_AND_AIR_CONDITIONING_SUPPLY = LkOccupationTitle(
        133, 3, 221330, "Steam and Air-Conditioning Supply"
    )
    RESIDENTIAL_BUILDING_CONSTRUCTION = LkOccupationTitle(
        134, 4, 2361, "Residential Building Construction"
    )
    NEW_SINGLE_FAMILY_HOUSING_CONSTRUCTION_EXCEPT_FOR_SALE_BUILDERS = LkOccupationTitle(
        135, 4, 236115, "New Single-Family Housing Construction (except For-Sale Builders)"
    )
    NEW_MULTIFAMILY_HOUSING_CONSTRUCTION_EXCEPT_FOR_SALE_BUILDERS = LkOccupationTitle(
        136, 4, 236116, "New Multifamily Housing Construction (except For-Sale Builders)"
    )
    NEW_HOUSING_FOR_SALE_BUILDERS = LkOccupationTitle(
        137, 4, 236117, "New Housing For-Sale Builders"
    )
    RESIDENTIAL_REMODELERS = LkOccupationTitle(138, 4, 236118, "Residential Remodelers")
    NONRESIDENTIAL_BUILDING_CONSTRUCTION = LkOccupationTitle(
        139, 4, 2362, "Nonresidential Building Construction"
    )
    INDUSTRIAL_BUILDING_CONSTRUCTION = LkOccupationTitle(
        140, 4, 236210, "Industrial Building Construction"
    )
    COMMERCIAL_AND_INSTITUTIONAL_BUILDING_CONSTRUCTION = LkOccupationTitle(
        141, 4, 236220, "Commercial and Institutional Building Construction"
    )
    UTILITY_SYSTEM_CONSTRUCTION = LkOccupationTitle(142, 4, 2371, "Utility System Construction")
    WATER_AND_SEWER_LINE_AND_RELATED_STRUCTURES_CONSTRUCTION = LkOccupationTitle(
        143, 4, 237110, "Water and Sewer Line and Related Structures Construction"
    )
    OIL_AND_GAS_PIPELINE_AND_RELATED_STRUCTURES_CONSTRUCTION = LkOccupationTitle(
        144, 4, 237120, "Oil and Gas Pipeline and Related Structures Construction"
    )
    POWER_AND_COMMUNICATION_LINE_AND_RELATED_STRUCTURES_CONSTRUCTION = LkOccupationTitle(
        145, 4, 237130, "Power and Communication Line and Related Structures Construction"
    )
    LAND_SUBDIVISION_4 = LkOccupationTitle(146, 4, 2372, "Land Subdivision")
    LAND_SUBDIVISION = LkOccupationTitle(147, 4, 237210, "Land Subdivision")
    HIGHWAY_STREET_AND_BRIDGE_CONSTRUCTION_4 = LkOccupationTitle(
        148, 4, 2373, "Highway, Street, and Bridge Construction"
    )
    HIGHWAY_STREET_AND_BRIDGE_CONSTRUCTION = LkOccupationTitle(
        149, 4, 237310, "Highway, Street, and Bridge Construction"
    )
    OTHER_HEAVY_AND_CIVIL_ENGINEERING_CONSTRUCTION_4 = LkOccupationTitle(
        150, 4, 2379, "Other Heavy and Civil Engineering Construction"
    )
    OTHER_HEAVY_AND_CIVIL_ENGINEERING_CONSTRUCTION = LkOccupationTitle(
        151, 4, 237990, "Other Heavy and Civil Engineering Construction"
    )
    FOUNDATION_STRUCTURE_AND_BUILDING_EXTERIOR_CONTRACTORS = LkOccupationTitle(
        152, 4, 2381, "Foundation, Structure, and Building Exterior Contractors"
    )
    POURED_CONCRETE_FOUNDATION_AND_STRUCTURE_CONTRACTORS = LkOccupationTitle(
        153, 4, 238110, "Poured Concrete Foundation and Structure Contractors"
    )
    STRUCTURAL_STEEL_AND_PRECAST_CONCRETE_CONTRACTORS = LkOccupationTitle(
        154, 4, 238120, "Structural Steel and Precast Concrete Contractors"
    )
    FRAMING_CONTRACTORS = LkOccupationTitle(155, 4, 238130, "Framing Contractors")
    MASONRY_CONTRACTORS = LkOccupationTitle(156, 4, 238140, "Masonry Contractors")
    GLASS_AND_GLAZING_CONTRACTORS = LkOccupationTitle(
        157, 4, 238150, "Glass and Glazing Contractors"
    )
    ROOFING_CONTRACTORS = LkOccupationTitle(158, 4, 238160, "Roofing Contractors")
    SIDING_CONTRACTORS = LkOccupationTitle(159, 4, 238170, "Siding Contractors")
    OTHER_FOUNDATION_STRUCTURE_AND_BUILDING_EXTERIOR_CONTRACTORS = LkOccupationTitle(
        160, 4, 238190, "Other Foundation, Structure, and Building Exterior Contractors"
    )
    BUILDING_EQUIPMENT_CONTRACTORS = LkOccupationTitle(
        161, 4, 2382, "Building Equipment Contractors"
    )
    ELECTRICAL_CONTRACTORS_AND_OTHER_WIRING_INSTALLATION_CONTRACTORS = LkOccupationTitle(
        162, 4, 238210, "Electrical Contractors and Other Wiring Installation Contractors"
    )
    PLUMBING_HEATING_AND_AIR_CONDITIONING_CONTRACTORS = LkOccupationTitle(
        163, 4, 238220, "Plumbing, Heating, and Air-Conditioning Contractors"
    )
    OTHER_BUILDING_EQUIPMENT_CONTRACTORS = LkOccupationTitle(
        164, 4, 238290, "Other Building Equipment Contractors"
    )
    BUILDING_FINISHING_CONTRACTORS = LkOccupationTitle(
        165, 4, 2383, "Building Finishing Contractors"
    )
    DRYWALL_AND_INSULATION_CONTRACTORS = LkOccupationTitle(
        166, 4, 238310, "Drywall and Insulation Contractors"
    )
    PAINTING_AND_WALL_COVERING_CONTRACTORS = LkOccupationTitle(
        167, 4, 238320, "Painting and Wall Covering Contractors"
    )
    FLOORING_CONTRACTORS = LkOccupationTitle(168, 4, 238330, "Flooring Contractors")
    TILE_AND_TERRAZZO_CONTRACTORS = LkOccupationTitle(
        169, 4, 238340, "Tile and Terrazzo Contractors"
    )
    FINISH_CARPENTRY_CONTRACTORS = LkOccupationTitle(170, 4, 238350, "Finish Carpentry Contractors")
    OTHER_BUILDING_FINISHING_CONTRACTORS = LkOccupationTitle(
        171, 4, 238390, "Other Building Finishing Contractors"
    )
    OTHER_SPECIALTY_TRADE_CONTRACTORS = LkOccupationTitle(
        172, 4, 2389, "Other Specialty Trade Contractors"
    )
    SITE_PREPARATION_CONTRACTORS = LkOccupationTitle(173, 4, 238910, "Site Preparation Contractors")
    ALL_OTHER_SPECIALTY_TRADE_CONTRACTORS = LkOccupationTitle(
        174, 4, 238990, "All Other Specialty Trade Contractors"
    )
    ANIMAL_FOOD_MANUFACTURING = LkOccupationTitle(175, 5, 3111, "Animal Food Manufacturing")
    DOG_AND_CAT_FOOD_MANUFACTURING = LkOccupationTitle(
        176, 5, 311111, "Dog and Cat Food Manufacturing"
    )
    OTHER_ANIMAL_FOOD_MANUFACTURING = LkOccupationTitle(
        177, 5, 311119, "Other Animal Food Manufacturing"
    )
    GRAIN_AND_OILSEED_MILLING = LkOccupationTitle(178, 5, 3112, "Grain and Oilseed Milling")
    FLOUR_MILLING = LkOccupationTitle(179, 5, 311211, "Flour Milling")
    RICE_MILLING = LkOccupationTitle(180, 5, 311212, "Rice Milling")
    MALT_MANUFACTURING = LkOccupationTitle(181, 5, 311213, "Malt Manufacturing")
    WET_CORN_MILLING = LkOccupationTitle(182, 5, 311221, "Wet Corn Milling")
    SOYBEAN_AND_OTHER_OILSEED_PROCESSING = LkOccupationTitle(
        183, 5, 311224, "Soybean and Other Oilseed Processing"
    )
    FATS_AND_OILS_REFINING_AND_BLENDING = LkOccupationTitle(
        184, 5, 311225, "Fats and Oils Refining and Blending"
    )
    BREAKFAST_CEREAL_MANUFACTURING = LkOccupationTitle(
        185, 5, 311230, "Breakfast Cereal Manufacturing"
    )
    SUGAR_AND_CONFECTIONERY_PRODUCT_MANUFACTURING = LkOccupationTitle(
        186, 5, 3113, "Sugar and Confectionery Product Manufacturing"
    )
    BEET_SUGAR_MANUFACTURING = LkOccupationTitle(187, 5, 311313, "Beet Sugar Manufacturing")
    CANE_SUGAR_MANUFACTURING = LkOccupationTitle(188, 5, 311314, "Cane Sugar Manufacturing")
    NONCHOCOLATE_CONFECTIONERY_MANUFACTURING = LkOccupationTitle(
        189, 5, 311340, "Nonchocolate Confectionery Manufacturing"
    )
    CHOCOLATE_AND_CONFECTIONERY_MANUFACTURING_FROM_CACAO_BEANS = LkOccupationTitle(
        190, 5, 311351, "Chocolate and Confectionery Manufacturing from Cacao Beans"
    )
    CONFECTIONERY_MANUFACTURING_FROM_PURCHASED_CHOCOLATE = LkOccupationTitle(
        191, 5, 311352, "Confectionery Manufacturing from Purchased Chocolate"
    )
    FRUIT_AND_VEGETABLE_PRESERVING_AND_SPECIALTY_FOOD_MANUFACTURING = LkOccupationTitle(
        192, 5, 3114, "Fruit and Vegetable Preserving and Specialty Food Manufacturing"
    )
    FROZEN_FRUIT_JUICE_AND_VEGETABLE_MANUFACTURING = LkOccupationTitle(
        193, 5, 311411, "Frozen Fruit, Juice, and Vegetable Manufacturing"
    )
    FROZEN_SPECIALTY_FOOD_MANUFACTURING = LkOccupationTitle(
        194, 5, 311412, "Frozen Specialty Food Manufacturing"
    )
    FRUIT_AND_VEGETABLE_CANNING = LkOccupationTitle(195, 5, 311421, "Fruit and Vegetable Canning")
    SPECIALTY_CANNING = LkOccupationTitle(196, 5, 311422, "Specialty Canning")
    DRIED_AND_DEHYDRATED_FOOD_MANUFACTURING = LkOccupationTitle(
        197, 5, 311423, "Dried and Dehydrated Food Manufacturing"
    )
    DAIRY_PRODUCT_MANUFACTURING = LkOccupationTitle(198, 5, 3115, "Dairy Product Manufacturing")
    FLUID_MILK_MANUFACTURING = LkOccupationTitle(199, 5, 311511, "Fluid Milk Manufacturing")
    CREAMERY_BUTTER_MANUFACTURING = LkOccupationTitle(
        200, 5, 311512, "Creamery Butter Manufacturing"
    )
    CHEESE_MANUFACTURING = LkOccupationTitle(201, 5, 311513, "Cheese Manufacturing")
    DRY_CONDENSED_AND_EVAPORATED_DAIRY_PRODUCT_MANUFACTURING = LkOccupationTitle(
        202, 5, 311514, "Dry, Condensed, and Evaporated Dairy Product Manufacturing"
    )
    ICE_CREAM_AND_FROZEN_DESSERT_MANUFACTURING = LkOccupationTitle(
        203, 5, 311520, "Ice Cream and Frozen Dessert Manufacturing"
    )
    ANIMAL_SLAUGHTERING_AND_PROCESSING = LkOccupationTitle(
        204, 5, 3116, "Animal Slaughtering and Processing"
    )
    ANIMAL_EXCEPT_POULTRY_SLAUGHTERING = LkOccupationTitle(
        205, 5, 311611, "Animal (except Poultry) Slaughtering"
    )
    MEAT_PROCESSED_FROM_CARCASSES = LkOccupationTitle(
        206, 5, 311612, "Meat Processed from Carcasses"
    )
    RENDERING_AND_MEAT_BYPRODUCT_PROCESSING = LkOccupationTitle(
        207, 5, 311613, "Rendering and Meat Byproduct Processing"
    )
    POULTRY_PROCESSING = LkOccupationTitle(208, 5, 311615, "Poultry Processing")
    SEAFOOD_PRODUCT_PREPARATION_AND_PACKAGING_4 = LkOccupationTitle(
        209, 5, 3117, "Seafood Product Preparation and Packaging"
    )
    SEAFOOD_PRODUCT_PREPARATION_AND_PACKAGING = LkOccupationTitle(
        210, 5, 311710, "Seafood Product Preparation and Packaging"
    )
    BAKERIES_AND_TORTILLA_MANUFACTURING = LkOccupationTitle(
        211, 5, 3118, "Bakeries and Tortilla Manufacturing"
    )
    RETAIL_BAKERIES = LkOccupationTitle(212, 5, 311811, "Retail Bakeries")
    COMMERCIAL_BAKERIES = LkOccupationTitle(213, 5, 311812, "Commercial Bakeries")
    FROZEN_CAKES_PIES_AND_OTHER_PASTRIES_MANUFACTURING = LkOccupationTitle(
        214, 5, 311813, "Frozen Cakes, Pies, and Other Pastries Manufacturing"
    )
    COOKIE_AND_CRACKER_MANUFACTURING = LkOccupationTitle(
        215, 5, 311821, "Cookie and Cracker Manufacturing"
    )
    DRY_PASTA_DOUGH_AND_FLOUR_MIXES_MANUFACTURING_FROM_PURCHASED_FLOUR = LkOccupationTitle(
        216, 5, 311824, "Dry Pasta, Dough, and Flour Mixes Manufacturing from Purchased Flour"
    )
    TORTILLA_MANUFACTURING = LkOccupationTitle(217, 5, 311830, "Tortilla Manufacturing")
    OTHER_FOOD_MANUFACTURING = LkOccupationTitle(218, 5, 3119, "Other Food Manufacturing")
    ROASTED_NUTS_AND_PEANUT_BUTTER_MANUFACTURING = LkOccupationTitle(
        219, 5, 311911, "Roasted Nuts and Peanut Butter Manufacturing"
    )
    OTHER_SNACK_FOOD_MANUFACTURING = LkOccupationTitle(
        220, 5, 311919, "Other Snack Food Manufacturing"
    )
    COFFEE_AND_TEA_MANUFACTURING = LkOccupationTitle(221, 5, 311920, "Coffee and Tea Manufacturing")
    FLAVORING_SYRUP_AND_CONCENTRATE_MANUFACTURING = LkOccupationTitle(
        222, 5, 311930, "Flavoring Syrup and Concentrate Manufacturing"
    )
    MAYONNAISE_DRESSING_AND_OTHER_PREPARED_SAUCE_MANUFACTURING = LkOccupationTitle(
        223, 5, 311941, "Mayonnaise, Dressing, and Other Prepared Sauce Manufacturing"
    )
    SPICE_AND_EXTRACT_MANUFACTURING = LkOccupationTitle(
        224, 5, 311942, "Spice and Extract Manufacturing"
    )
    PERISHABLE_PREPARED_FOOD_MANUFACTURING = LkOccupationTitle(
        225, 5, 311991, "Perishable Prepared Food Manufacturing"
    )
    ALL_OTHER_MISCELLANEOUS_FOOD_MANUFACTURING = LkOccupationTitle(
        226, 5, 311999, "All Other Miscellaneous Food Manufacturing"
    )
    BEVERAGE_MANUFACTURING = LkOccupationTitle(227, 5, 3121, "Beverage Manufacturing")
    SOFT_DRINK_MANUFACTURING = LkOccupationTitle(228, 5, 312111, "Soft Drink Manufacturing")
    BOTTLED_WATER_MANUFACTURING = LkOccupationTitle(229, 5, 312112, "Bottled Water Manufacturing")
    ICE_MANUFACTURING = LkOccupationTitle(230, 5, 312113, "Ice Manufacturing")
    BREWERIES = LkOccupationTitle(231, 5, 312120, "Breweries")
    WINERIES = LkOccupationTitle(232, 5, 312130, "Wineries")
    DISTILLERIES = LkOccupationTitle(233, 5, 312140, "Distilleries")
    TOBACCO_MANUFACTURING_4 = LkOccupationTitle(234, 5, 3122, "Tobacco Manufacturing")
    TOBACCO_MANUFACTURING = LkOccupationTitle(235, 5, 312230, "Tobacco Manufacturing")
    FIBER_YARN_AND_THREAD_MILLS_4 = LkOccupationTitle(236, 5, 3131, "Fiber, Yarn, and Thread Mills")
    FIBER_YARN_AND_THREAD_MILLS = LkOccupationTitle(237, 5, 313110, "Fiber, Yarn, and Thread Mills")
    FABRIC_MILLS = LkOccupationTitle(238, 5, 3132, "Fabric Mills")
    BROADWOVEN_FABRIC_MILLS = LkOccupationTitle(239, 5, 313210, "Broadwoven Fabric Mills")
    NARROW_FABRIC_MILLS_AND_SCHIFFLI_MACHINE_EMBROIDERY = LkOccupationTitle(
        240, 5, 313220, "Narrow Fabric Mills and Schiffli Machine Embroidery"
    )
    NONWOVEN_FABRIC_MILLS = LkOccupationTitle(241, 5, 313230, "Nonwoven Fabric Mills")
    KNIT_FABRIC_MILLS = LkOccupationTitle(242, 5, 313240, "Knit Fabric Mills")
    TEXTILE_AND_FABRIC_FINISHING_AND_FABRIC_COATING_MILLS = LkOccupationTitle(
        243, 5, 3133, "Textile and Fabric Finishing and Fabric Coating Mills"
    )
    TEXTILE_AND_FABRIC_FINISHING_MILLS = LkOccupationTitle(
        244, 5, 313310, "Textile and Fabric Finishing Mills"
    )
    FABRIC_COATING_MILLS = LkOccupationTitle(245, 5, 313320, "Fabric Coating Mills")
    TEXTILE_FURNISHINGS_MILLS = LkOccupationTitle(246, 5, 3141, "Textile Furnishings Mills")
    CARPET_AND_RUG_MILLS = LkOccupationTitle(247, 5, 314110, "Carpet and Rug Mills")
    CURTAIN_AND_LINEN_MILLS = LkOccupationTitle(248, 5, 314120, "Curtain and Linen Mills")
    OTHER_TEXTILE_PRODUCT_MILLS = LkOccupationTitle(249, 5, 3149, "Other Textile Product Mills")
    TEXTILE_BAG_AND_CANVAS_MILLS = LkOccupationTitle(250, 5, 314910, "Textile Bag and Canvas Mills")
    ROPE_CORDAGE_TWINE_TIRE_CORD_AND_TIRE_FABRIC_MILLS = LkOccupationTitle(
        251, 5, 314994, "Rope, Cordage, Twine, Tire Cord, and Tire Fabric Mills"
    )
    ALL_OTHER_MISCELLANEOUS_TEXTILE_PRODUCT_MILLS = LkOccupationTitle(
        252, 5, 314999, "All Other Miscellaneous Textile Product Mills"
    )
    APPAREL_KNITTING_MILLS = LkOccupationTitle(253, 5, 3151, "Apparel Knitting Mills")
    HOSIERY_AND_SOCK_MILLS = LkOccupationTitle(254, 5, 315110, "Hosiery and Sock Mills")
    OTHER_APPAREL_KNITTING_MILLS = LkOccupationTitle(255, 5, 315190, "Other Apparel Knitting Mills")
    CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(
        256, 5, 3152, "Cut and Sew Apparel Manufacturing"
    )
    CUT_AND_SEW_APPAREL_CONTRACTORS = LkOccupationTitle(
        257, 5, 315210, "Cut and Sew Apparel Contractors"
    )
    MEN_S_AND_BOYS_CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(
        258, 5, 315220, "Men's and Boys' Cut and Sew Apparel Manufacturing"
    )
    WOMEN_S_GIRLS_AND_INFANTS_CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(
        259, 5, 315240, "Women's, Girls', and Infants' Cut and Sew Apparel Manufacturing"
    )
    OTHER_CUT_AND_SEW_APPAREL_MANUFACTURING = LkOccupationTitle(
        260, 5, 315280, "Other Cut and Sew Apparel Manufacturing"
    )
    APPAREL_ACCESSORIES_AND_OTHER_APPAREL_MANUFACTURING_4 = LkOccupationTitle(
        261, 5, 3159, "Apparel Accessories and Other Apparel Manufacturing"
    )
    APPAREL_ACCESSORIES_AND_OTHER_APPAREL_MANUFACTURING = LkOccupationTitle(
        262, 5, 315990, "Apparel Accessories and Other Apparel Manufacturing"
    )
    LEATHER_AND_HIDE_TANNING_AND_FINISHING_4 = LkOccupationTitle(
        263, 5, 3161, "Leather and Hide Tanning and Finishing"
    )
    LEATHER_AND_HIDE_TANNING_AND_FINISHING = LkOccupationTitle(
        264, 5, 316110, "Leather and Hide Tanning and Finishing"
    )
    FOOTWEAR_MANUFACTURING_4 = LkOccupationTitle(265, 5, 3162, "Footwear Manufacturing")
    FOOTWEAR_MANUFACTURING = LkOccupationTitle(266, 5, 316210, "Footwear Manufacturing")
    OTHER_LEATHER_AND_ALLIED_PRODUCT_MANUFACTURING = LkOccupationTitle(
        267, 5, 3169, "Other Leather and Allied Product Manufacturing"
    )
    WOMEN_S_HANDBAG_AND_PURSE_MANUFACTURING = LkOccupationTitle(
        268, 5, 316992, "Women's Handbag and Purse Manufacturing"
    )
    ALL_OTHER_LEATHER_GOOD_AND_ALLIED_PRODUCT_MANUFACTURING = LkOccupationTitle(
        269, 5, 316998, "All Other Leather Good and Allied Product Manufacturing"
    )
    SAWMILLS_AND_WOOD_PRESERVATION = LkOccupationTitle(
        270, 5, 3211, "Sawmills and Wood Preservation"
    )
    SAWMILLS = LkOccupationTitle(271, 5, 321113, "Sawmills")
    WOOD_PRESERVATION = LkOccupationTitle(272, 5, 321114, "Wood Preservation")
    VENEER_PLYWOOD_AND_ENGINEERED_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(
        273, 5, 3212, "Veneer, Plywood, and Engineered Wood Product Manufacturing"
    )
    HARDWOOD_VENEER_AND_PLYWOOD_MANUFACTURING = LkOccupationTitle(
        274, 5, 321211, "Hardwood Veneer and Plywood Manufacturing"
    )
    SOFTWOOD_VENEER_AND_PLYWOOD_MANUFACTURING = LkOccupationTitle(
        275, 5, 321212, "Softwood Veneer and Plywood Manufacturing"
    )
    ENGINEERED_WOOD_MEMBER_EXCEPT_TRUSS_MANUFACTURING = LkOccupationTitle(
        276, 5, 321213, "Engineered Wood Member (except Truss) Manufacturing"
    )
    TRUSS_MANUFACTURING = LkOccupationTitle(277, 5, 321214, "Truss Manufacturing")
    RECONSTITUTED_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(
        278, 5, 321219, "Reconstituted Wood Product Manufacturing"
    )
    OTHER_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(
        279, 5, 3219, "Other Wood Product Manufacturing"
    )
    WOOD_WINDOW_AND_DOOR_MANUFACTURING = LkOccupationTitle(
        280, 5, 321911, "Wood Window and Door Manufacturing"
    )
    CUT_STOCK_RESAWING_LUMBER_AND_PLANING = LkOccupationTitle(
        281, 5, 321912, "Cut Stock, Resawing Lumber, and Planing"
    )
    OTHER_MILLWORK_INCLUDING_FLOORING = LkOccupationTitle(
        282, 5, 321918, "Other Millwork (including Flooring)"
    )
    WOOD_CONTAINER_AND_PALLET_MANUFACTURING = LkOccupationTitle(
        283, 5, 321920, "Wood Container and Pallet Manufacturing"
    )
    MANUFACTURED_HOME_MOBILE_HOME_MANUFACTURING = LkOccupationTitle(
        284, 5, 321991, "Manufactured Home (Mobile Home) Manufacturing"
    )
    PREFABRICATED_WOOD_BUILDING_MANUFACTURING = LkOccupationTitle(
        285, 5, 321992, "Prefabricated Wood Building Manufacturing"
    )
    ALL_OTHER_MISCELLANEOUS_WOOD_PRODUCT_MANUFACTURING = LkOccupationTitle(
        286, 5, 321999, "All Other Miscellaneous Wood Product Manufacturing"
    )
    PULP_PAPER_AND_PAPERBOARD_MILLS = LkOccupationTitle(
        287, 5, 3221, "Pulp, Paper, and Paperboard Mills"
    )
    PULP_MILLS = LkOccupationTitle(288, 5, 322110, "Pulp Mills")
    PAPER_EXCEPT_NEWSPRINT_MILLS = LkOccupationTitle(
        289, 5, 322121, "Paper (except Newsprint) Mills"
    )
    NEWSPRINT_MILLS = LkOccupationTitle(290, 5, 322122, "Newsprint Mills")
    PAPERBOARD_MILLS = LkOccupationTitle(291, 5, 322130, "Paperboard Mills")
    CONVERTED_PAPER_PRODUCT_MANUFACTURING = LkOccupationTitle(
        292, 5, 3222, "Converted Paper Product Manufacturing"
    )
    CORRUGATED_AND_SOLID_FIBER_BOX_MANUFACTURING = LkOccupationTitle(
        293, 5, 322211, "Corrugated and Solid Fiber Box Manufacturing"
    )
    FOLDING_PAPERBOARD_BOX_MANUFACTURING = LkOccupationTitle(
        294, 5, 322212, "Folding Paperboard Box Manufacturing"
    )
    OTHER_PAPERBOARD_CONTAINER_MANUFACTURING = LkOccupationTitle(
        295, 5, 322219, "Other Paperboard Container Manufacturing"
    )
    PAPER_BAG_AND_COATED_AND_TREATED_PAPER_MANUFACTURING = LkOccupationTitle(
        296, 5, 322220, "Paper Bag and Coated and Treated Paper Manufacturing"
    )
    STATIONERY_PRODUCT_MANUFACTURING = LkOccupationTitle(
        297, 5, 322230, "Stationery Product Manufacturing"
    )
    SANITARY_PAPER_PRODUCT_MANUFACTURING = LkOccupationTitle(
        298, 5, 322291, "Sanitary Paper Product Manufacturing"
    )
    ALL_OTHER_CONVERTED_PAPER_PRODUCT_MANUFACTURING = LkOccupationTitle(
        299, 5, 322299, "All Other Converted Paper Product Manufacturing"
    )
    PRINTING_AND_RELATED_SUPPORT_ACTIVITIES = LkOccupationTitle(
        300, 5, 3231, "Printing and Related Support Activities"
    )
    COMMERCIAL_PRINTING_EXCEPT_SCREEN_AND_BOOKS = LkOccupationTitle(
        301, 5, 323111, "Commercial Printing (except Screen and Books)"
    )
    COMMERCIAL_SCREEN_PRINTING = LkOccupationTitle(302, 5, 323113, "Commercial Screen Printing")
    BOOKS_PRINTING = LkOccupationTitle(303, 5, 323117, "Books Printing")
    SUPPORT_ACTIVITIES_FOR_PRINTING = LkOccupationTitle(
        304, 5, 323120, "Support Activities for Printing"
    )
    PETROLEUM_AND_COAL_PRODUCTS_MANUFACTURING = LkOccupationTitle(
        305, 5, 3241, "Petroleum and Coal Products Manufacturing"
    )
    PETROLEUM_REFINERIES = LkOccupationTitle(306, 5, 324110, "Petroleum Refineries")
    ASPHALT_PAVING_MIXTURE_AND_BLOCK_MANUFACTURING = LkOccupationTitle(
        307, 5, 324121, "Asphalt Paving Mixture and Block Manufacturing"
    )
    ASPHALT_SHINGLE_AND_COATING_MATERIALS_MANUFACTURING = LkOccupationTitle(
        308, 5, 324122, "Asphalt Shingle and Coating Materials Manufacturing"
    )
    PETROLEUM_LUBRICATING_OIL_AND_GREASE_MANUFACTURING = LkOccupationTitle(
        309, 5, 324191, "Petroleum Lubricating Oil and Grease Manufacturing"
    )
    ALL_OTHER_PETROLEUM_AND_COAL_PRODUCTS_MANUFACTURING = LkOccupationTitle(
        310, 5, 324199, "All Other Petroleum and Coal Products Manufacturing"
    )
    BASIC_CHEMICAL_MANUFACTURING = LkOccupationTitle(311, 5, 3251, "Basic Chemical Manufacturing")
    PETROCHEMICAL_MANUFACTURING = LkOccupationTitle(312, 5, 325110, "Petrochemical Manufacturing")
    INDUSTRIAL_GAS_MANUFACTURING = LkOccupationTitle(313, 5, 325120, "Industrial Gas Manufacturing")
    SYNTHETIC_DYE_AND_PIGMENT_MANUFACTURING = LkOccupationTitle(
        314, 5, 325130, "Synthetic Dye and Pigment Manufacturing"
    )
    OTHER_BASIC_INORGANIC_CHEMICAL_MANUFACTURING = LkOccupationTitle(
        315, 5, 325180, "Other Basic Inorganic Chemical Manufacturing"
    )
    ETHYL_ALCOHOL_MANUFACTURING = LkOccupationTitle(316, 5, 325193, "Ethyl Alcohol Manufacturing")
    CYCLIC_CRUDE_INTERMEDIATE_AND_GUM_AND_WOOD_CHEMICAL_MANUFACTURING = LkOccupationTitle(
        317, 5, 325194, "Cyclic Crude, Intermediate, and Gum and Wood Chemical Manufacturing"
    )
    ALL_OTHER_BASIC_ORGANIC_CHEMICAL_MANUFACTURING = LkOccupationTitle(
        318, 5, 325199, "All Other Basic Organic Chemical Manufacturing"
    )
    RESIN_SYNTHETIC_RUBBER_AND_ARTIFICIAL_AND_SYNTHETIC_FIBERS_AND_FILAMENTS_MANUFACTURING = LkOccupationTitle(
        319,
        5,
        3252,
        "Resin, Synthetic Rubber, and Artificial and Synthetic Fibers and Filaments Manufacturing",
    )
    PLASTICS_MATERIAL_AND_RESIN_MANUFACTURING = LkOccupationTitle(
        320, 5, 325211, "Plastics Material and Resin Manufacturing"
    )
    SYNTHETIC_RUBBER_MANUFACTURING = LkOccupationTitle(
        321, 5, 325212, "Synthetic Rubber Manufacturing"
    )
    ARTIFICIAL_AND_SYNTHETIC_FIBERS_AND_FILAMENTS_MANUFACTURING = LkOccupationTitle(
        322, 5, 325220, "Artificial and Synthetic Fibers and Filaments Manufacturing"
    )
    PESTICIDE_FERTILIZER_AND_OTHER_AGRICULTURAL_CHEMICAL_MANUFACTURING = LkOccupationTitle(
        323, 5, 3253, "Pesticide, Fertilizer, and Other Agricultural Chemical Manufacturing"
    )
    NITROGENOUS_FERTILIZER_MANUFACTURING = LkOccupationTitle(
        324, 5, 325311, "Nitrogenous Fertilizer Manufacturing"
    )
    PHOSPHATIC_FERTILIZER_MANUFACTURING = LkOccupationTitle(
        325, 5, 325312, "Phosphatic Fertilizer Manufacturing"
    )
    FERTILIZER_MIXING_ONLY_MANUFACTURING = LkOccupationTitle(
        326, 5, 325314, "Fertilizer (Mixing Only) Manufacturing"
    )
    PESTICIDE_AND_OTHER_AGRICULTURAL_CHEMICAL_MANUFACTURING = LkOccupationTitle(
        327, 5, 325320, "Pesticide and Other Agricultural Chemical Manufacturing"
    )
    PHARMACEUTICAL_AND_MEDICINE_MANUFACTURING = LkOccupationTitle(
        328, 5, 3254, "Pharmaceutical and Medicine Manufacturing"
    )
    MEDICINAL_AND_BOTANICAL_MANUFACTURING = LkOccupationTitle(
        329, 5, 325411, "Medicinal and Botanical Manufacturing"
    )
    PHARMACEUTICAL_PREPARATION_MANUFACTURING = LkOccupationTitle(
        330, 5, 325412, "Pharmaceutical Preparation Manufacturing"
    )
    IN_VITRO_DIAGNOSTIC_SUBSTANCE_MANUFACTURING = LkOccupationTitle(
        331, 5, 325413, "In-Vitro Diagnostic Substance Manufacturing"
    )
    BIOLOGICAL_PRODUCT_EXCEPT_DIAGNOSTIC_MANUFACTURING = LkOccupationTitle(
        332, 5, 325414, "Biological Product (except Diagnostic) Manufacturing"
    )
    PAINT_COATING_AND_ADHESIVE_MANUFACTURING = LkOccupationTitle(
        333, 5, 3255, "Paint, Coating, and Adhesive Manufacturing"
    )
    PAINT_AND_COATING_MANUFACTURING = LkOccupationTitle(
        334, 5, 325510, "Paint and Coating Manufacturing"
    )
    ADHESIVE_MANUFACTURING = LkOccupationTitle(335, 5, 325520, "Adhesive Manufacturing")
    SOAP_CLEANING_COMPOUND_AND_TOILET_PREPARATION_MANUFACTURING = LkOccupationTitle(
        336, 5, 3256, "Soap, Cleaning Compound, and Toilet Preparation Manufacturing"
    )
    SOAP_AND_OTHER_DETERGENT_MANUFACTURING = LkOccupationTitle(
        337, 5, 325611, "Soap and Other Detergent Manufacturing"
    )
    POLISH_AND_OTHER_SANITATION_GOOD_MANUFACTURING = LkOccupationTitle(
        338, 5, 325612, "Polish and Other Sanitation Good Manufacturing"
    )
    SURFACE_ACTIVE_AGENT_MANUFACTURING = LkOccupationTitle(
        339, 5, 325613, "Surface Active Agent Manufacturing"
    )
    TOILET_PREPARATION_MANUFACTURING = LkOccupationTitle(
        340, 5, 325620, "Toilet Preparation Manufacturing"
    )
    OTHER_CHEMICAL_PRODUCT_AND_PREPARATION_MANUFACTURING = LkOccupationTitle(
        341, 5, 3259, "Other Chemical Product and Preparation Manufacturing"
    )
    PRINTING_INK_MANUFACTURING = LkOccupationTitle(342, 5, 325910, "Printing Ink Manufacturing")
    EXPLOSIVES_MANUFACTURING = LkOccupationTitle(343, 5, 325920, "Explosives Manufacturing")
    CUSTOM_COMPOUNDING_OF_PURCHASED_RESINS = LkOccupationTitle(
        344, 5, 325991, "Custom Compounding of Purchased Resins"
    )
    PHOTOGRAPHIC_FILM_PAPER_PLATE_AND_CHEMICAL_MANUFACTURING = LkOccupationTitle(
        345, 5, 325992, "Photographic Film, Paper, Plate, and Chemical Manufacturing"
    )
    ALL_OTHER_MISCELLANEOUS_CHEMICAL_PRODUCT_AND_PREPARATION_MANUFACTURING = LkOccupationTitle(
        346, 5, 325998, "All Other Miscellaneous Chemical Product and Preparation Manufacturing"
    )
    PLASTICS_PRODUCT_MANUFACTURING = LkOccupationTitle(
        347, 5, 3261, "Plastics Product Manufacturing"
    )
    PLASTICS_BAG_AND_POUCH_MANUFACTURING = LkOccupationTitle(
        348, 5, 326111, "Plastics Bag and Pouch Manufacturing"
    )
    PLASTICS_PACKAGING_FILM_AND_SHEET_INCLUDING_LAMINATED_MANUFACTURING = LkOccupationTitle(
        349, 5, 326112, "Plastics Packaging Film and Sheet (including Laminated) Manufacturing"
    )
    UNLAMINATED_PLASTICS_FILM_AND_SHEET_EXCEPT_PACKAGING_MANUFACTURING = LkOccupationTitle(
        350, 5, 326113, "Unlaminated Plastics Film and Sheet (except Packaging) Manufacturing"
    )
    UNLAMINATED_PLASTICS_PROFILE_SHAPE_MANUFACTURING = LkOccupationTitle(
        351, 5, 326121, "Unlaminated Plastics Profile Shape Manufacturing"
    )
    PLASTICS_PIPE_AND_PIPE_FITTING_MANUFACTURING = LkOccupationTitle(
        352, 5, 326122, "Plastics Pipe and Pipe Fitting Manufacturing"
    )
    LAMINATED_PLASTICS_PLATE_SHEET_EXCEPT_PACKAGING_AND_SHAPE_MANUFACTURING = LkOccupationTitle(
        353,
        5,
        326130,
        "Laminated Plastics Plate, Sheet (except Packaging), and Shape Manufacturing",
    )
    POLYSTYRENE_FOAM_PRODUCT_MANUFACTURING = LkOccupationTitle(
        354, 5, 326140, "Polystyrene Foam Product Manufacturing"
    )
    URETHANE_AND_OTHER_FOAM_PRODUCT_EXCEPT_POLYSTYRENE_MANUFACTURING = LkOccupationTitle(
        355, 5, 326150, "Urethane and Other Foam Product (except Polystyrene) Manufacturing"
    )
    PLASTICS_BOTTLE_MANUFACTURING = LkOccupationTitle(
        356, 5, 326160, "Plastics Bottle Manufacturing"
    )
    PLASTICS_PLUMBING_FIXTURE_MANUFACTURING = LkOccupationTitle(
        357, 5, 326191, "Plastics Plumbing Fixture Manufacturing"
    )
    ALL_OTHER_PLASTICS_PRODUCT_MANUFACTURING = LkOccupationTitle(
        358, 5, 326199, "All Other Plastics Product Manufacturing"
    )
    RUBBER_PRODUCT_MANUFACTURING = LkOccupationTitle(359, 5, 3262, "Rubber Product Manufacturing")
    TIRE_MANUFACTURING_EXCEPT_RETREADING = LkOccupationTitle(
        360, 5, 326211, "Tire Manufacturing (except Retreading)"
    )
    TIRE_RETREADING = LkOccupationTitle(361, 5, 326212, "Tire Retreading")
    RUBBER_AND_PLASTICS_HOSES_AND_BELTING_MANUFACTURING = LkOccupationTitle(
        362, 5, 326220, "Rubber and Plastics Hoses and Belting Manufacturing"
    )
    RUBBER_PRODUCT_MANUFACTURING_FOR_MECHANICAL_USE = LkOccupationTitle(
        363, 5, 326291, "Rubber Product Manufacturing for Mechanical Use"
    )
    ALL_OTHER_RUBBER_PRODUCT_MANUFACTURING = LkOccupationTitle(
        364, 5, 326299, "All Other Rubber Product Manufacturing"
    )
    CLAY_PRODUCT_AND_REFRACTORY_MANUFACTURING = LkOccupationTitle(
        365, 5, 3271, "Clay Product and Refractory Manufacturing"
    )
    POTTERY_CERAMICS_AND_PLUMBING_FIXTURE_MANUFACTURING = LkOccupationTitle(
        366, 5, 327110, "Pottery, Ceramics, and Plumbing Fixture Manufacturing"
    )
    CLAY_BUILDING_MATERIAL_AND_REFRACTORIES_MANUFACTURING = LkOccupationTitle(
        367, 5, 327120, "Clay Building Material and Refractories Manufacturing"
    )
    GLASS_AND_GLASS_PRODUCT_MANUFACTURING = LkOccupationTitle(
        368, 5, 3272, "Glass and Glass Product Manufacturing"
    )
    FLAT_GLASS_MANUFACTURING = LkOccupationTitle(369, 5, 327211, "Flat Glass Manufacturing")
    OTHER_PRESSED_AND_BLOWN_GLASS_AND_GLASSWARE_MANUFACTURING = LkOccupationTitle(
        370, 5, 327212, "Other Pressed and Blown Glass and Glassware Manufacturing"
    )
    GLASS_CONTAINER_MANUFACTURING = LkOccupationTitle(
        371, 5, 327213, "Glass Container Manufacturing"
    )
    GLASS_PRODUCT_MANUFACTURING_MADE_OF_PURCHASED_GLASS = LkOccupationTitle(
        372, 5, 327215, "Glass Product Manufacturing Made of Purchased Glass"
    )
    CEMENT_AND_CONCRETE_PRODUCT_MANUFACTURING = LkOccupationTitle(
        373, 5, 3273, "Cement and Concrete Product Manufacturing"
    )
    CEMENT_MANUFACTURING = LkOccupationTitle(374, 5, 327310, "Cement Manufacturing")
    READY_MIX_CONCRETE_MANUFACTURING = LkOccupationTitle(
        375, 5, 327320, "Ready-Mix Concrete Manufacturing"
    )
    CONCRETE_BLOCK_AND_BRICK_MANUFACTURING = LkOccupationTitle(
        376, 5, 327331, "Concrete Block and Brick Manufacturing"
    )
    CONCRETE_PIPE_MANUFACTURING = LkOccupationTitle(377, 5, 327332, "Concrete Pipe Manufacturing")
    OTHER_CONCRETE_PRODUCT_MANUFACTURING = LkOccupationTitle(
        378, 5, 327390, "Other Concrete Product Manufacturing"
    )
    LIME_AND_GYPSUM_PRODUCT_MANUFACTURING = LkOccupationTitle(
        379, 5, 3274, "Lime and Gypsum Product Manufacturing"
    )
    LIME_MANUFACTURING = LkOccupationTitle(380, 5, 327410, "Lime Manufacturing")
    GYPSUM_PRODUCT_MANUFACTURING = LkOccupationTitle(381, 5, 327420, "Gypsum Product Manufacturing")
    OTHER_NONMETALLIC_MINERAL_PRODUCT_MANUFACTURING = LkOccupationTitle(
        382, 5, 3279, "Other Nonmetallic Mineral Product Manufacturing"
    )
    ABRASIVE_PRODUCT_MANUFACTURING = LkOccupationTitle(
        383, 5, 327910, "Abrasive Product Manufacturing"
    )
    CUT_STONE_AND_STONE_PRODUCT_MANUFACTURING = LkOccupationTitle(
        384, 5, 327991, "Cut Stone and Stone Product Manufacturing"
    )
    GROUND_OR_TREATED_MINERAL_AND_EARTH_MANUFACTURING = LkOccupationTitle(
        385, 5, 327992, "Ground or Treated Mineral and Earth Manufacturing"
    )
    MINERAL_WOOL_MANUFACTURING = LkOccupationTitle(386, 5, 327993, "Mineral Wool Manufacturing")
    ALL_OTHER_MISCELLANEOUS_NONMETALLIC_MINERAL_PRODUCT_MANUFACTURING = LkOccupationTitle(
        387, 5, 327999, "All Other Miscellaneous Nonmetallic Mineral Product Manufacturing"
    )
    IRON_AND_STEEL_MILLS_AND_FERROALLOY_MANUFACTURING_4 = LkOccupationTitle(
        388, 5, 3311, "Iron and Steel Mills and Ferroalloy Manufacturing"
    )
    IRON_AND_STEEL_MILLS_AND_FERROALLOY_MANUFACTURING = LkOccupationTitle(
        389, 5, 331110, "Iron and Steel Mills and Ferroalloy Manufacturing"
    )
    STEEL_PRODUCT_MANUFACTURING_FROM_PURCHASED_STEEL = LkOccupationTitle(
        390, 5, 3312, "Steel Product Manufacturing from Purchased Steel"
    )
    IRON_AND_STEEL_PIPE_AND_TUBE_MANUFACTURING_FROM_PURCHASED_STEEL = LkOccupationTitle(
        391, 5, 331210, "Iron and Steel Pipe and Tube Manufacturing from Purchased Steel"
    )
    ROLLED_STEEL_SHAPE_MANUFACTURING = LkOccupationTitle(
        392, 5, 331221, "Rolled Steel Shape Manufacturing"
    )
    STEEL_WIRE_DRAWING = LkOccupationTitle(393, 5, 331222, "Steel Wire Drawing")
    ALUMINA_AND_ALUMINUM_PRODUCTION_AND_PROCESSING = LkOccupationTitle(
        394, 5, 3313, "Alumina and Aluminum Production and Processing"
    )
    ALUMINA_REFINING_AND_PRIMARY_ALUMINUM_PRODUCTION = LkOccupationTitle(
        395, 5, 331313, "Alumina Refining and Primary Aluminum Production"
    )
    SECONDARY_SMELTING_AND_ALLOYING_OF_ALUMINUM = LkOccupationTitle(
        396, 5, 331314, "Secondary Smelting and Alloying of Aluminum"
    )
    ALUMINUM_SHEET_PLATE_AND_FOIL_MANUFACTURING = LkOccupationTitle(
        397, 5, 331315, "Aluminum Sheet, Plate, and Foil Manufacturing"
    )
    OTHER_ALUMINUM_ROLLING_DRAWING_AND_EXTRUDING = LkOccupationTitle(
        398, 5, 331318, "Other Aluminum Rolling, Drawing, and Extruding"
    )
    NONFERROUS_METAL_EXCEPT_ALUMINUM_PRODUCTION_AND_PROCESSING = LkOccupationTitle(
        399, 5, 3314, "Nonferrous Metal (except Aluminum) Production and Processing"
    )
    NONFERROUS_METAL_EXCEPT_ALUMINUM_SMELTING_AND_REFINING = LkOccupationTitle(
        400, 5, 331410, "Nonferrous Metal (except Aluminum) Smelting and Refining"
    )
    COPPER_ROLLING_DRAWING_EXTRUDING_AND_ALLOYING = LkOccupationTitle(
        401, 5, 331420, "Copper Rolling, Drawing, Extruding, and Alloying"
    )
    NONFERROUS_METAL_EXCEPT_COPPER_AND_ALUMINUM_ROLLING_DRAWING_AND_EXTRUDING = LkOccupationTitle(
        402,
        5,
        331491,
        "Nonferrous Metal (except Copper and Aluminum) Rolling, Drawing, and Extruding",
    )
    SECONDARY_SMELTING_REFINING_AND_ALLOYING_OF_NONFERROUS_METAL_EXCEPT_COPPER_AND_ALUMINUM = LkOccupationTitle(
        403,
        5,
        331492,
        "Secondary Smelting, Refining, and Alloying of Nonferrous Metal (except Copper and Aluminum)",
    )
    FOUNDRIES = LkOccupationTitle(404, 5, 3315, "Foundries")
    IRON_FOUNDRIES = LkOccupationTitle(405, 5, 331511, "Iron Foundries")
    STEEL_INVESTMENT_FOUNDRIES = LkOccupationTitle(406, 5, 331512, "Steel Investment Foundries")
    STEEL_FOUNDRIES_EXCEPT_INVESTMENT = LkOccupationTitle(
        407, 5, 331513, "Steel Foundries (except Investment)"
    )
    NONFERROUS_METAL_DIE_CASTING_FOUNDRIES = LkOccupationTitle(
        408, 5, 331523, "Nonferrous Metal Die-Casting Foundries"
    )
    ALUMINUM_FOUNDRIES_EXCEPT_DIE_CASTING = LkOccupationTitle(
        409, 5, 331524, "Aluminum Foundries (except Die-Casting)"
    )
    OTHER_NONFERROUS_METAL_FOUNDRIES_EXCEPT_DIE_CASTING = LkOccupationTitle(
        410, 5, 331529, "Other Nonferrous Metal Foundries (except Die-Casting)"
    )
    FORGING_AND_STAMPING = LkOccupationTitle(411, 5, 3321, "Forging and Stamping")
    IRON_AND_STEEL_FORGING = LkOccupationTitle(412, 5, 332111, "Iron and Steel Forging")
    NONFERROUS_FORGING = LkOccupationTitle(413, 5, 332112, "Nonferrous Forging")
    CUSTOM_ROLL_FORMING = LkOccupationTitle(414, 5, 332114, "Custom Roll Forming")
    POWDER_METALLURGY_PART_MANUFACTURING = LkOccupationTitle(
        415, 5, 332117, "Powder Metallurgy Part Manufacturing"
    )
    METAL_CROWN_CLOSURE_AND_OTHER_METAL_STAMPING_EXCEPT_AUTOMOTIVE = LkOccupationTitle(
        416, 5, 332119, "Metal Crown, Closure, and Other Metal Stamping (except Automotive)"
    )
    CUTLERY_AND_HANDTOOL_MANUFACTURING = LkOccupationTitle(
        417, 5, 3322, "Cutlery and Handtool Manufacturing"
    )
    METAL_KITCHEN_COOKWARE_UTENSIL_CUTLERY_AND_FLATWARE_EXCEPT_PRECIOUS_MANUFACTURING_273 = LkOccupationTitle(
        418,
        5,
        332215,
        "Metal Kitchen Cookware, Utensil, Cutlery, and Flatware (except Precious) Manufacturing273",
    )
    SAW_BLADE_AND_HANDTOOL_MANUFACTURING = LkOccupationTitle(
        419, 5, 332216, "Saw Blade and Handtool Manufacturing"
    )
    ARCHITECTURAL_AND_STRUCTURAL_METALS_MANUFACTURING = LkOccupationTitle(
        420, 5, 3323, "Architectural and Structural Metals Manufacturing"
    )
    PREFABRICATED_METAL_BUILDING_AND_COMPONENT_MANUFACTURING = LkOccupationTitle(
        421, 5, 332311, "Prefabricated Metal Building and Component Manufacturing"
    )
    FABRICATED_STRUCTURAL_METAL_MANUFACTURING = LkOccupationTitle(
        422, 5, 332312, "Fabricated Structural Metal Manufacturing"
    )
    PLATE_WORK_MANUFACTURING = LkOccupationTitle(423, 5, 332313, "Plate Work Manufacturing")
    METAL_WINDOW_AND_DOOR_MANUFACTURING = LkOccupationTitle(
        424, 5, 332321, "Metal Window and Door Manufacturing"
    )
    SHEET_METAL_WORK_MANUFACTURING = LkOccupationTitle(
        425, 5, 332322, "Sheet Metal Work Manufacturing"
    )
    ORNAMENTAL_AND_ARCHITECTURAL_METAL_WORK_MANUFACTURING = LkOccupationTitle(
        426, 5, 332323, "Ornamental and Architectural Metal Work Manufacturing"
    )
    BOILER_TANK_AND_SHIPPING_CONTAINER_MANUFACTURING = LkOccupationTitle(
        427, 5, 3324, "Boiler, Tank, and Shipping Container Manufacturing"
    )
    POWER_BOILER_AND_HEAT_EXCHANGER_MANUFACTURING = LkOccupationTitle(
        428, 5, 332410, "Power Boiler and Heat Exchanger Manufacturing"
    )
    METAL_TANK_HEAVY_GAUGE_MANUFACTURING = LkOccupationTitle(
        429, 5, 332420, "Metal Tank (Heavy Gauge) Manufacturing"
    )
    METAL_CAN_MANUFACTURING = LkOccupationTitle(430, 5, 332431, "Metal Can Manufacturing")
    OTHER_METAL_CONTAINER_MANUFACTURING = LkOccupationTitle(
        431, 5, 332439, "Other Metal Container Manufacturing"
    )
    HARDWARE_MANUFACTURING_4 = LkOccupationTitle(432, 5, 3325, "Hardware Manufacturing")
    HARDWARE_MANUFACTURING = LkOccupationTitle(433, 5, 332510, "Hardware Manufacturing")
    SPRING_AND_WIRE_PRODUCT_MANUFACTURING = LkOccupationTitle(
        434, 5, 3326, "Spring and Wire Product Manufacturing"
    )
    SPRING_MANUFACTURING = LkOccupationTitle(435, 5, 332613, "Spring Manufacturing")
    OTHER_FABRICATED_WIRE_PRODUCT_MANUFACTURING = LkOccupationTitle(
        436, 5, 332618, "Other Fabricated Wire Product Manufacturing"
    )
    MACHINE_SHOPS_TURNED_PRODUCT_AND_SCREW_NUT_AND_BOLT_MANUFACTURING = LkOccupationTitle(
        437, 5, 3327, "Machine Shops; Turned Product; and Screw, Nut, and Bolt Manufacturing"
    )
    MACHINE_SHOPS = LkOccupationTitle(438, 5, 332710, "Machine Shops")
    PRECISION_TURNED_PRODUCT_MANUFACTURING = LkOccupationTitle(
        439, 5, 332721, "Precision Turned Product Manufacturing"
    )
    BOLT_NUT_SCREW_RIVET_AND_WASHER_MANUFACTURING = LkOccupationTitle(
        440, 5, 332722, "Bolt, Nut, Screw, Rivet, and Washer Manufacturing"
    )
    COATING_ENGRAVING_HEAT_TREATING_AND_ALLIED_ACTIVITIES = LkOccupationTitle(
        441, 5, 3328, "Coating, Engraving, Heat Treating, and Allied Activities"
    )
    METAL_HEAT_TREATING = LkOccupationTitle(442, 5, 332811, "Metal Heat Treating")
    METAL_COATING_ENGRAVING_EXCEPT_JEWELRY_AND_SILVERWARE_AND_ALLIED_SERVICES_TO_MANUFACTURERS = LkOccupationTitle(
        443,
        5,
        332812,
        "Metal Coating, Engraving (except Jewelry and Silverware), and Allied Services to Manufacturers",
    )
    ELECTROPLATING_PLATING_POLISHING_ANODIZING_AND_COLORING = LkOccupationTitle(
        444, 5, 332813, "Electroplating, Plating, Polishing, Anodizing, and Coloring"
    )
    OTHER_FABRICATED_METAL_PRODUCT_MANUFACTURING = LkOccupationTitle(
        445, 5, 3329, "Other Fabricated Metal Product Manufacturing"
    )
    INDUSTRIAL_VALVE_MANUFACTURING = LkOccupationTitle(
        446, 5, 332911, "Industrial Valve Manufacturing"
    )
    FLUID_POWER_VALVE_AND_HOSE_FITTING_MANUFACTURING = LkOccupationTitle(
        447, 5, 332912, "Fluid Power Valve and Hose Fitting Manufacturing"
    )
    PLUMBING_FIXTURE_FITTING_AND_TRIM_MANUFACTURING = LkOccupationTitle(
        448, 5, 332913, "Plumbing Fixture Fitting and Trim Manufacturing"
    )
    OTHER_METAL_VALVE_AND_PIPE_FITTING_MANUFACTURING = LkOccupationTitle(
        449, 5, 332919, "Other Metal Valve and Pipe Fitting Manufacturing"
    )
    BALL_AND_ROLLER_BEARING_MANUFACTURING = LkOccupationTitle(
        450, 5, 332991, "Ball and Roller Bearing Manufacturing"
    )
    SMALL_ARMS_AMMUNITION_MANUFACTURING = LkOccupationTitle(
        451, 5, 332992, "Small Arms Ammunition Manufacturing"
    )
    AMMUNITION_EXCEPT_SMALL_ARMS_MANUFACTURING = LkOccupationTitle(
        452, 5, 332993, "Ammunition (except Small Arms) Manufacturing"
    )
    SMALL_ARMS_ORDNANCE_AND_ORDNANCE_ACCESSORIES_MANUFACTURING = LkOccupationTitle(
        453, 5, 332994, "Small Arms, Ordnance, and Ordnance Accessories Manufacturing"
    )
    FABRICATED_PIPE_AND_PIPE_FITTING_MANUFACTURING = LkOccupationTitle(
        454, 5, 332996, "Fabricated Pipe and Pipe Fitting Manufacturing"
    )
    ALL_OTHER_MISCELLANEOUS_FABRICATED_METAL_PRODUCT_MANUFACTURING = LkOccupationTitle(
        455, 5, 332999, "All Other Miscellaneous Fabricated Metal Product Manufacturing"
    )
    AGRICULTURE_CONSTRUCTION_AND_MINING_MACHINERY_MANUFACTURING = LkOccupationTitle(
        456, 5, 3331, "Agriculture, Construction, and Mining Machinery Manufacturing"
    )
    FARM_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        457, 5, 333111, "Farm Machinery and Equipment Manufacturing"
    )
    LAWN_AND_GARDEN_TRACTOR_AND_HOME_LAWN_AND_GARDEN_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        458, 5, 333112, "Lawn and Garden Tractor and Home Lawn and Garden Equipment Manufacturing"
    )
    CONSTRUCTION_MACHINERY_MANUFACTURING = LkOccupationTitle(
        459, 5, 333120, "Construction Machinery Manufacturing"
    )
    MINING_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        460, 5, 333131, "Mining Machinery and Equipment Manufacturing"
    )
    OIL_AND_GAS_FIELD_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        461, 5, 333132, "Oil and Gas Field Machinery and Equipment Manufacturing"
    )
    INDUSTRIAL_MACHINERY_MANUFACTURING = LkOccupationTitle(
        462, 5, 3332, "Industrial Machinery Manufacturing"
    )
    FOOD_PRODUCT_MACHINERY_MANUFACTURING = LkOccupationTitle(
        463, 5, 333241, "Food Product Machinery Manufacturing"
    )
    SEMICONDUCTOR_MACHINERY_MANUFACTURING = LkOccupationTitle(
        464, 5, 333242, "Semiconductor Machinery Manufacturing"
    )
    SAWMILL_WOODWORKING_AND_PAPER_MACHINERY_MANUFACTURING = LkOccupationTitle(
        465, 5, 333243, "Sawmill, Woodworking, and Paper Machinery Manufacturing"
    )
    PRINTING_MACHINERY_AND_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        466, 5, 333244, "Printing Machinery and Equipment Manufacturing"
    )
    OTHER_INDUSTRIAL_MACHINERY_MANUFACTURING = LkOccupationTitle(
        467, 5, 333249, "Other Industrial Machinery Manufacturing"
    )
    COMMERCIAL_AND_SERVICE_INDUSTRY_MACHINERY_MANUFACTURING = LkOccupationTitle(
        468, 5, 3333, "Commercial and Service Industry Machinery Manufacturing"
    )
    OPTICAL_INSTRUMENT_AND_LENS_MANUFACTURING = LkOccupationTitle(
        469, 5, 333314, "Optical Instrument and Lens Manufacturing"
    )
    PHOTOGRAPHIC_AND_PHOTOCOPYING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        470, 5, 333316, "Photographic and Photocopying Equipment Manufacturing"
    )
    OTHER_COMMERCIAL_AND_SERVICE_INDUSTRY_MACHINERY_MANUFACTURING = LkOccupationTitle(
        471, 5, 333318, "Other Commercial and Service Industry Machinery Manufacturing"
    )
    VENTILATION_HEATING_AIR_CONDITIONING_AND_COMMERCIAL_REFRIGERATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        472,
        5,
        3334,
        "Ventilation, Heating, Air-Conditioning, and Commercial Refrigeration Equipment Manufacturing",
    )
    INDUSTRIAL_AND_COMMERCIAL_FAN_AND_BLOWER_AND_AIR_PURIFICATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        473,
        5,
        333413,
        "Industrial and Commercial Fan and Blower and Air Purification Equipment Manufacturing",
    )
    HEATING_EQUIPMENT_EXCEPT_WARM_AIR_FURNACES_MANUFACTURING = LkOccupationTitle(
        474, 5, 333414, "Heating Equipment (except Warm Air Furnaces) Manufacturing"
    )
    AIR_CONDITIONING_AND_WARM_AIR_HEATING_EQUIPMENT_AND_COMMERCIAL_AND_INDUSTRIAL_REFRIGERATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        475,
        5,
        333415,
        "Air-Conditioning and Warm Air Heating Equipment and Commercial and Industrial Refrigeration Equipment Manufacturing",
    )
    METALWORKING_MACHINERY_MANUFACTURING = LkOccupationTitle(
        476, 5, 3335, "Metalworking Machinery Manufacturing"
    )
    INDUSTRIAL_MOLD_MANUFACTURING = LkOccupationTitle(
        477, 5, 333511, "Industrial Mold Manufacturing"
    )
    SPECIAL_DIE_AND_TOOL_DIE_SET_JIG_AND_FIXTURE_MANUFACTURING = LkOccupationTitle(
        478, 5, 333514, "Special Die and Tool, Die Set, Jig, and Fixture Manufacturing"
    )
    CUTTING_TOOL_AND_MACHINE_TOOL_ACCESSORY_MANUFACTURING = LkOccupationTitle(
        479, 5, 333515, "Cutting Tool and Machine Tool Accessory Manufacturing"
    )
    MACHINE_TOOL_MANUFACTURING = LkOccupationTitle(480, 5, 333517, "Machine Tool Manufacturing")
    ROLLING_MILL_AND_OTHER_METALWORKING_MACHINERY_MANUFACTURING = LkOccupationTitle(
        481, 5, 333519, "Rolling Mill and Other Metalworking Machinery Manufacturing"
    )
    ENGINE_TURBINE_AND_POWER_TRANSMISSION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        482, 5, 3336, "Engine, Turbine, and Power Transmission Equipment Manufacturing"
    )
    TURBINE_AND_TURBINE_GENERATOR_SET_UNITS_MANUFACTURING = LkOccupationTitle(
        483, 5, 333611, "Turbine and Turbine Generator Set Units Manufacturing"
    )
    SPEED_CHANGER_INDUSTRIAL_HIGH_SPEED_DRIVE_AND_GEAR_MANUFACTURING = LkOccupationTitle(
        484, 5, 333612, "Speed Changer, Industrial High-Speed Drive, and Gear Manufacturing"
    )
    MECHANICAL_POWER_TRANSMISSION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        485, 5, 333613, "Mechanical Power Transmission Equipment Manufacturing"
    )
    OTHER_ENGINE_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        486, 5, 333618, "Other Engine Equipment Manufacturing"
    )
    OTHER_GENERAL_PURPOSE_MACHINERY_MANUFACTURING = LkOccupationTitle(
        487, 5, 3339, "Other General Purpose Machinery Manufacturing"
    )
    AIR_AND_GAS_COMPRESSOR_MANUFACTURING = LkOccupationTitle(
        488, 5, 333912, "Air and Gas Compressor Manufacturing"
    )
    MEASURING_DISPENSING_AND_OTHER_PUMPING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        489, 5, 333914, "Measuring, Dispensing, and Other Pumping Equipment Manufacturing"
    )
    ELEVATOR_AND_MOVING_STAIRWAY_MANUFACTURING = LkOccupationTitle(
        490, 5, 333921, "Elevator and Moving Stairway Manufacturing"
    )
    CONVEYOR_AND_CONVEYING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        491, 5, 333922, "Conveyor and Conveying Equipment Manufacturing"
    )
    OVERHEAD_TRAVELING_CRANE_HOIST_AND_MONORAIL_SYSTEM_MANUFACTURING = LkOccupationTitle(
        492, 5, 333923, "Overhead Traveling Crane, Hoist, and Monorail System Manufacturing"
    )
    INDUSTRIAL_TRUCK_TRACTOR_TRAILER_AND_STACKER_MACHINERY_MANUFACTURING = LkOccupationTitle(
        493, 5, 333924, "Industrial Truck, Tractor, Trailer, and Stacker Machinery Manufacturing"
    )
    POWER_DRIVEN_HANDTOOL_MANUFACTURING = LkOccupationTitle(
        494, 5, 333991, "Power-Driven Handtool Manufacturing"
    )
    WELDING_AND_SOLDERING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        495, 5, 333992, "Welding and Soldering Equipment Manufacturing"
    )
    PACKAGING_MACHINERY_MANUFACTURING = LkOccupationTitle(
        496, 5, 333993, "Packaging Machinery Manufacturing"
    )
    INDUSTRIAL_PROCESS_FURNACE_AND_OVEN_MANUFACTURING = LkOccupationTitle(
        497, 5, 333994, "Industrial Process Furnace and Oven Manufacturing"
    )
    FLUID_POWER_CYLINDER_AND_ACTUATOR_MANUFACTURING = LkOccupationTitle(
        498, 5, 333995, "Fluid Power Cylinder and Actuator Manufacturing"
    )
    FLUID_POWER_PUMP_AND_MOTOR_MANUFACTURING = LkOccupationTitle(
        499, 5, 333996, "Fluid Power Pump and Motor Manufacturing"
    )
    SCALE_AND_BALANCE_MANUFACTURING = LkOccupationTitle(
        500, 5, 333997, "Scale and Balance Manufacturing"
    )
    ALL_OTHER_MISCELLANEOUS_GENERAL_PURPOSE_MACHINERY_MANUFACTURING = LkOccupationTitle(
        501, 5, 333999, "All Other Miscellaneous General Purpose Machinery Manufacturing"
    )
    COMPUTER_AND_PERIPHERAL_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        502, 5, 3341, "Computer and Peripheral Equipment Manufacturing"
    )
    ELECTRONIC_COMPUTER_MANUFACTURING = LkOccupationTitle(
        503, 5, 334111, "Electronic Computer Manufacturing"
    )
    COMPUTER_STORAGE_DEVICE_MANUFACTURING = LkOccupationTitle(
        504, 5, 334112, "Computer Storage Device Manufacturing"
    )
    COMPUTER_TERMINAL_AND_OTHER_COMPUTER_PERIPHERAL_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        505, 5, 334118, "Computer Terminal and Other Computer Peripheral Equipment Manufacturing"
    )
    COMMUNICATIONS_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        506, 5, 3342, "Communications Equipment Manufacturing"
    )
    TELEPHONE_APPARATUS_MANUFACTURING = LkOccupationTitle(
        507, 5, 334210, "Telephone Apparatus Manufacturing"
    )
    RADIO_AND_TELEVISION_BROADCASTING_AND_WIRELESS_COMMUNICATIONS_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        508,
        5,
        334220,
        "Radio and Television Broadcasting and Wireless Communications Equipment Manufacturing",
    )
    OTHER_COMMUNICATIONS_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        509, 5, 334290, "Other Communications Equipment Manufacturing"
    )
    AUDIO_AND_VIDEO_EQUIPMENT_MANUFACTURING_4 = LkOccupationTitle(
        510, 5, 3343, "Audio and Video Equipment Manufacturing"
    )
    AUDIO_AND_VIDEO_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        511, 5, 334310, "Audio and Video Equipment Manufacturing"
    )
    SEMICONDUCTOR_AND_OTHER_ELECTRONIC_COMPONENT_MANUFACTURING = LkOccupationTitle(
        512, 5, 3344, "Semiconductor and Other Electronic Component Manufacturing"
    )
    BARE_PRINTED_CIRCUIT_BOARD_MANUFACTURING = LkOccupationTitle(
        513, 5, 334412, "Bare Printed Circuit Board Manufacturing"
    )
    SEMICONDUCTOR_AND_RELATED_DEVICE_MANUFACTURING = LkOccupationTitle(
        514, 5, 334413, "Semiconductor and Related Device Manufacturing"
    )
    CAPACITOR_RESISTOR_COIL_TRANSFORMER_AND_OTHER_INDUCTOR_MANUFACTURING = LkOccupationTitle(
        515, 5, 334416, "Capacitor, Resistor, Coil, Transformer, and Other Inductor Manufacturing"
    )
    ELECTRONIC_CONNECTOR_MANUFACTURING = LkOccupationTitle(
        516, 5, 334417, "Electronic Connector Manufacturing"
    )
    PRINTED_CIRCUIT_ASSEMBLY_ELECTRONIC_ASSEMBLY_MANUFACTURING = LkOccupationTitle(
        517, 5, 334418, "Printed Circuit Assembly (Electronic Assembly) Manufacturing"
    )
    OTHER_ELECTRONIC_COMPONENT_MANUFACTURING = LkOccupationTitle(
        518, 5, 334419, "Other Electronic Component Manufacturing"
    )
    NAVIGATIONAL_MEASURING_ELECTROMEDICAL_AND_CONTROL_INSTRUMENTS_MANUFACTURING = LkOccupationTitle(
        519,
        5,
        3345,
        "Navigational, Measuring, Electromedical, and Control Instruments Manufacturing",
    )
    ELECTROMEDICAL_AND_ELECTROTHERAPEUTIC_APPARATUS_MANUFACTURING = LkOccupationTitle(
        520, 5, 334510, "Electromedical and Electrotherapeutic Apparatus Manufacturing"
    )
    SEARCH_DETECTION_NAVIGATION_GUIDANCE_AERONAUTICAL_AND_NAUTICAL_SYSTEM_AND_INSTRUMENT_MANUFACTURING = LkOccupationTitle(
        521,
        5,
        334511,
        "Search, Detection, Navigation, Guidance, Aeronautical, and Nautical System and Instrument Manufacturing",
    )
    AUTOMATIC_ENVIRONMENTAL_CONTROL_MANUFACTURING_FOR_RESIDENTIAL_COMMERCIAL_AND_APPLIANCE_USE = LkOccupationTitle(
        522,
        5,
        334512,
        "Automatic Environmental Control Manufacturing for Residential, Commercial, and Appliance Use",
    )
    INSTRUMENTS_AND_RELATED_PRODUCTS_MANUFACTURING_FOR_MEASURING_DISPLAYING_AND_CONTROLLING_INDUSTRIAL_PROCESS_VARIABLES = LkOccupationTitle(
        523,
        5,
        334513,
        "Instruments and Related Products Manufacturing for Measuring, Displaying, and Controlling Industrial Process Variables",
    )
    TOTALIZING_FLUID_METER_AND_COUNTING_DEVICE_MANUFACTURING = LkOccupationTitle(
        524, 5, 334514, "Totalizing Fluid Meter and Counting Device Manufacturing"
    )
    INSTRUMENT_MANUFACTURING_FOR_MEASURING_AND_TESTING_ELECTRICITY_AND_ELECTRICAL_SIGNALS_832 = LkOccupationTitle(
        525,
        5,
        334515,
        "Instrument Manufacturing for Measuring and Testing Electricity and Electrical Signals832",
    )
    ANALYTICAL_LABORATORY_INSTRUMENT_MANUFACTURING = LkOccupationTitle(
        526, 5, 334516, "Analytical Laboratory Instrument Manufacturing"
    )
    IRRADIATION_APPARATUS_MANUFACTURING = LkOccupationTitle(
        527, 5, 334517, "Irradiation Apparatus Manufacturing"
    )
    OTHER_MEASURING_AND_CONTROLLING_DEVICE_MANUFACTURING = LkOccupationTitle(
        528, 5, 334519, "Other Measuring and Controlling Device Manufacturing"
    )
    MANUFACTURING_AND_REPRODUCING_MAGNETIC_AND_OPTICAL_MEDIA = LkOccupationTitle(
        529, 5, 3346, "Manufacturing and Reproducing Magnetic and Optical Media"
    )
    BLANK_MAGNETIC_AND_OPTICAL_RECORDING_MEDIA_MANUFACTURING = LkOccupationTitle(
        530, 5, 334613, "Blank Magnetic and Optical Recording Media Manufacturing"
    )
    SOFTWARE_AND_OTHER_PRERECORDED_COMPACT_DISC_TAPE_AND_RECORD_REPRODUCING = LkOccupationTitle(
        531, 5, 334614, "Software and Other Prerecorded Compact Disc, Tape, and Record Reproducing"
    )
    ELECTRIC_LIGHTING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        532, 5, 3351, "Electric Lighting Equipment Manufacturing"
    )
    ELECTRIC_LAMP_BULB_AND_PART_MANUFACTURING = LkOccupationTitle(
        533, 5, 335110, "Electric Lamp Bulb and Part Manufacturing"
    )
    RESIDENTIAL_ELECTRIC_LIGHTING_FIXTURE_MANUFACTURING = LkOccupationTitle(
        534, 5, 335121, "Residential Electric Lighting Fixture Manufacturing"
    )
    COMMERCIAL_INDUSTRIAL_AND_INSTITUTIONAL_ELECTRIC_LIGHTING_FIXTURE_MANUFACTURING = LkOccupationTitle(
        535,
        5,
        335122,
        "Commercial, Industrial, and Institutional Electric Lighting Fixture Manufacturing",
    )
    OTHER_LIGHTING_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        536, 5, 335129, "Other Lighting Equipment Manufacturing"
    )
    HOUSEHOLD_APPLIANCE_MANUFACTURING = LkOccupationTitle(
        537, 5, 3352, "Household Appliance Manufacturing"
    )
    SMALL_ELECTRICAL_APPLIANCE_MANUFACTURING = LkOccupationTitle(
        538, 5, 335210, "Small Electrical Appliance Manufacturing"
    )
    MAJOR_HOUSEHOLD_APPLIANCE_MANUFACTURING = LkOccupationTitle(
        539, 5, 335220, "Major Household Appliance Manufacturing"
    )
    ELECTRICAL_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        540, 5, 3353, "Electrical Equipment Manufacturing"
    )
    POWER_DISTRIBUTION_AND_SPECIALTY_TRANSFORMER_MANUFACTURING = LkOccupationTitle(
        541, 5, 335311, "Power, Distribution, and Specialty Transformer Manufacturing"
    )
    MOTOR_AND_GENERATOR_MANUFACTURING = LkOccupationTitle(
        542, 5, 335312, "Motor and Generator Manufacturing"
    )
    SWITCHGEAR_AND_SWITCHBOARD_APPARATUS_MANUFACTURING = LkOccupationTitle(
        543, 5, 335313, "Switchgear and Switchboard Apparatus Manufacturing"
    )
    RELAY_AND_INDUSTRIAL_CONTROL_MANUFACTURING = LkOccupationTitle(
        544, 5, 335314, "Relay and Industrial Control Manufacturing"
    )
    OTHER_ELECTRICAL_EQUIPMENT_AND_COMPONENT_MANUFACTURING = LkOccupationTitle(
        545, 5, 3359, "Other Electrical Equipment and Component Manufacturing"
    )
    STORAGE_BATTERY_MANUFACTURING = LkOccupationTitle(
        546, 5, 335911, "Storage Battery Manufacturing"
    )
    PRIMARY_BATTERY_MANUFACTURING = LkOccupationTitle(
        547, 5, 335912, "Primary Battery Manufacturing"
    )
    FIBER_OPTIC_CABLE_MANUFACTURING = LkOccupationTitle(
        548, 5, 335921, "Fiber Optic Cable Manufacturing"
    )
    OTHER_COMMUNICATION_AND_ENERGY_WIRE_MANUFACTURING = LkOccupationTitle(
        549, 5, 335929, "Other Communication and Energy Wire Manufacturing"
    )
    CURRENT_CARRYING_WIRING_DEVICE_MANUFACTURING = LkOccupationTitle(
        550, 5, 335931, "Current-Carrying Wiring Device Manufacturing"
    )
    NONCURRENT_CARRYING_WIRING_DEVICE_MANUFACTURING = LkOccupationTitle(
        551, 5, 335932, "Noncurrent-Carrying Wiring Device Manufacturing"
    )
    CARBON_AND_GRAPHITE_PRODUCT_MANUFACTURING = LkOccupationTitle(
        552, 5, 335991, "Carbon and Graphite Product Manufacturing"
    )
    ALL_OTHER_MISCELLANEOUS_ELECTRICAL_EQUIPMENT_AND_COMPONENT_MANUFACTURING = LkOccupationTitle(
        553, 5, 335999, "All Other Miscellaneous Electrical Equipment and Component Manufacturing"
    )
    MOTOR_VEHICLE_MANUFACTURING = LkOccupationTitle(554, 5, 3361, "Motor Vehicle Manufacturing")
    AUTOMOBILE_MANUFACTURING = LkOccupationTitle(555, 5, 336111, "Automobile Manufacturing")
    LIGHT_TRUCK_AND_UTILITY_VEHICLE_MANUFACTURING = LkOccupationTitle(
        556, 5, 336112, "Light Truck and Utility Vehicle Manufacturing"
    )
    HEAVY_DUTY_TRUCK_MANUFACTURING = LkOccupationTitle(
        557, 5, 336120, "Heavy Duty Truck Manufacturing"
    )
    MOTOR_VEHICLE_BODY_AND_TRAILER_MANUFACTURING = LkOccupationTitle(
        558, 5, 3362, "Motor Vehicle Body and Trailer Manufacturing"
    )
    MOTOR_VEHICLE_BODY_MANUFACTURING = LkOccupationTitle(
        559, 5, 336211, "Motor Vehicle Body Manufacturing"
    )
    TRUCK_TRAILER_MANUFACTURING = LkOccupationTitle(560, 5, 336212, "Truck Trailer Manufacturing")
    MOTOR_HOME_MANUFACTURING = LkOccupationTitle(561, 5, 336213, "Motor Home Manufacturing")
    TRAVEL_TRAILER_AND_CAMPER_MANUFACTURING = LkOccupationTitle(
        562, 5, 336214, "Travel Trailer and Camper Manufacturing"
    )
    MOTOR_VEHICLE_PARTS_MANUFACTURING = LkOccupationTitle(
        563, 5, 3363, "Motor Vehicle Parts Manufacturing"
    )
    MOTOR_VEHICLE_GASOLINE_ENGINE_AND_ENGINE_PARTS_MANUFACTURING = LkOccupationTitle(
        564, 5, 336310, "Motor Vehicle Gasoline Engine and Engine Parts Manufacturing"
    )
    MOTOR_VEHICLE_ELECTRICAL_AND_ELECTRONIC_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        565, 5, 336320, "Motor Vehicle Electrical and Electronic Equipment Manufacturing"
    )
    MOTOR_VEHICLE_STEERING_AND_SUSPENSION_COMPONENTS_EXCEPT_SPRING_MANUFACTURING = LkOccupationTitle(
        566,
        5,
        336330,
        "Motor Vehicle Steering and Suspension Components (except Spring) Manufacturing",
    )
    MOTOR_VEHICLE_BRAKE_SYSTEM_MANUFACTURING = LkOccupationTitle(
        567, 5, 336340, "Motor Vehicle Brake System Manufacturing"
    )
    MOTOR_VEHICLE_TRANSMISSION_AND_POWER_TRAIN_PARTS_MANUFACTURING = LkOccupationTitle(
        568, 5, 336350, "Motor Vehicle Transmission and Power Train Parts Manufacturing"
    )
    MOTOR_VEHICLE_SEATING_AND_INTERIOR_TRIM_MANUFACTURING = LkOccupationTitle(
        569, 5, 336360, "Motor Vehicle Seating and Interior Trim Manufacturing"
    )
    MOTOR_VEHICLE_METAL_STAMPING = LkOccupationTitle(570, 5, 336370, "Motor Vehicle Metal Stamping")
    OTHER_MOTOR_VEHICLE_PARTS_MANUFACTURING = LkOccupationTitle(
        571, 5, 336390, "Other Motor Vehicle Parts Manufacturing"
    )
    AEROSPACE_PRODUCT_AND_PARTS_MANUFACTURING = LkOccupationTitle(
        572, 5, 3364, "Aerospace Product and Parts Manufacturing"
    )
    AIRCRAFT_MANUFACTURING = LkOccupationTitle(573, 5, 336411, "Aircraft Manufacturing")
    AIRCRAFT_ENGINE_AND_ENGINE_PARTS_MANUFACTURING = LkOccupationTitle(
        574, 5, 336412, "Aircraft Engine and Engine Parts Manufacturing"
    )
    OTHER_AIRCRAFT_PARTS_AND_AUXILIARY_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        575, 5, 336413, "Other Aircraft Parts and Auxiliary Equipment Manufacturing"
    )
    GUIDED_MISSILE_AND_SPACE_VEHICLE_MANUFACTURING = LkOccupationTitle(
        576, 5, 336414, "Guided Missile and Space Vehicle Manufacturing"
    )
    GUIDED_MISSILE_AND_SPACE_VEHICLE_PROPULSION_UNIT_AND_PROPULSION_UNIT_PARTS_MANUFACTURING = LkOccupationTitle(
        577,
        5,
        336415,
        "Guided Missile and Space Vehicle Propulsion Unit and Propulsion Unit Parts Manufacturing",
    )
    OTHER_GUIDED_MISSILE_AND_SPACE_VEHICLE_PARTS_AND_AUXILIARY_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        578,
        5,
        336419,
        "Other Guided Missile and Space Vehicle Parts and Auxiliary Equipment Manufacturing",
    )
    RAILROAD_ROLLING_STOCK_MANUFACTURING_4 = LkOccupationTitle(
        579, 5, 3365, "Railroad Rolling Stock Manufacturing"
    )
    RAILROAD_ROLLING_STOCK_MANUFACTURING = LkOccupationTitle(
        580, 5, 336510, "Railroad Rolling Stock Manufacturing"
    )
    SHIP_AND_BOAT_BUILDING = LkOccupationTitle(581, 5, 3366, "Ship and Boat Building")
    SHIP_BUILDING_AND_REPAIRING = LkOccupationTitle(582, 5, 336611, "Ship Building and Repairing")
    BOAT_BUILDING = LkOccupationTitle(583, 5, 336612, "Boat Building")
    OTHER_TRANSPORTATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        584, 5, 3369, "Other Transportation Equipment Manufacturing"
    )
    MOTORCYCLE_BICYCLE_AND_PARTS_MANUFACTURING = LkOccupationTitle(
        585, 5, 336991, "Motorcycle, Bicycle, and Parts Manufacturing"
    )
    MILITARY_ARMORED_VEHICLE_TANK_AND_TANK_COMPONENT_MANUFACTURING = LkOccupationTitle(
        586, 5, 336992, "Military Armored Vehicle, Tank, and Tank Component Manufacturing"
    )
    ALL_OTHER_TRANSPORTATION_EQUIPMENT_MANUFACTURING = LkOccupationTitle(
        587, 5, 336999, "All Other Transportation Equipment Manufacturing"
    )
    HOUSEHOLD_AND_INSTITUTIONAL_FURNITURE_AND_KITCHEN_CABINET_MANUFACTURING = LkOccupationTitle(
        588, 5, 3371, "Household and Institutional Furniture and Kitchen Cabinet Manufacturing"
    )
    WOOD_KITCHEN_CABINET_AND_COUNTERTOP_MANUFACTURING = LkOccupationTitle(
        589, 5, 337110, "Wood Kitchen Cabinet and Countertop Manufacturing"
    )
    UPHOLSTERED_HOUSEHOLD_FURNITURE_MANUFACTURING = LkOccupationTitle(
        590, 5, 337121, "Upholstered Household Furniture Manufacturing"
    )
    NONUPHOLSTERED_WOOD_HOUSEHOLD_FURNITURE_MANUFACTURING = LkOccupationTitle(
        591, 5, 337122, "Nonupholstered Wood Household Furniture Manufacturing"
    )
    METAL_HOUSEHOLD_FURNITURE_MANUFACTURING = LkOccupationTitle(
        592, 5, 337124, "Metal Household Furniture Manufacturing"
    )
    HOUSEHOLD_FURNITURE_EXCEPT_WOOD_AND_METAL_MANUFACTURING = LkOccupationTitle(
        593, 5, 337125, "Household Furniture (except Wood and Metal) Manufacturing"
    )
    INSTITUTIONAL_FURNITURE_MANUFACTURING = LkOccupationTitle(
        594, 5, 337127, "Institutional Furniture Manufacturing"
    )
    OFFICE_FURNITURE_INCLUDING_FIXTURES_MANUFACTURING = LkOccupationTitle(
        595, 5, 3372, "Office Furniture (including Fixtures) Manufacturing"
    )
    WOOD_OFFICE_FURNITURE_MANUFACTURING = LkOccupationTitle(
        596, 5, 337211, "Wood Office Furniture Manufacturing"
    )
    CUSTOM_ARCHITECTURAL_WOODWORK_AND_MILLWORK_MANUFACTURING = LkOccupationTitle(
        597, 5, 337212, "Custom Architectural Woodwork and Millwork Manufacturing"
    )
    OFFICE_FURNITURE_EXCEPT_WOOD_MANUFACTURING = LkOccupationTitle(
        598, 5, 337214, "Office Furniture (except Wood) Manufacturing"
    )
    SHOWCASE_PARTITION_SHELVING_AND_LOCKER_MANUFACTURING = LkOccupationTitle(
        599, 5, 337215, "Showcase, Partition, Shelving, and Locker Manufacturing"
    )
    OTHER_FURNITURE_RELATED_PRODUCT_MANUFACTURING = LkOccupationTitle(
        600, 5, 3379, "Other Furniture Related Product Manufacturing"
    )
    MATTRESS_MANUFACTURING = LkOccupationTitle(601, 5, 337910, "Mattress Manufacturing")
    BLIND_AND_SHADE_MANUFACTURING = LkOccupationTitle(
        602, 5, 337920, "Blind and Shade Manufacturing"
    )
    MEDICAL_EQUIPMENT_AND_SUPPLIES_MANUFACTURING = LkOccupationTitle(
        603, 5, 3391, "Medical Equipment and Supplies Manufacturing"
    )
    SURGICAL_AND_MEDICAL_INSTRUMENT_MANUFACTURING = LkOccupationTitle(
        604, 5, 339112, "Surgical and Medical Instrument Manufacturing"
    )
    SURGICAL_APPLIANCE_AND_SUPPLIES_MANUFACTURING = LkOccupationTitle(
        605, 5, 339113, "Surgical Appliance and Supplies Manufacturing"
    )
    DENTAL_EQUIPMENT_AND_SUPPLIES_MANUFACTURING = LkOccupationTitle(
        606, 5, 339114, "Dental Equipment and Supplies Manufacturing"
    )
    OPHTHALMIC_GOODS_MANUFACTURING = LkOccupationTitle(
        607, 5, 339115, "Ophthalmic Goods Manufacturing"
    )
    DENTAL_LABORATORIES = LkOccupationTitle(608, 5, 339116, "Dental Laboratories")
    OTHER_MISCELLANEOUS_MANUFACTURING = LkOccupationTitle(
        609, 5, 3399, "Other Miscellaneous Manufacturing"
    )
    JEWELRY_AND_SILVERWARE_MANUFACTURING = LkOccupationTitle(
        610, 5, 339910, "Jewelry and Silverware Manufacturing"
    )
    SPORTING_AND_ATHLETIC_GOODS_MANUFACTURING = LkOccupationTitle(
        611, 5, 339920, "Sporting and Athletic Goods Manufacturing"
    )
    DOLL_TOY_AND_GAME_MANUFACTURING = LkOccupationTitle(
        612, 5, 339930, "Doll, Toy, and Game Manufacturing"
    )
    OFFICE_SUPPLIES_EXCEPT_PAPER_MANUFACTURING = LkOccupationTitle(
        613, 5, 339940, "Office Supplies (except Paper) Manufacturing"
    )
    SIGN_MANUFACTURING = LkOccupationTitle(614, 5, 339950, "Sign Manufacturing")
    GASKET_PACKING_AND_SEALING_DEVICE_MANUFACTURING = LkOccupationTitle(
        615, 5, 339991, "Gasket, Packing, and Sealing Device Manufacturing"
    )
    MUSICAL_INSTRUMENT_MANUFACTURING = LkOccupationTitle(
        616, 5, 339992, "Musical Instrument Manufacturing"
    )
    FASTENER_BUTTON_NEEDLE_AND_PIN_MANUFACTURING = LkOccupationTitle(
        617, 5, 339993, "Fastener, Button, Needle, and Pin Manufacturing"
    )
    BROOM_BRUSH_AND_MOP_MANUFACTURING = LkOccupationTitle(
        618, 5, 339994, "Broom, Brush, and Mop Manufacturing"
    )
    BURIAL_CASKET_MANUFACTURING = LkOccupationTitle(619, 5, 339995, "Burial Casket Manufacturing")
    ALL_OTHER_MISCELLANEOUS_MANUFACTURING = LkOccupationTitle(
        620, 5, 339999, "All Other Miscellaneous Manufacturing"
    )
    MOTOR_VEHICLE_AND_MOTOR_VEHICLE_PARTS_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        621, 6, 4231, "Motor Vehicle and Motor Vehicle Parts and Supplies Merchant Wholesalers"
    )
    AUTOMOBILE_AND_OTHER_MOTOR_VEHICLE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        622, 6, 423110, "Automobile and Other Motor Vehicle Merchant Wholesalers"
    )
    MOTOR_VEHICLE_SUPPLIES_AND_NEW_PARTS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        623, 6, 423120, "Motor Vehicle Supplies and New Parts Merchant Wholesalers"
    )
    TIRE_AND_TUBE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        624, 6, 423130, "Tire and Tube Merchant Wholesalers"
    )
    MOTOR_VEHICLE_PARTS_USED_MERCHANT_WHOLESALERS = LkOccupationTitle(
        625, 6, 423140, "Motor Vehicle Parts (Used) Merchant Wholesalers"
    )
    FURNITURE_AND_HOME_FURNISHING_MERCHANT_WHOLESALERS = LkOccupationTitle(
        626, 6, 4232, "Furniture and Home Furnishing Merchant Wholesalers"
    )
    FURNITURE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        627, 6, 423210, "Furniture Merchant Wholesalers"
    )
    HOME_FURNISHING_MERCHANT_WHOLESALERS = LkOccupationTitle(
        628, 6, 423220, "Home Furnishing Merchant Wholesalers"
    )
    LUMBER_AND_OTHER_CONSTRUCTION_MATERIALS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        629, 6, 4233, "Lumber and Other Construction Materials Merchant Wholesalers"
    )
    LUMBER_PLYWOOD_MILLWORK_AND_WOOD_PANEL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        630, 6, 423310, "Lumber, Plywood, Millwork, and Wood Panel Merchant Wholesalers"
    )
    BRICK_STONE_AND_RELATED_CONSTRUCTION_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        631, 6, 423320, "Brick, Stone, and Related Construction Material Merchant Wholesalers"
    )
    ROOFING_SIDING_AND_INSULATION_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        632, 6, 423330, "Roofing, Siding, and Insulation Material Merchant Wholesalers"
    )
    OTHER_CONSTRUCTION_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        633, 6, 423390, "Other Construction Material Merchant Wholesalers"
    )
    PROFESSIONAL_AND_COMMERCIAL_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        634, 6, 4234, "Professional and Commercial Equipment and Supplies Merchant Wholesalers"
    )
    PHOTOGRAPHIC_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        635, 6, 423410, "Photographic Equipment and Supplies Merchant Wholesalers"
    )
    OFFICE_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        636, 6, 423420, "Office Equipment Merchant Wholesalers"
    )
    COMPUTER_AND_COMPUTER_PERIPHERAL_EQUIPMENT_AND_SOFTWARE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        637,
        6,
        423430,
        "Computer and Computer Peripheral Equipment and Software Merchant Wholesalers",
    )
    OTHER_COMMERCIAL_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        638, 6, 423440, "Other Commercial Equipment Merchant Wholesalers"
    )
    MEDICAL_DENTAL_AND_HOSPITAL_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        639, 6, 423450, "Medical, Dental, and Hospital Equipment and Supplies Merchant Wholesalers"
    )
    OPHTHALMIC_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        640, 6, 423460, "Ophthalmic Goods Merchant Wholesalers"
    )
    OTHER_PROFESSIONAL_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        641, 6, 423490, "Other Professional Equipment and Supplies Merchant Wholesalers"
    )
    METAL_AND_MINERAL_EXCEPT_PETROLEUM_MERCHANT_WHOLESALERS = LkOccupationTitle(
        642, 6, 4235, "Metal and Mineral (except Petroleum) Merchant Wholesalers"
    )
    METAL_SERVICE_CENTERS_AND_OTHER_METAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        643, 6, 423510, "Metal Service Centers and Other Metal Merchant Wholesalers"
    )
    COAL_AND_OTHER_MINERAL_AND_ORE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        644, 6, 423520, "Coal and Other Mineral and Ore Merchant Wholesalers"
    )
    HOUSEHOLD_APPLIANCES_AND_ELECTRICAL_AND_ELECTRONIC_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        645,
        6,
        4236,
        "Household Appliances and Electrical and Electronic Goods Merchant Wholesalers",
    )
    ELECTRICAL_APPARATUS_AND_EQUIPMENT_WIRING_SUPPLIES_AND_RELATED_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        646,
        6,
        423610,
        "Electrical Apparatus and Equipment, Wiring Supplies, and Related Equipment Merchant Wholesalers",
    )
    HOUSEHOLD_APPLIANCES_ELECTRIC_HOUSEWARES_AND_CONSUMER_ELECTRONICS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        647,
        6,
        423620,
        "Household Appliances, Electric Housewares, and Consumer Electronics Merchant Wholesalers",
    )
    OTHER_ELECTRONIC_PARTS_AND_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        648, 6, 423690, "Other Electronic Parts and Equipment Merchant Wholesalers"
    )
    HARDWARE_AND_PLUMBING_AND_HEATING_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        649,
        6,
        4237,
        "Hardware, and Plumbing and Heating Equipment and Supplies Merchant Wholesalers",
    )
    HARDWARE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        650, 6, 423710, "Hardware Merchant Wholesalers"
    )
    PLUMBING_AND_HEATING_EQUIPMENT_AND_SUPPLIES_HYDRONICS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        651,
        6,
        423720,
        "Plumbing and Heating Equipment and Supplies (Hydronics) Merchant Wholesalers",
    )
    WARM_AIR_HEATING_AND_AIR_CONDITIONING_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        652,
        6,
        423730,
        "Warm Air Heating and Air-Conditioning Equipment and Supplies Merchant Wholesalers",
    )
    REFRIGERATION_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        653, 6, 423740, "Refrigeration Equipment and Supplies Merchant Wholesalers"
    )
    MACHINERY_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        654, 6, 4238, "Machinery, Equipment, and Supplies Merchant Wholesalers"
    )
    CONSTRUCTION_AND_MINING_EXCEPT_OIL_WELL_MACHINERY_AND_EQUIPMENT_MERCHANT_WHOLESALERS_220 = LkOccupationTitle(
        655,
        6,
        423810,
        "Construction and Mining (except Oil Well) Machinery and Equipment Merchant Wholesalers220",
    )
    FARM_AND_GARDEN_MACHINERY_AND_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        656, 6, 423820, "Farm and Garden Machinery and Equipment Merchant Wholesalers"
    )
    INDUSTRIAL_MACHINERY_AND_EQUIPMENT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        657, 6, 423830, "Industrial Machinery and Equipment Merchant Wholesalers"
    )
    INDUSTRIAL_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        658, 6, 423840, "Industrial Supplies Merchant Wholesalers"
    )
    SERVICE_ESTABLISHMENT_EQUIPMENT_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        659, 6, 423850, "Service Establishment Equipment and Supplies Merchant Wholesalers"
    )
    TRANSPORTATION_EQUIPMENT_AND_SUPPLIES_EXCEPT_MOTOR_VEHICLE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        660,
        6,
        423860,
        "Transportation Equipment and Supplies (except Motor Vehicle) Merchant Wholesalers",
    )
    MISCELLANEOUS_DURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        661, 6, 4239, "Miscellaneous Durable Goods Merchant Wholesalers"
    )
    SPORTING_AND_RECREATIONAL_GOODS_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        662, 6, 423910, "Sporting and Recreational Goods and Supplies Merchant Wholesalers"
    )
    TOY_AND_HOBBY_GOODS_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        663, 6, 423920, "Toy and Hobby Goods and Supplies Merchant Wholesalers"
    )
    RECYCLABLE_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        664, 6, 423930, "Recyclable Material Merchant Wholesalers"
    )
    JEWELRY_WATCH_PRECIOUS_STONE_AND_PRECIOUS_METAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        665, 6, 423940, "Jewelry, Watch, Precious Stone, and Precious Metal Merchant Wholesalers"
    )
    OTHER_MISCELLANEOUS_DURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        666, 6, 423990, "Other Miscellaneous Durable Goods Merchant Wholesalers"
    )
    PAPER_AND_PAPER_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        667, 6, 4241, "Paper and Paper Product Merchant Wholesalers"
    )
    PRINTING_AND_WRITING_PAPER_MERCHANT_WHOLESALERS = LkOccupationTitle(
        668, 6, 424110, "Printing and Writing Paper Merchant Wholesalers"
    )
    STATIONERY_AND_OFFICE_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        669, 6, 424120, "Stationery and Office Supplies Merchant Wholesalers"
    )
    INDUSTRIAL_AND_PERSONAL_SERVICE_PAPER_MERCHANT_WHOLESALERS = LkOccupationTitle(
        670, 6, 424130, "Industrial and Personal Service Paper Merchant Wholesalers"
    )
    DRUGS_AND_DRUGGISTS_SUNDRIES_MERCHANT_WHOLESALERS_4 = LkOccupationTitle(
        671, 6, 4242, "Drugs and Druggists' Sundries Merchant Wholesalers"
    )
    DRUGS_AND_DRUGGISTS_SUNDRIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        672, 6, 424210, "Drugs and Druggists' Sundries Merchant Wholesalers"
    )
    APPAREL_PIECE_GOODS_AND_NOTIONS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        673, 6, 4243, "Apparel, Piece Goods, and Notions Merchant Wholesalers"
    )
    PIECE_GOODS_NOTIONS_AND_OTHER_DRY_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        674, 6, 424310, "Piece Goods, Notions, and Other Dry Goods Merchant Wholesalers"
    )
    MEN_S_AND_BOYS_CLOTHING_AND_FURNISHINGS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        675, 6, 424320, "Men's and Boys' Clothing and Furnishings Merchant Wholesalers"
    )
    WOMEN_S_CHILDREN_S_AND_INFANTS_CLOTHING_AND_ACCESSORIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        676,
        6,
        424330,
        "Women's, Children's, and Infants' Clothing and Accessories Merchant Wholesalers",
    )
    FOOTWEAR_MERCHANT_WHOLESALERS = LkOccupationTitle(
        677, 6, 424340, "Footwear Merchant Wholesalers"
    )
    GROCERY_AND_RELATED_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        678, 6, 4244, "Grocery and Related Product Merchant Wholesalers"
    )
    GENERAL_LINE_GROCERY_MERCHANT_WHOLESALERS = LkOccupationTitle(
        679, 6, 424410, "General Line Grocery Merchant Wholesalers"
    )
    PACKAGED_FROZEN_FOOD_MERCHANT_WHOLESALERS = LkOccupationTitle(
        680, 6, 424420, "Packaged Frozen Food Merchant Wholesalers"
    )
    DAIRY_PRODUCT_EXCEPT_DRIED_OR_CANNED_MERCHANT_WHOLESALERS = LkOccupationTitle(
        681, 6, 424430, "Dairy Product (except Dried or Canned) Merchant Wholesalers"
    )
    POULTRY_AND_POULTRY_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        682, 6, 424440, "Poultry and Poultry Product Merchant Wholesalers"
    )
    CONFECTIONERY_MERCHANT_WHOLESALERS = LkOccupationTitle(
        683, 6, 424450, "Confectionery Merchant Wholesalers"
    )
    FISH_AND_SEAFOOD_MERCHANT_WHOLESALERS = LkOccupationTitle(
        684, 6, 424460, "Fish and Seafood Merchant Wholesalers"
    )
    MEAT_AND_MEAT_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        685, 6, 424470, "Meat and Meat Product Merchant Wholesalers"
    )
    FRESH_FRUIT_AND_VEGETABLE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        686, 6, 424480, "Fresh Fruit and Vegetable Merchant Wholesalers"
    )
    OTHER_GROCERY_AND_RELATED_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        687, 6, 424490, "Other Grocery and Related Products Merchant Wholesalers"
    )
    FARM_PRODUCT_RAW_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        688, 6, 4245, "Farm Product Raw Material Merchant Wholesalers"
    )
    GRAIN_AND_FIELD_BEAN_MERCHANT_WHOLESALERS = LkOccupationTitle(
        689, 6, 424510, "Grain and Field Bean Merchant Wholesalers"
    )
    LIVESTOCK_MERCHANT_WHOLESALERS = LkOccupationTitle(
        690, 6, 424520, "Livestock Merchant Wholesalers"
    )
    OTHER_FARM_PRODUCT_RAW_MATERIAL_MERCHANT_WHOLESALERS = LkOccupationTitle(
        691, 6, 424590, "Other Farm Product Raw Material Merchant Wholesalers"
    )
    CHEMICAL_AND_ALLIED_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        692, 6, 4246, "Chemical and Allied Products Merchant Wholesalers"
    )
    PLASTICS_MATERIALS_AND_BASIC_FORMS_AND_SHAPES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        693, 6, 424610, "Plastics Materials and Basic Forms and Shapes Merchant Wholesalers"
    )
    OTHER_CHEMICAL_AND_ALLIED_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        694, 6, 424690, "Other Chemical and Allied Products Merchant Wholesalers"
    )
    PETROLEUM_AND_PETROLEUM_PRODUCTS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        695, 6, 4247, "Petroleum and Petroleum Products Merchant Wholesalers"
    )
    PETROLEUM_BULK_STATIONS_AND_TERMINALS = LkOccupationTitle(
        696, 6, 424710, "Petroleum Bulk Stations and Terminals"
    )
    PETROLEUM_AND_PETROLEUM_PRODUCTS_MERCHANT_WHOLESALERS_EXCEPT_BULK_STATIONS_AND_TERMINALS = LkOccupationTitle(
        697,
        6,
        424720,
        "Petroleum and Petroleum Products Merchant Wholesalers (except Bulk Stations and Terminals)",
    )
    BEER_WINE_AND_DISTILLED_ALCOHOLIC_BEVERAGE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        698, 6, 4248, "Beer, Wine, and Distilled Alcoholic Beverage Merchant Wholesalers"
    )
    BEER_AND_ALE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        699, 6, 424810, "Beer and Ale Merchant Wholesalers"
    )
    WINE_AND_DISTILLED_ALCOHOLIC_BEVERAGE_MERCHANT_WHOLESALERS = LkOccupationTitle(
        700, 6, 424820, "Wine and Distilled Alcoholic Beverage Merchant Wholesalers"
    )
    MISCELLANEOUS_NONDURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        701, 6, 4249, "Miscellaneous Nondurable Goods Merchant Wholesalers"
    )
    FARM_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        702, 6, 424910, "Farm Supplies Merchant Wholesalers"
    )
    BOOK_PERIODICAL_AND_NEWSPAPER_MERCHANT_WHOLESALERS = LkOccupationTitle(
        703, 6, 424920, "Book, Periodical, and Newspaper Merchant Wholesalers"
    )
    FLOWER_NURSERY_STOCK_AND_FLORISTS_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        704, 6, 424930, "Flower, Nursery Stock, and Florists' Supplies Merchant Wholesalers"
    )
    TOBACCO_AND_TOBACCO_PRODUCT_MERCHANT_WHOLESALERS = LkOccupationTitle(
        705, 6, 424940, "Tobacco and Tobacco Product Merchant Wholesalers"
    )
    PAINT_VARNISH_AND_SUPPLIES_MERCHANT_WHOLESALERS = LkOccupationTitle(
        706, 6, 424950, "Paint, Varnish, and Supplies Merchant Wholesalers"
    )
    OTHER_MISCELLANEOUS_NONDURABLE_GOODS_MERCHANT_WHOLESALERS = LkOccupationTitle(
        707, 6, 424990, "Other Miscellaneous Nondurable Goods Merchant Wholesalers"
    )
    WHOLESALE_ELECTRONIC_MARKETS_AND_AGENTS_AND_BROKERS = LkOccupationTitle(
        708, 6, 4251, "Wholesale Electronic Markets and Agents and Brokers"
    )
    BUSINESS_TO_BUSINESS_ELECTRONIC_MARKETS = LkOccupationTitle(
        709, 6, 425110, "Business to Business Electronic Markets"
    )
    WHOLESALE_TRADE_AGENTS_AND_BROKERS = LkOccupationTitle(
        710, 6, 425120, "Wholesale Trade Agents and Brokers"
    )
    AUTOMOBILE_DEALERS = LkOccupationTitle(711, 7, 4411, "Automobile Dealers")
    NEW_CAR_DEALERS = LkOccupationTitle(712, 7, 441110, "New Car Dealers")
    USED_CAR_DEALERS = LkOccupationTitle(713, 7, 441120, "Used Car Dealers")
    OTHER_MOTOR_VEHICLE_DEALERS = LkOccupationTitle(714, 7, 4412, "Other Motor Vehicle Dealers")
    RECREATIONAL_VEHICLE_DEALERS = LkOccupationTitle(715, 7, 441210, "Recreational Vehicle Dealers")
    BOAT_DEALERS = LkOccupationTitle(716, 7, 441222, "Boat Dealers")
    MOTORCYCLE_ATV_AND_ALL_OTHER_MOTOR_VEHICLE_DEALERS = LkOccupationTitle(
        717, 7, 441228, "Motorcycle, ATV, and All Other Motor Vehicle Dealers"
    )
    AUTOMOTIVE_PARTS_ACCESSORIES_AND_TIRE_STORES = LkOccupationTitle(
        718, 7, 4413, "Automotive Parts, Accessories, and Tire Stores"
    )
    AUTOMOTIVE_PARTS_AND_ACCESSORIES_STORES = LkOccupationTitle(
        719, 7, 441310, "Automotive Parts and Accessories Stores"
    )
    TIRE_DEALERS = LkOccupationTitle(720, 7, 441320, "Tire Dealers")
    FURNITURE_STORES_4 = LkOccupationTitle(721, 7, 4421, "Furniture Stores")
    FURNITURE_STORES = LkOccupationTitle(722, 7, 442110, "Furniture Stores")
    HOME_FURNISHINGS_STORES = LkOccupationTitle(723, 7, 4422, "Home Furnishings Stores")
    FLOOR_COVERING_STORES = LkOccupationTitle(724, 7, 442210, "Floor Covering Stores")
    WINDOW_TREATMENT_STORES = LkOccupationTitle(725, 7, 442291, "Window Treatment Stores")
    ALL_OTHER_HOME_FURNISHINGS_STORES = LkOccupationTitle(
        726, 7, 442299, "All Other Home Furnishings Stores"
    )
    ELECTRONICS_AND_APPLIANCE_STORES = LkOccupationTitle(
        727, 7, 4431, "Electronics and Appliance Stores"
    )
    HOUSEHOLD_APPLIANCE_STORES = LkOccupationTitle(728, 7, 443141, "Household Appliance Stores")
    ELECTRONICS_STORES = LkOccupationTitle(729, 7, 443142, "Electronics Stores")
    BUILDING_MATERIAL_AND_SUPPLIES_DEALERS = LkOccupationTitle(
        730, 7, 4441, "Building Material and Supplies Dealers"
    )
    HOME_CENTERS = LkOccupationTitle(731, 7, 444110, "Home Centers")
    PAINT_AND_WALLPAPER_STORES = LkOccupationTitle(732, 7, 444120, "Paint and Wallpaper Stores")
    HARDWARE_STORES = LkOccupationTitle(733, 7, 444130, "Hardware Stores")
    OTHER_BUILDING_MATERIAL_DEALERS = LkOccupationTitle(
        734, 7, 444190, "Other Building Material Dealers"
    )
    LAWN_AND_GARDEN_EQUIPMENT_AND_SUPPLIES_STORES = LkOccupationTitle(
        735, 7, 4442, "Lawn and Garden Equipment and Supplies Stores"
    )
    OUTDOOR_POWER_EQUIPMENT_STORES = LkOccupationTitle(
        736, 7, 444210, "Outdoor Power Equipment Stores"
    )
    NURSERY_GARDEN_CENTER_AND_FARM_SUPPLY_STORES = LkOccupationTitle(
        737, 7, 444220, "Nursery, Garden Center, and Farm Supply Stores"
    )
    GROCERY_STORES = LkOccupationTitle(738, 7, 4451, "Grocery Stores")
    SUPERMARKETS_AND_OTHER_GROCERY_EXCEPT_CONVENIENCE_STORES = LkOccupationTitle(
        739, 7, 445110, "Supermarkets and Other Grocery (except Convenience) Stores"
    )
    CONVENIENCE_STORES = LkOccupationTitle(740, 7, 445120, "Convenience Stores")
    SPECIALTY_FOOD_STORES = LkOccupationTitle(741, 7, 4452, "Specialty Food Stores")
    MEAT_MARKETS = LkOccupationTitle(742, 7, 445210, "Meat Markets")
    FISH_AND_SEAFOOD_MARKETS = LkOccupationTitle(743, 7, 445220, "Fish and Seafood Markets")
    FRUIT_AND_VEGETABLE_MARKETS = LkOccupationTitle(744, 7, 445230, "Fruit and Vegetable Markets")
    BAKED_GOODS_STORES = LkOccupationTitle(745, 7, 445291, "Baked Goods Stores")
    CONFECTIONERY_AND_NUT_STORES = LkOccupationTitle(746, 7, 445292, "Confectionery and Nut Stores")
    ALL_OTHER_SPECIALTY_FOOD_STORES = LkOccupationTitle(
        747, 7, 445299, "All Other Specialty Food Stores"
    )
    BEER_WINE_AND_LIQUOR_STORES_4 = LkOccupationTitle(748, 7, 4453, "Beer, Wine, and Liquor Stores")
    BEER_WINE_AND_LIQUOR_STORES = LkOccupationTitle(749, 7, 445310, "Beer, Wine, and Liquor Stores")
    HEALTH_AND_PERSONAL_CARE_STORES = LkOccupationTitle(
        750, 7, 4461, "Health and Personal Care Stores"
    )
    PHARMACIES_AND_DRUG_STORES = LkOccupationTitle(751, 7, 446110, "Pharmacies and Drug Stores")
    COSMETICS_BEAUTY_SUPPLIES_AND_PERFUME_STORES = LkOccupationTitle(
        752, 7, 446120, "Cosmetics, Beauty Supplies, and Perfume Stores"
    )
    OPTICAL_GOODS_STORES = LkOccupationTitle(753, 7, 446130, "Optical Goods Stores")
    FOOD_HEALTH_SUPPLEMENT_STORES = LkOccupationTitle(
        754, 7, 446191, "Food (Health) Supplement Stores"
    )
    ALL_OTHER_HEALTH_AND_PERSONAL_CARE_STORES = LkOccupationTitle(
        755, 7, 446199, "All Other Health and Personal Care Stores"
    )
    GASOLINE_STATIONS = LkOccupationTitle(756, 7, 4471, "Gasoline Stations")
    GASOLINE_STATIONS_WITH_CONVENIENCE_STORES = LkOccupationTitle(
        757, 7, 447110, "Gasoline Stations with Convenience Stores"
    )
    OTHER_GASOLINE_STATIONS = LkOccupationTitle(758, 7, 447190, "Other Gasoline Stations")
    CLOTHING_STORES = LkOccupationTitle(759, 7, 4481, "Clothing Stores")
    MEN_S_CLOTHING_STORES = LkOccupationTitle(760, 7, 448110, "Men's Clothing Stores")
    WOMEN_S_CLOTHING_STORES = LkOccupationTitle(761, 7, 448120, "Women's Clothing Stores")
    CHILDREN_S_AND_INFANTS_CLOTHING_STORES = LkOccupationTitle(
        762, 7, 448130, "Children's and Infants' Clothing Stores"
    )
    FAMILY_CLOTHING_STORES = LkOccupationTitle(763, 7, 448140, "Family Clothing Stores")
    CLOTHING_ACCESSORIES_STORES = LkOccupationTitle(764, 7, 448150, "Clothing Accessories Stores")
    OTHER_CLOTHING_STORES = LkOccupationTitle(765, 7, 448190, "Other Clothing Stores")
    SHOE_STORES_4 = LkOccupationTitle(766, 7, 4482, "Shoe Stores")
    SHOE_STORES = LkOccupationTitle(767, 7, 448210, "Shoe Stores")
    JEWELRY_LUGGAGE_AND_LEATHER_GOODS_STORES = LkOccupationTitle(
        768, 7, 4483, "Jewelry, Luggage, and Leather Goods Stores"
    )
    JEWELRY_STORES = LkOccupationTitle(769, 7, 448310, "Jewelry Stores")
    LUGGAGE_AND_LEATHER_GOODS_STORES = LkOccupationTitle(
        770, 7, 448320, "Luggage and Leather Goods Stores"
    )
    SPORTING_GOODS_HOBBY_AND_MUSICAL_INSTRUMENT_STORES = LkOccupationTitle(
        771, 7, 4511, "Sporting Goods, Hobby, and Musical Instrument Stores"
    )
    SPORTING_GOODS_STORES = LkOccupationTitle(772, 7, 451110, "Sporting Goods Stores")
    HOBBY_TOY_AND_GAME_STORES = LkOccupationTitle(773, 7, 451120, "Hobby, Toy, and Game Stores")
    SEWING_NEEDLEWORK_AND_PIECE_GOODS_STORES = LkOccupationTitle(
        774, 7, 451130, "Sewing, Needlework, and Piece Goods Stores"
    )
    MUSICAL_INSTRUMENT_AND_SUPPLIES_STORES = LkOccupationTitle(
        775, 7, 451140, "Musical Instrument and Supplies Stores"
    )
    BOOK_STORES_AND_NEWS_DEALERS = LkOccupationTitle(776, 7, 4512, "Book Stores and News Dealers")
    BOOK_STORES = LkOccupationTitle(777, 7, 451211, "Book Stores")
    NEWS_DEALERS_AND_NEWSSTANDS = LkOccupationTitle(778, 7, 451212, "News Dealers and Newsstands")
    DEPARTMENT_STORES_4 = LkOccupationTitle(779, 7, 4522, "Department Stores")
    DEPARTMENT_STORES = LkOccupationTitle(780, 7, 452210, "Department Stores")
    GENERAL_MERCHANDISE_STORES_INCLUDING_WAREHOUSE_CLUBS_AND_SUPERCENTERS = LkOccupationTitle(
        781, 7, 4523, "General Merchandise Stores, including Warehouse Clubs and Supercenters"
    )
    WAREHOUSE_CLUBS_AND_SUPERCENTERS = LkOccupationTitle(
        782, 7, 452311, "Warehouse Clubs and Supercenters"
    )
    ALL_OTHER_GENERAL_MERCHANDISE_STORES = LkOccupationTitle(
        783, 7, 452319, "All Other General Merchandise Stores"
    )
    FLORISTS_4 = LkOccupationTitle(784, 7, 4531, "Florists")
    FLORISTS = LkOccupationTitle(785, 7, 453110, "Florists")
    OFFICE_SUPPLIES_STATIONERY_AND_GIFT_STORES = LkOccupationTitle(
        786, 7, 4532, "Office Supplies, Stationery, and Gift Stores"
    )
    OFFICE_SUPPLIES_AND_STATIONERY_STORES = LkOccupationTitle(
        787, 7, 453210, "Office Supplies and Stationery Stores"
    )
    GIFT_NOVELTY_AND_SOUVENIR_STORES = LkOccupationTitle(
        788, 7, 453220, "Gift, Novelty, and Souvenir Stores"
    )
    USED_MERCHANDISE_STORES_4 = LkOccupationTitle(789, 7, 4533, "Used Merchandise Stores")
    USED_MERCHANDISE_STORES = LkOccupationTitle(790, 7, 453310, "Used Merchandise Stores")
    OTHER_MISCELLANEOUS_STORE_RETAILERS = LkOccupationTitle(
        791, 7, 4539, "Other Miscellaneous Store Retailers"
    )
    PET_AND_PET_SUPPLIES_STORES = LkOccupationTitle(792, 7, 453910, "Pet and Pet Supplies Stores")
    ART_DEALERS = LkOccupationTitle(793, 7, 453920, "Art Dealers")
    MANUFACTURED_MOBILE_HOME_DEALERS = LkOccupationTitle(
        794, 7, 453930, "Manufactured (Mobile) Home Dealers"
    )
    TOBACCO_STORES = LkOccupationTitle(795, 7, 453991, "Tobacco Stores")
    ALL_OTHER_MISCELLANEOUS_STORE_RETAILERS_EXCEPT_TOBACCO_STORES = LkOccupationTitle(
        796, 7, 453998, "All Other Miscellaneous Store Retailers (except Tobacco Stores)"
    )
    ELECTRONIC_SHOPPING_AND_MAIL_ORDER_HOUSES_4 = LkOccupationTitle(
        797, 7, 4541, "Electronic Shopping and Mail-Order Houses"
    )
    ELECTRONIC_SHOPPING_AND_MAIL_ORDER_HOUSES = LkOccupationTitle(
        798, 7, 454110, "Electronic Shopping and Mail-Order Houses"
    )
    VENDING_MACHINE_OPERATORS_4 = LkOccupationTitle(799, 7, 4542, "Vending Machine Operators")
    VENDING_MACHINE_OPERATORS = LkOccupationTitle(800, 7, 454210, "Vending Machine Operators")
    DIRECT_SELLING_ESTABLISHMENTS = LkOccupationTitle(801, 7, 4543, "Direct Selling Establishments")
    FUEL_DEALERS = LkOccupationTitle(802, 7, 454310, "Fuel Dealers")
    OTHER_DIRECT_SELLING_ESTABLISHMENTS = LkOccupationTitle(
        803, 7, 454390, "Other Direct Selling Establishments"
    )
    SCHEDULED_AIR_TRANSPORTATION = LkOccupationTitle(804, 8, 4811, "Scheduled Air Transportation")
    SCHEDULED_PASSENGER_AIR_TRANSPORTATION = LkOccupationTitle(
        805, 8, 481111, "Scheduled Passenger Air Transportation"
    )
    SCHEDULED_FREIGHT_AIR_TRANSPORTATION = LkOccupationTitle(
        806, 8, 481112, "Scheduled Freight Air Transportation"
    )
    NONSCHEDULED_AIR_TRANSPORTATION = LkOccupationTitle(
        807, 8, 4812, "Nonscheduled Air Transportation"
    )
    NONSCHEDULED_CHARTERED_PASSENGER_AIR_TRANSPORTATION = LkOccupationTitle(
        808, 8, 481211, "Nonscheduled Chartered Passenger Air Transportation"
    )
    NONSCHEDULED_CHARTERED_FREIGHT_AIR_TRANSPORTATION = LkOccupationTitle(
        809, 8, 481212, "Nonscheduled Chartered Freight Air Transportation"
    )
    OTHER_NONSCHEDULED_AIR_TRANSPORTATION = LkOccupationTitle(
        810, 8, 481219, "Other Nonscheduled Air Transportation"
    )
    RAIL_TRANSPORTATION = LkOccupationTitle(811, 8, 4821, "Rail Transportation")
    LINE_HAUL_RAILROADS = LkOccupationTitle(812, 8, 482111, "Line-Haul Railroads")
    SHORT_LINE_RAILROADS = LkOccupationTitle(813, 8, 482112, "Short Line Railroads")
    DEEP_SEA_COASTAL_AND_GREAT_LAKES_WATER_TRANSPORTATION = LkOccupationTitle(
        814, 8, 4831, "Deep Sea, Coastal, and Great Lakes Water Transportation"
    )
    DEEP_SEA_FREIGHT_TRANSPORTATION = LkOccupationTitle(
        815, 8, 483111, "Deep Sea Freight Transportation"
    )
    DEEP_SEA_PASSENGER_TRANSPORTATION = LkOccupationTitle(
        816, 8, 483112, "Deep Sea Passenger Transportation"
    )
    COASTAL_AND_GREAT_LAKES_FREIGHT_TRANSPORTATION = LkOccupationTitle(
        817, 8, 483113, "Coastal and Great Lakes Freight Transportation"
    )
    COASTAL_AND_GREAT_LAKES_PASSENGER_TRANSPORTATION = LkOccupationTitle(
        818, 8, 483114, "Coastal and Great Lakes Passenger Transportation"
    )
    INLAND_WATER_TRANSPORTATION = LkOccupationTitle(819, 8, 4832, "Inland Water Transportation")
    INLAND_WATER_FREIGHT_TRANSPORTATION = LkOccupationTitle(
        820, 8, 483211, "Inland Water Freight Transportation"
    )
    INLAND_WATER_PASSENGER_TRANSPORTATION = LkOccupationTitle(
        821, 8, 483212, "Inland Water Passenger Transportation"
    )
    GENERAL_FREIGHT_TRUCKING = LkOccupationTitle(822, 8, 4841, "General Freight Trucking")
    GENERAL_FREIGHT_TRUCKING_LOCAL = LkOccupationTitle(
        823, 8, 484110, "General Freight Trucking, Local"
    )
    GENERAL_FREIGHT_TRUCKING_LONG_DISTANCE_TRUCKLOAD = LkOccupationTitle(
        824, 8, 484121, "General Freight Trucking, Long-Distance, Truckload"
    )
    GENERAL_FREIGHT_TRUCKING_LONG_DISTANCE_LESS_THAN_TRUCKLOAD = LkOccupationTitle(
        825, 8, 484122, "General Freight Trucking, Long-Distance, Less Than Truckload"
    )
    SPECIALIZED_FREIGHT_TRUCKING = LkOccupationTitle(826, 8, 4842, "Specialized Freight Trucking")
    USED_HOUSEHOLD_AND_OFFICE_GOODS_MOVING = LkOccupationTitle(
        827, 8, 484210, "Used Household and Office Goods Moving"
    )
    SPECIALIZED_FREIGHT_EXCEPT_USED_GOODS_TRUCKING_LOCAL = LkOccupationTitle(
        828, 8, 484220, "Specialized Freight (except Used Goods) Trucking, Local"
    )
    SPECIALIZED_FREIGHT_EXCEPT_USED_GOODS_TRUCKING_LONG_DISTANCE = LkOccupationTitle(
        829, 8, 484230, "Specialized Freight (except Used Goods) Trucking, Long-Distance"
    )
    URBAN_TRANSIT_SYSTEMS = LkOccupationTitle(830, 8, 4851, "Urban Transit Systems")
    MIXED_MODE_TRANSIT_SYSTEMS = LkOccupationTitle(831, 8, 485111, "Mixed Mode Transit Systems")
    COMMUTER_RAIL_SYSTEMS = LkOccupationTitle(832, 8, 485112, "Commuter Rail Systems")
    BUS_AND_OTHER_MOTOR_VEHICLE_TRANSIT_SYSTEMS = LkOccupationTitle(
        833, 8, 485113, "Bus and Other Motor Vehicle Transit Systems"
    )
    OTHER_URBAN_TRANSIT_SYSTEMS = LkOccupationTitle(834, 8, 485119, "Other Urban Transit Systems")
    INTERURBAN_AND_RURAL_BUS_TRANSPORTATION_4 = LkOccupationTitle(
        835, 8, 4852, "Interurban and Rural Bus Transportation"
    )
    INTERURBAN_AND_RURAL_BUS_TRANSPORTATION = LkOccupationTitle(
        836, 8, 485210, "Interurban and Rural Bus Transportation"
    )
    TAXI_AND_LIMOUSINE_SERVICE = LkOccupationTitle(837, 8, 4853, "Taxi and Limousine Service")
    TAXI_SERVICE = LkOccupationTitle(838, 8, 485310, "Taxi Service")
    LIMOUSINE_SERVICE = LkOccupationTitle(839, 8, 485320, "Limousine Service")
    SCHOOL_AND_EMPLOYEE_BUS_TRANSPORTATION_4 = LkOccupationTitle(
        840, 8, 4854, "School and Employee Bus Transportation"
    )
    SCHOOL_AND_EMPLOYEE_BUS_TRANSPORTATION = LkOccupationTitle(
        841, 8, 485410, "School and Employee Bus Transportation"
    )
    CHARTER_BUS_INDUSTRY_4 = LkOccupationTitle(842, 8, 4855, "Charter Bus Industry")
    CHARTER_BUS_INDUSTRY = LkOccupationTitle(843, 8, 485510, "Charter Bus Industry")
    OTHER_TRANSIT_AND_GROUND_PASSENGER_TRANSPORTATION = LkOccupationTitle(
        844, 8, 4859, "Other Transit and Ground Passenger Transportation"
    )
    SPECIAL_NEEDS_TRANSPORTATION = LkOccupationTitle(845, 8, 485991, "Special Needs Transportation")
    ALL_OTHER_TRANSIT_AND_GROUND_PASSENGER_TRANSPORTATION = LkOccupationTitle(
        846, 8, 485999, "All Other Transit and Ground Passenger Transportation"
    )
    PIPELINE_TRANSPORTATION_OF_CRUDE_OIL_4 = LkOccupationTitle(
        847, 8, 4861, "Pipeline Transportation of Crude Oil"
    )
    PIPELINE_TRANSPORTATION_OF_CRUDE_OIL = LkOccupationTitle(
        848, 8, 486110, "Pipeline Transportation of Crude Oil"
    )
    PIPELINE_TRANSPORTATION_OF_NATURAL_GAS_4 = LkOccupationTitle(
        849, 8, 4862, "Pipeline Transportation of Natural Gas"
    )
    PIPELINE_TRANSPORTATION_OF_NATURAL_GAS = LkOccupationTitle(
        850, 8, 486210, "Pipeline Transportation of Natural Gas"
    )
    OTHER_PIPELINE_TRANSPORTATION = LkOccupationTitle(851, 8, 4869, "Other Pipeline Transportation")
    PIPELINE_TRANSPORTATION_OF_REFINED_PETROLEUM_PRODUCTS = LkOccupationTitle(
        852, 8, 486910, "Pipeline Transportation of Refined Petroleum Products"
    )
    ALL_OTHER_PIPELINE_TRANSPORTATION = LkOccupationTitle(
        853, 8, 486990, "All Other Pipeline Transportation"
    )
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_LAND_4 = LkOccupationTitle(
        854, 8, 4871, "Scenic and Sightseeing Transportation, Land"
    )
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_LAND = LkOccupationTitle(
        855, 8, 487110, "Scenic and Sightseeing Transportation, Land"
    )
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_WATER_4 = LkOccupationTitle(
        856, 8, 4872, "Scenic and Sightseeing Transportation, Water"
    )
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_WATER = LkOccupationTitle(
        857, 8, 487210, "Scenic and Sightseeing Transportation, Water"
    )
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_OTHER_4 = LkOccupationTitle(
        858, 8, 4879, "Scenic and Sightseeing Transportation, Other"
    )
    SCENIC_AND_SIGHTSEEING_TRANSPORTATION_OTHER = LkOccupationTitle(
        859, 8, 487990, "Scenic and Sightseeing Transportation, Other"
    )
    SUPPORT_ACTIVITIES_FOR_AIR_TRANSPORTATION = LkOccupationTitle(
        860, 8, 4881, "Support Activities for Air Transportation"
    )
    AIR_TRAFFIC_CONTROL = LkOccupationTitle(861, 8, 488111, "Air Traffic Control")
    OTHER_AIRPORT_OPERATIONS = LkOccupationTitle(862, 8, 488119, "Other Airport Operations")
    OTHER_SUPPORT_ACTIVITIES_FOR_AIR_TRANSPORTATION = LkOccupationTitle(
        863, 8, 488190, "Other Support Activities for Air Transportation"
    )
    SUPPORT_ACTIVITIES_FOR_RAIL_TRANSPORTATION_4 = LkOccupationTitle(
        864, 8, 4882, "Support Activities for Rail Transportation"
    )
    SUPPORT_ACTIVITIES_FOR_RAIL_TRANSPORTATION = LkOccupationTitle(
        865, 8, 488210, "Support Activities for Rail Transportation"
    )
    SUPPORT_ACTIVITIES_FOR_WATER_TRANSPORTATION = LkOccupationTitle(
        866, 8, 4883, "Support Activities for Water Transportation"
    )
    PORT_AND_HARBOR_OPERATIONS = LkOccupationTitle(867, 8, 488310, "Port and Harbor Operations")
    MARINE_CARGO_HANDLING = LkOccupationTitle(868, 8, 488320, "Marine Cargo Handling")
    NAVIGATIONAL_SERVICES_TO_SHIPPING = LkOccupationTitle(
        869, 8, 488330, "Navigational Services to Shipping"
    )
    OTHER_SUPPORT_ACTIVITIES_FOR_WATER_TRANSPORTATION = LkOccupationTitle(
        870, 8, 488390, "Other Support Activities for Water Transportation"
    )
    SUPPORT_ACTIVITIES_FOR_ROAD_TRANSPORTATION = LkOccupationTitle(
        871, 8, 4884, "Support Activities for Road Transportation"
    )
    MOTOR_VEHICLE_TOWING = LkOccupationTitle(872, 8, 488410, "Motor Vehicle Towing")
    OTHER_SUPPORT_ACTIVITIES_FOR_ROAD_TRANSPORTATION = LkOccupationTitle(
        873, 8, 488490, "Other Support Activities for Road Transportation"
    )
    FREIGHT_TRANSPORTATION_ARRANGEMENT_4 = LkOccupationTitle(
        874, 8, 4885, "Freight Transportation Arrangement"
    )
    FREIGHT_TRANSPORTATION_ARRANGEMENT = LkOccupationTitle(
        875, 8, 488510, "Freight Transportation Arrangement"
    )
    OTHER_SUPPORT_ACTIVITIES_FOR_TRANSPORTATION = LkOccupationTitle(
        876, 8, 4889, "Other Support Activities for Transportation"
    )
    PACKING_AND_CRATING = LkOccupationTitle(877, 8, 488991, "Packing and Crating")
    ALL_OTHER_SUPPORT_ACTIVITIES_FOR_TRANSPORTATION = LkOccupationTitle(
        878, 8, 488999, "All Other Support Activities for Transportation"
    )
    POSTAL_SERVICE_4 = LkOccupationTitle(879, 8, 4911, "Postal Service")
    POSTAL_SERVICE = LkOccupationTitle(880, 8, 491110, "Postal Service")
    COURIERS_AND_EXPRESS_DELIVERY_SERVICES_4 = LkOccupationTitle(
        881, 8, 4921, "Couriers and Express Delivery Services"
    )
    COURIERS_AND_EXPRESS_DELIVERY_SERVICES = LkOccupationTitle(
        882, 8, 492110, "Couriers and Express Delivery Services"
    )
    LOCAL_MESSENGERS_AND_LOCAL_DELIVERY_4 = LkOccupationTitle(
        883, 8, 4922, "Local Messengers and Local Delivery"
    )
    LOCAL_MESSENGERS_AND_LOCAL_DELIVERY = LkOccupationTitle(
        884, 8, 492210, "Local Messengers and Local Delivery"
    )
    WAREHOUSING_AND_STORAGE = LkOccupationTitle(885, 8, 4931, "Warehousing and Storage")
    GENERAL_WAREHOUSING_AND_STORAGE = LkOccupationTitle(
        886, 8, 493110, "General Warehousing and Storage"
    )
    REFRIGERATED_WAREHOUSING_AND_STORAGE = LkOccupationTitle(
        887, 8, 493120, "Refrigerated Warehousing and Storage"
    )
    FARM_PRODUCT_WAREHOUSING_AND_STORAGE = LkOccupationTitle(
        888, 8, 493130, "Farm Product Warehousing and Storage"
    )
    OTHER_WAREHOUSING_AND_STORAGE = LkOccupationTitle(
        889, 8, 493190, "Other Warehousing and Storage"
    )
    NEWSPAPER_PERIODICAL_BOOK_AND_DIRECTORY_PUBLISHERS = LkOccupationTitle(
        890, 9, 5111, "Newspaper, Periodical, Book, and Directory Publishers"
    )
    NEWSPAPER_PUBLISHERS = LkOccupationTitle(891, 9, 511110, "Newspaper Publishers")
    PERIODICAL_PUBLISHERS = LkOccupationTitle(892, 9, 511120, "Periodical Publishers")
    BOOK_PUBLISHERS = LkOccupationTitle(893, 9, 511130, "Book Publishers")
    DIRECTORY_AND_MAILING_LIST_PUBLISHERS = LkOccupationTitle(
        894, 9, 511140, "Directory and Mailing List Publishers"
    )
    GREETING_CARD_PUBLISHERS = LkOccupationTitle(895, 9, 511191, "Greeting Card Publishers")
    ALL_OTHER_PUBLISHERS = LkOccupationTitle(896, 9, 511199, "All Other Publishers")
    SOFTWARE_PUBLISHERS_4 = LkOccupationTitle(897, 9, 5112, "Software Publishers")
    SOFTWARE_PUBLISHERS = LkOccupationTitle(898, 9, 511210, "Software Publishers")
    MOTION_PICTURE_AND_VIDEO_INDUSTRIES = LkOccupationTitle(
        899, 9, 5121, "Motion Picture and Video Industries"
    )
    MOTION_PICTURE_AND_VIDEO_PRODUCTION = LkOccupationTitle(
        900, 9, 512110, "Motion Picture and Video Production"
    )
    MOTION_PICTURE_AND_VIDEO_DISTRIBUTION = LkOccupationTitle(
        901, 9, 512120, "Motion Picture and Video Distribution"
    )
    MOTION_PICTURE_THEATERS_EXCEPT_DRIVE_INS = LkOccupationTitle(
        902, 9, 512131, "Motion Picture Theaters (except Drive-Ins)"
    )
    DRIVE_IN_MOTION_PICTURE_THEATERS = LkOccupationTitle(
        903, 9, 512132, "Drive-In Motion Picture Theaters"
    )
    TELEPRODUCTION_AND_OTHER_POSTPRODUCTION_SERVICES = LkOccupationTitle(
        904, 9, 512191, "Teleproduction and Other Postproduction Services"
    )
    OTHER_MOTION_PICTURE_AND_VIDEO_INDUSTRIES = LkOccupationTitle(
        905, 9, 512199, "Other Motion Picture and Video Industries"
    )
    SOUND_RECORDING_INDUSTRIES = LkOccupationTitle(906, 9, 5122, "Sound Recording Industries")
    MUSIC_PUBLISHERS = LkOccupationTitle(907, 9, 512230, "Music Publishers")
    SOUND_RECORDING_STUDIOS = LkOccupationTitle(908, 9, 512240, "Sound Recording Studios")
    RECORD_PRODUCTION_AND_DISTRIBUTION = LkOccupationTitle(
        909, 9, 512250, "Record Production and Distribution"
    )
    OTHER_SOUND_RECORDING_INDUSTRIES = LkOccupationTitle(
        910, 9, 512290, "Other Sound Recording Industries"
    )
    RADIO_AND_TELEVISION_BROADCASTING = LkOccupationTitle(
        911, 9, 5151, "Radio and Television Broadcasting"
    )
    RADIO_NETWORKS = LkOccupationTitle(912, 9, 515111, "Radio Networks")
    RADIO_STATIONS = LkOccupationTitle(913, 9, 515112, "Radio Stations")
    TELEVISION_BROADCASTING = LkOccupationTitle(914, 9, 515120, "Television Broadcasting")
    CABLE_AND_OTHER_SUBSCRIPTION_PROGRAMMING_4 = LkOccupationTitle(
        915, 9, 5152, "Cable and Other Subscription Programming"
    )
    CABLE_AND_OTHER_SUBSCRIPTION_PROGRAMMING = LkOccupationTitle(
        916, 9, 515210, "Cable and Other Subscription Programming"
    )
    WIRED_AND_WIRELESS_TELECOMMUNICATIONS_CARRIERS = LkOccupationTitle(
        917, 9, 5173, "Wired and Wireless Telecommunications Carriers"
    )
    WIRED_TELECOMMUNICATIONS_CARRIERS = LkOccupationTitle(
        918, 9, 517311, "Wired Telecommunications Carriers"
    )
    WIRELESS_TELECOMMUNICATIONS_CARRIERS_EXCEPT_SATELLITE = LkOccupationTitle(
        919, 9, 517312, "Wireless Telecommunications Carriers (except Satellite)"
    )
    SATELLITE_TELECOMMUNICATIONS_4 = LkOccupationTitle(920, 9, 5174, "Satellite Telecommunications")
    SATELLITE_TELECOMMUNICATIONS = LkOccupationTitle(921, 9, 517410, "Satellite Telecommunications")
    OTHER_TELECOMMUNICATIONS = LkOccupationTitle(922, 9, 5179, "Other Telecommunications")
    TELECOMMUNICATIONS_RESELLERS = LkOccupationTitle(923, 9, 517911, "Telecommunications Resellers")
    ALL_OTHER_TELECOMMUNICATIONS = LkOccupationTitle(924, 9, 517919, "All Other Telecommunications")
    DATA_PROCESSING_HOSTING_AND_RELATED_SERVICES_4 = LkOccupationTitle(
        925, 9, 5182, "Data Processing, Hosting, and Related Services"
    )
    DATA_PROCESSING_HOSTING_AND_RELATED_SERVICES = LkOccupationTitle(
        926, 9, 518210, "Data Processing, Hosting, and Related Services"
    )
    OTHER_INFORMATION_SERVICES = LkOccupationTitle(927, 9, 5191, "Other Information Services")
    NEWS_SYNDICATES = LkOccupationTitle(928, 9, 519110, "News Syndicates")
    LIBRARIES_AND_ARCHIVES = LkOccupationTitle(929, 9, 519120, "Libraries and Archives")
    INTERNET_PUBLISHING_AND_BROADCASTING_AND_WEB_SEARCH_PORTALS = LkOccupationTitle(
        930, 9, 519130, "Internet Publishing and Broadcasting and Web Search Portals"
    )
    ALL_OTHER_INFORMATION_SERVICES = LkOccupationTitle(
        931, 9, 519190, "All Other Information Services"
    )
    MONETARY_AUTHORITIES_CENTRAL_BANK_4 = LkOccupationTitle(
        932, 10, 5211, "Monetary Authorities-Central Bank"
    )
    MONETARY_AUTHORITIES_CENTRAL_BANK = LkOccupationTitle(
        933, 10, 521110, "Monetary Authorities-Central Bank"
    )
    DEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(
        934, 10, 5221, "Depository Credit Intermediation"
    )
    COMMERCIAL_BANKING = LkOccupationTitle(935, 10, 522110, "Commercial Banking")
    SAVINGS_INSTITUTIONS = LkOccupationTitle(936, 10, 522120, "Savings Institutions")
    CREDIT_UNIONS = LkOccupationTitle(937, 10, 522130, "Credit Unions")
    OTHER_DEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(
        938, 10, 522190, "Other Depository Credit Intermediation"
    )
    NONDEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(
        939, 10, 5222, "Nondepository Credit Intermediation"
    )
    CREDIT_CARD_ISSUING = LkOccupationTitle(940, 10, 522210, "Credit Card Issuing")
    SALES_FINANCING = LkOccupationTitle(941, 10, 522220, "Sales Financing")
    CONSUMER_LENDING = LkOccupationTitle(942, 10, 522291, "Consumer Lending")
    REAL_ESTATE_CREDIT = LkOccupationTitle(943, 10, 522292, "Real Estate Credit")
    INTERNATIONAL_TRADE_FINANCING = LkOccupationTitle(
        944, 10, 522293, "International Trade Financing"
    )
    SECONDARY_MARKET_FINANCING = LkOccupationTitle(945, 10, 522294, "Secondary Market Financing")
    ALL_OTHER_NONDEPOSITORY_CREDIT_INTERMEDIATION = LkOccupationTitle(
        946, 10, 522298, "All Other Nondepository Credit Intermediation"
    )
    ACTIVITIES_RELATED_TO_CREDIT_INTERMEDIATION = LkOccupationTitle(
        947, 10, 5223, "Activities Related to Credit Intermediation"
    )
    MORTGAGE_AND_NONMORTGAGE_LOAN_BROKERS = LkOccupationTitle(
        948, 10, 522310, "Mortgage and Nonmortgage Loan Brokers"
    )
    FINANCIAL_TRANSACTIONS_PROCESSING_RESERVE_AND_CLEARINGHOUSE_ACTIVITIES = LkOccupationTitle(
        949, 10, 522320, "Financial Transactions Processing, Reserve, and Clearinghouse Activities"
    )
    OTHER_ACTIVITIES_RELATED_TO_CREDIT_INTERMEDIATION = LkOccupationTitle(
        950, 10, 522390, "Other Activities Related to Credit Intermediation"
    )
    SECURITIES_AND_COMMODITY_CONTRACTS_INTERMEDIATION_AND_BROKERAGE = LkOccupationTitle(
        951, 10, 5231, "Securities and Commodity Contracts Intermediation and Brokerage"
    )
    INVESTMENT_BANKING_AND_SECURITIES_DEALING = LkOccupationTitle(
        952, 10, 523110, "Investment Banking and Securities Dealing"
    )
    SECURITIES_BROKERAGE = LkOccupationTitle(953, 10, 523120, "Securities Brokerage")
    COMMODITY_CONTRACTS_DEALING = LkOccupationTitle(954, 10, 523130, "Commodity Contracts Dealing")
    COMMODITY_CONTRACTS_BROKERAGE = LkOccupationTitle(
        955, 10, 523140, "Commodity Contracts Brokerage"
    )
    SECURITIES_AND_COMMODITY_EXCHANGES_4 = LkOccupationTitle(
        956, 10, 5232, "Securities and Commodity Exchanges"
    )
    SECURITIES_AND_COMMODITY_EXCHANGES = LkOccupationTitle(
        957, 10, 523210, "Securities and Commodity Exchanges"
    )
    OTHER_FINANCIAL_INVESTMENT_ACTIVITIES = LkOccupationTitle(
        958, 10, 5239, "Other Financial Investment Activities"
    )
    MISCELLANEOUS_INTERMEDIATION = LkOccupationTitle(
        959, 10, 523910, "Miscellaneous Intermediation"
    )
    PORTFOLIO_MANAGEMENT = LkOccupationTitle(960, 10, 523920, "Portfolio Management")
    INVESTMENT_ADVICE = LkOccupationTitle(961, 10, 523930, "Investment Advice")
    TRUST_FIDUCIARY_AND_CUSTODY_ACTIVITIES = LkOccupationTitle(
        962, 10, 523991, "Trust, Fiduciary, and Custody Activities"
    )
    MISCELLANEOUS_FINANCIAL_INVESTMENT_ACTIVITIES = LkOccupationTitle(
        963, 10, 523999, "Miscellaneous Financial Investment Activities"
    )
    INSURANCE_CARRIERS = LkOccupationTitle(964, 10, 5241, "Insurance Carriers")
    DIRECT_LIFE_INSURANCE_CARRIERS = LkOccupationTitle(
        965, 10, 524113, "Direct Life Insurance Carriers"
    )
    DIRECT_HEALTH_AND_MEDICAL_INSURANCE_CARRIERS = LkOccupationTitle(
        966, 10, 524114, "Direct Health and Medical Insurance Carriers"
    )
    DIRECT_PROPERTY_AND_CASUALTY_INSURANCE_CARRIERS = LkOccupationTitle(
        967, 10, 524126, "Direct Property and Casualty Insurance Carriers"
    )
    DIRECT_TITLE_INSURANCE_CARRIERS = LkOccupationTitle(
        968, 10, 524127, "Direct Title Insurance Carriers"
    )
    OTHER_DIRECT_INSURANCE_EXCEPT_LIFE_HEALTH_AND_MEDICAL_CARRIERS = LkOccupationTitle(
        969, 10, 524128, "Other Direct Insurance (except Life, Health, and Medical) Carriers"
    )
    REINSURANCE_CARRIERS = LkOccupationTitle(970, 10, 524130, "Reinsurance Carriers")
    AGENCIES_BROKERAGES_AND_OTHER_INSURANCE_RELATED_ACTIVITIES = LkOccupationTitle(
        971, 10, 5242, "Agencies, Brokerages, and Other Insurance Related Activities"
    )
    INSURANCE_AGENCIES_AND_BROKERAGES = LkOccupationTitle(
        972, 10, 524210, "Insurance Agencies and Brokerages"
    )
    CLAIMS_ADJUSTING = LkOccupationTitle(973, 10, 524291, "Claims Adjusting")
    THIRD_PARTY_ADMINISTRATION_OF_INSURANCE_AND_PENSION_FUNDS = LkOccupationTitle(
        974, 10, 524292, "Third Party Administration of Insurance and Pension Funds"
    )
    ALL_OTHER_INSURANCE_RELATED_ACTIVITIES = LkOccupationTitle(
        975, 10, 524298, "All Other Insurance Related Activities"
    )
    INSURANCE_AND_EMPLOYEE_BENEFIT_FUNDS = LkOccupationTitle(
        976, 10, 5251, "Insurance and Employee Benefit Funds"
    )
    PENSION_FUNDS = LkOccupationTitle(977, 10, 525110, "Pension Funds")
    HEALTH_AND_WELFARE_FUNDS = LkOccupationTitle(978, 10, 525120, "Health and Welfare Funds")
    OTHER_INSURANCE_FUNDS = LkOccupationTitle(979, 10, 525190, "Other Insurance Funds")
    OTHER_INVESTMENT_POOLS_AND_FUNDS = LkOccupationTitle(
        980, 10, 5259, "Other Investment Pools and Funds"
    )
    OPEN_END_INVESTMENT_FUNDS = LkOccupationTitle(981, 10, 525910, "Open-End Investment Funds")
    TRUSTS_ESTATES_AND_AGENCY_ACCOUNTS = LkOccupationTitle(
        982, 10, 525920, "Trusts, Estates, and Agency Accounts"
    )
    OTHER_FINANCIAL_VEHICLES = LkOccupationTitle(983, 10, 525990, "Other Financial Vehicles")
    LESSORS_OF_REAL_ESTATE = LkOccupationTitle(984, 11, 5311, "Lessors of Real Estate")
    LESSORS_OF_RESIDENTIAL_BUILDINGS_AND_DWELLINGS = LkOccupationTitle(
        985, 11, 531110, "Lessors of Residential Buildings and Dwellings"
    )
    LESSORS_OF_NONRESIDENTIAL_BUILDINGS_EXCEPT_MINIWAREHOUSES = LkOccupationTitle(
        986, 11, 531120, "Lessors of Nonresidential Buildings (except Miniwarehouses)"
    )
    LESSORS_OF_MINIWAREHOUSES_AND_SELF_STORAGE_UNITS = LkOccupationTitle(
        987, 11, 531130, "Lessors of Miniwarehouses and Self-Storage Units"
    )
    LESSORS_OF_OTHER_REAL_ESTATE_PROPERTY = LkOccupationTitle(
        988, 11, 531190, "Lessors of Other Real Estate Property"
    )
    OFFICES_OF_REAL_ESTATE_AGENTS_AND_BROKERS_4 = LkOccupationTitle(
        989, 11, 5312, "Offices of Real Estate Agents and Brokers"
    )
    OFFICES_OF_REAL_ESTATE_AGENTS_AND_BROKERS = LkOccupationTitle(
        990, 11, 531210, "Offices of Real Estate Agents and Brokers"
    )
    ACTIVITIES_RELATED_TO_REAL_ESTATE = LkOccupationTitle(
        991, 11, 5313, "Activities Related to Real Estate"
    )
    RESIDENTIAL_PROPERTY_MANAGERS = LkOccupationTitle(
        992, 11, 531311, "Residential Property Managers"
    )
    NONRESIDENTIAL_PROPERTY_MANAGERS = LkOccupationTitle(
        993, 11, 531312, "Nonresidential Property Managers"
    )
    OFFICES_OF_REAL_ESTATE_APPRAISERS = LkOccupationTitle(
        994, 11, 531320, "Offices of Real Estate Appraisers"
    )
    OTHER_ACTIVITIES_RELATED_TO_REAL_ESTATE = LkOccupationTitle(
        995, 11, 531390, "Other Activities Related to Real Estate"
    )
    AUTOMOTIVE_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(
        996, 11, 5321, "Automotive Equipment Rental and Leasing"
    )
    PASSENGER_CAR_RENTAL = LkOccupationTitle(997, 11, 532111, "Passenger Car Rental")
    PASSENGER_CAR_LEASING = LkOccupationTitle(998, 11, 532112, "Passenger Car Leasing")
    TRUCK_UTILITY_TRAILER_AND_RV_RECREATIONAL_VEHICLE_RENTAL_AND_LEASING = LkOccupationTitle(
        999, 11, 532120, "Truck, Utility Trailer, and RV (Recreational Vehicle) Rental and Leasing"
    )
    CONSUMER_GOODS_RENTAL = LkOccupationTitle(1000, 11, 5322, "Consumer Goods Rental")
    CONSUMER_ELECTRONICS_AND_APPLIANCES_RENTAL = LkOccupationTitle(
        1001, 11, 532210, "Consumer Electronics and Appliances Rental"
    )
    FORMAL_WEAR_AND_COSTUME_RENTAL = LkOccupationTitle(
        1002, 11, 532281, "Formal Wear and Costume Rental"
    )
    VIDEO_TAPE_AND_DISC_RENTAL = LkOccupationTitle(1003, 11, 532282, "Video Tape and Disc Rental")
    HOME_HEALTH_EQUIPMENT_RENTAL = LkOccupationTitle(
        1004, 11, 532283, "Home Health Equipment Rental"
    )
    RECREATIONAL_GOODS_RENTAL = LkOccupationTitle(1005, 11, 532284, "Recreational Goods Rental")
    ALL_OTHER_CONSUMER_GOODS_RENTAL = LkOccupationTitle(
        1006, 11, 532289, "All Other Consumer Goods Rental"
    )
    GENERAL_RENTAL_CENTERS_4 = LkOccupationTitle(1007, 11, 5323, "General Rental Centers")
    GENERAL_RENTAL_CENTERS = LkOccupationTitle(1008, 11, 532310, "General Rental Centers")
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(
        1009, 11, 5324, "Commercial and Industrial Machinery and Equipment Rental and Leasing"
    )
    COMMERCIAL_AIR_RAIL_AND_WATER_TRANSPORTATION_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(
        1010,
        11,
        532411,
        "Commercial Air, Rail, and Water Transportation Equipment Rental and Leasing",
    )
    CONSTRUCTION_MINING_AND_FORESTRY_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(
        1011,
        11,
        532412,
        "Construction, Mining, and Forestry Machinery and Equipment Rental and Leasing",
    )
    OFFICE_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(
        1012, 11, 532420, "Office Machinery and Equipment Rental and Leasing"
    )
    OTHER_COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_RENTAL_AND_LEASING = LkOccupationTitle(
        1013,
        11,
        532490,
        "Other Commercial and Industrial Machinery and Equipment Rental and Leasing",
    )
    LESSORS_OF_NONFINANCIAL_INTANGIBLE_ASSETS_EXCEPT_COPYRIGHTED_WORKS_4 = LkOccupationTitle(
        1014, 11, 5331, "Lessors of Nonfinancial Intangible Assets (except Copyrighted Works)"
    )
    LESSORS_OF_NONFINANCIAL_INTANGIBLE_ASSETS_EXCEPT_COPYRIGHTED_WORKS = LkOccupationTitle(
        1015, 11, 533110, "Lessors of Nonfinancial Intangible Assets (except Copyrighted Works)"
    )
    LEGAL_SERVICES = LkOccupationTitle(1016, 12, 5411, "Legal Services")
    OFFICES_OF_LAWYERS = LkOccupationTitle(1017, 12, 541110, "Offices of Lawyers")
    OFFICES_OF_NOTARIES = LkOccupationTitle(1018, 12, 541120, "Offices of Notaries")
    TITLE_ABSTRACT_AND_SETTLEMENT_OFFICES = LkOccupationTitle(
        1019, 12, 541191, "Title Abstract and Settlement Offices"
    )
    ALL_OTHER_LEGAL_SERVICES = LkOccupationTitle(1020, 12, 541199, "All Other Legal Services")
    ACCOUNTING_TAX_PREPARATION_BOOKKEEPING_AND_PAYROLL_SERVICES = LkOccupationTitle(
        1021, 12, 5412, "Accounting, Tax Preparation, Bookkeeping, and Payroll Services"
    )
    OFFICES_OF_CERTIFIED_PUBLIC_ACCOUNTANTS = LkOccupationTitle(
        1022, 12, 541211, "Offices of Certified Public Accountants"
    )
    TAX_PREPARATION_SERVICES = LkOccupationTitle(1023, 12, 541213, "Tax Preparation Services")
    PAYROLL_SERVICES = LkOccupationTitle(1024, 12, 541214, "Payroll Services")
    OTHER_ACCOUNTING_SERVICES = LkOccupationTitle(1025, 12, 541219, "Other Accounting Services")
    ARCHITECTURAL_ENGINEERING_AND_RELATED_SERVICES = LkOccupationTitle(
        1026, 12, 5413, "Architectural, Engineering, and Related Services"
    )
    ARCHITECTURAL_SERVICES = LkOccupationTitle(1027, 12, 541310, "Architectural Services")
    LANDSCAPE_ARCHITECTURAL_SERVICES = LkOccupationTitle(
        1028, 12, 541320, "Landscape Architectural Services"
    )
    ENGINEERING_SERVICES = LkOccupationTitle(1029, 12, 541330, "Engineering Services")
    DRAFTING_SERVICES = LkOccupationTitle(1030, 12, 541340, "Drafting Services")
    BUILDING_INSPECTION_SERVICES = LkOccupationTitle(
        1031, 12, 541350, "Building Inspection Services"
    )
    GEOPHYSICAL_SURVEYING_AND_MAPPING_SERVICES = LkOccupationTitle(
        1032, 12, 541360, "Geophysical Surveying and Mapping Services"
    )
    SURVEYING_AND_MAPPING_EXCEPT_GEOPHYSICAL_SERVICES = LkOccupationTitle(
        1033, 12, 541370, "Surveying and Mapping (except Geophysical) Services"
    )
    TESTING_LABORATORIES = LkOccupationTitle(1034, 12, 541380, "Testing Laboratories")
    SPECIALIZED_DESIGN_SERVICES = LkOccupationTitle(1035, 12, 5414, "Specialized Design Services")
    INTERIOR_DESIGN_SERVICES = LkOccupationTitle(1036, 12, 541410, "Interior Design Services")
    INDUSTRIAL_DESIGN_SERVICES = LkOccupationTitle(1037, 12, 541420, "Industrial Design Services")
    GRAPHIC_DESIGN_SERVICES = LkOccupationTitle(1038, 12, 541430, "Graphic Design Services")
    OTHER_SPECIALIZED_DESIGN_SERVICES = LkOccupationTitle(
        1039, 12, 541490, "Other Specialized Design Services"
    )
    COMPUTER_SYSTEMS_DESIGN_AND_RELATED_SERVICES = LkOccupationTitle(
        1040, 12, 5415, "Computer Systems Design and Related Services"
    )
    CUSTOM_COMPUTER_PROGRAMMING_SERVICES = LkOccupationTitle(
        1041, 12, 541511, "Custom Computer Programming Services"
    )
    COMPUTER_SYSTEMS_DESIGN_SERVICES = LkOccupationTitle(
        1042, 12, 541512, "Computer Systems Design Services"
    )
    COMPUTER_FACILITIES_MANAGEMENT_SERVICES = LkOccupationTitle(
        1043, 12, 541513, "Computer Facilities Management Services"
    )
    OTHER_COMPUTER_RELATED_SERVICES = LkOccupationTitle(
        1044, 12, 541519, "Other Computer Related Services"
    )
    MANAGEMENT_SCIENTIFIC_AND_TECHNICAL_CONSULTING_SERVICES = LkOccupationTitle(
        1045, 12, 5416, "Management, Scientific, and Technical Consulting Services"
    )
    ADMINISTRATIVE_MANAGEMENT_AND_GENERAL_MANAGEMENT_CONSULTING_SERVICES = LkOccupationTitle(
        1046, 12, 541611, "Administrative Management and General Management Consulting Services"
    )
    HUMAN_RESOURCES_CONSULTING_SERVICES = LkOccupationTitle(
        1047, 12, 541612, "Human Resources Consulting Services"
    )
    MARKETING_CONSULTING_SERVICES = LkOccupationTitle(
        1048, 12, 541613, "Marketing Consulting Services"
    )
    PROCESS_PHYSICAL_DISTRIBUTION_AND_LOGISTICS_CONSULTING_SERVICES = LkOccupationTitle(
        1049, 12, 541614, "Process, Physical Distribution, and Logistics Consulting Services"
    )
    OTHER_MANAGEMENT_CONSULTING_SERVICES = LkOccupationTitle(
        1050, 12, 541618, "Other Management Consulting Services"
    )
    ENVIRONMENTAL_CONSULTING_SERVICES = LkOccupationTitle(
        1051, 12, 541620, "Environmental Consulting Services"
    )
    OTHER_SCIENTIFIC_AND_TECHNICAL_CONSULTING_SERVICES = LkOccupationTitle(
        1052, 12, 541690, "Other Scientific and Technical Consulting Services"
    )
    SCIENTIFIC_RESEARCH_AND_DEVELOPMENT_SERVICES = LkOccupationTitle(
        1053, 12, 5417, "Scientific Research and Development Services"
    )
    RESEARCH_AND_DEVELOPMENT_IN_NANOTECHNOLOGY = LkOccupationTitle(
        1054, 12, 541713, "Research and Development in Nanotechnology"
    )
    RESEARCH_AND_DEVELOPMENT_IN_BIOTECHNOLOGY_EXCEPT_NANOBIOTECHNOLOGY = LkOccupationTitle(
        1055, 12, 541714, "Research and Development in Biotechnology (except Nanobiotechnology)"
    )
    RESEARCH_AND_DEVELOPMENT_IN_THE_PHYSICAL_ENGINEERING_AND_LIFE_SCIENCES_EXCEPT_NANOTECHNOLOGY_AND_BIOTECHNOLOGY = LkOccupationTitle(
        1056,
        12,
        541715,
        "Research and Development in the Physical, Engineering, and Life Sciences (except Nanotechnology and Biotechnology)",
    )
    RESEARCH_AND_DEVELOPMENT_IN_THE_SOCIAL_SCIENCES_AND_HUMANITIES = LkOccupationTitle(
        1057, 12, 541720, "Research and Development in the Social Sciences and Humanities"
    )
    ADVERTISING_PUBLIC_RELATIONS_AND_RELATED_SERVICES = LkOccupationTitle(
        1058, 12, 5418, "Advertising, Public Relations, and Related Services"
    )
    ADVERTISING_AGENCIES = LkOccupationTitle(1059, 12, 541810, "Advertising Agencies")
    PUBLIC_RELATIONS_AGENCIES = LkOccupationTitle(1060, 12, 541820, "Public Relations Agencies")
    MEDIA_BUYING_AGENCIES = LkOccupationTitle(1061, 12, 541830, "Media Buying Agencies")
    MEDIA_REPRESENTATIVES = LkOccupationTitle(1062, 12, 541840, "Media Representatives")
    OUTDOOR_ADVERTISING = LkOccupationTitle(1063, 12, 541850, "Outdoor Advertising")
    DIRECT_MAIL_ADVERTISING = LkOccupationTitle(1064, 12, 541860, "Direct Mail Advertising")
    ADVERTISING_MATERIAL_DISTRIBUTION_SERVICES = LkOccupationTitle(
        1065, 12, 541870, "Advertising Material Distribution Services"
    )
    OTHER_SERVICES_RELATED_TO_ADVERTISING = LkOccupationTitle(
        1066, 12, 541890, "Other Services Related to Advertising"
    )
    OTHER_PROFESSIONAL_SCIENTIFIC_AND_TECHNICAL_SERVICES = LkOccupationTitle(
        1067, 12, 5419, "Other Professional, Scientific, and Technical Services"
    )
    MARKETING_RESEARCH_AND_PUBLIC_OPINION_POLLING = LkOccupationTitle(
        1068, 12, 541910, "Marketing Research and Public Opinion Polling"
    )
    PHOTOGRAPHY_STUDIOS_PORTRAIT = LkOccupationTitle(
        1069, 12, 541921, "Photography Studios, Portrait"
    )
    COMMERCIAL_PHOTOGRAPHY = LkOccupationTitle(1070, 12, 541922, "Commercial Photography")
    TRANSLATION_AND_INTERPRETATION_SERVICES = LkOccupationTitle(
        1071, 12, 541930, "Translation and Interpretation Services"
    )
    VETERINARY_SERVICES = LkOccupationTitle(1072, 12, 541940, "Veterinary Services")
    ALL_OTHER_PROFESSIONAL_SCIENTIFIC_AND_TECHNICAL_SERVICES = LkOccupationTitle(
        1073, 12, 541990, "All Other Professional, Scientific, and Technical Services"
    )
    MANAGEMENT_OF_COMPANIES_AND_ENTERPRISES = LkOccupationTitle(
        1074, 13, 5511, "Management of Companies and Enterprises"
    )
    OFFICES_OF_BANK_HOLDING_COMPANIES = LkOccupationTitle(
        1075, 13, 551111, "Offices of Bank Holding Companies"
    )
    OFFICES_OF_OTHER_HOLDING_COMPANIES = LkOccupationTitle(
        1076, 13, 551112, "Offices of Other Holding Companies"
    )
    CORPORATE_SUBSIDIARY_AND_REGIONAL_MANAGING_OFFICES = LkOccupationTitle(
        1077, 13, 551114, "Corporate, Subsidiary, and Regional Managing Offices"
    )
    OFFICE_ADMINISTRATIVE_SERVICES_4 = LkOccupationTitle(
        1078, 14, 5611, "Office Administrative Services"
    )
    OFFICE_ADMINISTRATIVE_SERVICES = LkOccupationTitle(
        1079, 14, 561110, "Office Administrative Services"
    )
    FACILITIES_SUPPORT_SERVICES_4 = LkOccupationTitle(1080, 14, 5612, "Facilities Support Services")
    FACILITIES_SUPPORT_SERVICES = LkOccupationTitle(1081, 14, 561210, "Facilities Support Services")
    EMPLOYMENT_SERVICES = LkOccupationTitle(1082, 14, 5613, "Employment Services")
    EMPLOYMENT_PLACEMENT_AGENCIES = LkOccupationTitle(
        1083, 14, 561311, "Employment Placement Agencies"
    )
    EXECUTIVE_SEARCH_SERVICES = LkOccupationTitle(1084, 14, 561312, "Executive Search Services")
    TEMPORARY_HELP_SERVICES = LkOccupationTitle(1085, 14, 561320, "Temporary Help Services")
    PROFESSIONAL_EMPLOYER_ORGANIZATIONS = LkOccupationTitle(
        1086, 14, 561330, "Professional Employer Organizations"
    )
    BUSINESS_SUPPORT_SERVICES = LkOccupationTitle(1087, 14, 5614, "Business Support Services")
    DOCUMENT_PREPARATION_SERVICES = LkOccupationTitle(
        1088, 14, 561410, "Document Preparation Services"
    )
    TELEPHONE_ANSWERING_SERVICES = LkOccupationTitle(
        1089, 14, 561421, "Telephone Answering Services"
    )
    TELEMARKETING_BUREAUS_AND_OTHER_CONTACT_CENTERS = LkOccupationTitle(
        1090, 14, 561422, "Telemarketing Bureaus and Other Contact Centers"
    )
    PRIVATE_MAIL_CENTERS = LkOccupationTitle(1091, 14, 561431, "Private Mail Centers")
    OTHER_BUSINESS_SERVICE_CENTERS_INCLUDING_COPY_SHOPS = LkOccupationTitle(
        1092, 14, 561439, "Other Business Service Centers (including Copy Shops)"
    )
    COLLECTION_AGENCIES = LkOccupationTitle(1093, 14, 561440, "Collection Agencies")
    CREDIT_BUREAUS = LkOccupationTitle(1094, 14, 561450, "Credit Bureaus")
    REPOSSESSION_SERVICES = LkOccupationTitle(1095, 14, 561491, "Repossession Services")
    COURT_REPORTING_AND_STENOTYPE_SERVICES = LkOccupationTitle(
        1096, 14, 561492, "Court Reporting and Stenotype Services"
    )
    ALL_OTHER_BUSINESS_SUPPORT_SERVICES = LkOccupationTitle(
        1097, 14, 561499, "All Other Business Support Services"
    )
    TRAVEL_ARRANGEMENT_AND_RESERVATION_SERVICES = LkOccupationTitle(
        1098, 14, 5615, "Travel Arrangement and Reservation Services"
    )
    TRAVEL_AGENCIES = LkOccupationTitle(1099, 14, 561510, "Travel Agencies")
    TOUR_OPERATORS = LkOccupationTitle(1100, 14, 561520, "Tour Operators")
    CONVENTION_AND_VISITORS_BUREAUS = LkOccupationTitle(
        1101, 14, 561591, "Convention and Visitors Bureaus"
    )
    ALL_OTHER_TRAVEL_ARRANGEMENT_AND_RESERVATION_SERVICES = LkOccupationTitle(
        1102, 14, 561599, "All Other Travel Arrangement and Reservation Services"
    )
    INVESTIGATION_AND_SECURITY_SERVICES = LkOccupationTitle(
        1103, 14, 5616, "Investigation and Security Services"
    )
    INVESTIGATION_SERVICES = LkOccupationTitle(1104, 14, 561611, "Investigation Services")
    SECURITY_GUARDS_AND_PATROL_SERVICES = LkOccupationTitle(
        1105, 14, 561612, "Security Guards and Patrol Services"
    )
    ARMORED_CAR_SERVICES = LkOccupationTitle(1106, 14, 561613, "Armored Car Services")
    SECURITY_SYSTEMS_SERVICES_EXCEPT_LOCKSMITHS = LkOccupationTitle(
        1107, 14, 561621, "Security Systems Services (except Locksmiths)"
    )
    LOCKSMITHS = LkOccupationTitle(1108, 14, 561622, "Locksmiths")
    SERVICES_TO_BUILDINGS_AND_DWELLINGS = LkOccupationTitle(
        1109, 14, 5617, "Services to Buildings and Dwellings"
    )
    EXTERMINATING_AND_PEST_CONTROL_SERVICES = LkOccupationTitle(
        1110, 14, 561710, "Exterminating and Pest Control Services"
    )
    JANITORIAL_SERVICES = LkOccupationTitle(1111, 14, 561720, "Janitorial Services")
    LANDSCAPING_SERVICES = LkOccupationTitle(1112, 14, 561730, "Landscaping Services")
    CARPET_AND_UPHOLSTERY_CLEANING_SERVICES = LkOccupationTitle(
        1113, 14, 561740, "Carpet and Upholstery Cleaning Services"
    )
    OTHER_SERVICES_TO_BUILDINGS_AND_DWELLINGS = LkOccupationTitle(
        1114, 14, 561790, "Other Services to Buildings and Dwellings"
    )
    OTHER_SUPPORT_SERVICES = LkOccupationTitle(1115, 14, 5619, "Other Support Services")
    PACKAGING_AND_LABELING_SERVICES = LkOccupationTitle(
        1116, 14, 561910, "Packaging and Labeling Services"
    )
    CONVENTION_AND_TRADE_SHOW_ORGANIZERS = LkOccupationTitle(
        1117, 14, 561920, "Convention and Trade Show Organizers"
    )
    ALL_OTHER_SUPPORT_SERVICES = LkOccupationTitle(1118, 14, 561990, "All Other Support Services")
    WASTE_COLLECTION = LkOccupationTitle(1119, 14, 5621, "Waste Collection")
    SOLID_WASTE_COLLECTION = LkOccupationTitle(1120, 14, 562111, "Solid Waste Collection")
    HAZARDOUS_WASTE_COLLECTION = LkOccupationTitle(1121, 14, 562112, "Hazardous Waste Collection")
    OTHER_WASTE_COLLECTION = LkOccupationTitle(1122, 14, 562119, "Other Waste Collection")
    WASTE_TREATMENT_AND_DISPOSAL = LkOccupationTitle(1123, 14, 5622, "Waste Treatment and Disposal")
    HAZARDOUS_WASTE_TREATMENT_AND_DISPOSAL = LkOccupationTitle(
        1124, 14, 562211, "Hazardous Waste Treatment and Disposal"
    )
    SOLID_WASTE_LANDFILL = LkOccupationTitle(1125, 14, 562212, "Solid Waste Landfill")
    SOLID_WASTE_COMBUSTORS_AND_INCINERATORS = LkOccupationTitle(
        1126, 14, 562213, "Solid Waste Combustors and Incinerators"
    )
    OTHER_NONHAZARDOUS_WASTE_TREATMENT_AND_DISPOSAL = LkOccupationTitle(
        1127, 14, 562219, "Other Nonhazardous Waste Treatment and Disposal"
    )
    REMEDIATION_AND_OTHER_WASTE_MANAGEMENT_SERVICES = LkOccupationTitle(
        1128, 14, 5629, "Remediation and Other Waste Management Services"
    )
    REMEDIATION_SERVICES = LkOccupationTitle(1129, 14, 562910, "Remediation Services")
    MATERIALS_RECOVERY_FACILITIES = LkOccupationTitle(
        1130, 14, 562920, "Materials Recovery Facilities"
    )
    SEPTIC_TANK_AND_RELATED_SERVICES = LkOccupationTitle(
        1131, 14, 562991, "Septic Tank and Related Services"
    )
    ALL_OTHER_MISCELLANEOUS_WASTE_MANAGEMENT_SERVICES = LkOccupationTitle(
        1132, 14, 562998, "All Other Miscellaneous Waste Management Services"
    )
    ELEMENTARY_AND_SECONDARY_SCHOOLS_4 = LkOccupationTitle(
        1133, 15, 6111, "Elementary and Secondary Schools"
    )
    ELEMENTARY_AND_SECONDARY_SCHOOLS = LkOccupationTitle(
        1134, 15, 611110, "Elementary and Secondary Schools"
    )
    JUNIOR_COLLEGES_4 = LkOccupationTitle(1135, 15, 6112, "Junior Colleges")
    JUNIOR_COLLEGES = LkOccupationTitle(1136, 15, 611210, "Junior Colleges")
    COLLEGES_UNIVERSITIES_AND_PROFESSIONAL_SCHOOLS_4 = LkOccupationTitle(
        1137, 15, 6113, "Colleges, Universities, and Professional Schools"
    )
    COLLEGES_UNIVERSITIES_AND_PROFESSIONAL_SCHOOLS = LkOccupationTitle(
        1138, 15, 611310, "Colleges, Universities, and Professional Schools"
    )
    BUSINESS_SCHOOLS_AND_COMPUTER_AND_MANAGEMENT_TRAINING = LkOccupationTitle(
        1139, 15, 6114, "Business Schools and Computer and Management Training"
    )
    BUSINESS_AND_SECRETARIAL_SCHOOLS = LkOccupationTitle(
        1140, 15, 611410, "Business and Secretarial Schools"
    )
    COMPUTER_TRAINING = LkOccupationTitle(1141, 15, 611420, "Computer Training")
    PROFESSIONAL_AND_MANAGEMENT_DEVELOPMENT_TRAINING = LkOccupationTitle(
        1142, 15, 611430, "Professional and Management Development Training"
    )
    TECHNICAL_AND_TRADE_SCHOOLS = LkOccupationTitle(1143, 15, 6115, "Technical and Trade Schools")
    COSMETOLOGY_AND_BARBER_SCHOOLS = LkOccupationTitle(
        1144, 15, 611511, "Cosmetology and Barber Schools"
    )
    FLIGHT_TRAINING = LkOccupationTitle(1145, 15, 611512, "Flight Training")
    APPRENTICESHIP_TRAINING = LkOccupationTitle(1146, 15, 611513, "Apprenticeship Training")
    OTHER_TECHNICAL_AND_TRADE_SCHOOLS = LkOccupationTitle(
        1147, 15, 611519, "Other Technical and Trade Schools"
    )
    OTHER_SCHOOLS_AND_INSTRUCTION = LkOccupationTitle(
        1148, 15, 6116, "Other Schools and Instruction"
    )
    FINE_ARTS_SCHOOLS = LkOccupationTitle(1149, 15, 611610, "Fine Arts Schools")
    SPORTS_AND_RECREATION_INSTRUCTION = LkOccupationTitle(
        1150, 15, 611620, "Sports and Recreation Instruction"
    )
    LANGUAGE_SCHOOLS = LkOccupationTitle(1151, 15, 611630, "Language Schools")
    EXAM_PREPARATION_AND_TUTORING = LkOccupationTitle(
        1152, 15, 611691, "Exam Preparation and Tutoring"
    )
    AUTOMOBILE_DRIVING_SCHOOLS = LkOccupationTitle(1153, 15, 611692, "Automobile Driving Schools")
    ALL_OTHER_MISCELLANEOUS_SCHOOLS_AND_INSTRUCTION = LkOccupationTitle(
        1154, 15, 611699, "All Other Miscellaneous Schools and Instruction"
    )
    EDUCATIONAL_SUPPORT_SERVICES_4 = LkOccupationTitle(
        1155, 15, 6117, "Educational Support Services"
    )
    EDUCATIONAL_SUPPORT_SERVICES = LkOccupationTitle(
        1156, 15, 611710, "Educational Support Services"
    )
    OFFICES_OF_PHYSICIANS = LkOccupationTitle(1157, 16, 6211, "Offices of Physicians")
    OFFICES_OF_PHYSICIANS_EXCEPT_MENTAL_HEALTH_SPECIALISTS = LkOccupationTitle(
        1158, 16, 621111, "Offices of Physicians (except Mental Health Specialists)"
    )
    OFFICES_OF_PHYSICIANS_MENTAL_HEALTH_SPECIALISTS = LkOccupationTitle(
        1159, 16, 621112, "Offices of Physicians, Mental Health Specialists"
    )
    OFFICES_OF_DENTISTS_4 = LkOccupationTitle(1160, 16, 6212, "Offices of Dentists")
    OFFICES_OF_DENTISTS = LkOccupationTitle(1161, 16, 621210, "Offices of Dentists")
    OFFICES_OF_OTHER_HEALTH_PRACTITIONERS = LkOccupationTitle(
        1162, 16, 6213, "Offices of Other Health Practitioners"
    )
    OFFICES_OF_CHIROPRACTORS = LkOccupationTitle(1163, 16, 621310, "Offices of Chiropractors")
    OFFICES_OF_OPTOMETRISTS = LkOccupationTitle(1164, 16, 621320, "Offices of Optometrists")
    OFFICES_OF_MENTAL_HEALTH_PRACTITIONERS_EXCEPT_PHYSICIANS = LkOccupationTitle(
        1165, 16, 621330, "Offices of Mental Health Practitioners (except Physicians)"
    )
    OFFICES_OF_PHYSICAL_OCCUPATIONAL_AND_SPEECH_THERAPISTS_AND_AUDIOLOGISTS = LkOccupationTitle(
        1166,
        16,
        621340,
        "Offices of Physical, Occupational and Speech Therapists, and Audiologists",
    )
    OFFICES_OF_PODIATRISTS = LkOccupationTitle(1167, 16, 621391, "Offices of Podiatrists")
    OFFICES_OF_ALL_OTHER_MISCELLANEOUS_HEALTH_PRACTITIONERS = LkOccupationTitle(
        1168, 16, 621399, "Offices of All Other Miscellaneous Health Practitioners"
    )
    OUTPATIENT_CARE_CENTERS = LkOccupationTitle(1169, 16, 6214, "Outpatient Care Centers")
    FAMILY_PLANNING_CENTERS = LkOccupationTitle(1170, 16, 621410, "Family Planning Centers")
    OUTPATIENT_MENTAL_HEALTH_AND_SUBSTANCE_ABUSE_CENTERS = LkOccupationTitle(
        1171, 16, 621420, "Outpatient Mental Health and Substance Abuse Centers"
    )
    HMO_MEDICAL_CENTERS = LkOccupationTitle(1172, 16, 621491, "HMO Medical Centers")
    KIDNEY_DIALYSIS_CENTERS = LkOccupationTitle(1173, 16, 621492, "Kidney Dialysis Centers")
    FREESTANDING_AMBULATORY_SURGICAL_AND_EMERGENCY_CENTERS = LkOccupationTitle(
        1174, 16, 621493, "Freestanding Ambulatory Surgical and Emergency Centers"
    )
    ALL_OTHER_OUTPATIENT_CARE_CENTERS = LkOccupationTitle(
        1175, 16, 621498, "All Other Outpatient Care Centers"
    )
    MEDICAL_AND_DIAGNOSTIC_LABORATORIES = LkOccupationTitle(
        1176, 16, 6215, "Medical and Diagnostic Laboratories"
    )
    MEDICAL_LABORATORIES = LkOccupationTitle(1177, 16, 621511, "Medical Laboratories")
    DIAGNOSTIC_IMAGING_CENTERS = LkOccupationTitle(1178, 16, 621512, "Diagnostic Imaging Centers")
    HOME_HEALTH_CARE_SERVICES_4 = LkOccupationTitle(1179, 16, 6216, "Home Health Care Services")
    HOME_HEALTH_CARE_SERVICES = LkOccupationTitle(1180, 16, 621610, "Home Health Care Services")
    OTHER_AMBULATORY_HEALTH_CARE_SERVICES = LkOccupationTitle(
        1181, 16, 6219, "Other Ambulatory Health Care Services"
    )
    AMBULANCE_SERVICES = LkOccupationTitle(1182, 16, 621910, "Ambulance Services")
    BLOOD_AND_ORGAN_BANKS = LkOccupationTitle(1183, 16, 621991, "Blood and Organ Banks")
    ALL_OTHER_MISCELLANEOUS_AMBULATORY_HEALTH_CARE_SERVICES = LkOccupationTitle(
        1184, 16, 621999, "All Other Miscellaneous Ambulatory Health Care Services"
    )
    GENERAL_MEDICAL_AND_SURGICAL_HOSPITALS_4 = LkOccupationTitle(
        1185, 16, 6221, "General Medical and Surgical Hospitals"
    )
    GENERAL_MEDICAL_AND_SURGICAL_HOSPITALS = LkOccupationTitle(
        1186, 16, 622110, "General Medical and Surgical Hospitals"
    )
    PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS_4 = LkOccupationTitle(
        1187, 16, 6222, "Psychiatric and Substance Abuse Hospitals"
    )
    PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkOccupationTitle(
        1188, 16, 622210, "Psychiatric and Substance Abuse Hospitals"
    )
    SPECIALTY_EXCEPT_PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS_4 = LkOccupationTitle(
        1189, 16, 6223, "Specialty (except Psychiatric and Substance Abuse) Hospitals"
    )
    SPECIALTY_EXCEPT_PSYCHIATRIC_AND_SUBSTANCE_ABUSE_HOSPITALS = LkOccupationTitle(
        1190, 16, 622310, "Specialty (except Psychiatric and Substance Abuse) Hospitals"
    )
    NURSING_CARE_FACILITIES_SKILLED_NURSING_FACILITIES_4 = LkOccupationTitle(
        1191, 16, 6231, "Nursing Care Facilities (Skilled Nursing Facilities)"
    )
    NURSING_CARE_FACILITIES_SKILLED_NURSING_FACILITIES = LkOccupationTitle(
        1192, 16, 623110, "Nursing Care Facilities (Skilled Nursing Facilities)"
    )
    RESIDENTIAL_INTELLECTUAL_AND_DEVELOPMENTAL_DISABILITY_MENTAL_HEALTH_AND_SUBSTANCE_ABUSE_FACILITIES = LkOccupationTitle(
        1193,
        16,
        6232,
        "Residential Intellectual and Developmental Disability, Mental Health, and Substance Abuse Facilities",
    )
    RESIDENTIAL_INTELLECTUAL_AND_DEVELOPMENTAL_DISABILITY_FACILITIES = LkOccupationTitle(
        1194, 16, 623210, "Residential Intellectual and Developmental Disability Facilities"
    )
    RESIDENTIAL_MENTAL_HEALTH_AND_SUBSTANCE_ABUSE_FACILITIES = LkOccupationTitle(
        1195, 16, 623220, "Residential Mental Health and Substance Abuse Facilities"
    )
    CONTINUING_CARE_RETIREMENT_COMMUNITIES_AND_ASSISTED_LIVING_FACILITIES_FOR_THE_ELDERLY = LkOccupationTitle(
        1196,
        16,
        6233,
        "Continuing Care Retirement Communities and Assisted Living Facilities for the Elderly",
    )
    CONTINUING_CARE_RETIREMENT_COMMUNITIES = LkOccupationTitle(
        1197, 16, 623311, "Continuing Care Retirement Communities"
    )
    ASSISTED_LIVING_FACILITIES_FOR_THE_ELDERLY = LkOccupationTitle(
        1198, 16, 623312, "Assisted Living Facilities for the Elderly"
    )
    OTHER_RESIDENTIAL_CARE_FACILITIES_4 = LkOccupationTitle(
        1199, 16, 6239, "Other Residential Care Facilities"
    )
    OTHER_RESIDENTIAL_CARE_FACILITIES = LkOccupationTitle(
        1200, 16, 623990, "Other Residential Care Facilities"
    )
    INDIVIDUAL_AND_FAMILY_SERVICES = LkOccupationTitle(
        1201, 16, 6241, "Individual and Family Services"
    )
    CHILD_AND_YOUTH_SERVICES = LkOccupationTitle(1202, 16, 624110, "Child and Youth Services")
    SERVICES_FOR_THE_ELDERLY_AND_PERSONS_WITH_DISABILITIES = LkOccupationTitle(
        1203, 16, 624120, "Services for the Elderly and Persons with Disabilities"
    )
    OTHER_INDIVIDUAL_AND_FAMILY_SERVICES = LkOccupationTitle(
        1204, 16, 624190, "Other Individual and Family Services"
    )
    COMMUNITY_FOOD_AND_HOUSING_AND_EMERGENCY_AND_OTHER_RELIEF_SERVICES = LkOccupationTitle(
        1205, 16, 6242, "Community Food and Housing, and Emergency and Other Relief Services"
    )
    COMMUNITY_FOOD_SERVICES = LkOccupationTitle(1206, 16, 624210, "Community Food Services")
    TEMPORARY_SHELTERS = LkOccupationTitle(1207, 16, 624221, "Temporary Shelters")
    OTHER_COMMUNITY_HOUSING_SERVICES = LkOccupationTitle(
        1208, 16, 624229, "Other Community Housing Services"
    )
    EMERGENCY_AND_OTHER_RELIEF_SERVICES = LkOccupationTitle(
        1209, 16, 624230, "Emergency and Other Relief Services"
    )
    VOCATIONAL_REHABILITATION_SERVICES_4 = LkOccupationTitle(
        1210, 16, 6243, "Vocational Rehabilitation Services"
    )
    VOCATIONAL_REHABILITATION_SERVICES = LkOccupationTitle(
        1211, 16, 624310, "Vocational Rehabilitation Services"
    )
    CHILD_DAY_CARE_SERVICES_4 = LkOccupationTitle(1212, 16, 6244, "Child Day Care Services")
    CHILD_DAY_CARE_SERVICES = LkOccupationTitle(1213, 16, 624410, "Child Day Care Services")
    PERFORMING_ARTS_COMPANIES = LkOccupationTitle(1214, 17, 7111, "Performing Arts Companies")
    THEATER_COMPANIES_AND_DINNER_THEATERS = LkOccupationTitle(
        1215, 17, 711110, "Theater Companies and Dinner Theaters"
    )
    DANCE_COMPANIES = LkOccupationTitle(1216, 17, 711120, "Dance Companies")
    MUSICAL_GROUPS_AND_ARTISTS = LkOccupationTitle(1217, 17, 711130, "Musical Groups and Artists")
    OTHER_PERFORMING_ARTS_COMPANIES = LkOccupationTitle(
        1218, 17, 711190, "Other Performing Arts Companies"
    )
    SPECTATOR_SPORTS = LkOccupationTitle(1219, 17, 7112, "Spectator Sports")
    SPORTS_TEAMS_AND_CLUBS = LkOccupationTitle(1220, 17, 711211, "Sports Teams and Clubs")
    RACETRACKS = LkOccupationTitle(1221, 17, 711212, "Racetracks")
    OTHER_SPECTATOR_SPORTS = LkOccupationTitle(1222, 17, 711219, "Other Spectator Sports")
    PROMOTERS_OF_PERFORMING_ARTS_SPORTS_AND_SIMILAR_EVENTS = LkOccupationTitle(
        1223, 17, 7113, "Promoters of Performing Arts, Sports, and Similar Events"
    )
    PROMOTERS_OF_PERFORMING_ARTS_SPORTS_AND_SIMILAR_EVENTS_WITH_FACILITIES = LkOccupationTitle(
        1224, 17, 711310, "Promoters of Performing Arts, Sports, and Similar Events with Facilities"
    )
    PROMOTERS_OF_PERFORMING_ARTS_SPORTS_AND_SIMILAR_EVENTS_WITHOUT_FACILITIES = LkOccupationTitle(
        1225,
        17,
        711320,
        "Promoters of Performing Arts, Sports, and Similar Events without Facilities",
    )
    AGENTS_AND_MANAGERS_FOR_ARTISTS_ATHLETES_ENTERTAINERS_AND_OTHER_PUBLIC_FIGURES_4 = LkOccupationTitle(
        1226,
        17,
        7114,
        "Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures",
    )
    AGENTS_AND_MANAGERS_FOR_ARTISTS_ATHLETES_ENTERTAINERS_AND_OTHER_PUBLIC_FIGURES = LkOccupationTitle(
        1227,
        17,
        711410,
        "Agents and Managers for Artists, Athletes, Entertainers, and Other Public Figures",
    )
    INDEPENDENT_ARTISTS_WRITERS_AND_PERFORMERS_4 = LkOccupationTitle(
        1228, 17, 7115, "Independent Artists, Writers, and Performers"
    )
    INDEPENDENT_ARTISTS_WRITERS_AND_PERFORMERS = LkOccupationTitle(
        1229, 17, 711510, "Independent Artists, Writers, and Performers"
    )
    MUSEUMS_HISTORICAL_SITES_AND_SIMILAR_INSTITUTIONS = LkOccupationTitle(
        1230, 17, 7121, "Museums, Historical Sites, and Similar Institutions"
    )
    MUSEUMS = LkOccupationTitle(1231, 17, 712110, "Museums")
    HISTORICAL_SITES = LkOccupationTitle(1232, 17, 712120, "Historical Sites")
    ZOOS_AND_BOTANICAL_GARDENS = LkOccupationTitle(1233, 17, 712130, "Zoos and Botanical Gardens")
    NATURE_PARKS_AND_OTHER_SIMILAR_INSTITUTIONS = LkOccupationTitle(
        1234, 17, 712190, "Nature Parks and Other Similar Institutions"
    )
    AMUSEMENT_PARKS_AND_ARCADES = LkOccupationTitle(1235, 17, 7131, "Amusement Parks and Arcades")
    AMUSEMENT_AND_THEME_PARKS = LkOccupationTitle(1236, 17, 713110, "Amusement and Theme Parks")
    AMUSEMENT_ARCADES = LkOccupationTitle(1237, 17, 713120, "Amusement Arcades")
    GAMBLING_INDUSTRIES = LkOccupationTitle(1238, 17, 7132, "Gambling Industries")
    CASINOS_EXCEPT_CASINO_HOTELS = LkOccupationTitle(
        1239, 17, 713210, "Casinos (except Casino Hotels)"
    )
    OTHER_GAMBLING_INDUSTRIES = LkOccupationTitle(1240, 17, 713290, "Other Gambling Industries")
    OTHER_AMUSEMENT_AND_RECREATION_INDUSTRIES = LkOccupationTitle(
        1241, 17, 7139, "Other Amusement and Recreation Industries"
    )
    GOLF_COURSES_AND_COUNTRY_CLUBS = LkOccupationTitle(
        1242, 17, 713910, "Golf Courses and Country Clubs"
    )
    SKIING_FACILITIES = LkOccupationTitle(1243, 17, 713920, "Skiing Facilities")
    MARINAS = LkOccupationTitle(1244, 17, 713930, "Marinas")
    FITNESS_AND_RECREATIONAL_SPORTS_CENTERS = LkOccupationTitle(
        1245, 17, 713940, "Fitness and Recreational Sports Centers"
    )
    BOWLING_CENTERS = LkOccupationTitle(1246, 17, 713950, "Bowling Centers")
    ALL_OTHER_AMUSEMENT_AND_RECREATION_INDUSTRIES = LkOccupationTitle(
        1247, 17, 713990, "All Other Amusement and Recreation Industries"
    )
    TRAVELER_ACCOMMODATION = LkOccupationTitle(1248, 18, 7211, "Traveler Accommodation")
    HOTELS_EXCEPT_CASINO_HOTELS_AND_MOTELS = LkOccupationTitle(
        1249, 18, 721110, "Hotels (except Casino Hotels) and Motels"
    )
    CASINO_HOTELS = LkOccupationTitle(1250, 18, 721120, "Casino Hotels")
    BED_AND_BREAKFAST_INNS = LkOccupationTitle(1251, 18, 721191, "Bed-and-Breakfast Inns")
    ALL_OTHER_TRAVELER_ACCOMMODATION = LkOccupationTitle(
        1252, 18, 721199, "All Other Traveler Accommodation"
    )
    RV_RECREATIONAL_VEHICLE_PARKS_AND_RECREATIONAL_CAMPS = LkOccupationTitle(
        1253, 18, 7212, "RV (Recreational Vehicle) Parks and Recreational Camps"
    )
    RV_RECREATIONAL_VEHICLE_PARKS_AND_CAMPGROUNDS = LkOccupationTitle(
        1254, 18, 721211, "RV (Recreational Vehicle) Parks and Campgrounds"
    )
    RECREATIONAL_AND_VACATION_CAMPS_EXCEPT_CAMPGROUNDS = LkOccupationTitle(
        1255, 18, 721214, "Recreational and Vacation Camps (except Campgrounds)"
    )
    ROOMING_AND_BOARDING_HOUSES_DORMITORIES_AND_WORKERS_CAMPS_4 = LkOccupationTitle(
        1256, 18, 7213, "Rooming and Boarding Houses, Dormitories, and Workers' Camps"
    )
    ROOMING_AND_BOARDING_HOUSES_DORMITORIES_AND_WORKERS_CAMPS = LkOccupationTitle(
        1257, 18, 721310, "Rooming and Boarding Houses, Dormitories, and Workers' Camps"
    )
    SPECIAL_FOOD_SERVICES = LkOccupationTitle(1258, 18, 7223, "Special Food Services")
    FOOD_SERVICE_CONTRACTORS = LkOccupationTitle(1259, 18, 722310, "Food Service Contractors")
    CATERERS = LkOccupationTitle(1260, 18, 722320, "Caterers")
    MOBILE_FOOD_SERVICES = LkOccupationTitle(1261, 18, 722330, "Mobile Food Services")
    DRINKING_PLACES_ALCOHOLIC_BEVERAGES_4 = LkOccupationTitle(
        1262, 18, 7224, "Drinking Places (Alcoholic Beverages)"
    )
    DRINKING_PLACES_ALCOHOLIC_BEVERAGES = LkOccupationTitle(
        1263, 18, 722410, "Drinking Places (Alcoholic Beverages)"
    )
    RESTAURANTS_AND_OTHER_EATING_PLACES = LkOccupationTitle(
        1264, 18, 7225, "Restaurants and Other Eating Places"
    )
    FULL_SERVICE_RESTAURANTS = LkOccupationTitle(1265, 18, 722511, "Full-Service Restaurants")
    LIMITED_SERVICE_RESTAURANTS = LkOccupationTitle(1266, 18, 722513, "Limited-Service Restaurants")
    CAFETERIAS_GRILL_BUFFETS_AND_BUFFETS = LkOccupationTitle(
        1267, 18, 722514, "Cafeterias, Grill Buffets, and Buffets"
    )
    SNACK_AND_NONALCOHOLIC_BEVERAGE_BARS = LkOccupationTitle(
        1268, 18, 722515, "Snack and Nonalcoholic Beverage Bars"
    )
    AUTOMOTIVE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1269, 19, 8111, "Automotive Repair and Maintenance"
    )
    GENERAL_AUTOMOTIVE_REPAIR = LkOccupationTitle(1270, 19, 811111, "General Automotive Repair")
    AUTOMOTIVE_EXHAUST_SYSTEM_REPAIR = LkOccupationTitle(
        1271, 19, 811112, "Automotive Exhaust System Repair"
    )
    AUTOMOTIVE_TRANSMISSION_REPAIR = LkOccupationTitle(
        1272, 19, 811113, "Automotive Transmission Repair"
    )
    OTHER_AUTOMOTIVE_MECHANICAL_AND_ELECTRICAL_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1273, 19, 811118, "Other Automotive Mechanical and Electrical Repair and Maintenance"
    )
    AUTOMOTIVE_BODY_PAINT_AND_INTERIOR_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1274, 19, 811121, "Automotive Body, Paint, and Interior Repair and Maintenance"
    )
    AUTOMOTIVE_GLASS_REPLACEMENT_SHOPS = LkOccupationTitle(
        1275, 19, 811122, "Automotive Glass Replacement Shops"
    )
    AUTOMOTIVE_OIL_CHANGE_AND_LUBRICATION_SHOPS = LkOccupationTitle(
        1276, 19, 811191, "Automotive Oil Change and Lubrication Shops"
    )
    CAR_WASHES = LkOccupationTitle(1277, 19, 811192, "Car Washes")
    ALL_OTHER_AUTOMOTIVE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1278, 19, 811198, "All Other Automotive Repair and Maintenance"
    )
    ELECTRONIC_AND_PRECISION_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1279, 19, 8112, "Electronic and Precision Equipment Repair and Maintenance"
    )
    CONSUMER_ELECTRONICS_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1280, 19, 811211, "Consumer Electronics Repair and Maintenance"
    )
    COMPUTER_AND_OFFICE_MACHINE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1281, 19, 811212, "Computer and Office Machine Repair and Maintenance"
    )
    COMMUNICATION_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1282, 19, 811213, "Communication Equipment Repair and Maintenance"
    )
    OTHER_ELECTRONIC_AND_PRECISION_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1283, 19, 811219, "Other Electronic and Precision Equipment Repair and Maintenance"
    )
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_EXCEPT_AUTOMOTIVE_AND_ELECTRONIC_REPAIR_AND_MAINTENANCE_4 = LkOccupationTitle(
        1284,
        19,
        8113,
        "Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance",
    )
    COMMERCIAL_AND_INDUSTRIAL_MACHINERY_AND_EQUIPMENT_EXCEPT_AUTOMOTIVE_AND_ELECTRONIC_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1285,
        19,
        811310,
        "Commercial and Industrial Machinery and Equipment (except Automotive and Electronic) Repair and Maintenance",
    )
    PERSONAL_AND_HOUSEHOLD_GOODS_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1286, 19, 8114, "Personal and Household Goods Repair and Maintenance"
    )
    HOME_AND_GARDEN_EQUIPMENT_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1287, 19, 811411, "Home and Garden Equipment Repair and Maintenance"
    )
    APPLIANCE_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1288, 19, 811412, "Appliance Repair and Maintenance"
    )
    REUPHOLSTERY_AND_FURNITURE_REPAIR = LkOccupationTitle(
        1289, 19, 811420, "Reupholstery and Furniture Repair"
    )
    FOOTWEAR_AND_LEATHER_GOODS_REPAIR = LkOccupationTitle(
        1290, 19, 811430, "Footwear and Leather Goods Repair"
    )
    OTHER_PERSONAL_AND_HOUSEHOLD_GOODS_REPAIR_AND_MAINTENANCE = LkOccupationTitle(
        1291, 19, 811490, "Other Personal and Household Goods Repair and Maintenance"
    )
    PERSONAL_CARE_SERVICES = LkOccupationTitle(1292, 19, 8121, "Personal Care Services")
    BARBER_SHOPS = LkOccupationTitle(1293, 19, 812111, "Barber Shops")
    BEAUTY_SALONS = LkOccupationTitle(1294, 19, 812112, "Beauty Salons")
    NAIL_SALONS = LkOccupationTitle(1295, 19, 812113, "Nail Salons")
    DIET_AND_WEIGHT_REDUCING_CENTERS = LkOccupationTitle(
        1296, 19, 812191, "Diet and Weight Reducing Centers"
    )
    OTHER_PERSONAL_CARE_SERVICES = LkOccupationTitle(
        1297, 19, 812199, "Other Personal Care Services"
    )
    DEATH_CARE_SERVICES = LkOccupationTitle(1298, 19, 8122, "Death Care Services")
    FUNERAL_HOMES_AND_FUNERAL_SERVICES = LkOccupationTitle(
        1299, 19, 812210, "Funeral Homes and Funeral Services"
    )
    CEMETERIES_AND_CREMATORIES = LkOccupationTitle(1300, 19, 812220, "Cemeteries and Crematories")
    DRYCLEANING_AND_LAUNDRY_SERVICES = LkOccupationTitle(
        1301, 19, 8123, "Drycleaning and Laundry Services"
    )
    COIN_OPERATED_LAUNDRIES_AND_DRYCLEANERS = LkOccupationTitle(
        1302, 19, 812310, "Coin-Operated Laundries and Drycleaners"
    )
    DRYCLEANING_AND_LAUNDRY_SERVICES_EXCEPT_COIN_OPERATED = LkOccupationTitle(
        1303, 19, 812320, "Drycleaning and Laundry Services (except Coin-Operated)"
    )
    LINEN_SUPPLY = LkOccupationTitle(1304, 19, 812331, "Linen Supply")
    INDUSTRIAL_LAUNDERERS = LkOccupationTitle(1305, 19, 812332, "Industrial Launderers")
    OTHER_PERSONAL_SERVICES = LkOccupationTitle(1306, 19, 8129, "Other Personal Services")
    PET_CARE_EXCEPT_VETERINARY_SERVICES = LkOccupationTitle(
        1307, 19, 812910, "Pet Care (except Veterinary) Services"
    )
    PHOTOFINISHING_LABORATORIES_EXCEPT_ONE_HOUR = LkOccupationTitle(
        1308, 19, 812921, "Photofinishing Laboratories (except One-Hour)"
    )
    ONE_HOUR_PHOTOFINISHING = LkOccupationTitle(1309, 19, 812922, "One-Hour Photofinishing")
    PARKING_LOTS_AND_GARAGES = LkOccupationTitle(1310, 19, 812930, "Parking Lots and Garages")
    ALL_OTHER_PERSONAL_SERVICES = LkOccupationTitle(1311, 19, 812990, "All Other Personal Services")
    RELIGIOUS_ORGANIZATIONS_4 = LkOccupationTitle(1312, 19, 8131, "Religious Organizations")
    RELIGIOUS_ORGANIZATIONS = LkOccupationTitle(1313, 19, 813110, "Religious Organizations")
    GRANTMAKING_AND_GIVING_SERVICES = LkOccupationTitle(
        1314, 19, 8132, "Grantmaking and Giving Services"
    )
    GRANTMAKING_FOUNDATIONS = LkOccupationTitle(1315, 19, 813211, "Grantmaking Foundations")
    VOLUNTARY_HEALTH_ORGANIZATIONS = LkOccupationTitle(
        1316, 19, 813212, "Voluntary Health Organizations"
    )
    OTHER_GRANTMAKING_AND_GIVING_SERVICES = LkOccupationTitle(
        1317, 19, 813219, "Other Grantmaking and Giving Services"
    )
    SOCIAL_ADVOCACY_ORGANIZATIONS = LkOccupationTitle(
        1318, 19, 8133, "Social Advocacy Organizations"
    )
    HUMAN_RIGHTS_ORGANIZATIONS = LkOccupationTitle(1319, 19, 813311, "Human Rights Organizations")
    ENVIRONMENT_CONSERVATION_AND_WILDLIFE_ORGANIZATIONS = LkOccupationTitle(
        1320, 19, 813312, "Environment, Conservation and Wildlife Organizations"
    )
    OTHER_SOCIAL_ADVOCACY_ORGANIZATIONS = LkOccupationTitle(
        1321, 19, 813319, "Other Social Advocacy Organizations"
    )
    CIVIC_AND_SOCIAL_ORGANIZATIONS_4 = LkOccupationTitle(
        1322, 19, 8134, "Civic and Social Organizations"
    )
    CIVIC_AND_SOCIAL_ORGANIZATIONS = LkOccupationTitle(
        1323, 19, 813410, "Civic and Social Organizations"
    )
    BUSINESS_PROFESSIONAL_LABOR_POLITICAL_AND_SIMILAR_ORGANIZATIONS = LkOccupationTitle(
        1324, 19, 8139, "Business, Professional, Labor, Political, and Similar Organizations"
    )
    BUSINESS_ASSOCIATIONS = LkOccupationTitle(1325, 19, 813910, "Business Associations")
    PROFESSIONAL_ORGANIZATIONS = LkOccupationTitle(1326, 19, 813920, "Professional Organizations")
    LABOR_UNIONS_AND_SIMILAR_LABOR_ORGANIZATIONS = LkOccupationTitle(
        1327, 19, 813930, "Labor Unions and Similar Labor Organizations"
    )
    OTHER_SIMILAR_ORGANIZATIONS_EXCEPT_BUSINESS_PROFESSIONAL_LABOR_AND_POLITICAL_ORGANIZATIONS = LkOccupationTitle(
        1328,
        19,
        813990,
        "Other Similar Organizations (except Business, Professional, Labor, and Political Organizations)",
    )
    PRIVATE_HOUSEHOLDS_4 = LkOccupationTitle(1329, 19, 8141, "Private Households")
    PRIVATE_HOUSEHOLDS = LkOccupationTitle(1330, 19, 814110, "Private Households")
    EXECUTIVE_LEGISLATIVE_AND_OTHER_GENERAL_GOVERNMENT_SUPPORT = LkOccupationTitle(
        1331, 20, 9211, "Executive, Legislative, and Other General Government Support"
    )
    EXECUTIVE_OFFICES = LkOccupationTitle(1332, 20, 921110, "Executive Offices")
    LEGISLATIVE_BODIES = LkOccupationTitle(1333, 20, 921120, "Legislative Bodies")
    PUBLIC_FINANCE_ACTIVITIES = LkOccupationTitle(1334, 20, 921130, "Public Finance Activities")
    EXECUTIVE_AND_LEGISLATIVE_OFFICES_COMBINED = LkOccupationTitle(
        1335, 20, 921140, "Executive and Legislative Offices, Combined"
    )
    AMERICAN_INDIAN_AND_ALASKA_NATIVE_TRIBAL_GOVERNMENTS = LkOccupationTitle(
        1336, 20, 921150, "American Indian and Alaska Native Tribal Governments"
    )
    OTHER_GENERAL_GOVERNMENT_SUPPORT = LkOccupationTitle(
        1337, 20, 921190, "Other General Government Support"
    )
    JUSTICE_PUBLIC_ORDER_AND_SAFETY_ACTIVITIES = LkOccupationTitle(
        1338, 20, 9221, "Justice, Public Order, and Safety Activities"
    )
    COURTS = LkOccupationTitle(1339, 20, 922110, "Courts")
    POLICE_PROTECTION = LkOccupationTitle(1340, 20, 922120, "Police Protection")
    LEGAL_COUNSEL_AND_PROSECUTION = LkOccupationTitle(
        1341, 20, 922130, "Legal Counsel and Prosecution"
    )
    CORRECTIONAL_INSTITUTIONS = LkOccupationTitle(1342, 20, 922140, "Correctional Institutions")
    PAROLE_OFFICES_AND_PROBATION_OFFICES = LkOccupationTitle(
        1343, 20, 922150, "Parole Offices and Probation Offices"
    )
    FIRE_PROTECTION = LkOccupationTitle(1344, 20, 922160, "Fire Protection")
    OTHER_JUSTICE_PUBLIC_ORDER_AND_SAFETY_ACTIVITIES = LkOccupationTitle(
        1345, 20, 922190, "Other Justice, Public Order, and Safety Activities"
    )
    ADMINISTRATION_OF_HUMAN_RESOURCE_PROGRAMS = LkOccupationTitle(
        1346, 20, 9231, "Administration of Human Resource Programs"
    )
    ADMINISTRATION_OF_EDUCATION_PROGRAMS = LkOccupationTitle(
        1347, 20, 923110, "Administration of Education Programs"
    )
    ADMINISTRATION_OF_HUMAN_RESOURCE_PROGRAMS_EXCEPT_EDUCATION_PUBLIC_HEALTH_AND_VETERANS_AFFAIRS_PROGRAMS = LkOccupationTitle(
        1348,
        20,
        923130,
        "Administration of Human Resource Programs (except Education, Public Health, and Veterans' Affairs Programs)",
    )
    ADMINISTRATION_OF_VETERANS_AFFAIRS = LkOccupationTitle(
        1349, 20, 923140, "Administration of Veterans' Affairs"
    )
    ADMINISTRATION_OF_ENVIRONMENTAL_QUALITY_PROGRAMS = LkOccupationTitle(
        1350, 20, 9241, "Administration of Environmental Quality Programs"
    )
    ADMINISTRATION_OF_AIR_AND_WATER_RESOURCE_AND_SOLID_WASTE_MANAGEMENT_PROGRAMS = LkOccupationTitle(
        1351,
        20,
        924110,
        "Administration of Air and Water Resource and Solid Waste Management Programs",
    )
    ADMINISTRATION_OF_CONSERVATION_PROGRAMS = LkOccupationTitle(
        1352, 20, 924120, "Administration of Conservation Programs"
    )
    ADMINISTRATION_OF_HOUSING_PROGRAMS_URBAN_PLANNING_AND_COMMUNITY_DEVELOPMENT = LkOccupationTitle(
        1353,
        20,
        9251,
        "Administration of Housing Programs, Urban Planning, and Community Development",
    )
    ADMINISTRATION_OF_HOUSING_PROGRAMS = LkOccupationTitle(
        1354, 20, 925110, "Administration of Housing Programs"
    )
    ADMINISTRATION_OF_URBAN_PLANNING_AND_COMMUNITY_AND_RURAL_DEVELOPMENT = LkOccupationTitle(
        1355, 20, 925120, "Administration of Urban Planning and Community and Rural Development"
    )
    ADMINISTRATION_OF_ECONOMIC_PROGRAMS = LkOccupationTitle(
        1356, 20, 9261, "Administration of Economic Programs"
    )
    ADMINISTRATION_OF_GENERAL_ECONOMIC_PROGRAMS = LkOccupationTitle(
        1357, 20, 926110, "Administration of General Economic Programs"
    )
    REGULATION_AND_ADMINISTRATION_OF_TRANSPORTATION_PROGRAMS = LkOccupationTitle(
        1358, 20, 926120, "Regulation and Administration of Transportation Programs"
    )
    REGULATION_AND_ADMINISTRATION_OF_COMMUNICATIONS_ELECTRIC_GAS_AND_OTHER_UTILITIES = LkOccupationTitle(
        1359,
        20,
        926130,
        "Regulation and Administration of Communications, Electric, Gas, and Other Utilities",
    )
    REGULATION_OF_AGRICULTURAL_MARKETING_AND_COMMODITIES = LkOccupationTitle(
        1360, 20, 926140, "Regulation of Agricultural Marketing and Commodities"
    )
    REGULATION_LICENSING_AND_INSPECTION_OF_MISCELLANEOUS_COMMERCIAL_SECTORS = LkOccupationTitle(
        1361,
        20,
        926150,
        "Regulation, Licensing, and Inspection of Miscellaneous Commercial Sectors",
    )
    SPACE_RESEARCH_AND_TECHNOLOGY_4 = LkOccupationTitle(
        1362, 20, 9271, "Space Research and Technology"
    )
    SPACE_RESEARCH_AND_TECHNOLOGY = LkOccupationTitle(
        1363, 20, 927110, "Space Research and Technology"
    )
    NATIONAL_SECURITY_AND_INTERNATIONAL_AFFAIRS = LkOccupationTitle(
        1364, 20, 9281, "National Security and International Affairs"
    )
    NATIONAL_SECURITY = LkOccupationTitle(1365, 20, 928110, "National Security")
    INTERNATIONAL_AFFAIRS = LkOccupationTitle(1366, 20, 928120, "International Affairs")


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
    OccupationTitle.sync_to_database(db_session)
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
