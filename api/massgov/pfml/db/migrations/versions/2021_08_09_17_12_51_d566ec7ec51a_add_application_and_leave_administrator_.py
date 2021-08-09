"""Add application and leave administrator deparment collection

Revision ID: d566ec7ec51a
Revises: b09e9c9cfd01
Create Date: 2021-08-09 17:12:51.731573

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d566ec7ec51a"
down_revision = "b09e9c9cfd01"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_reporting_unit",
        sa.Column("reporting_unit_id", sa.Integer(), nullable=False),
        sa.Column("reporting_unit_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("reporting_unit_id"),
    )
    op.create_table(
        "lk_worksite",
        sa.Column("worksite_id", sa.Integer(), nullable=False),
        sa.Column("worksite_description", sa.Text(), nullable=True),
        sa.Column("worksite_fineos_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("worksite_id"),
    )
    op.create_unique_constraint(
        "user_leave_administrator_id_unique", "link_user_leave_administrator", ["user_leave_administrator_id"]
    )
    op.create_table(
        "lk_user_leave_administrator_department",
        sa.Column("user_leave_administrator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporting_unit_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["reporting_unit_id"], ["lk_reporting_unit.reporting_unit_id"],),
        sa.ForeignKeyConstraint(
            ["user_leave_administrator_id"],
            ["link_user_leave_administrator.user_leave_administrator_id"],
        ),
        sa.PrimaryKeyConstraint("user_leave_administrator_id", "reporting_unit_id"),
    )
    op.add_column("application", sa.Column("reporting_unit_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "application_reporting_unit_id_fkey", "application", "lk_reporting_unit", ["reporting_unit_id"], ["reporting_unit_id"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("user_leave_administrator_id_unique", "link_user_leave_administrator", type_="unique")
    op.drop_constraint("application_reporting_unit_id_fkey", "application", type_="foreignkey")
    op.drop_column("application", "reporting_unit_id")
    op.drop_table("lk_user_leave_administrator_department")
    op.drop_table("lk_worksite")
    op.drop_table("lk_reporting_unit")
    # ### end Alembic commands ###
