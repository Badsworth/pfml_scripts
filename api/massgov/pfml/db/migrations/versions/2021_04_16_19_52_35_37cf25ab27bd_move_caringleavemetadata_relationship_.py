"""move CaringLeaveMetadata relationship to Application

Revision ID: 37cf25ab27bd
Revises: 27e8f899e06b
Create Date: 2021-04-16 19:52:35.271397

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "37cf25ab27bd"
down_revision = "27e8f899e06b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "application",
        sa.Column("caring_leave_metadata_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        None,
        "application",
        "caring_leave_metadata",
        ["caring_leave_metadata_id"],
        ["caring_leave_metadata_id"],
    )
    op.drop_index("ix_caring_leave_metadata_application_id", table_name="caring_leave_metadata")
    op.drop_constraint(
        "caring_leave_metadata_application_id_fkey", "caring_leave_metadata", type_="foreignkey"
    )
    op.drop_column("caring_leave_metadata", "application_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "caring_leave_metadata",
        sa.Column("application_id", postgresql.UUID(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "caring_leave_metadata_application_id_fkey",
        "caring_leave_metadata",
        "application",
        ["application_id"],
        ["application_id"],
    )
    op.create_index(
        "ix_caring_leave_metadata_application_id",
        "caring_leave_metadata",
        ["application_id"],
        unique=True,
    )
    op.drop_constraint(
        "application_caring_leave_metadata_id_fkey", "application", type_="foreignkey"
    )
    op.drop_column("application", "caring_leave_metadata_id")
    # ### end Alembic commands ###
