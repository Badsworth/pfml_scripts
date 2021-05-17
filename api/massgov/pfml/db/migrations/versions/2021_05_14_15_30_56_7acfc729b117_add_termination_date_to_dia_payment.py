"""add termination date to dia payment

Revision ID: 7acfc729b117
Revises: c911058236e6
Create Date: 2021-05-14 15:30:56.652423

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7acfc729b117"
down_revision = "c911058236e6"
branch_labels = None
depends_on = None


def upgrade():
    # Remove old index
    op.drop_index(
        op.f("dia_reduction_payment_unique_payment_data_idx"), table_name="dia_reduction_payment",
    )

    op.add_column("dia_reduction_payment", sa.Column("termination_date", sa.Date(), nullable=True))

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
            coalesce(award_created_date, '1788-02-06'),
            coalesce(termination_date, '1788-02-06')
        )
    """
    )


def downgrade():
    op.drop_index(
        op.f("dia_reduction_payment_unique_payment_data_idx"), table_name="dia_reduction_payment",
    )

    op.drop_column("dia_reduction_payment", "termination_date")

    op.execute(
        """
        create unique index on dia_reduction_payment (
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
