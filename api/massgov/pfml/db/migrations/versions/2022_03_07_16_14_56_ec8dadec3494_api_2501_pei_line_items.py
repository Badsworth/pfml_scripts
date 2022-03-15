"""API-2501: PEI Line Items

Revision ID: ec8dadec3494
Revises: 028f08735753
Create Date: 2022-03-07 16:14:56.839140

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ec8dadec3494"
down_revision = "028f08735753"
branch_labels = None
depends_on = None


def upgrade():
    # Fix payment_details_pkey
    op.drop_constraint("payment_details_pkey", "payment_details", type_="primary")
    op.create_primary_key("payment_details_pkey", "payment_details", ["payment_details_id"])

    op.create_table(
        "fineos_extract_vpei_payment_line",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("vpei_payment_line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("c", sa.Text(), nullable=True),
        sa.Column("i", sa.Text(), nullable=True),
        sa.Column("lastupdatedate", sa.Text(), nullable=True),
        sa.Column("c_osuser_updatedby", sa.Text(), nullable=True),
        sa.Column("i_osuser_updatedby", sa.Text(), nullable=True),
        sa.Column("amount_monamt", sa.Text(), nullable=True),
        sa.Column("amount_moncur", sa.Text(), nullable=True),
        sa.Column("integrtype", sa.Text(), nullable=True),
        sa.Column("linetype", sa.Text(), nullable=True),
        sa.Column("reference", sa.Text(), nullable=True),
        sa.Column("reservecatego", sa.Text(), nullable=True),
        sa.Column("reservetype", sa.Text(), nullable=True),
        sa.Column("sequencenumbe", sa.Text(), nullable=True),
        sa.Column("subtotals", sa.Text(), nullable=True),
        sa.Column("taxableincome", sa.Text(), nullable=True),
        sa.Column("usetocalcrule", sa.Text(), nullable=True),
        sa.Column("c_pymnteif_paymentlines", sa.Text(), nullable=True),
        sa.Column("i_pymnteif_paymentlines", sa.Text(), nullable=True),
        sa.Column("paymentdetailclassid", sa.Text(), nullable=True),
        sa.Column("paymentdetailindexid", sa.Text(), nullable=True),
        sa.Column("purchasedetailclassid", sa.Text(), nullable=True),
        sa.Column("purchasedetailindexid", sa.Text(), nullable=True),
        sa.Column("dateinterface", sa.Text(), nullable=True),
        sa.Column("reference_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fineos_extract_import_log_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["fineos_extract_import_log_id"],
            ["import_log.import_log_id"],
        ),
        sa.ForeignKeyConstraint(
            ["reference_file_id"],
            ["reference_file.reference_file_id"],
        ),
        sa.PrimaryKeyConstraint("vpei_payment_line_id"),
    )
    op.create_index(
        op.f("ix_fineos_extract_vpei_payment_line_fineos_extract_import_log_id"),
        "fineos_extract_vpei_payment_line",
        ["fineos_extract_import_log_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fineos_extract_vpei_payment_line_reference_file_id"),
        "fineos_extract_vpei_payment_line",
        ["reference_file_id"],
        unique=False,
    )
    op.create_table(
        "payment_line",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("payment_line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vpei_payment_line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_details_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_line_c_value", sa.Text(), nullable=False),
        sa.Column("payment_line_i_value", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("line_type", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["payment_details_id"],
            ["payment_details.payment_details_id"],
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payment.payment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["vpei_payment_line_id"],
            ["fineos_extract_vpei_payment_line.vpei_payment_line_id"],
        ),
        sa.PrimaryKeyConstraint("payment_line_id"),
    )
    op.create_index(
        op.f("ix_payment_line_payment_details_id"),
        "payment_line",
        ["payment_details_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_line_payment_id"), "payment_line", ["payment_id"], unique=False
    )
    op.create_index(
        op.f("ix_payment_line_payment_line_c_value"),
        "payment_line",
        ["payment_line_c_value"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_line_payment_line_i_value"),
        "payment_line",
        ["payment_line_i_value"],
        unique=False,
    )
    op.add_column("payment_details", sa.Column("payment_details_c_value", sa.Text(), nullable=True))
    op.add_column("payment_details", sa.Column("payment_details_i_value", sa.Text(), nullable=True))
    op.add_column(
        "payment_details",
        sa.Column("vpei_payment_details_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_payment_details_payment_details_c_value"),
        "payment_details",
        ["payment_details_c_value"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_details_payment_details_i_value"),
        "payment_details",
        ["payment_details_i_value"],
        unique=False,
    )
    op.create_foreign_key(
        "payment_details_fineos_extract_vpei_payment_details_fkey",
        "payment_details",
        "fineos_extract_vpei_payment_details",
        ["vpei_payment_details_id"],
        ["vpei_payment_details_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "payment_details_fineos_extract_vpei_payment_details_fkey",
        "payment_details",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_payment_details_payment_details_i_value"), table_name="payment_details")
    op.drop_index(op.f("ix_payment_details_payment_details_c_value"), table_name="payment_details")
    op.drop_column("payment_details", "vpei_payment_details_id")
    op.drop_column("payment_details", "payment_details_i_value")
    op.drop_column("payment_details", "payment_details_c_value")
    op.drop_index(op.f("ix_payment_line_payment_line_i_value"), table_name="payment_line")
    op.drop_index(op.f("ix_payment_line_payment_line_c_value"), table_name="payment_line")
    op.drop_index(op.f("ix_payment_line_payment_id"), table_name="payment_line")
    op.drop_index(op.f("ix_payment_line_payment_details_id"), table_name="payment_line")
    op.drop_table("payment_line")
    op.drop_index(
        op.f("ix_fineos_extract_vpei_payment_line_reference_file_id"),
        table_name="fineos_extract_vpei_payment_line",
    )
    op.drop_index(
        op.f("ix_fineos_extract_vpei_payment_line_fineos_extract_import_log_id"),
        table_name="fineos_extract_vpei_payment_line",
    )
    op.drop_table("fineos_extract_vpei_payment_line")

    op.drop_constraint("payment_details_pkey", "payment_details", type_="primary")
    op.create_primary_key(
        "payment_details_pkey", "payment_details", ["payment_details_id", "payment_id"]
    )
    # ### end Alembic commands ###
