"""Create dua_reduction_payment table

Revision ID: 14155f78d8e6
Revises: cf724b0a7cc4
Create Date: 2021-01-29 15:51:16.741203

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "14155f78d8e6"
down_revision = "cf724b0a7cc4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dua_reduction_payment",
        sa.Column("dua_reduction_payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("absence_case_id", sa.Text(), nullable=False),
        sa.Column("employer_fein", sa.Text(), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("request_week_begin_date", sa.Date(), nullable=True),
        sa.Column("gross_payment_amount_cents", sa.Integer(), nullable=True),
        sa.Column("payment_amount_cents", sa.Integer(), nullable=True),
        sa.Column("fraud_indicator", sa.Text(), nullable=True),
        sa.Column("benefit_year_begin_date", sa.Date(), nullable=True),
        sa.Column("benefit_year_end_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("dua_reduction_payment_id"),
    )

    # Adjust the unique index so that we coalesce all nullable fields to empty strings, 99999999
    # (for integers), and 1788-02-06 (for dates) to ensure uniqueness across all fields.
    op.execute(
        """
        create unique index on dua_reduction_payment (
            absence_case_id,
            coalesce(employer_fein, ''),
            coalesce(payment_date, '1788-02-06'),
            coalesce(request_week_begin_date, '1788-02-06'),
            coalesce(gross_payment_amount_cents, 99999999),
            coalesce(payment_amount_cents, 99999999),
            coalesce(fraud_indicator, ''),
            coalesce(benefit_year_end_date, '1788-02-06'),
            coalesce(benefit_year_begin_date, '1788-02-06')
        )
    """
    )


def downgrade():
    op.drop_table("dua_reduction_payment")
