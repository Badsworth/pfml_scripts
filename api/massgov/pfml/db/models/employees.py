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
import re
from datetime import date, timedelta
from typing import TYPE_CHECKING, List, Optional, cast

from bouncer.constants import EDIT, READ  # noqa: F401 F403
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
    and_,
    desc,
    or_,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import Query, aliased, dynamic_loader, object_session, relationship, validates
from sqlalchemy.schema import Sequence
from sqlalchemy.sql.expression import func
from sqlalchemy.types import JSON

import massgov.pfml.util.logging
from massgov.pfml.util.datetime import utcnow

from ..lookup import LookupTable
from .absences import (
    LkAbsencePeriodType,
    LkAbsenceReason,
    LkAbsenceReasonQualifierOne,
    LkAbsenceReasonQualifierTwo,
    LkAbsenceStatus,
)
from .base import Base, TimestampMixin, utc_timestamp_gen, uuid_gen
from .common import PostgreSQLUUID
from .dua import DuaEmployeeDemographics
from .geo import LkCountry, LkGeoState
from .industry_codes import LkIndustryCode
from .state import LkState, State
from .verifications import Verification

# (typed_hybrid_property) https://github.com/dropbox/sqlalchemy-stubs/issues/98
if TYPE_CHECKING:
    # Use this to make hybrid_property's have the same typing as a normal property until stubs are improved.
    typed_hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property as typed_hybrid_property


logger = massgov.pfml.util.logging.get_logger(__name__)


class LkAddressType(Base):
    __tablename__ = "lk_address_type"
    address_type_id = Column(Integer, primary_key=True, autoincrement=True)
    address_description = Column(Text, nullable=False)

    def __init__(self, address_type_id, address_description):
        self.address_type_id = address_type_id
        self.address_description = address_description


class LkClaimType(Base):
    __tablename__ = "lk_claim_type"
    claim_type_id = Column(Integer, primary_key=True, autoincrement=True)
    claim_type_description = Column(Text, nullable=False)

    def __init__(self, claim_type_id, claim_type_description):
        self.claim_type_id = claim_type_id
        self.claim_type_description = claim_type_description


class LkRace(Base):
    __tablename__ = "lk_race"
    race_id = Column(Integer, primary_key=True)
    race_description = Column(Text, nullable=False)

    def __init__(self, race_id, race_description):
        self.race_id = race_id
        self.race_description = race_description


class LkMaritalStatus(Base):
    __tablename__ = "lk_marital_status"
    marital_status_id = Column(Integer, primary_key=True, autoincrement=True)
    marital_status_description = Column(Text, nullable=False)

    def __init__(self, marital_status_id, marital_status_description):
        self.marital_status_id = marital_status_id
        self.marital_status_description = marital_status_description


class LkGender(Base):
    __tablename__ = "lk_gender"
    gender_id = Column(Integer, primary_key=True, autoincrement=True)
    gender_description = Column(Text, nullable=False)
    fineos_gender_description = Column(Text, nullable=True)

    def __init__(self, gender_id, gender_description, fineos_gender_description):
        self.gender_id = gender_id
        self.gender_description = gender_description
        self.fineos_gender_description = fineos_gender_description


class LkOccupation(Base):
    __tablename__ = "lk_occupation"
    occupation_id = Column(Integer, primary_key=True)
    occupation_description = Column(Text, nullable=False)

    def __init__(self, occupation_id, occupation_description):
        self.occupation_id = occupation_id
        self.occupation_description = occupation_description


class LkEducationLevel(Base):
    __tablename__ = "lk_education_level"
    education_level_id = Column(Integer, primary_key=True, autoincrement=True)
    education_level_description = Column(Text, nullable=False)

    def __init__(self, education_level_id, education_level_description):
        self.education_level_id = education_level_id
        self.education_level_description = education_level_description


class LkRole(Base):
    __tablename__ = "lk_role"
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_description = Column(Text, nullable=False)

    def __init__(self, role_id, role_description):
        self.role_id = role_id
        self.role_description = role_description


class LkPaymentMethod(Base):
    __tablename__ = "lk_payment_method"
    payment_method_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_method_description = Column(Text, nullable=False)

    def __init__(self, payment_method_id, payment_method_description):
        self.payment_method_id = payment_method_id
        self.payment_method_description = payment_method_description


class LkBankAccountType(Base):
    __tablename__ = "lk_bank_account_type"
    bank_account_type_id = Column(Integer, primary_key=True, autoincrement=True)
    bank_account_type_description = Column(Text, nullable=False)

    def __init__(self, bank_account_type_id, bank_account_type_description):
        self.bank_account_type_id = bank_account_type_id
        self.bank_account_type_description = bank_account_type_description


class LkPrenoteState(Base):
    __tablename__ = "lk_prenote_state"
    prenote_state_id = Column(Integer, primary_key=True, autoincrement=True)
    prenote_state_description = Column(Text, nullable=False)

    def __init__(self, prenote_state_id, prenote_state_description):
        self.prenote_state_id = prenote_state_id
        self.prenote_state_description = prenote_state_description


class LkPaymentRelevantParty(Base):
    __tablename__ = "lk_payment_relevant_party"
    payment_relevant_party_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_relevant_party_description = Column(Text, nullable=False)

    def __init__(self, payment_relevant_party_id, payment_relevant_party_description):
        self.payment_relevant_party_id = payment_relevant_party_id
        self.payment_relevant_party_description = payment_relevant_party_description


class LkPaymentTransactionType(Base):
    __tablename__ = "lk_payment_transaction_type"
    payment_transaction_type_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_transaction_type_description = Column(Text, nullable=False)

    def __init__(self, payment_transaction_type_id, payment_transaction_type_description):
        self.payment_transaction_type_id = payment_transaction_type_id
        self.payment_transaction_type_description = payment_transaction_type_description


class LkPaymentCheckStatus(Base):
    __tablename__ = "lk_payment_check_status"
    payment_check_status_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_check_status_description = Column(Text, nullable=False)

    def __init__(self, payment_check_status_id, payment_check_status_description):
        self.payment_check_status_id = payment_check_status_id
        self.payment_check_status_description = payment_check_status_description


class LkReferenceFileType(Base):
    __tablename__ = "lk_reference_file_type"
    reference_file_type_id = Column(Integer, primary_key=True, autoincrement=True)
    reference_file_type_description = Column(Text, nullable=False)
    num_files_in_set = Column(Integer)

    def __init__(self, reference_file_type_id, reference_file_type_description, num_files_in_set):
        self.reference_file_type_id = reference_file_type_id
        self.reference_file_type_description = reference_file_type_description
        self.num_files_in_set = num_files_in_set


class LkTitle(Base):
    __tablename__ = "lk_title"
    title_id = Column(Integer, primary_key=True, autoincrement=True)
    title_description = Column(Text, nullable=False)

    def __init__(self, title_id, title_description):
        self.title_id = title_id
        self.title_description = title_description


class LkLeaveRequestDecision(Base):
    __tablename__ = "lk_leave_request_decision"
    leave_request_decision_id = Column(Integer, primary_key=True, autoincrement=True)
    leave_request_decision_description = Column(Text, nullable=False)

    def __init__(self, leave_request_decision_id, leave_request_decision_description):
        self.leave_request_decision_id = leave_request_decision_id
        self.leave_request_decision_description = leave_request_decision_description


class LkMFADeliveryPreference(Base):
    __tablename__ = "lk_mfa_delivery_preference"
    mfa_delivery_preference_id = Column(Integer, primary_key=True, autoincrement=True)
    mfa_delivery_preference_description = Column(Text, nullable=False)

    def __init__(self, mfa_delivery_preference_id, mfa_delivery_preference_description):
        self.mfa_delivery_preference_id = mfa_delivery_preference_id
        self.mfa_delivery_preference_description = mfa_delivery_preference_description

    @typed_hybrid_property
    def description(self) -> str:
        return self.mfa_delivery_preference_description


