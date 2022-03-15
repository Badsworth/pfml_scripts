"""Alter reference_file table

Revision ID: 8e69b1f33fbb
Revises: f1d2e7bf289b
Create Date: 2020-12-15 14:38:48.763395

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8e69b1f33fbb"
down_revision = "f1d2e7bf289b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "reference_file", "reference_file_type_id", existing_type=sa.Integer(), nullable=True
    )
    op.create_index(
        op.f("ix_reference_file_file_location"), "reference_file", ["file_location"], unique=True
    )
    pass


def downgrade():
    op.alter_column(
        "reference_file", "reference_file_type_id", existing_type=sa.Integer(), nullable=False
    )
    op.drop_index(op.f("ix_reference_file_file_location"), table_name="reference_file")
    pass
