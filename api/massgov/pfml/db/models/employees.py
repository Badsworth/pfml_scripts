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
from sqlalchemy.types import JSON, TypeEngine

from ..lookup import LookupTable
from .base import Base, TimestampMixin, utc_timestamp_gen, uuid_gen
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
    sort_order = Column(Integer, default=0, nullable=False)
    # use to set order when sorting (non alphabetic) by absence status

    def __init__(self, absence_status_id, absence_status_description, sort_order):
        self.absence_status_id = absence_status_id
        self.absence_status_description = absence_status_description
        self.sort_order = sort_order


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
    fineos_gender_description = Column(Text, nullable=True)

    def __init__(self, gender_id, gender_description, fineos_gender_description):
        self.gender_id = gender_id
        self.gender_description = gender_description
        self.fineos_gender_description = fineos_gender_description


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


class LkLeaveRequestDecision(Base):
    __tablename__ = "lk_leave_request_decision"
    leave_request_decision_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_request_decision_description = Column(Text)

    def __init__(self, leave_request_decision_id, leave_request_decision_description):
        self.leave_request_decision_id = leave_request_decision_id
        self.leave_request_decision_description = leave_request_decision_description


class AbsencePeriod(Base, TimestampMixin):
    __tablename__ = "absence_period"
    __table_args__ = (
        UniqueConstraint(
            "fineos_absence_period_index_id",
            "fineos_absence_period_class_id",
            name="uix_absence_period_index_id_absence_period_class_id",
        ),
    )

    absence_period_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True, nullable=False)
    fineos_absence_period_class_id = Column(Integer, nullable=False, index=True)
    fineos_absence_period_index_id = Column(Integer, nullable=False, index=True)
    fineos_leave_request_id = Column(Integer)
    absence_period_start_date = Column(Date)
    absence_period_end_date = Column(Date)
    leave_request_decision_id = Column(
        Integer, ForeignKey("lk_leave_request_decision.leave_request_decision_id"), nullable=False
    )
    is_id_proofed = Column(Boolean)
    claim_type_id = Column(Integer, ForeignKey("lk_claim_type.claim_type_id"), nullable=False)

    claim = relationship("Claim")
    claim_type = relationship(LkClaimType)
    leave_request_decision = relationship(LkLeaveRequestDecision)


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


class Employer(Base, TimestampMixin):
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
    fineos_employer_id = Column(Integer, index=True, unique=True)

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
        PostgreSQLUUID, ForeignKey("employer.employer_id"), index=True, primary_key=True
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


class PubEft(Base, TimestampMixin):
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
    prenote_approved_at = Column(TIMESTAMP(timezone=True))
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


class Employee(Base, TimestampMixin):
    __tablename__ = "employee"
    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    tax_identifier_id = Column(
        UUID(as_uuid=True), ForeignKey("tax_identifier.tax_identifier_id"), index=True, unique=True,
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


class Claim(Base, TimestampMixin):
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

    # Not sure if these are currently used.
    authorized_representative_id = Column(UUID(as_uuid=True))
    benefit_amount = Column(Numeric(asdecimal=True))
    benefit_days = Column(Integer)

    claim_type = relationship(LkClaimType)
    fineos_absence_status = cast(Optional[LkAbsenceStatus], relationship(LkAbsenceStatus))
    employee = relationship("Employee", back_populates="claims")
    employer = relationship("Employer", back_populates="claims")
    state_logs = relationship("StateLog", back_populates="claim")
    payments: "Query[Payment]" = dynamic_loader("Payment", back_populates="claim")
    managed_requirements = cast(
        Optional[List["ManagedRequirement"]],
        relationship("ManagedRequirement", back_populates="claim"),
    )


class Payment(Base, TimestampMixin):
    __tablename__ = "payment"
    payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True)
    payment_transaction_type_id = Column(
        Integer, ForeignKey("lk_payment_transaction_type.payment_transaction_type_id")
    )
    period_start_date = Column(Date)
    period_end_date = Column(Date)
    payment_date = Column(Date)
    absence_case_creation_date = Column(Date)
    amount = Column(Numeric(asdecimal=True), nullable=False)
    fineos_pei_c_value = Column(Text, index=True)
    fineos_pei_i_value = Column(Text, index=True)
    is_adhoc_payment = Column(Boolean, default=False, server_default="FALSE")
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
    claim_type_id = Column(Integer, ForeignKey("lk_claim_type.claim_type_id"))
    leave_request_id = Column(UUID(as_uuid=True), ForeignKey("absence_period.absence_period_id"))

    claim = relationship("Claim", back_populates="payments")
    claim_type = relationship(LkClaimType)
    payment_transaction_type = relationship(LkPaymentTransactionType)
    disb_method = relationship(LkPaymentMethod, foreign_keys=disb_method_id)
    pub_eft = relationship(PubEft)
    experian_address_pair = relationship(ExperianAddressPair, foreign_keys=experian_address_pair_id)
    fineos_extract_import_log = relationship("ImportLog")
    reference_files = relationship("PaymentReferenceFile", back_populates="payment")
    state_logs = relationship("StateLog", back_populates="payment")
    # fineos_writeback_details = relationship("FineosWritebackDetails", back_populates="payment", uselist=False)

    check = relationship("PaymentCheck", backref="payment", uselist=False)


