"""Switch DIA payment table from absence case to customer number

Revision ID: e4ec4cc9647d
Revises: 3e9650966949
Create Date: 2021-03-30 16:38:15.186838

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e4ec4cc9647d"
down_revision = "3e9650966949"
branch_labels = None
depends_on = None


def upgrade():
    # Remove old index that references absence_case_id
    op.drop_index(
        op.f("dia_reduction_payment_absence_case_id_coalesce_coalesce1_co_idx"),
        table_name="dia_reduction_payment",
    )

    op.add_column(
        "dia_reduction_payment", sa.Column("fineos_customer_number", sa.Text(), nullable=False)
    )
    op.drop_column("dia_reduction_payment", "absence_case_id")

    # Adjust the unique index so that we coalesce all nullable fields to empty strings, 99999999
    # (for numeric), and 1788-02-06 (for dates) to ensure uniqueness across all fields.
    op.execute(
        """
        CREATE UNIQUE INDEX dia_reduction_payment_unique_payment_data_idx ON dia_reduction_payment (
            fineos_customer_number,
            coalesce(board_no, ''),
            coalesce(event_id, ''),
            coalesce(event_description, ''),
            coalesce(eve_created_date, '1788-02-06'),
            coalesce(event_occurrence_date, '1788-02-06'),
            coalesce(award_id, ''),
            coalesce(award_code, ''),
            coalesce(award_amount, 99999999),
            coalesce(award_date, '1788-02-06'),
            coalesce(start_date, '1788-02-06'),
            coalesce(end_date, '1788-02-06'),
            coalesce(weekly_amount, 99999999),
            coalesce(award_created_date, '1788-02-06')
        )
    """
    )


def downgrade():
    op.add_column(
        "dia_reduction_payment",
        sa.Column("absence_case_id", sa.TEXT(), autoincrement=False, nullable=False),
    )
    op.drop_column("dia_reduction_payment", "fineos_customer_number")

    op.execute(
        """
        create unique index on dia_reduction_payment (
            absence_case_id,
            coalesce(board_no, ''),
            coalesce(event_id, ''),
            coalesce(event_description, ''),
            coalesce(eve_created_date, '1788-02-06'),
            coalesce(event_occurrence_date, '1788-02-06'),
            coalesce(award_id, ''),
            coalesce(award_code, ''),
            coalesce(award_amount, 99999999),
            coalesce(award_date, '1788-02-06'),
            coalesce(start_date, '1788-02-06'),
            coalesce(end_date, '1788-02-06'),
            coalesce(weekly_amount, 99999999),
            coalesce(award_created_date, '1788-02-06')
        )
    """
    )
