"""Switch DUA payment data to use FINEOS customer number

Revision ID: a654bf03da3f
Revises: f11d9353b6f6
Create Date: 2021-04-27 17:07:38.485043

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a654bf03da3f"
down_revision = "f11d9353b6f6"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(
        op.f("dua_reduction_payment_absence_case_id_coalesce_coalesce1_co_idx"),
        table_name="dua_reduction_payment",
    )

    op.add_column(
        "dua_reduction_payment", sa.Column("fineos_customer_number", sa.Text(), nullable=True)
    )

    # Update payment rows with customer number for recorded absence_case_id
    op.execute(
        """
        WITH q AS (
            SELECT c.fineos_absence_id, ee.fineos_customer_number
            FROM claim c
            JOIN employee ee ON ee.employee_id = c.employee_id
        )
        UPDATE dua_reduction_payment drp
        SET fineos_customer_number = q.fineos_customer_number
        FROM q
        WHERE drp.absence_case_id = q.fineos_absence_id
        """
    )

    # Add delete cascade to handle reference files easily
    op.execute(
        "ALTER TABLE link_dua_reduction_payment_reference_file DROP CONSTRAINT link_dua_reduction_payment_refere_dua_reduction_payment_id_fkey"
    )
    op.execute(
        "ALTER TABLE link_dua_reduction_payment_reference_file ADD FOREIGN KEY (dua_reduction_payment_id) REFERENCES dua_reduction_payment(dua_reduction_payment_id) ON DELETE CASCADE"
    )

    # This should not be possible, but if there are any NULL
    # fineos_customer_number values, populate the column with the
    # absence_case_id value so we can inspect and fix after the migration
    op.execute(
        """
        UPDATE dua_reduction_payment
        SET fineos_customer_number = absence_case_id
        WHERE fineos_customer_number IS NULL
        """
    )

    # De-dupe reduction payments rows
    # Basically any row that matches on everything except absence_case_id and created_at
    op.execute(
        """
        DELETE FROM dua_reduction_payment
        WHERE dua_reduction_payment_id IN (
            SELECT dua_reduction_payment_id
                FROM (
                SELECT
                    dua_reduction_payment_id,
                    row_number() OVER w as rnum
                FROM dua_reduction_payment
                WINDOW w AS (
                    PARTITION BY
                        fineos_customer_number,
                        employer_fein,
                        payment_date,
                        request_week_begin_date,
                        gross_payment_amount_cents,
                        payment_amount_cents,
                        fraud_indicator,
                        benefit_year_begin_date,
                        benefit_year_end_date
                    ORDER BY created_at
                )
            ) t
            WHERE t.rnum > 1
        )
        """
    )

    # Add back non-cascading constraint
    op.execute(
        "ALTER TABLE link_dua_reduction_payment_reference_file DROP CONSTRAINT link_dua_reduction_payment_refere_dua_reduction_payment_id_fkey"
    )
    op.execute(
        "ALTER TABLE link_dua_reduction_payment_reference_file ADD FOREIGN KEY (dua_reduction_payment_id) REFERENCES dua_reduction_payment(dua_reduction_payment_id)"
    )

    # Update column to be NOT NULL
    op.alter_column(
        "dua_reduction_payment", "fineos_customer_number", existing_type=sa.TEXT(), nullable=False
    )

    # Remove old column
    op.drop_column("dua_reduction_payment", "absence_case_id")

    # Recreate index
    op.execute(
        """
        CREATE UNIQUE INDEX dua_reduction_payment_unique_payment_data_idx ON dua_reduction_payment (
            fineos_customer_number,
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
    # There's effectively no going back
    pass
