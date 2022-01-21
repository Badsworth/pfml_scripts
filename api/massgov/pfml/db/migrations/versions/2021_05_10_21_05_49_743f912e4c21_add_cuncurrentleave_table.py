"""Add CuncurrentLeave table.

Revision ID: 743f912e4c21
Revises: f11d9353b6f6
Create Date: 2021-05-10 21:05:49.630009

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "743f912e4c21"
down_revision = "a654bf03da3f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "concurrent_leave",
        sa.Column("concurrent_leave_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_for_current_employer", sa.Boolean(), nullable=True),
        sa.Column("leave_start_date", sa.Date(), nullable=True),
        sa.Column("leave_end_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["application.application_id"],),
        sa.PrimaryKeyConstraint("concurrent_leave_id"),
    )
    op.create_index(
        op.f("ix_concurrent_leave_application_id"),
        "concurrent_leave",
        ["application_id"],
        unique=False,
    )
    op.add_column("application", sa.Column("has_concurrent_leave", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("application", "has_concurrent_leave")
    op.drop_index(op.f("ix_concurrent_leave_application_id"), table_name="concurrent_leave")
    op.drop_table("concurrent_leave")
    # ### end Alembic commands ###