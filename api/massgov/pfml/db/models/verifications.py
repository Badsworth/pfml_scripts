""" Grouping for tables related to Verifications """
# ORM and serialization models for Verifications - Verifications
#
# A model's ORM representation should always match the database so we can
# properly read and write data. If you make a change, follow the instructions
# in the API README to generate an associated table migration.

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..lookup import LookupTable
from .base import Base, TimestampMixin, uuid_gen
from .common import PostgreSQLUUID


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
    MANUAL = LkVerificationType(2, "Manual Verification")
    PFML_WITHHOLDING = LkVerificationType(3, "PFML Withholding")


class Verification(Base, TimestampMixin):
    """ Stores a record of a Verification that occurred for association with a Role;
    """

    __tablename__ = "verification"
    verification_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    verification_type_id = Column(
        Integer, ForeignKey("lk_verification_type.verification_type_id"), nullable=False
    )
    verification_type = relationship("LkVerificationType")
    verification_metadata = Column(JSONB)


def sync_lookup_tables(db_session):
    """Synchronize lookup tables to the database."""
    VerificationType.sync_to_database(db_session)
    db_session.commit()