class LkMFADeliveryPreferenceUpdatedBy(Base):
    __tablename__ = "lk_mfa_delivery_preference_updated_by"
    mfa_delivery_preference_updated_by_id = Column(Integer, primary_key=True, autoincrement=True)
    mfa_delivery_preference_updated_by_description = Column(Text, nullable=False)

    def __init__(
        self, mfa_delivery_preference_updated_by_id, mfa_delivery_preference_updated_by_description
    ):
        self.mfa_delivery_preference_updated_by_id = mfa_delivery_preference_updated_by_id
        self.mfa_delivery_preference_updated_by_description = (
            mfa_delivery_preference_updated_by_description
        )

    @typed_hybrid_property
    def description(self) -> str:
        return self.mfa_delivery_preference_updated_by_description


class AbsencePeriod(Base, TimestampMixin):
    __tablename__ = "absence_period"
    __table_args__ = (
        UniqueConstraint(
            "fineos_absence_period_index_id",
            "fineos_absence_period_class_id",
            name="uix_absence_period_index_id_absence_period_class_id",
        ),
    )

    absence_period_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    absence_period_start_date = Column(Date)
    absence_period_end_date = Column(Date)
    absence_period_type_id = Column(
        Integer, ForeignKey("lk_absence_period_type.absence_period_type_id")
    )
    absence_reason_qualifier_one_id = Column(
        Integer, ForeignKey("lk_absence_reason_qualifier_one.absence_reason_qualifier_one_id")
    )
    absence_reason_qualifier_two_id = Column(
        Integer, ForeignKey("lk_absence_reason_qualifier_two.absence_reason_qualifier_two_id")
    )
    absence_reason_id = Column(Integer, ForeignKey("lk_absence_reason.absence_reason_id"))
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True, nullable=False)
    fineos_absence_period_class_id = Column(Integer, nullable=False, index=True)
    fineos_absence_period_index_id = Column(Integer, nullable=False, index=True)
    fineos_leave_request_id = Column(Integer, index=True)
    fineos_average_weekly_wage = Column(Numeric(asdecimal=True))
    leave_request_decision_id = Column(
        Integer, ForeignKey("lk_leave_request_decision.leave_request_decision_id")
    )
    is_id_proofed = Column(Boolean)

    claim = relationship("Claim")
    absence_period_type = relationship(LkAbsencePeriodType)
    absence_reason = relationship(LkAbsenceReason)
    absence_reason_qualifier_one = relationship(LkAbsenceReasonQualifierOne)
    absence_reason_qualifier_two = relationship(LkAbsenceReasonQualifierTwo)
    leave_request_decision = relationship(LkLeaveRequestDecision)

    @property
    def has_final_decision(self):
        return self.leave_request_decision_id not in [
            LeaveRequestDecision.PENDING.leave_request_decision_id,
            LeaveRequestDecision.IN_REVIEW.leave_request_decision_id,
            LeaveRequestDecision.PROJECTED.leave_request_decision_id,
            None,
        ]


class AuthorizedRepresentative(Base, TimestampMixin):
    __tablename__ = "authorized_representative"
    authorized_representative_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    first_name = Column(Text)
    last_name = Column(Text)

    employees = relationship("AuthorizedRepEmployee", back_populates="authorized_rep")


class HealthCareProvider(Base, TimestampMixin):
    __tablename__ = "health_care_provider"
    health_care_provider_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    provider_name = Column(Text)

    addresses = relationship("HealthCareProviderAddress", back_populates="health_care_provider")


class OrganizationUnit(Base, TimestampMixin):
    __tablename__ = "organization_unit"
    __table_args__ = (
        UniqueConstraint("name", "employer_id", name="uix_organization_unit_name_employer_id"),
    )
    organization_unit_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    fineos_id = Column(Text, nullable=True, unique=True)
    name = Column(Text, nullable=False)
    employer_id = Column(
        PostgreSQLUUID, ForeignKey("employer.employer_id"), nullable=False, index=True
    )

    employer = relationship("Employer")
    dua_reporting_units: "Query[DuaReportingUnit]" = dynamic_loader(
        "DuaReportingUnit", back_populates="organization_unit"
    )

    @validates("fineos_id")
    def validate_fineos_id(self, key: str, fineos_id: Optional[str]) -> Optional[str]:
        if not fineos_id:
            return fineos_id
        if not re.fullmatch(r"[A-Z]{2}:[0-9]{5}:[0-9]{10}", fineos_id):
            raise ValueError(
                f"Invalid fineos_id: {fineos_id}. Expected a format of AA:00001:0000000001"
            )
        return fineos_id


class EmployerQuarterlyContribution(Base, TimestampMixin):
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


class Employer(Base, TimestampMixin):
    __tablename__ = "employer"
    employer_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    account_key = Column(Text, index=True)
    employer_fein = Column(Text, nullable=False, index=True)
    employer_name = Column(Text)
    employer_dba = Column(Text)
    family_exemption = Column(Boolean)
    medical_exemption = Column(Boolean)
    exemption_commence_date = Column(Date)
    exemption_cease_date = Column(Date)
    dor_updated_date = Column(TIMESTAMP(timezone=True))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)
    fineos_employer_id = Column(Integer, index=True, unique=True)
    industry_code_id = Column(Integer, ForeignKey("lk_industry_code.industry_code_id"))

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
    employer_quarterly_contribution = relationship(
        "EmployerQuarterlyContribution", back_populates="employer"
    )
    employee_benefit_year_contributions: "Query[BenefitYearContribution]" = dynamic_loader(
        "BenefitYearContribution", back_populates="employer"
    )

    lk_industry_code = relationship(LkIndustryCode)

    @property
    def organization_units(self) -> list[OrganizationUnit]:
        return (
            object_session(self)
            .query(OrganizationUnit)
            .filter(
                OrganizationUnit.employer_id == self.employer_id,
                OrganizationUnit.fineos_id.isnot(None),
            )
            .all()
        )

    @property
    def uses_organization_units(self):
        return any(self.organization_units)

    @typed_hybrid_property
    def verification_data(self) -> Optional[EmployerQuarterlyContribution]:
        """Get the most recent withholding data. Portal uses this data in order to verify a
        user can become a leave admin for this employer"""

        current_date = date.today()
        last_years_date = current_date - relativedelta(years=1)

        # Check the last four quarters. Does not include the current quarter, which would be a future filing period.
        non_zero_contribution = (
            object_session(self)
            .query(EmployerQuarterlyContribution)
            .filter(EmployerQuarterlyContribution.employer_id == self.employer_id)
            .filter(EmployerQuarterlyContribution.employer_total_pfml_contribution > 0)
            .filter(
                EmployerQuarterlyContribution.filing_period.between(last_years_date, current_date)
            )
            .order_by(desc(EmployerQuarterlyContribution.filing_period))
            .first()
        )

        if non_zero_contribution is None:
            # If this is a new or previously-exempt Employer to the program, we may not
            # have any non-zero contributions within the past year. We still want to support
            # verification for them, so for them we check future filing periods, which includes
            # the current quarter:
            non_zero_contribution = (
                object_session(self)
                .query(EmployerQuarterlyContribution)
                .filter(EmployerQuarterlyContribution.employer_id == self.employer_id)
                .filter(EmployerQuarterlyContribution.employer_total_pfml_contribution > 0)
                .filter(EmployerQuarterlyContribution.filing_period > current_date)
                .order_by(desc(EmployerQuarterlyContribution.filing_period))
                .first()
            )

        return non_zero_contribution

    @typed_hybrid_property
    def has_verification_data(self) -> bool:
        current_date = date.today()
        last_years_date = current_date - relativedelta(years=1)

        return any(
            quarter.employer_total_pfml_contribution > 0
            and quarter.filing_period >= last_years_date
            and quarter.filing_period <= current_date
            for quarter in self.employer_quarterly_contribution  # type: ignore
        ) or any(
            quarter.employer_total_pfml_contribution > 0 and quarter.filing_period > current_date
            for quarter in self.employer_quarterly_contribution  # type: ignore
        )

    @validates("employer_fein")
    def validate_employer_fein(self, key: str, employer_fein: str) -> str:
        fein = str(employer_fein)
        error = re.match(r"^[0-9]{9}$", fein) is None
        if error:
            raise ValueError(f"Invalid FEIN: {employer_fein}. Expected a 9-digit integer value")
        return employer_fein