class PaymentCheck(Base, TimestampMixin):
    __tablename__ = "payment_check"
    payment_id = Column(PostgreSQLUUID, ForeignKey(Payment.payment_id), primary_key=True)
    check_number = Column(Integer, nullable=False, index=True, unique=True)
    check_posted_date = Column(Date)
    payment_check_status_id = Column(
        Integer, ForeignKey("lk_payment_check_status.payment_check_status_id")
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


class User(Base, TimestampMixin):
    __tablename__ = "user"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    active_directory_id = deferred(
        Column(Text().evaluates_none(), index=True, unique=True)
    )  # renaming to sub_id
    sub_id = Column(Text, index=True, unique=True)
    email_address = Column(Text)
    consented_to_data_sharing = Column(Boolean, default=False, nullable=False)

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


class UserRole(Base, TimestampMixin):
    __tablename__ = "link_user_role"
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("lk_role.role_id"), primary_key=True)

    user = relationship(User)
    role = relationship(LkRole)


class LkWorksite(Base):
    __tablename__ = "lk_worksite"
    worksite_id = Column(Integer, primary_key=True, autoincrement=True)
    worksite_description = Column(Text)
    worksite_fineos_id = Column(Text)

    def __init__(self, worksite_id, worksite_description, worksite_fineos_id):
        self.worksite_id = worksite_id
        self.worksite_description = worksite_description
        self.worksite_fineos_id = worksite_fineos_id


class LkReportingUnit(Base):
    __tablename__ = "lk_reporting_unit"
    reporting_unit_id = Column(Integer, primary_key=True, autoincrement=True)
    reporting_unit_description = Column(Text)

    def __init__(self, reporting_unit_id, reporting_unit_description):
        self.reporting_unit_id = reporting_unit_id
        self.reporting_unit_description = reporting_unit_description


class LkUserLeaveAdminDepartment(Base):
    __tablename__ = "lk_user_leave_administrator_department"
    # there is no unique constraint matching given keys for referenced table "link_user_leave_administrator"    
    user_leave_administrator_id = Column(UUID(as_uuid=True), ForeignKey("link_user_leave_administrator.user_leave_administrator_id"), primary_key=True)
    reporting_unit_id = Column(Integer, ForeignKey("lk_reporting_unit.reporting_unit_id"), primary_key=True)

    reporting_unit = relationship(LkReportingUnit)


class UserLeaveAdministrator(Base, TimestampMixin):
    __tablename__ = "link_user_leave_administrator"
    __table_args__ = (UniqueConstraint("user_id", "employer_id"),)
    user_leave_administrator_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"), nullable=False)
    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=False)
    fineos_web_id = Column(Text)
    verification_id = Column(
        UUID(as_uuid=True), ForeignKey("verification.verification_id"), nullable=True
    )

    user = relationship(User)
    employer = relationship(Employer)
    verification = relationship(Verification)
    reporting_units = relationship(LkUserLeaveAdminDepartment)

    @typed_hybrid_property
    def has_fineos_registration(self) -> bool:
        """Indicates whether the leave admin exists in Fineos yet, signalling if Fineos
        API calls can be called on behalf of this leave admin yet"""
        return bool(self.fineos_web_id)

    @typed_hybrid_property
    def verified(self) -> bool:
        return bool(self.verification_id)


