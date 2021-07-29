""" Grouping for tables related to feature flags """
# ORM models for feature flags
#
# A model's ORM representation should always match the database so we can
# properly read and write data. If you make a change, follow the instructions
# in the API README to generate an associated table migration.

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.functions import now as sqlnow

from .base import Base, utc_timestamp_gen


class Flag(Base):
    __tablename__ = "flag"
    flag_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(Text, nullable=False, unique=True)
    options = Column(JSONB, nullable=True)
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
    start = Column(TIMESTAMP(timezone=True), nullable=True)
    end = Column(TIMESTAMP(timezone=True), nullable=True)
    enabled = Column(Boolean(), nullable=False)


class FlagLog(Base):
    __tablename__ = "flag_log"
    flag_log_id = Column(Integer, primary_key=True, autoincrement=True)
    flag_id = Column(Integer, ForeignKey("flag.flag_id"))
    action = Column(Text, index=True)
    name = Column(Text, nullable=False)
    options = Column(JSONB, nullable=True)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=utc_timestamp_gen,
        server_default=sqlnow(),
    )
    start = Column(TIMESTAMP(timezone=True), nullable=True)
    end = Column(TIMESTAMP(timezone=True), nullable=True)
    enabled = Column(Boolean(), nullable=False)