class DuaReportingUnit(Base, TimestampMixin):
    __tablename__ = "dua_reporting_unit"
    __table_args__ = (UniqueConstraint("dua_id", "employer_id"),)
    dua_reporting_unit_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    dua_id = Column(Text, nullable=False)  # The Reporting Unit Number from DUA
    dba = Column(Text, nullable=True)
    employer_id = Column(PostgreSQLUUID, ForeignKey("employer.employer_id"), nullable=False)
    organization_unit_id = Column(
        PostgreSQLUUID,
        ForeignKey("organization_unit.organization_unit_id"),
        nullable=True,
        index=True,
    )

    employer = relationship(Employer)
    organization_unit = relationship("OrganizationUnit", back_populates="dua_reporting_units")


class EmployerPushToFineosQueue(Base, TimestampMixin):
    __tablename__ = "employer_push_to_fineos_queue"
    employer_push_to_fineos_queue_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    employer_id = Column(PostgreSQLUUID, index=True)
    action = Column(Text, index=True)
    modified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)
    process_id = Column(Integer, index=True)
    family_exemption = Column(Boolean)
    medical_exemption = Column(Boolean)
    exemption_commence_date = Column(Date)
    exemption_cease_date = Column(Date)


class EFT(Base, TimestampMixin):
    __tablename__ = "eft"
    eft_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    routing_nbr = Column(Text, nullable=False)
    account_nbr = Column(Text, nullable=False)
    bank_account_type_id = Column(
        Integer, ForeignKey("lk_bank_account_type.bank_account_type_id"), nullable=False
    )
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True)

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

    fineos_employee_first_name = Column(Text)
    fineos_employee_middle_name = Column(Text)
    fineos_employee_last_name = Column(Text)

    bank_account_type = relationship(LkBankAccountType)
    prenote_state = relationship(LkPrenoteState)

    employees = relationship("EmployeePubEftPair", back_populates="pub_eft")


class TaxIdentifier(Base, TimestampMixin):
    __tablename__ = "tax_identifier"
    tax_identifier_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    tax_identifier = Column(Text, nullable=False, unique=True)

    employee = relationship("Employee", back_populates="tax_identifier")

    @typed_hybrid_property
    def tax_identifier_last4(self) -> str:
        return self.tax_identifier[-4:]

    @tax_identifier_last4.expression
    def tax_identifier_last4(self):
        return func.right(TaxIdentifier.tax_identifier, 4)


class CtrAddressPair(Base, TimestampMixin):
    __tablename__ = "link_ctr_address_pair"
    fineos_address_id = Column(
        PostgreSQLUUID, ForeignKey("address.address_id"), primary_key=True, unique=True
    )
    ctr_address_id = Column(
        PostgreSQLUUID, ForeignKey("address.address_id"), nullable=True, index=True
    )

    fineos_address = relationship("Address", foreign_keys=fineos_address_id)
    ctr_address = cast("Optional[Address]", relationship("Address", foreign_keys=ctr_address_id))


class ExperianAddressPair(Base, TimestampMixin):
    __tablename__ = "link_experian_address_pair"
    fineos_address_id = Column(
        PostgreSQLUUID, ForeignKey("address.address_id"), primary_key=True, unique=True
    )
    experian_address_id = Column(
        PostgreSQLUUID, ForeignKey("address.address_id"), nullable=True, index=True
    )

    fineos_address = relationship("Address", foreign_keys=fineos_address_id)
    experian_address = cast(
        "Optional[Address]", relationship("Address", foreign_keys=experian_address_id)
    )


class EmployeeAddress(Base, TimestampMixin):
    __tablename__ = "link_employee_address"
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), primary_key=True)
    address_id = Column(PostgreSQLUUID, ForeignKey("address.address_id"), primary_key=True)

    employee = relationship("Employee", back_populates="employee_addresses")
    address = relationship("Address", back_populates="employees")


class Employee(Base, TimestampMixin):
    __tablename__ = "employee"
    employee_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    tax_identifier_id = Column(
        PostgreSQLUUID, ForeignKey("tax_identifier.tax_identifier_id"), index=True, unique=True
    )
    title_id = Column(Integer, ForeignKey("lk_title.title_id"))
    first_name = Column(Text, nullable=False, index=True)
    middle_name = Column(Text, index=True)
    last_name = Column(Text, nullable=False, index=True)
    other_name = Column(Text, index=True)
    email_address = Column(Text, index=True)
    phone_number = Column(Text, index=True)  # Formatted in E.164
    cell_phone_number = Column(Text, index=True)  # Formatted in E.164
    preferred_comm_method_type = Column(Text)
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    # https://lwd.atlassian.net/browse/PORTAL-439 will make this unique
    fineos_customer_number = Column(Text, nullable=True, index=True)
    race_id = Column(Integer, ForeignKey("lk_race.race_id"))
    marital_status_id = Column(Integer, ForeignKey("lk_marital_status.marital_status_id"))
    gender_id = Column(Integer, ForeignKey("lk_gender.gender_id"))
    occupation_id = Column(Integer, ForeignKey("lk_occupation.occupation_id"))
    education_level_id = Column(Integer, ForeignKey("lk_education_level.education_level_id"))
    latest_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)
    payment_method_id = Column(Integer, ForeignKey("lk_payment_method.payment_method_id"))
    ctr_vendor_customer_code = Column(Text)
    ctr_address_pair_id = Column(
        PostgreSQLUUID, ForeignKey("link_ctr_address_pair.fineos_address_id"), index=True
    )
    mass_id_number = Column(Text)
    out_of_state_id_number = Column(Text)

    fineos_employee_first_name = Column(Text, index=True)
    fineos_employee_middle_name = Column(Text, index=True)
    fineos_employee_last_name = Column(Text, index=True)

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
    addresses = relationship("Address", secondary=EmployeeAddress.__table__)
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
    employee_addresses: "Query[EmployeeAddress]" = dynamic_loader(
        "EmployeeAddress", back_populates="employee"
    )
    employee_occupations: "Query[EmployeeOccupation]" = dynamic_loader(
        "EmployeeOccupation", back_populates="employee"
    )

    benefit_years: "Query[BenefitYear]" = dynamic_loader("BenefitYear", back_populates="employee")
    employer_benefit_year_contributions: "Query[BenefitYearContribution]" = dynamic_loader(
        "BenefitYearContribution", back_populates="employee"
    )

    @property
    def latest_mass_id_number_from_id_proofed_applications(self) -> Optional[str]:
        # This is imported here to prevent circular import error
        from massgov.pfml.db.models.applications import Application

        application = (
            object_session(self)
            .query(Application)
            .join(Claim, Claim.claim_id == Application.claim_id)
            .filter(Claim.is_id_proofed, Claim.employee_id == self.employee_id)
            .order_by(desc(Claim.created_at))
            .first()
        )

        if application:
            return application.mass_id
        else:
            return None

    @hybrid_method
    def get_organization_units(self, employer: Employer) -> list[OrganizationUnit]:
        if not self.fineos_customer_number:
            return []
        return (
            object_session(self)
            .query(OrganizationUnit)
            .join(EmployeeOccupation)
            .join(DuaReportingUnit)
            .join(
                DuaEmployeeDemographics,
                and_(
                    DuaReportingUnit.dua_id
                    == DuaEmployeeDemographics.employer_reporting_unit_number,
                    DuaReportingUnit.employer_id == EmployeeOccupation.employer_id,
                ),
            )
            .filter(DuaEmployeeDemographics.fineos_customer_number == self.fineos_customer_number)
            .filter(
                OrganizationUnit.fineos_id is not None,
                DuaReportingUnit.organization_unit_id is not None,
                DuaEmployeeDemographics.employer_fein == employer.employer_fein,
                EmployeeOccupation.employee_id == self.employee_id,
                EmployeeOccupation.employer_id == employer.employer_id,
            )
            .distinct()
            .all()
        )


