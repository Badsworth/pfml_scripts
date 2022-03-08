"""Add tables for employer benefits and other incomes

Revision ID: e01223effa2b
Revises: 3267f0d49aed
Create Date: 2020-11-16 22:50:51.834879

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e01223effa2b"
down_revision = "3267f0d49aed"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_amount_frequency",
        sa.Column("amount_frequency_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("amount_frequency_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("amount_frequency_id"),
    )
    op.create_table(
        "lk_employer_benefit_type",
        sa.Column("employer_benefit_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employer_benefit_type_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("employer_benefit_type_id"),
    )
    op.create_table(
        "lk_other_income_type",
        sa.Column("other_income_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("other_income_type_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("other_income_type_id"),
    )
    op.create_table(
        "employer_benefit",
        sa.Column("employer_benefit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("benefit_start_date", sa.Date(), nullable=True),
        sa.Column("benefit_end_date", sa.Date(), nullable=True),
        sa.Column("benefit_type_id", sa.Integer(), nullable=True),
        sa.Column("benefit_amount_dollars", sa.Numeric(), nullable=True),
        sa.Column("benefit_amount_frequency_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.application_id"]),
        sa.ForeignKeyConstraint(
            ["benefit_amount_frequency_id"], ["lk_amount_frequency.amount_frequency_id"]
        ),
        sa.ForeignKeyConstraint(
            ["benefit_type_id"], ["lk_employer_benefit_type.employer_benefit_type_id"]
        ),
        sa.PrimaryKeyConstraint("employer_benefit_id"),
    )
    op.create_index(
        op.f("ix_employer_benefit_application_id"),
        "employer_benefit",
        ["application_id"],
        unique=False,
    )
    op.create_table(
        "other_income",
        sa.Column("other_income_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("income_start_date", sa.Date(), nullable=True),
        sa.Column("income_end_date", sa.Date(), nullable=True),
        sa.Column("income_type_id", sa.Integer(), nullable=True),
        sa.Column("income_amount_dollars", sa.Numeric(), nullable=True),
        sa.Column("income_amount_frequency_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.application_id"]),
        sa.ForeignKeyConstraint(
            ["income_amount_frequency_id"], ["lk_amount_frequency.amount_frequency_id"]
        ),
        sa.ForeignKeyConstraint(["income_type_id"], ["lk_other_income_type.other_income_type_id"]),
        sa.PrimaryKeyConstraint("other_income_id"),
    )
    op.create_index(
        op.f("ix_other_income_application_id"), "other_income", ["application_id"], unique=False
    )
    op.add_column("application", sa.Column("has_employer_benefits", sa.Boolean(), nullable=True))
    op.add_column("application", sa.Column("has_other_incomes", sa.Boolean(), nullable=True))
    op.add_column(
        "application", sa.Column("other_incomes_awaiting_approval", sa.Boolean(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("application", "other_incomes_awaiting_approval")
    op.drop_column("application", "has_other_incomes")
    op.drop_column("application", "has_employer_benefits")
    op.drop_index(op.f("ix_other_income_application_id"), table_name="other_income")
    op.drop_table("other_income")
    op.drop_index(op.f("ix_employer_benefit_application_id"), table_name="employer_benefit")
    op.drop_table("employer_benefit")
    op.drop_table("lk_other_income_type")
    op.drop_table("lk_employer_benefit_type")
    op.drop_table("lk_amount_frequency")
    # ### end Alembic commands ###