class LkManagedRequirementStatus(Base):
    __tablename__ = "lk_managed_requirement_status"
    managed_requirement_status_id = Column(Integer, primary_key=True, autoincrement=True)
    managed_requirement_status_description = Column(Text)

    def __init__(self, managed_requirement_status_id, managed_requirement_status_description):
        self.managed_requirement_status_id = managed_requirement_status_id
        self.managed_requirement_status_description = managed_requirement_status_description


class LkManagedRequirementCategory(Base):
    __tablename__ = "lk_managed_requirement_category"
    managed_requirement_category_id = Column(Integer, primary_key=True, autoincrement=True)
    managed_requirement_category_description = Column(Text)

    def __init__(self, managed_requirement_category_id, managed_requirement_category_description):
        self.managed_requirement_category_id = managed_requirement_category_id
        self.managed_requirement_category_description = managed_requirement_category_description


class LkManagedRequirementType(Base):
    __tablename__ = "lk_managed_requirement_type"
    managed_requirement_type_id = Column(Integer, primary_key=True, autoincrement=True)
    managed_requirement_type_description = Column(Text)

    def __init__(self, managed_requirement_type_id, managed_requirement_type_description):
        self.managed_requirement_type_id = managed_requirement_type_id
        self.managed_requirement_type_description = managed_requirement_type_description


class ManagedRequirement(Base, TimestampMixin):
    """PFML-relevant data from a Managed Requirement in Fineos. Example managed requirement is an Employer info request."""

    __tablename__ = "managed_requirement"
    managed_requirement_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True, nullable=False)
    respondent_user_id = Column(UUID(as_uuid=True), ForeignKey("user.user_id"))
    fineos_managed_requirement_id = Column(Text, unique=True, nullable=False)
    follow_up_date = Column(Date)
    responded_at = Column(TIMESTAMP(timezone=True))
    managed_requirement_status_id = Column(
        Integer,
        ForeignKey("lk_managed_requirement_status.managed_requirement_status_id"),
        nullable=False,
    )
    managed_requirement_category_id = Column(
        Integer,
        ForeignKey("lk_managed_requirement_category.managed_requirement_category_id"),
        nullable=False,
    )
    managed_requirement_type_id = Column(
        Integer,
        ForeignKey("lk_managed_requirement_type.managed_requirement_type_id"),
        nullable=False,
    )

    managed_requirement_status = relationship(LkManagedRequirementStatus)
    managed_requirement_category = relationship(LkManagedRequirementCategory)
    managed_requirement_type = relationship(LkManagedRequirementType)

    claim = relationship("Claim", back_populates="managed_requirements")
    respondent_user = relationship(User)


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


class ReferenceFile(Base, TimestampMixin):
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
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True)
    prev_state_log_id = Column(UUID(as_uuid=True), ForeignKey("state_log.state_log_id"))
    associated_type = Column(Text, index=True)

    import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True, nullable=True,
    )
    end_state = cast("Optional[LkState]", relationship(LkState, foreign_keys=[end_state_id]))
    payment = relationship("Payment", back_populates="state_logs")
    reference_file = relationship("ReferenceFile", back_populates="state_logs")
    employee = relationship("Employee", back_populates="state_logs")
    claim = relationship("Claim", back_populates="state_logs")
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
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claim.claim_id"), index=True)
    reference_file_id = Column(
        UUID(as_uuid=True), ForeignKey("reference_file.reference_file_id"), index=True
    )

    state_log = relationship("StateLog")
    payment = relationship("Payment")
    employee = relationship("Employee")
    claim = relationship("Claim")
    reference_file = relationship("ReferenceFile")


class DuaReductionPayment(Base, TimestampMixin):
    __tablename__ = "dua_reduction_payment"
    dua_reduction_payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    fineos_customer_number = Column(Text, nullable=False)
    employer_fein = Column(Text)
    payment_date = Column(Date)
    request_week_begin_date = Column(Date)
    gross_payment_amount_cents = Column(Integer)
    payment_amount_cents = Column(Integer)
    fraud_indicator = Column(Text)
    benefit_year_begin_date = Column(Date)
    benefit_year_end_date = Column(Date)

    # Each row should be unique. This enables us to load only new rows from a CSV and ensures that
    # we don't include payments twice as two different rows. Almost all fields are nullable so we
    # have to coalesce those null values to empty strings. We've manually adjusted the migration
    # that adds this unique constraint to coalesce those nullable fields.
    # See: 2021_01_29_15_51_16_14155f78d8e6_create_dua_reduction_payment_table.py