class EmployeePushToFineosQueue(Base, TimestampMixin):
    __tablename__ = "employee_push_to_fineos_queue"
    employee_push_to_fineos_queue_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    employee_id = Column(PostgreSQLUUID, index=True)
    action = Column(Text, index=True)
    modified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)
    process_id = Column(Integer, index=True)
    employer_id = Column(PostgreSQLUUID, index=True)


class EmployeePubEftPair(Base, TimestampMixin):
    __tablename__ = "link_employee_pub_eft_pair"
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), primary_key=True)
    pub_eft_id = Column(PostgreSQLUUID, ForeignKey("pub_eft.pub_eft_id"), primary_key=True)

    employee = relationship("Employee", back_populates="pub_efts")
    pub_eft = relationship("PubEft", back_populates="employees")


class LkChangeRequestType(Base):
    __tablename__ = "lk_change_request_type"

    change_request_type_id = Column(Integer, primary_key=True, autoincrement=True)
    change_request_type_description = Column(Text, nullable=False)

    def __init__(self, change_request_type_id, change_request_type_description):
        self.change_request_type_id = change_request_type_id
        self.change_request_type_description = change_request_type_description

    @typed_hybrid_property
    def description(self) -> str:
        return self.change_request_type_description


class ChangeRequest(Base, TimestampMixin):
    __tablename__ = "change_request"
    change_request_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    change_request_type_id = Column(
        Integer, ForeignKey("lk_change_request_type.change_request_type_id"), nullable=False
    )
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    documents_submitted_at = Column(TIMESTAMP(timezone=True))
    submitted_time = Column(TIMESTAMP(timezone=True))

    change_request_type_instance = relationship(LkChangeRequestType)
    claim = relationship("Claim", back_populates="change_request")

    @typed_hybrid_property
    def type(self) -> str:
        return self.change_request_type_instance.description

    @typed_hybrid_property
    def application(self):
        if not self.claim:
            return None

        return self.claim.application  # type: ignore


class Claim(Base, TimestampMixin):
    __tablename__ = "claim"
    claim_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    claim_type_id = Column(Integer, ForeignKey("lk_claim_type.claim_type_id"))
    employer_id = Column(PostgreSQLUUID, ForeignKey("employer.employer_id"), index=True)
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True)
    fineos_absence_id = Column(Text, index=True, unique=True)
    fineos_absence_status_id = Column(Integer, ForeignKey("lk_absence_status.absence_status_id"))
    absence_period_start_date = Column(Date)
    absence_period_end_date = Column(Date)
    fineos_notification_id = Column(Text)
    is_id_proofed = Column(Boolean)
    organization_unit_id = Column(
        PostgreSQLUUID, ForeignKey("organization_unit.organization_unit_id"), nullable=True
    )

    # Not sure if these are currently used.
    authorized_representative_id = Column(PostgreSQLUUID)
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
    absence_periods = cast(
        Optional[List["AbsencePeriod"]], relationship("AbsencePeriod", back_populates="claim")
    )
    organization_unit = relationship(OrganizationUnit)
    change_request = relationship("ChangeRequest", back_populates="claim")

    @typed_hybrid_property
    def soonest_open_requirement_date(self) -> Optional[date]:
        def _filter(requirement: ManagedRequirement) -> bool:
            valid_status = (
                requirement.managed_requirement_status_id
                == ManagedRequirementStatus.OPEN.managed_requirement_status_id
            )
            valid_type = (
                requirement.managed_requirement_type_id
                == ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id
            )
            not_expired = (
                requirement.follow_up_date is not None
                and requirement.follow_up_date >= date.today()
            )
            return valid_status and valid_type and not_expired

        if not self.managed_requirements:
            return None
        filtered_requirements = filter(_filter, self.managed_requirements)
        requirements = sorted(filtered_requirements, key=lambda x: x.follow_up_date)  # type: ignore
        if len(requirements):
            return requirements[0].follow_up_date
        return None

    @soonest_open_requirement_date.expression
    def soonest_open_requirement_date(cls):  # noqa: B902
        aliasManagedRequirement = aliased(ManagedRequirement)
        status_id = aliasManagedRequirement.managed_requirement_status_id
        type_id = aliasManagedRequirement.managed_requirement_type_id
        filters = and_(
            aliasManagedRequirement.claim_id == cls.claim_id,
            status_id == ManagedRequirementStatus.OPEN.managed_requirement_status_id,
            type_id == ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
            aliasManagedRequirement.follow_up_date >= date.today(),
        )
        return (
            select([func.min(aliasManagedRequirement.follow_up_date)])
            .where(filters)
            .label("soonest_open_requirement_date")
        )

    @typed_hybrid_property
    def latest_follow_up_date(self) -> Optional[date]:
        """
        Note that this property (for use in our dashboard sorting),
        returns the latest_follow_up_date only when the requirement is not open,
        as well as a few other filters.
        """

        def _filter(requirement: ManagedRequirement) -> bool:
            not_open_status = (
                requirement.managed_requirement_status_id
                != ManagedRequirementStatus.OPEN.managed_requirement_status_id
            )
            valid_type = (
                requirement.managed_requirement_type_id
                == ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id
            )
            expired = (
                requirement.follow_up_date is not None and requirement.follow_up_date < date.today()
            )
            return valid_type and (not_open_status or expired)

        if not self.managed_requirements:
            return None
        filtered_requirements = filter(_filter, self.managed_requirements)
        requirements = sorted(filtered_requirements, key=lambda x: x.follow_up_date, reverse=True)  # type: ignore
        if len(requirements):
            return requirements[0].follow_up_date
        return None

    @latest_follow_up_date.expression
    def latest_follow_up_date(cls):  # noqa: B902
        aliasManagedRequirement = aliased(ManagedRequirement)
        type_id = aliasManagedRequirement.managed_requirement_type_id
        status_id = aliasManagedRequirement.managed_requirement_status_id

        filters = and_(
            aliasManagedRequirement.claim_id == cls.claim_id,
            type_id == ManagedRequirementType.EMPLOYER_CONFIRMATION.managed_requirement_type_id,
            or_(
                status_id != ManagedRequirementStatus.OPEN.managed_requirement_status_id,
                aliasManagedRequirement.follow_up_date < date.today(),
            ),
        )
        return (
            select([func.max(aliasManagedRequirement.follow_up_date)])
            .where(filters)
            .label("latest_follow_up_date")
        )

    @typed_hybrid_property
    def employee_tax_identifier(self) -> Optional[str]:
        if not self.employee:
            return None

        if self.employee.tax_identifier is None:
            return None

        return self.employee.tax_identifier.tax_identifier

    @typed_hybrid_property
    def employer_fein(self) -> Optional[str]:
        if not self.employer:
            return None

        return self.employer.employer_fein

    @typed_hybrid_property
    def has_paid_payments(self) -> bool:
        # Joining to LatestStateLog filters out StateLogs
        # which are no longer the most recent state for a given payment
        paid_payments = (
            object_session(self)
            .query(func.count(Payment.payment_id))
            .join(StateLog)
            .join(LatestStateLog)
            .filter(Payment.claim_id == self.claim_id)
            .filter(StateLog.end_state_id.in_(SharedPaymentConstants.PAID_STATE_IDS))
            .scalar()
        )

        return paid_payments > 0


