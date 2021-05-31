"""Merge multiple heads

Revision ID: ce1a02cea019
Revises: fb5262bede61, 7e4cd8f28ddc
Create Date: 2021-05-26 17:01:11.635194

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ce1a02cea019"
down_revision = ("fb5262bede61", "7e4cd8f28ddc")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
