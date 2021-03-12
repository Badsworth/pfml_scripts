"""PUB-76: Add batch ID fkeys

Revision ID: 329cb33857e6
Revises: 69d14fefa414
Create Date: 2021-03-11 19:49:10.001825

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "329cb33857e6"
down_revision = "69d14fefa414"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "fineos_extract_employee_feed",
        sa.Column("fineos_extract_import_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_fineos_extract_employee_feed_fineos_extract_import_log_id"),
        "fineos_extract_employee_feed",
        ["fineos_extract_import_log_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fineos_extract_employee_feed_import_log_fkey",
        "fineos_extract_employee_feed",
        "import_log",
        ["fineos_extract_import_log_id"],
        ["import_log_id"],
    )
    op.add_column(
        "fineos_extract_vbi_requested_absence_som",
        sa.Column("fineos_extract_import_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_fineos_extract_vbi_requested_absence_som_fineos_extract_import_log_id"),
        "fineos_extract_vbi_requested_absence_som",
        ["fineos_extract_import_log_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fineos_extract_vbi_requested_absence_som_import_log_fkey",
        "fineos_extract_vbi_requested_absence_som",
        "import_log",
        ["fineos_extract_import_log_id"],
        ["import_log_id"],
    )
    op.add_column(
        "fineos_extract_vpei",
        sa.Column("fineos_extract_import_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_fineos_extract_vpei_fineos_extract_import_log_id"),
        "fineos_extract_vpei",
        ["fineos_extract_import_log_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fineos_extract_vpei_import_log_fkey",
        "fineos_extract_vpei",
        "import_log",
        ["fineos_extract_import_log_id"],
        ["import_log_id"],
    )
    op.add_column(
        "fineos_extract_vpei_claim_details",
        sa.Column("fineos_extract_import_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_fineos_extract_vpei_claim_details_fineos_extract_import_log_id"),
        "fineos_extract_vpei_claim_details",
        ["fineos_extract_import_log_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fineos_extract_vpei_claim_details_import_log_fkey",
        "fineos_extract_vpei_claim_details",
        "import_log",
        ["fineos_extract_import_log_id"],
        ["import_log_id"],
    )
    op.add_column(
        "fineos_extract_vpei_payment_details",
        sa.Column("fineos_extract_import_log_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_fineos_extract_vpei_payment_details_fineos_extract_import_log_id"),
        "fineos_extract_vpei_payment_details",
        ["fineos_extract_import_log_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fineos_extract_vpei_payment_details_import_log_fkey",
        "fineos_extract_vpei_payment_details",
        "import_log",
        ["fineos_extract_import_log_id"],
        ["import_log_id"],
    )
    op.add_column("payment", sa.Column("fineos_extract_import_log_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_payment_fineos_extract_import_log_id"),
        "payment",
        ["fineos_extract_import_log_id"],
        unique=False,
    )
    op.create_foreign_key(
        "payment_import_log_fkey",
        "payment",
        "import_log",
        ["fineos_extract_import_log_id"],
        ["import_log_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("payment_import_log_fkey", "payment", type_="foreignkey")
    op.drop_index(op.f("ix_payment_fineos_extract_import_log_id"), table_name="payment")
    op.drop_column("payment", "fineos_extract_import_log_id")
    op.drop_constraint(
        "fineos_extract_vpei_payment_details_import_log_fkey",
        "fineos_extract_vpei_payment_details",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_fineos_extract_vpei_payment_details_fineos_extract_import_log_id"),
        table_name="fineos_extract_vpei_payment_details",
    )
    op.drop_column("fineos_extract_vpei_payment_details", "fineos_extract_import_log_id")
    op.drop_constraint(
        "fineos_extract_vpei_claim_details_import_log_fkey",
        "fineos_extract_vpei_claim_details",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_fineos_extract_vpei_claim_details_fineos_extract_import_log_id"),
        table_name="fineos_extract_vpei_claim_details",
    )
    op.drop_column("fineos_extract_vpei_claim_details", "fineos_extract_import_log_id")
    op.drop_constraint(
        "fineos_extract_vpei_import_log_fkey", "fineos_extract_vpei", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_fineos_extract_vpei_fineos_extract_import_log_id"),
        table_name="fineos_extract_vpei",
    )
    op.drop_column("fineos_extract_vpei", "fineos_extract_import_log_id")
    op.drop_constraint(
        "fineos_extract_vbi_requested_absence_som_import_log_fkey",
        "fineos_extract_vbi_requested_absence_som",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_fineos_extract_vbi_requested_absence_som_fineos_extract_import_log_id"),
        table_name="fineos_extract_vbi_requested_absence_som",
    )
    op.drop_column("fineos_extract_vbi_requested_absence_som", "fineos_extract_import_log_id")
    op.drop_constraint(
        "fineos_extract_employee_feed_import_log_fkey",
        "fineos_extract_employee_feed",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_fineos_extract_employee_feed_fineos_extract_import_log_id"),
        table_name="fineos_extract_employee_feed",
    )
    op.drop_column("fineos_extract_employee_feed", "fineos_extract_import_log_id")
    # ### end Alembic commands ###
