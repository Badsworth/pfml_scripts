"""Add DOR received date

Revision ID: 32eb1f376dbd
Revises: ac1f0c370b1f
Create Date: 2020-11-19 13:31:00.063466

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "32eb1f376dbd"
down_revision = "ac1f0c370b1f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "uix_employer_quarterly_contribution_employer_id_filing_period",
        "employer_quarterly_contribution",
    )

    op.add_column(
        "employer_quarterly_contribution",
        sa.Column("dor_received_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "uix_employer_quarterly_contribution_employer_id_filing_period",
        "employer_quarterly_contribution",
        ["employer_id", "filing_period"],
    )

    op.drop_column("employer_quarterly_contribution", "dor_received_date")
    # ### end Alembic commands ###