class DiaReductionPayment(Base, TimestampMixin):
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
    termination_date = Column(Date)

    # Each row should be unique.


class PubError(Base, TimestampMixin):
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
    column_names = ("absence_status_id", "absence_status_description", "sort_order")

    ADJUDICATION = LkAbsenceStatus(1, "Adjudication", 2)
    APPROVED = LkAbsenceStatus(2, "Approved", 5)
    CLOSED = LkAbsenceStatus(3, "Closed", 7)
    COMPLETED = LkAbsenceStatus(4, "Completed", 6)
    DECLINED = LkAbsenceStatus(5, "Declined", 4)
    IN_REVIEW = LkAbsenceStatus(6, "In Review", 3)
    INTAKE_IN_PROGRESS = LkAbsenceStatus(7, "Intake In Progress", 1)


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


class ManagedRequirementStatus(LookupTable):
    model = LkManagedRequirementStatus
    column_names = ("managed_requirement_status_id", "managed_requirement_status_description")

    OPEN = LkManagedRequirementStatus(1, "Open")
    COMPLETE = LkManagedRequirementStatus(2, "Complete")
    SUPPRESSED = LkManagedRequirementStatus(3, "Suppressed")


class ManagedRequirementCategory(LookupTable):
    model = LkManagedRequirementCategory
    column_names = ("managed_requirement_category_id", "managed_requirement_category_description")

    EMPLOYER_CONFIRMATION = LkManagedRequirementCategory(1, "Employer Confirmation")


