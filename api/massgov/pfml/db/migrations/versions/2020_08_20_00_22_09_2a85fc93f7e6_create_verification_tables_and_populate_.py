"""Create Verification tables and populate VerificationType

Revision ID: 2a85fc93f7e6
Revises: 89e55ef4d333
Create Date: 2020-08-20 00:22:09.030280

"""
import csv
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2a85fc93f7e6"
down_revision = "89e55ef4d333"
branch_labels = None
depends_on = None

with open(Path(__file__).parents[2] / "seed" / "lookups" / "lk_verification_type.csv") as csvfile:
    # read in the data
    reader = csv.DictReader(csvfile, delimiter=",")
    verification_rows = [r for r in csv.DictReader(csvfile, delimiter=",")]


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_verification_type",
        sa.Column("verification_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("verification_type_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("verification_type_id"),
    )
    op.create_table(
        "verification",
        sa.Column("verification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_type_id", sa.Integer(), nullable=True),
        sa.Column("verification_ts", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("related_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["verification_type_id"], ["lk_verification_type.verification_type_id"],
        ),
        sa.PrimaryKeyConstraint("verification_id"),
    )
    op.create_table(
        "verification_code",
        sa.Column("verification_code_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employer_fein", sa.Text(), nullable=True),
        sa.Column("verification_code", sa.Text(), nullable=False),
        sa.Column("expiration_ts", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("issue_ts", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("remaining_uses", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["employer_id"], ["employer.employer_id"],),
        sa.PrimaryKeyConstraint("verification_code_id"),
    )
    op.create_index(
        op.f("ix_verification_code_employer_fein"),
        "verification_code",
        ["employer_fein"],
        unique=False,
    )
    op.create_index(
        op.f("ix_verification_code_verification_code"),
        "verification_code",
        ["verification_code"],
        unique=False,
    )
    op.create_table(
        "verification_code_log",
        sa.Column("verification_code_log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_code_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("log_ts", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["verification_code_id"], ["verification_code.verification_code_id"],
        ),
        sa.PrimaryKeyConstraint("verification_code_log_id"),
    )
    # ### end Alembic commands ###
    # Insert seed data for Verification Types
    lk_id, lk_desc = verification_rows[0].keys()
    table_handle = sa.sql.table(
        "lk_verification_type", sa.sql.column(lk_id, sa.Integer), sa.sql.column(lk_desc, sa.Text)
    )
    op.bulk_insert(table_handle, verification_rows)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("verification_code_log")
    op.drop_index(op.f("ix_verification_code_verification_code"), table_name="verification_code")
    op.drop_index(op.f("ix_verification_code_employer_fein"), table_name="verification_code")
    op.drop_table("verification_code")
    op.drop_table("verification")
    op.drop_table("lk_verification_type")
    # ### end Alembic commands ###
