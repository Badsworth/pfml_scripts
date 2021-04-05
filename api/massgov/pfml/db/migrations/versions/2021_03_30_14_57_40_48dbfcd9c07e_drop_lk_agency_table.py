"""drop lk agency table

Revision ID: 48dbfcd9c07e
Revises: 54c32579e577
Create Date: 2021-03-30 14:57:40.960826

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "48dbfcd9c07e"
down_revision = "54c32579e577"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("lk_agency")


def downgrade():
    op.create_table(
        "lk_agency",
        sa.Column("agency_id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("agency_description", sa.TEXT(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("agency_id", name="lk_agency_pkey"),
    )
