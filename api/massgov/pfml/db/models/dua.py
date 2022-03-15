from sqlalchemy import Column, Date, Index, Text, UniqueConstraint

from .base import Base, TimestampMixin, uuid_gen
from .common import PostgreSQLUUID


class DuaEmployeeDemographics(Base, TimestampMixin):
    __tablename__ = "dua_employee_demographics"
    dua_employee_demographics_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)

    fineos_customer_number = Column(Text, nullable=True, index=True)
    date_of_birth = Column(Date, nullable=True)
    gender_code = Column(Text, nullable=True)
    occupation_code = Column(Text, nullable=True)
    occupation_description = Column(Text, nullable=True)
    employer_fein = Column(Text, nullable=True, index=True)
    employer_reporting_unit_number = Column(Text, nullable=True, index=True)

    # this Unique index is required since our test framework does not run migrations
    # it is excluded from migrations. see api/massgov/pfml/db/migrations/env.py
    Index(
        "dua_employee_demographics_unique_import_data_idx",
        fineos_customer_number,
        date_of_birth,
        gender_code,
        occupation_code,
        occupation_description,
        employer_fein,
        employer_reporting_unit_number,
        unique=True,
    )

    # Each row should be unique. This enables us to load only new rows from a CSV and ensures that
    # we don't include demographics twice as two different rows. Almost all fields are nullable so we
    # have to coalesce those null values to empty strings. We've manually adjusted the migration
    # that adds this unique constraint to coalesce those nullable fields.
    # See: 2021_10_04_13_30_03_95d3e464a5b2_add_dua_employee_demographics_table.py


class DuaEmployer(Base, TimestampMixin):
    __tablename__ = "dua_employer_data"
    __table_args__ = (
        UniqueConstraint(
            "fineos_employer_id",
            "dba",
            "attention",
            "email",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "address_city",
            "address_zip_code",
            "address_state",
            "naics_code",
            "naics_description",
            name="uix_dua_employer",
        ),
    )
    dua_employer_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    fineos_employer_id = Column(Text, nullable=False)
    dba = Column(Text, nullable=True)
    attention = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=False)
    address_line_1 = Column(Text, nullable=True)
    address_line_2 = Column(Text, nullable=True)
    address_city = Column(Text, nullable=True)
    address_zip_code = Column(Text, nullable=True)
    address_state = Column(Text, nullable=True)
    naics_code = Column(Text, nullable=True)
    naics_description = Column(Text, nullable=True)


class DuaReportingUnitRaw(Base, TimestampMixin):
    __tablename__ = "dua_reporting_unit_data"
    __table_args__ = (
        UniqueConstraint(
            "fineos_employer_id",
            "dua_id",
            "dba",
            "attention",
            "email",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "address_city",
            "address_zip_code",
            "address_state",
            name="uix_dua_reporting_unit_data",
        ),
    )
    dua_reporting_unit_data_id = Column(PostgreSQLUUID, primary_key=True, default=uuid_gen)
    fineos_employer_id = Column(Text, nullable=False)
    dua_id = Column(Text, nullable=True)
    dba = Column(Text, nullable=True)
    attention = Column(Text, nullable=True)
    email = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=False)
    address_line_1 = Column(Text, nullable=True)
    address_line_2 = Column(Text, nullable=True)
    address_city = Column(Text, nullable=True)
    address_zip_code = Column(Text, nullable=True)
    address_state = Column(Text, nullable=True)
