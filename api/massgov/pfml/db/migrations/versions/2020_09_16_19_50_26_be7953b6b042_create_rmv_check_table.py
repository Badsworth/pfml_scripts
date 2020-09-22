"""Create rmv_check table

Revision ID: be7953b6b042
Revises: 2f571f16ffb6
Create Date: 2020-09-16 19:50:26.828494

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "be7953b6b042"
down_revision = "2f571f16ffb6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rmv_check",
        sa.Column("rmv_check_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("request_to_rmv_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("request_to_rmv_completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("check_expiration", sa.Boolean(), server_default="FALSE", nullable=False),
        sa.Column("check_customer_inactive", sa.Boolean(), server_default="FALSE", nullable=False),
        sa.Column(
            "check_active_fraudulent_activity", sa.Boolean(), server_default="FALSE", nullable=False
        ),
        sa.Column("check_mass_id_number", sa.Boolean(), server_default="FALSE", nullable=False),
        sa.Column(
            "check_residential_address_line_1", sa.Boolean(), server_default="FALSE", nullable=False
        ),
        sa.Column(
            "check_residential_address_line_2", sa.Boolean(), server_default="FALSE", nullable=False
        ),
        sa.Column("check_residential_city", sa.Boolean(), server_default="FALSE", nullable=False),
        sa.Column(
            "check_residential_zip_code", sa.Boolean(), server_default="FALSE", nullable=False
        ),
        sa.Column("rmv_error_code", sa.Text(), nullable=True),
        sa.Column("api_error_code", sa.Text(), nullable=True),
        sa.Column("absence_case_id", sa.Text(), nullable=False),
        sa.Column("rmv_customer_key", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("rmv_check_id"),
    )


def downgrade():
    op.drop_table("rmv_check")
