"""Merge multiple heads

Revision ID: 209b024b1ea6
Revises: 12017bbb31e1, 3e14d30da6ff
Create Date: 2021-10-19 15:48:41.458186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "209b024b1ea6"
down_revision = ("12017bbb31e1", "3e14d30da6ff")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