class BenefitYear(Base, TimestampMixin):
    __tablename__ = "benefit_year"

    benefit_year_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), nullable=False, index=True
    )

    employee = cast(Optional["Employee"], relationship("Employee", back_populates="benefit_years"))

    start_date = Column(Date, nullable=False)

    end_date = Column(Date, nullable=False)

    # The base period used to calculate IAWW
    # in order to recalculate IAWW for other employers
    base_period_start_date = Column(Date)

    base_period_end_date = Column(Date)

    total_wages = Column(Numeric(asdecimal=True))

    @typed_hybrid_property
    def current_benefit_year(self) -> bool:
        today = date.today()
        return today >= self.start_date and today <= self.end_date

    @current_benefit_year.expression
    def current_benefit_year(cls) -> bool:  # noqa: B902
        return func.now().between(cls.start_date, cls.end_date)

    contributions = cast(
        List["BenefitYearContribution"],
        relationship("BenefitYearContribution", cascade="all, delete-orphan"),
    )


class BenefitYearContribution(Base, TimestampMixin):
    __tablename__ = "benefit_year_contribution"
    benefit_year_contribution_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    benefit_year_id = Column(
        PostgreSQLUUID, ForeignKey("benefit_year.benefit_year_id"), nullable=False, index=True
    )
    benefit_year = relationship("BenefitYear", back_populates="contributions")

    employer_id = Column(
        PostgreSQLUUID, ForeignKey("employer.employer_id"), nullable=False, index=True
    )
    employer = relationship("Employer", back_populates="employee_benefit_year_contributions")

    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), nullable=False, index=True
    )
    employee = relationship("Employee", back_populates="employer_benefit_year_contributions")

    average_weekly_wage = Column(Numeric(asdecimal=True), nullable=False)

    Index(
        "ix_benefit_year_id_employer_id_employee_id",
        benefit_year_id,
        employer_id,
        employee_id,
        unique=True,
    )


class Payment(Base, TimestampMixin):
    __tablename__ = "payment"
    payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True)
    # Attach the employee ID as well as some payments aren't associated with a claim
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True)
    payment_transaction_type_id = Column(
        Integer, ForeignKey("lk_payment_transaction_type.payment_transaction_type_id")
    )
    payment_relevant_party_id = Column(
        Integer, ForeignKey("lk_payment_relevant_party.payment_relevant_party_id")
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

    # Backfilled legacy MMARS payments use this for check number and EFT transaction number, all new payments leave null
    disb_check_eft_number = Column(Text)
    # Backfilled legacy MMARS payments use this for the paid date, all new payments leave null
    disb_check_eft_issue_date = Column(Date)

    disb_method_id = Column(Integer, ForeignKey("lk_payment_method.payment_method_id"))
    disb_amount = Column(Numeric(asdecimal=True))
    leave_request_decision = Column(Text)
    experian_address_pair_id = Column(
        PostgreSQLUUID, ForeignKey("link_experian_address_pair.fineos_address_id"), index=True
    )
    has_address_update = Column(Boolean, default=False, server_default="FALSE", nullable=False)
    has_eft_update = Column(Boolean, default=False, server_default="FALSE", nullable=False)
    fineos_extract_import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True
    )
    pub_eft_id = Column(PostgreSQLUUID, ForeignKey("pub_eft.pub_eft_id"))
    payment_individual_id_seq: Sequence = Sequence("payment_individual_id_seq")
    pub_individual_id = Column(
        Integer,
        payment_individual_id_seq,
        index=True,
        server_default=payment_individual_id_seq.next_value(),
    )
    claim_type_id = Column(Integer, ForeignKey("lk_claim_type.claim_type_id"))
    leave_request_id = Column(PostgreSQLUUID, ForeignKey("absence_period.absence_period_id"))

    vpei_id = Column(PostgreSQLUUID, ForeignKey("fineos_extract_vpei.vpei_id"))
    exclude_from_payment_status = Column(
        Boolean, default=False, server_default="FALSE", nullable=False
    )

    fineos_leave_request_id = Column(Integer, index=True)
    fineos_employee_first_name = Column(Text)
    fineos_employee_middle_name = Column(Text)
    fineos_employee_last_name = Column(Text)

    payee_name = Column(Text)

    claim = relationship("Claim", back_populates="payments")
    employee = relationship("Employee")
    claim_type = relationship(LkClaimType)
    payment_transaction_type = relationship(LkPaymentTransactionType)
    payment_relevant_party = relationship(LkPaymentRelevantParty)
    disb_method = relationship(LkPaymentMethod, foreign_keys=disb_method_id)
    pub_eft = relationship(PubEft)
    experian_address_pair = relationship(ExperianAddressPair, foreign_keys=experian_address_pair_id)
    fineos_extract_import_log = relationship("ImportLog")
    reference_files = relationship("PaymentReferenceFile", back_populates="payment")
    state_logs = relationship("StateLog", back_populates="payment")
    payment_details = cast(
        List["PaymentDetails"], relationship("PaymentDetails", back_populates="payment")
    )
    leave_request = relationship(AbsencePeriod)

    check = relationship("PaymentCheck", backref="payment", uselist=False)


class PaymentDetails(Base, TimestampMixin):
    __tablename__ = "payment_details"
    payment_details_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    payment_id = Column(PostgreSQLUUID, ForeignKey(Payment.payment_id), nullable=False, index=True)

    payment_details_c_value = Column(Text, index=True)
    payment_details_i_value = Column(Text, index=True)

    vpei_payment_details_id = Column(
        PostgreSQLUUID, ForeignKey("fineos_extract_vpei_payment_details.vpei_payment_details_id")
    )

    period_start_date = Column(Date)
    period_end_date = Column(Date)
    amount = Column(Numeric(asdecimal=True), nullable=False)
    business_net_amount = Column(Numeric(asdecimal=True), nullable=False)

    payment = relationship(Payment)


class PaymentCheck(Base, TimestampMixin):
    __tablename__ = "payment_check"
    payment_id = Column(PostgreSQLUUID, ForeignKey(Payment.payment_id), primary_key=True)
    check_number = Column(Integer, nullable=False, index=True, unique=True)
    check_posted_date = Column(Date)
    payment_check_status_id = Column(
        Integer, ForeignKey("lk_payment_check_status.payment_check_status_id")
    )

    payment_check_status = relationship(LkPaymentCheckStatus)


class AuthorizedRepEmployee(Base, TimestampMixin):
    __tablename__ = "link_authorized_rep_employee"
    authorized_representative_id = Column(
        PostgreSQLUUID,
        ForeignKey("authorized_representative.authorized_representative_id"),
        primary_key=True,
    )
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), primary_key=True)

    authorized_rep = relationship("AuthorizedRepresentative", back_populates="employees")
    employee = relationship("Employee", back_populates="authorized_reps")


class Address(Base, TimestampMixin):
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


class CtrDocumentIdentifier(Base, TimestampMixin):
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


class CtrBatchIdentifier(Base, TimestampMixin):
    __tablename__ = "ctr_batch_identifier"
    ctr_batch_identifier_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    ctr_batch_identifier = Column(Text, nullable=False)
    year = Column(Integer, nullable=False)
    batch_date = Column(Date, nullable=False)
    batch_counter = Column(Integer, nullable=False)
    inf_data = Column(JSON)

    Index("ix_year_ctr_batch_identifier", year, ctr_batch_identifier, unique=True)

    reference_files = relationship("ReferenceFile", back_populates="ctr_batch_identifier")


class EmployerAddress(Base, TimestampMixin):
    __tablename__ = "link_employer_address"
    employer_id = Column(
        PostgreSQLUUID, ForeignKey("employer.employer_id"), primary_key=True, unique=True
    )
    address_id = Column(
        PostgreSQLUUID, ForeignKey("address.address_id"), primary_key=True, unique=True
    )

    employer = relationship("Employer", back_populates="addresses")
    address = relationship("Address", back_populates="employers")


class HealthCareProviderAddress(Base, TimestampMixin):
    __tablename__ = "link_health_care_provider_address"
    health_care_provider_id = Column(
        PostgreSQLUUID, ForeignKey("health_care_provider.health_care_provider_id"), primary_key=True
    )
    address_id = Column(PostgreSQLUUID, ForeignKey("address.address_id"), primary_key=True)

    health_care_provider = relationship("HealthCareProvider", back_populates="addresses")
    address = relationship("Address", back_populates="health_care_providers")


