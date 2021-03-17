"""add has passed required checks to rmv check

Revision ID: 7a7f2607f99d
Revises: b18221900c52
Create Date: 2021-03-13 01:04:34.308839

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7a7f2607f99d"
down_revision = "b18221900c52"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "rmv_check",
        sa.Column(
            "has_passed_required_checks", sa.Boolean(), server_default="FALSE", nullable=False
        ),
    )

    op.execute(
        """
     UPDATE rmv_check
        SET has_passed_required_checks = TRUE
      WHERE check_expiration IS TRUE
        AND check_customer_inactive IS TRUE
        AND check_active_fraudulent_activity IS TRUE
        AND check_mass_id_number IS TRUE
        AND check_residential_address_line_1 IS TRUE
        AND check_residential_address_line_2 IS TRUE
        AND check_residential_city IS TRUE
        AND check_residential_zip_code IS TRUE;
"""
    )


def downgrade():
    op.drop_column("rmv_check", "has_passed_required_checks")
