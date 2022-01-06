"""Add DUA Employee Demographics table

Revision ID: 95d3e464a5b2
Revises: 2895730a681e
Create Date: 2021-10-04 13:30:03.888961

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "95d3e464a5b2"
down_revision = "2895730a681e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "dua_employee_demographics",
        sa.Column("dua_employee_demographics_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fineos_customer_number", sa.Text(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender_code", sa.Text(), nullable=True),
        sa.Column("occupation_code", sa.Text(), nullable=True),
        sa.Column("occupation_description", sa.Text(), nullable=True),
        sa.Column("employer_fein", sa.Text(), nullable=True),
        sa.Column("employer_reporting_unit_number", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("dua_employee_demographics_id"),
    )

    # Adjust the unique index so that we coalesce all nullable fields to empty strings, 1788-02-06 (for dates)
    # to ensure uniqueness across all fields.
    op.execute(
        """
        CREATE UNIQUE INDEX dua_employee_demographics_unique_import_data_idx ON dua_employee_demographics (
            fineos_customer_number,
            coalesce(date_of_birth, '1788-02-06'),
            coalesce(gender_code, 'M'),
            coalesce(occupation_code, ''),
            coalesce(occupation_description, ''),
            coalesce(employer_fein, ''),
            coalesce(employer_reporting_unit_number, '')
        )
    """
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("dua_employee_demographics")
    # ### end Alembic commands ###