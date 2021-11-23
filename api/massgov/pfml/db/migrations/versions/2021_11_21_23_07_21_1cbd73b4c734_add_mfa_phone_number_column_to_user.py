"""Add mfa_phone_number column to User

Revision ID: 1cbd73b4c734
Revises: 2d948baf863a
Create Date: 2021-11-21 23:07:21.967108

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1cbd73b4c734"
down_revision = "2d948baf863a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("mfa_phone_number", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("user", "mfa_phone_number")
