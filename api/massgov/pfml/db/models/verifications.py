""" Grouping for tables related to Verifications """
# ORM and serialization models for Verifications - Verifications, VerificationCodes, VerificationCodeLogs
#
# A model's ORM representation should always match the database so we can
# properly read and write data. If you make a change, follow the instructions
# in the API README to generate an associated table migration.

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..lookup import LookupTable
from .base import Base, utc_timestamp_gen, uuid_gen
from .employees import Employer


class LkVerificationType(Base):
    """ Lookup table for types of verifications
    """

    __tablename__ = "lk_verification_type"
    verification_type_id = Column(Integer, primary_key=True, autoincrement=True)
    verification_type_description = Column(Text)

    def __init__(self, verification_type_id, verification_type_description):
        self.verification_type_id = verification_type_id
        self.verification_type_description = verification_type_description


class VerificationType(LookupTable):
    model = LkVerificationType
    column_names = ("verification_type_id", "verification_type_description")

    VERIFICATION_CODE = LkVerificationType(1, "Verification Code")


class Verification(Base):
    """ Stores a record of a Verification that occurred for association with a Role;
        Initial verification_type is `Verification Code`
    """

    __tablename__ = "verification"
    verification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    verification_type_id = Column(Integer, ForeignKey("lk_verification_type.verification_type_id"))
    verification_type = relationship("LkVerificationType")
    verification_code_id = Column(
        UUID(as_uuid=True), ForeignKey("verification_code.verification_code_id"), nullable=True
    )
    verified_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)
    email_address = Column(Text)


class VerificationCode(Base):
    """ Stores a Code for distribution via some mechanism, associated with an Employer either
        directly (via employer_id) or indirectly (via employer_fein)
    """

    __tablename__ = "verification_code"
    verification_code_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)

    employer_id = Column(UUID(as_uuid=True), ForeignKey("employer.employer_id"), nullable=True)
    # After DOR import data, this column (employer_fein) becomes optional (in favor of only using employer_id)
    employer_fein = Column(Text, index=True, nullable=True)
    employer = relationship(Employer)

    verification_code = Column(Text, nullable=False, index=True)

    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    issued_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)
    remaining_uses = Column(Integer, nullable=False)


class VerificationCodeLogs(Base):
    """ Stores auditing logs for when VerificationCodes are used to create Verifications
        May benefit from a `back_populates` field for `verification_code` depending on application use
    """

    __tablename__ = "verification_code_log"
    verification_code_log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_gen)
    verification_code_id = Column(
        UUID(as_uuid=True), ForeignKey("verification_code.verification_code_id")
    )
    result = Column(Text)
    message = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=utc_timestamp_gen)


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    VerificationType.sync_to_database(db_session)
    db_session.commit()
