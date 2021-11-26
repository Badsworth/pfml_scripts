"""Include Benefit Year and Benefit Year Contribution Tables

Revision ID: 2d948baf863a
Revises: 7a466c88cc9a
Create Date: 2021-11-19 21:44:34.619755

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2d948baf863a"
down_revision = "7a466c88cc9a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "benefit_year",
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
        sa.Column("benefit_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_wages", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.employee_id"],),
        sa.PrimaryKeyConstraint("benefit_year_id"),
    )
    op.create_index(
        op.f("ix_benefit_year_employee_id"), "benefit_year", ["employee_id"], unique=False
    )
    op.create_table(
        "benefit_year_contribution",
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
        sa.Column("benefit_year_contribution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("benefit_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("average_weekly_wage", sa.Numeric(), nullable=False),
        sa.ForeignKeyConstraint(["benefit_year_id"], ["benefit_year.benefit_year_id"],),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.employee_id"],),
        sa.ForeignKeyConstraint(["employer_id"], ["employer.employer_id"],),
        sa.PrimaryKeyConstraint("benefit_year_contribution_id"),
    )
    op.create_index(
        op.f("ix_benefit_year_contribution_benefit_year_id"),
        "benefit_year_contribution",
        ["benefit_year_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benefit_year_contribution_employee_id"),
        "benefit_year_contribution",
        ["employee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_benefit_year_contribution_employer_id"),
        "benefit_year_contribution",
        ["employer_id"],
        unique=False,
    )
    op.create_index(
        "ix_benefit_year_id_employer_id_employee_id",
        "benefit_year_contribution",
        ["benefit_year_id", "employer_id", "employee_id"],
        unique=True,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "ix_benefit_year_id_employer_id_employee_id", table_name="benefit_year_contribution"
    )
    op.drop_index(
        op.f("ix_benefit_year_contribution_employer_id"), table_name="benefit_year_contribution"
    )
    op.drop_index(
        op.f("ix_benefit_year_contribution_employee_id"), table_name="benefit_year_contribution"
    )
    op.drop_index(
        op.f("ix_benefit_year_contribution_benefit_year_id"), table_name="benefit_year_contribution"
    )
    op.drop_table("benefit_year_contribution")
    op.drop_index(op.f("ix_benefit_year_employee_id"), table_name="benefit_year")
    op.drop_table("benefit_year")
    # ### end Alembic commands ###
