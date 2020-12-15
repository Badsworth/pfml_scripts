"""Create Agency lookups, AgencyReductionPaymentReferenceFile and AgencyReductionPayment. Added fields to Flow and State LkTables

Revision ID: d7a7eb9c0b9f
Revises: 2515d25d8e7c
Create Date: 2020-12-07 16:54:03.177011

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d7a7eb9c0b9f"
down_revision = "2515d25d8e7c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_agency",
        sa.Column("agency_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agency_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("agency_id"),
    )
    op.create_table(
        "agency_reduction_payment",
        sa.Column("agency_reduction_payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("absence_case_id", sa.Text(), nullable=True),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("payment_issued_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("gross_benefit_amount_cents", sa.Numeric(), nullable=True),
        sa.Column("net_benefit_amount_cents", sa.Numeric(), nullable=True),
        sa.Column("has_fraud_indicator", sa.Boolean(), nullable=True),
        sa.Column("benefit_week_start_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("benefit_week_end_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("benefit_year_start_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("benefit_year_end_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["lk_agency.agency_id"],),
        sa.PrimaryKeyConstraint("agency_reduction_payment_id"),
    )
    op.create_index(
        op.f("ix_agency_reduction_payment_absence_case_id"),
        "agency_reduction_payment",
        ["absence_case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agency_reduction_payment_benefit_week_end_date"),
        "agency_reduction_payment",
        ["benefit_week_end_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agency_reduction_payment_benefit_week_start_date"),
        "agency_reduction_payment",
        ["benefit_week_start_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agency_reduction_payment_benefit_year_end_date"),
        "agency_reduction_payment",
        ["benefit_year_end_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agency_reduction_payment_benefit_year_start_date"),
        "agency_reduction_payment",
        ["benefit_year_start_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agency_reduction_payment_created_at"),
        "agency_reduction_payment",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agency_reduction_payment_payment_issued_date"),
        "agency_reduction_payment",
        ["payment_issued_date"],
        unique=False,
    )
    op.create_table(
        "link_agency_reduction_payment_reference_file",
        sa.Column("reference_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agency_reduction_payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["agency_reduction_payment_id"],
            ["agency_reduction_payment.agency_reduction_payment_id"],
        ),
        sa.ForeignKeyConstraint(["reference_file_id"], ["reference_file.reference_file_id"],),
        sa.PrimaryKeyConstraint("reference_file_id", "agency_reduction_payment_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("link_agency_reduction_payment_reference_file")
    op.drop_index(
        op.f("ix_agency_reduction_payment_payment_issued_date"),
        table_name="agency_reduction_payment",
    )
    op.drop_index(
        op.f("ix_agency_reduction_payment_created_at"), table_name="agency_reduction_payment"
    )
    op.drop_index(
        op.f("ix_agency_reduction_payment_benefit_year_start_date"),
        table_name="agency_reduction_payment",
    )
    op.drop_index(
        op.f("ix_agency_reduction_payment_benefit_year_end_date"),
        table_name="agency_reduction_payment",
    )
    op.drop_index(
        op.f("ix_agency_reduction_payment_benefit_week_start_date"),
        table_name="agency_reduction_payment",
    )
    op.drop_index(
        op.f("ix_agency_reduction_payment_benefit_week_end_date"),
        table_name="agency_reduction_payment",
    )
    op.drop_index(
        op.f("ix_agency_reduction_payment_absence_case_id"), table_name="agency_reduction_payment"
    )
    op.drop_table("agency_reduction_payment")
    op.drop_table("lk_agency")
    # ### end Alembic commands ###