class ManagedRequirementType(LookupTable):
    model = LkManagedRequirementType
    column_names = ("managed_requirement_type_id", "managed_requirement_type_description")

    EMPLOYER_CONFIRMATION = LkManagedRequirementType(1, "Employer Confirmation of Leave Data")


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
    column_names = ("gender_id", "gender_description", "fineos_gender_description")
    WOMAN = LkGender(1, "Woman", "Female")
    MAN = LkGender(2, "Man", "Male")
    NONBINARY = LkGender(3, "Non-binary", "Neutral")
    NOT_LISTED = LkGender(4, "Gender not listed", "Unknown")
    NO_ANSWER = LkGender(5, "Prefer not to answer", "Not Provided")


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
    DELEGATED_CLAIM_VALIDATION = LkFlow(23, "Claim Validation")
    DELEGATED_PEI_WRITEBACK = LkFlow(24, "Payment PEI Writeback")


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
    # not used, see DUA_REDUCTIONS_REPORT_SENT
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

    DIA_REPORT_FOR_DFML_CREATED = LkState(
        162, "Create DIA report for DFML", Flow.DFML_AGENCY_REDUCTION_REPORT.flow_id
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

    DELEGATED_PAYMENT_PROCESSED_ZERO_PAYMENT = LkState(
        122, "Processed - $0 payment", Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_ZERO_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        123, "DEPRECATED STATE - Add $0 payment to FINEOS Writeback", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_ZERO_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        124, "DEPRECATED STATE - $0 payment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT = LkState(
        125, "Processed - overpayment", Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_OVERPAYMENT_TO_FINEOS_WRITEBACK = LkState(
        126,
        "DEPRECATED STATE - Add overpayment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPREACTED_DELEGATED_PAYMENT_OVERPAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        127, "DEPRECATED STATE - Overpayment FINEOS Writeback sent", Flow.DELEGATED_PAYMENT.flow_id
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

    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_CHECK_SENT = LkState(
        158, "FINEOS Writeback sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT = LkState(
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
    DELEGATED_PAYMENT_PROCESSED_CANCELLATION = LkState(
        145, "Processed - Cancellation", Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_CANCELLATION_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        146,
        "DEPRECATED STATE - Add cancellation payment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_CANCELLATION_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        147,
        "DEPRECATED STATE - cancellation payment FINEOS Writeback sent",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    # Report states for employer reimbursement payment states
    DELEGATED_PAYMENT_PROCESSED_EMPLOYER_REIMBURSEMENT = LkState(
        148, "Processed - Employer Reimbursement", Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_ADD_EMPLOYER_REIMBURSEMENT_PAYMENT_TO_FINEOS_WRITEBACK = LkState(
        149,
        "DEPRECATED STATE - Add employer reimbursement payment to FINEOS Writeback",
        Flow.DELEGATED_PAYMENT.flow_id,
    )
    DEPRECATED_DELEGATED_PAYMENT_EMPLOYER_REIMBURSEMENT_PAYMENT_FINEOS_WRITEBACK_SENT = LkState(
        150,
        "DEPRECATED STATE - Employer reimbursement payment FINEOS Writeback sent",
        Flow.DELEGATED_PAYMENT.flow_id,
    )

    # PEI WRITE BACK ERROR TO FINEOS
    # These states are not retryable because this is erroring after we've sent a payment to PUB
    # If there was an error, it will require a manual effort to fix.
    DEPRECATED_ADD_TO_ERRORED_PEI_WRITEBACK = LkState(
        151, "DEPRECATED STATE - Add to Errored PEI writeback", Flow.DELEGATED_PAYMENT.flow_id
    )

    DEPREACTED_ERRORED_PEI_WRITEBACK_SENT = LkState(
        152,
        "DEPRECATED STATE - Errored PEI write back sent to FINEOS",
        Flow.DELEGATED_PAYMENT.flow_id,
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
    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_ADD_CHECK = LkState(
        160, "DEPRECATED STATE - Add to FINEOS Writeback #2 - Check", Flow.DELEGATED_PAYMENT.flow_id
    )
    DEPRECATED_DELEGATED_PAYMENT_FINEOS_WRITEBACK_2_SENT_CHECK = LkState(
        161, "DEPRECATED STATE - FINEOS Writeback #2 sent - Check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_POST_PROCESSING_CHECK = LkState(
        163, "Delegated payment post processing check", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_CLAIM_EXTRACTED_FROM_FINEOS = LkState(
        164, "Claim extracted from FINEOS", Flow.DELEGATED_CLAIM_VALIDATION.flow_id
    )
    DELEGATED_CLAIM_ADD_TO_CLAIM_EXTRACT_ERROR_REPORT = LkState(
        165, "Add to Claim Extract Error Report", Flow.DELEGATED_CLAIM_VALIDATION.flow_id
    )

    ### Generic states used to send payment transaction statuses back to FINEOS
    ###  without preventing us from receiving them again in subsequent extracts
    DELEGATED_ADD_TO_FINEOS_WRITEBACK = LkState(
        170, "Add to FINEOS writeback", Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DELEGATED_FINEOS_WRITEBACK_SENT = LkState(
        171, "FINEOS writeback sent", Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )

    # Deprecated writeback states
    DEPRECATED_ADD_AUDIT_REJECT_TO_FINEOS_WRITEBACK = LkState(
        172,
        "DEPRECATED STATE - Add audit reject to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_AUDIT_REJECT_FINEOS_WRITEBACK_SENT = LkState(
        173,
        "DEPRECATED STATE - Audit reject FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_ADD_AUTOMATED_VALIDATION_ERROR_TO_FINEOS_WRITEBACK = LkState(
        174,
        "DEPRECATED STATE - Add automated validation error to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_AUTOMATED_VALIDATION_ERROR_FINEOS_WRITEBACK_SENT = LkState(
        175,
        "DEPRECATED STATE - Automated validation error FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_ADD_PENDING_PRENOTE_TO_FINEOS_WRITEBACK = LkState(
        176,
        "DEPRECATED STATE - Add pending prenote to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_PENDING_PRENOTE_FINEOS_WRITEBACK_SENT = LkState(
        177,
        "DEPRECATED STATE - Pending prenote FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_ADD_PRENOTE_REJECTED_ERROR_TO_FINEOS_WRITEBACK = LkState(
        178,
        "DEPRECATED STATE - Add prenote rejected error to FINEOS writeback",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )
    DEPRECATED_PRENOTE_REJECTED_ERROR_FINEOS_WRITEBACK_SENT = LkState(
        179,
        "DEPRECATED STATE - Prenote rejected error FINEOS writeback sent",
        Flow.DELEGATED_PEI_WRITEBACK.flow_id,
    )

    # Restartable error states. Payments in these states will be accepted
    # on subsequent runs of processing (assuming no other issues).
    DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE = LkState(
        180, "Add to Payment Error Report - RESTARTABLE", Flow.DELEGATED_PAYMENT.flow_id
    )

    DELEGATED_PAYMENT_ADD_TO_PAYMENT_REJECT_REPORT_RESTARTABLE = LkState(
        181, "Add to Payment Reject Report - RESTARTABLE", Flow.DELEGATED_PAYMENT.flow_id
    )

    # Payment was rejected as part of a PUB ACH or Check return file processing
    # Replaces deprecated DEPRECATED_ADD_TO_ERRORED_PEI_WRITEBACK and DEPREACTED_ERRORED_PEI_WRITEBACK_SENT states as part of transition to generic writeback flow
    DELEGATED_PAYMENT_ERROR_FROM_BANK = LkState(
        182, "Payment Errored from Bank", Flow.DELEGATED_PAYMENT.flow_id
    )

    # This state signifies that a payment was successfully sent, but the
    # bank told us it had issues that may prevent payment in the future
    DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION = LkState(
        183, "Payment Complete with change notification", Flow.DELEGATED_PAYMENT.flow_id
    )

    DIA_REDUCTIONS_REPORT_ERROR = LkState(
        184,
        "Error sending DIA reductions payments report to DFML",
        Flow.DFML_DIA_REDUCTION_REPORT.flow_id,
    )

    DUA_REDUCTIONS_REPORT_ERROR = LkState(
        185,
        "Error sending DUA reductions payments report to DFML",
        Flow.DFML_DUA_REDUCTION_REPORT.flow_id,
    )

    DIA_PAYMENT_LIST_ERROR_SAVE_TO_DB = LkState(
        186, "Error saving new DIA payments in database", Flow.DIA_PAYMENT_LIST.flow_id
    )

    DUA_PAYMENT_LIST_ERROR_SAVE_TO_DB = LkState(
        187, "Error saving new DUA payments in database", Flow.DUA_PAYMENT_LIST.flow_id
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
    OVERPAYMENT_ACTUAL_RECOVERY = LkPaymentTransactionType(7, "Overpayment Actual Recovery")
    OVERPAYMENT_RECOVERY = LkPaymentTransactionType(8, "Overpayment Recovery")
    OVERPAYMENT_ADJUSTMENT = LkPaymentTransactionType(9, "Overpayment Adjustment")
    OVERPAYMENT_RECOVERY_REVERSE = LkPaymentTransactionType(10, "Overpayment Recovery Reverse")
    OVERPAYMENT_RECOVERY_CANCELLATION = LkPaymentTransactionType(
        11, "Overpayment Recovery Cancellation"
    )


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


class LeaveRequestDecision(LookupTable):
    model = LkLeaveRequestDecision
    column_names = ("leave_request_decision_id", "leave_request_decision_description")

    PENDING = LkLeaveRequestDecision(1, "Pending")
    IN_REVIEW = LkLeaveRequestDecision(2, "In Review")
    APPROVED = LkLeaveRequestDecision(3, "Approved")
    DENIED = LkLeaveRequestDecision(4, "Denied")


class Worksite(LookupTable):
    model = LkWorksite
    column_names = ("worksite_id", "worksite_description", "worksite_fineos_id")

    DFML = LkWorksite(1, "DFML", None)


class ReportingUnit(LookupTable):
    model = LkReportingUnit
    column_names = ("reporting_unit_id", "reporting_unit_description")

    DFML = LkReportingUnit(1, "DFML")
    PFML = LkReportingUnit(2, "PFML")
    CCENTER = LkReportingUnit(3, "Contact Center")
    DEVOPS = LkReportingUnit(4, "DevOps")
    SAVILINX = LkReportingUnit(5, "Savilinx")
    HR = LkReportingUnit(6, "HR")


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
    ManagedRequirementStatus.sync_to_database(db_session)
    ManagedRequirementCategory.sync_to_database(db_session)
    ManagedRequirementType.sync_to_database(db_session)
    Worksite.sync_to_database(db_session)
    ReportingUnit.sync_to_database(db_session)
    db_session.commit()
