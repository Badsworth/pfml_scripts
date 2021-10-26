"""Add tax withholding column to application table

Revision ID: 63428c75d9ab
Revises: ad96057b62c9
Create Date: 2021-10-25 19:00:05.557829

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "63428c75d9ab"
down_revision = "ad96057b62c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("application", sa.Column("is_withholding_tax", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("application", "is_withholding_tax")