class User(Base, TimestampMixin):
    __tablename__ = "user"
    user_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    sub_id = Column(Text, index=True, unique=True)
    email_address = Column(Text, unique=True)
    consented_to_data_sharing = Column(Boolean, default=False, nullable=False)
    mfa_delivery_preference_id = Column(
        Integer, ForeignKey("lk_mfa_delivery_preference.mfa_delivery_preference_id")
    )
    mfa_phone_number = Column(Text)  # Formatted in E.164
    mfa_delivery_preference_updated_at = Column(TIMESTAMP(timezone=True))
    mfa_delivery_preference_updated_by_id = Column(
        Integer,
        ForeignKey("lk_mfa_delivery_preference_updated_by.mfa_delivery_preference_updated_by_id"),
    )

    roles = relationship("LkRole", secondary="link_user_role", uselist=True)
    user_leave_administrators = relationship(
        "UserLeaveAdministrator", back_populates="user", uselist=True
    )
    employers = relationship("Employer", secondary="link_user_leave_administrator", uselist=True)
    mfa_delivery_preference = relationship(LkMFADeliveryPreference)
    mfa_delivery_preference_updated_by = relationship(LkMFADeliveryPreferenceUpdatedBy)

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
    def get_verified_leave_admin_org_units(self) -> list[OrganizationUnit]:
        organization_units: list[OrganizationUnit] = []
        for la in self.user_leave_administrators:
            if not la.verified:
                continue
            organization_units.extend(la.organization_units)
        return organization_units

    @hybrid_method
    def get_leave_admin_notifications(self) -> list[str]:
        """
        Check if notifications were sent to this leave admin
        in the last 24 hours, to prevent leave admins
        with notifications, but no org units assigned,
        from seeing a blank page in the employer dashboard
        """
        # This is imported here to prevent circular import error
        from massgov.pfml.db.models.applications import Notification

        a_day_ago = utcnow() - timedelta(days=1)
        notifications = (
            object_session(self)
            .query(Notification.fineos_absence_id)
            # Filtering by date first lowers query execution cost substantially
            .filter(Notification.created_at > a_day_ago)
            .filter(
                Notification.request_json.contains(
                    {
                        "recipients": [{"email_address": self.email_address}],
                        "recipient_type": "Leave Administrator",
                    }
                )
            )
            .distinct()
        )
        # claims that this leave admin was notified about in the last 24 hours
        return [n.fineos_absence_id for n in notifications]

    @hybrid_method
    def verified_employer(self, employer: Employer) -> bool:
        # Return the `verified` state of the Employer (from the UserLeaveAdministrator record)
        user_leave_administrator = self.get_user_leave_admin_for_employer(employer=employer)
        return user_leave_administrator.verified if user_leave_administrator else False

    @hybrid_method
    def mfa_preference_description(self) -> Optional[str]:
        """Helper method for accessing mfa_delivery_preference_description in a null-safe way"""
        # explicit cast to Optional to make linter happy
        mfa_preference: Optional[LkMFADeliveryPreference] = self.mfa_delivery_preference
        if mfa_preference is None:
            return None

        return mfa_preference.description

    @hybrid_method
    def mfa_phone_number_last_four(self) -> Optional[str]:
        """Retrieves the last four digits of mfa_phone_number in a null-safe way"""
        if self.mfa_phone_number is None:
            return None

        return self.mfa_phone_number[-4:]

    @property
    def is_worker_user(self) -> bool:
        """
        Currently we do not populate a role for worker account users
        so for now we can rely on roles being empty to extrapolate

        See: create_user in users.py utility
        """
        return not self.roles


class UserRole(Base, TimestampMixin):
    __tablename__ = "link_user_role"
    user_id = Column(PostgreSQLUUID, ForeignKey("user.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("lk_role.role_id"), primary_key=True)

    user = relationship(User)
    role = relationship(LkRole)


class UserLeaveAdministratorOrgUnit(Base, TimestampMixin):
    __tablename__ = "link_user_leave_administrator_org_unit"
    user_leave_administrator_id = Column(
        PostgreSQLUUID,
        ForeignKey("link_user_leave_administrator.user_leave_administrator_id"),
        primary_key=True,
    )
    organization_unit_id = Column(
        PostgreSQLUUID, ForeignKey("organization_unit.organization_unit_id"), primary_key=True
    )

    organization_unit = relationship(OrganizationUnit)

    def __init__(self, user_leave_administrator_id, organization_unit_id):
        self.user_leave_administrator_id = user_leave_administrator_id
        self.organization_unit_id = organization_unit_id


class UserLeaveAdministrator(Base, TimestampMixin):
    __tablename__ = "link_user_leave_administrator"
    __table_args__ = (UniqueConstraint("user_id", "employer_id"),)
    user_leave_administrator_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    user_id = Column(PostgreSQLUUID, ForeignKey("user.user_id"), nullable=False)
    employer_id = Column(PostgreSQLUUID, ForeignKey("employer.employer_id"), nullable=False)
    fineos_web_id = Column(Text)
    verification_id = Column(
        PostgreSQLUUID, ForeignKey("verification.verification_id"), nullable=True
    )

    user = relationship(User)
    employer = relationship(Employer)
    verification = relationship(Verification)

    @property
    def organization_units(self) -> list[OrganizationUnit]:
        return (
            object_session(self)
            .query(OrganizationUnit)
            .join(UserLeaveAdministratorOrgUnit)
            .filter(
                UserLeaveAdministratorOrgUnit.user_leave_administrator_id
                == self.user_leave_administrator_id,
                OrganizationUnit.employer_id == self.employer_id,
                OrganizationUnit.fineos_id.isnot(None),
            )
            .all()
        )

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
    managed_requirement_status_description = Column(Text, nullable=False)

    def __init__(self, managed_requirement_status_id, managed_requirement_status_description):
        self.managed_requirement_status_id = managed_requirement_status_id
        self.managed_requirement_status_description = managed_requirement_status_description


class LkManagedRequirementCategory(Base):
    __tablename__ = "lk_managed_requirement_category"
    managed_requirement_category_id = Column(Integer, primary_key=True, autoincrement=True)
    managed_requirement_category_description = Column(Text, nullable=False)

    def __init__(self, managed_requirement_category_id, managed_requirement_category_description):
        self.managed_requirement_category_id = managed_requirement_category_id
        self.managed_requirement_category_description = managed_requirement_category_description


class LkManagedRequirementType(Base):
    __tablename__ = "lk_managed_requirement_type"
    managed_requirement_type_id = Column(Integer, primary_key=True, autoincrement=True)
    managed_requirement_type_description = Column(Text, nullable=False)

    def __init__(self, managed_requirement_type_id, managed_requirement_type_description):
        self.managed_requirement_type_id = managed_requirement_type_id
        self.managed_requirement_type_description = managed_requirement_type_description


class ManagedRequirement(Base, TimestampMixin):
    """PFML-relevant data from a Managed Requirement in Fineos. Example managed requirement is an Employer info request."""

    __tablename__ = "managed_requirement"
    managed_requirement_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True, nullable=False)
    respondent_user_id = Column(PostgreSQLUUID, ForeignKey("user.user_id"))
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

    @property
    def is_open(self):
        return (
            self.managed_requirement_status_id
            == ManagedRequirementStatus.OPEN.managed_requirement_status_id
        )


class WagesAndContributions(Base, TimestampMixin):
    __tablename__ = "wages_and_contributions"
    wage_and_contribution_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    account_key = Column(Text, nullable=False)
    filing_period = Column(Date, nullable=False, index=True)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), nullable=False, index=True
    )
    employer_id = Column(
        PostgreSQLUUID, ForeignKey("employer.employer_id"), nullable=False, index=True
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


class WagesAndContributionsHistory(Base, TimestampMixin):
    __tablename__ = "wages_and_contributions_history"
    wages_and_contributions_history_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    is_independent_contractor = Column(Boolean, nullable=False)
    is_opted_in = Column(Boolean, nullable=False)
    employee_ytd_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_qtr_wages = Column(Numeric(asdecimal=True), nullable=False)
    employee_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_med_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employee_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)
    employer_fam_contribution = Column(Numeric(asdecimal=True), nullable=False)
    import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True, nullable=True
    )
    wage_and_contribution_id = Column(
        PostgreSQLUUID,
        ForeignKey("wages_and_contributions.wage_and_contribution_id"),
        index=True,
        nullable=False,
    )

    wage_and_contribution = relationship("WagesAndContributions")


