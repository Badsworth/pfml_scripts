"""Add quarterly contribution table

Revision ID: ac1f0c370b1f
Revises: 1391944caff2
Create Date: 2020-11-18 22:06:31.493067

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ac1f0c370b1f"
down_revision = "1391944caff2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "employer_quarterly_contribution",
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filing_period", sa.Date(), nullable=False),
        sa.Column("employer_total_pfml_contribution", sa.Numeric(), nullable=False),
        sa.Column("dor_updated_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("latest_import_log_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["employer.employer_id"]),
        sa.ForeignKeyConstraint(["latest_import_log_id"], ["import_log.import_log_id"]),
        sa.PrimaryKeyConstraint("employer_id", "filing_period"),
        sa.UniqueConstraint(
            "employer_id",
            "filing_period",
            name="uix_employer_quarterly_contribution_employer_id_filing_period",
        ),
    )
    op.create_index(
        op.f("ix_employer_quarterly_contribution_employer_id"),
        "employer_quarterly_contribution",
        ["employer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employer_quarterly_contribution_latest_import_log_id"),
        "employer_quarterly_contribution",
        ["latest_import_log_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_employer_quarterly_contribution_latest_import_log_id"),
        table_name="employer_quarterly_contribution",
    )
    op.drop_index(
        op.f("ix_employer_quarterly_contribution_employer_id"),
        table_name="employer_quarterly_contribution",
    )
    op.drop_table("employer_quarterly_contribution")
    # ### end Alembic commands ###