class EmployeeOccupation(Base, TimestampMixin):
    __tablename__ = "employee_occupation"

    employee_occupation_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    employee_id = Column(
        PostgreSQLUUID, ForeignKey("employee.employee_id"), nullable=False, index=True
    )
    employer_id = Column(
        PostgreSQLUUID, ForeignKey("employer.employer_id"), nullable=False, index=True
    )
    organization_unit_id = Column(
        PostgreSQLUUID,
        ForeignKey("organization_unit.organization_unit_id"),
        nullable=True,
        index=True,
    )
    job_title = Column(Text)
    date_of_hire = Column(Date)
    date_job_ended = Column(Date)
    employment_status = Column(Text)
    hours_worked_per_week = Column(Numeric)
    days_worked_per_week = Column(Numeric)
    manager_id = Column(Text)
    worksite_id = Column(Text)
    occupation_qualifier = Column(Text)

    Index("ix_employee_occupation_employee_id_employer_id", employee_id, employer_id, unique=True)

    employee = relationship("Employee", back_populates="employee_occupations")
    employer = relationship("Employer", back_populates="employer_occupations")
    organization_unit = relationship("OrganizationUnit")


class ImportLog(Base, TimestampMixin):
    __tablename__ = "import_log"
    import_log_id = Column(Integer, primary_key=True)
    source = Column(Text, index=True)
    import_type = Column(Text, index=True)
    status = Column(Text)
    report = Column(Text)
    start = Column(TIMESTAMP(timezone=True), index=True)
    end = Column(TIMESTAMP(timezone=True))
    report_queue_item = relationship(
        "ImportLogReportQueue",
        back_populates="import_log",
        uselist=False,
        passive_deletes=True,
        cascade="all, delete-orphan",
    )


class ImportLogReportQueue(Base, TimestampMixin):
    __tablename__ = "import_log_report_queue"
    import_log_report_queue_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    import_log_id = Column(
        Integer,
        ForeignKey("import_log.import_log_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    import_log = cast(ImportLog, relationship("ImportLog", back_populates="report_queue_item"))


class ReferenceFile(Base, TimestampMixin):
    __tablename__ = "reference_file"
    reference_file_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    file_location = Column(Text, index=True, unique=True, nullable=False)
    reference_file_type_id = Column(
        Integer, ForeignKey("lk_reference_file_type.reference_file_type_id"), nullable=True
    )
    ctr_batch_identifier_id = Column(
        PostgreSQLUUID,
        ForeignKey("ctr_batch_identifier.ctr_batch_identifier_id"),
        nullable=True,
        index=True,
    )
    # When the data within the files was processed (as determined by the particular process)
    processed_import_log_id = Column(Integer, ForeignKey("import_log.import_log_id"), index=True)

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


class PaymentReferenceFile(Base, TimestampMixin):
    __tablename__ = "link_payment_reference_file"
    payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"), primary_key=True)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), primary_key=True
    )
    ctr_document_identifier_id = Column(
        PostgreSQLUUID, ForeignKey("ctr_document_identifier.ctr_document_identifier_id"), index=True
    )

    payment = relationship("Payment", back_populates="reference_files")
    reference_file = relationship("ReferenceFile", back_populates="payments")
    ctr_document_identifier = relationship(
        "CtrDocumentIdentifier", back_populates="payment_reference_files"
    )


class EmployeeReferenceFile(Base, TimestampMixin):
    __tablename__ = "link_employee_reference_file"
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), primary_key=True)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), primary_key=True
    )
    ctr_document_identifier_id = Column(
        PostgreSQLUUID, ForeignKey("ctr_document_identifier.ctr_document_identifier_id"), index=True
    )

    employee = relationship("Employee", back_populates="reference_files")
    reference_file = relationship("ReferenceFile", back_populates="employees")
    ctr_document_identifier = relationship(
        "CtrDocumentIdentifier", back_populates="employee_reference_files"
    )

    def __iter__(self):
        return self


class DuaReductionPaymentReferenceFile(Base, TimestampMixin):
    __tablename__ = "link_dua_reduction_payment_reference_file"
    dua_reduction_payment_id = Column(
        PostgreSQLUUID,
        ForeignKey("dua_reduction_payment.dua_reduction_payment_id"),
        primary_key=True,
    )
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), primary_key=True
    )

    dua_reduction_payment = relationship("DuaReductionPayment")
    reference_file = relationship("ReferenceFile")


class DiaReductionPaymentReferenceFile(Base, TimestampMixin):
    __tablename__ = "link_dia_reduction_payment_reference_file"
    dia_reduction_payment_id = Column(
        PostgreSQLUUID,
        ForeignKey("dia_reduction_payment.dia_reduction_payment_id"),
        primary_key=True,
    )
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), primary_key=True
    )

    dia_reduction_payment = relationship("DiaReductionPayment")
    reference_file = relationship("ReferenceFile")


class StateLog(Base, TimestampMixin):
    __tablename__ = "state_log"
    state_log_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    end_state_id = Column(Integer, ForeignKey("lk_state.state_id"), index=True)
    started_at = Column(TIMESTAMP(timezone=True))
    ended_at = Column(TIMESTAMP(timezone=True), index=True)
    outcome = Column(JSON)
    payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True)
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True)
    prev_state_log_id = Column(PostgreSQLUUID, ForeignKey("state_log.state_log_id"))
    associated_type = Column(Text, index=True)

    import_log_id = Column(
        Integer, ForeignKey("import_log.import_log_id"), index=True, nullable=True
    )
    end_state = cast("Optional[LkState]", relationship(LkState, foreign_keys=[end_state_id]))
    payment = relationship("Payment", back_populates="state_logs")
    reference_file = relationship("ReferenceFile", back_populates="state_logs")
    employee = relationship("Employee", back_populates="state_logs")
    claim = relationship("Claim", back_populates="state_logs")
    prev_state_log = relationship("StateLog", uselist=False, remote_side=state_log_id)
    import_log = cast("Optional[ImportLog]", relationship(ImportLog, foreign_keys=[import_log_id]))


class LatestStateLog(Base, TimestampMixin):
    __tablename__ = "latest_state_log"
    latest_state_log_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    state_log_id = Column(
        PostgreSQLUUID, ForeignKey("state_log.state_log_id"), index=True, nullable=False
    )
    payment_id = Column(PostgreSQLUUID, ForeignKey("payment.payment_id"), index=True)
    employee_id = Column(PostgreSQLUUID, ForeignKey("employee.employee_id"), index=True)
    claim_id = Column(PostgreSQLUUID, ForeignKey("claim.claim_id"), index=True)
    reference_file_id = Column(
        PostgreSQLUUID, ForeignKey("reference_file.reference_file_id"), index=True
    )

    state_log = relationship("StateLog")
    payment = relationship("Payment")
    employee = relationship("Employee")
    claim = relationship("Claim")
    reference_file = relationship("ReferenceFile")


class DuaReductionPayment(Base, TimestampMixin):
    __tablename__ = "dua_reduction_payment"
    dua_reduction_payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

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
    dia_reduction_payment_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

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

    Index(
        "ix_dia_reduction_payment_fineos_customer_number_board_no",
        fineos_customer_number,
        board_no,
        unique=False,
    )


class PubError(Base, TimestampMixin):
    __tablename__ = "pub_error"
    pub_error_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

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
    pub_error_type_description = Column(Text, nullable=False)

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

    MANUAL_PUB_REJECT_LINE_ERROR = LkPubErrorType(9, "Invalid manual PUB reject line")
    MANUAL_PUB_REJECT_ERROR = LkPubErrorType(10, "Manual PUB reject error processing")
    MANUAL_PUB_REJECT_EFT_PROCESSED = LkPubErrorType(11, "Manual PUB reject EFT processed")
    MANUAL_PUB_REJECT_PAYMENT_PROCESSED = LkPubErrorType(12, "Manual PUB reject payment processed")


class AddressType(LookupTable):
    model = LkAddressType
    column_names = ("address_type_id", "address_description")

    HOME = LkAddressType(1, "Home")
    BUSINESS = LkAddressType(2, "Business")
    MAILING = LkAddressType(3, "Mailing")
    RESIDENTIAL = LkAddressType(4, "Residential")


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
    PFML_CRM = LkRole(4, "PFML_CRM")


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


class SharedPaymentConstants:
    """
    A class to hold Payment-Specific constants relevant
    to more than one part of the application.
    Definining constants here allows them to be shared
    throughout the application without creating circular dependencies
    """

    # States that indicate we have sent a payment to PUB
    # and it has not yet errored.
    PAID_STATES = frozenset(
        [
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT,
            State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT,
            State.DELEGATED_PAYMENT_COMPLETE,
            State.DELEGATED_PAYMENT_COMPLETE_WITH_CHANGE_NOTIFICATION,
        ]
    )
    PAID_STATE_IDS = frozenset([state.state_id for state in PAID_STATES])


class PaymentRelevantParty(LookupTable):
    model = LkPaymentRelevantParty
    column_names = ("payment_relevant_party_id", "payment_relevant_party_description")

    UNKNOWN = LkPaymentRelevantParty(1, "Unknown")
    CLAIMANT = LkPaymentRelevantParty(2, "Claimant")
    STATE_TAX = LkPaymentRelevantParty(3, "State tax withholding")
    FEDERAL_TAX = LkPaymentRelevantParty(4, "Federal tax withholding")
    REIMBURSED_EMPLOYER = LkPaymentRelevantParty(5, "Reimbursed employer")


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
    FEDERAL_TAX_WITHHOLDING = LkPaymentTransactionType(12, "Federal Tax Withholding")
    STATE_TAX_WITHHOLDING = LkPaymentTransactionType(13, "State Tax Withholding")
    STANDARD_LEGACY_MMARS = LkPaymentTransactionType(14, "Standard Legacy MMARS")

    OVERPAYMENT_ACTUAL_RECOVERY_CANCELLATION = LkPaymentTransactionType(
        15, "Overpayment Actual Recovery Cancellation"
    )
    OVERPAYMENT_ADJUSTMENT_CANCELLATION = LkPaymentTransactionType(
        16, "Overpayment Adjustment Cancellation"
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
    FINEOS_CLAIMANT_EXTRACT = LkReferenceFileType(24, "Claimant extract", 3)
    FINEOS_PAYMENT_EXTRACT = LkReferenceFileType(25, "Payment extract", 3)

    PUB_EZ_CHECK = LkReferenceFileType(26, "PUB EZ check file", 1)
    PUB_POSITIVE_PAYMENT = LkReferenceFileType(27, "PUB positive pay file", 1)

    DELEGATED_PAYMENT_REPORT_FILE = LkReferenceFileType(28, "SQL Report", 1)
    DIA_CONSOLIDATED_REDUCTION_REPORT = LkReferenceFileType(
        29, "Consolidated DIA payments for DFML reduction report", 1
    )
    DIA_CONSOLIDATED_REDUCTION_REPORT_ERRORS = LkReferenceFileType(
        30, "Consolidated DIA payments for DFML reduction report", 1
    )
    FINEOS_PAYMENT_RECONCILIATION_EXTRACT = LkReferenceFileType(
        31, "Payment reconciliation extract", 3
    )

    DUA_DEMOGRAPHICS_FILE = LkReferenceFileType(32, "DUA demographics", 1)

    DUA_DEMOGRAPHICS_REQUEST_FILE = LkReferenceFileType(33, "DUA demographics request", 1)

    IRS_1099_FILE = LkReferenceFileType(34, "IRS 1099 file", 1)

    FINEOS_IAWW_EXTRACT = LkReferenceFileType(35, "IAWW extract", 2)

    # Claimant Address Report
    CLAIMANT_ADDRESS_VALIDATION_REPORT = LkReferenceFileType(
        36, "Claimant Address validation Report", 1
    )

    DUA_EMPLOYERS_REQUEST_FILE = LkReferenceFileType(37, "DUA employers request", 1)
    FINEOS_1099_DATA_EXTRACT = LkReferenceFileType(38, "1099 extract", 1)

    DUA_EMPLOYER_FILE = LkReferenceFileType(39, "DUA employer", 1)
    DUA_EMPLOYER_UNIT_FILE = LkReferenceFileType(40, "DUA employer unit", 1)

    FINEOS_VBI_TASKREPORT_SOM_EXTRACT = LkReferenceFileType(41, "VBI TaskReport Som extract", 1)

    MANUAL_PUB_REJECT_FILE = LkReferenceFileType(42, "Manual PUB Reject File", 1)


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
    CANCELLED = LkLeaveRequestDecision(5, "Cancelled")
    WITHDRAWN = LkLeaveRequestDecision(6, "Withdrawn")
    PROJECTED = LkLeaveRequestDecision(7, "Projected")
    VOIDED = LkLeaveRequestDecision(8, "Voided")


class MFADeliveryPreference(LookupTable):
    model = LkMFADeliveryPreference
    column_names = ("mfa_delivery_preference_id", "mfa_delivery_preference_description")

    SMS = LkMFADeliveryPreference(1, "SMS")
    OPT_OUT = LkMFADeliveryPreference(2, "Opt Out")


class MFADeliveryPreferenceUpdatedBy(LookupTable):
    model = LkMFADeliveryPreferenceUpdatedBy
    column_names = (
        "mfa_delivery_preference_updated_by_id",
        "mfa_delivery_preference_updated_by_description",
    )

    USER = LkMFADeliveryPreferenceUpdatedBy(1, "User")
    ADMIN = LkMFADeliveryPreferenceUpdatedBy(2, "Admin")


class ChangeRequestType(LookupTable):
    model = LkChangeRequestType
    column_names = ("change_request_type_id", "change_request_type_description")

    MODIFICATION = LkChangeRequestType(1, "Modification")
    WITHDRAWAL = LkChangeRequestType(2, "Withdrawal")
    MEDICAL_TO_BONDING = LkChangeRequestType(3, "Medical To Bonding Transition")


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    AddressType.sync_to_database(db_session)
    ClaimType.sync_to_database(db_session)
    Race.sync_to_database(db_session)
    LeaveRequestDecision.sync_to_database(db_session)
    MaritalStatus.sync_to_database(db_session)
    Gender.sync_to_database(db_session)
    Occupation.sync_to_database(db_session)
    Role.sync_to_database(db_session)
    PaymentMethod.sync_to_database(db_session)
    BankAccountType.sync_to_database(db_session)
    ReferenceFileType.sync_to_database(db_session)
    Title.sync_to_database(db_session)
    ReferenceFileType.sync_to_database(db_session)
    PaymentRelevantParty.sync_to_database(db_session)
    PaymentTransactionType.sync_to_database(db_session)
    PaymentCheckStatus.sync_to_database(db_session)
    PrenoteState.sync_to_database(db_session)
    PubErrorType.sync_to_database(db_session)
    ManagedRequirementStatus.sync_to_database(db_session)
    ManagedRequirementCategory.sync_to_database(db_session)
    ManagedRequirementType.sync_to_database(db_session)
    MFADeliveryPreference.sync_to_database(db_session)
    MFADeliveryPreferenceUpdatedBy.sync_to_database(db_session)
    ChangeRequestType.sync_to_database(db_session)
    db_session.commit()
