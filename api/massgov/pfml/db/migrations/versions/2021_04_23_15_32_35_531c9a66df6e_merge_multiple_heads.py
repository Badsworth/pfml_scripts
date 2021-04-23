"""Merge multiple heads

Revision ID: 531c9a66df6e
Revises: fd61facec777, f179009904e7
Create Date: 2021-04-23 15:32:35.794867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "531c9a66df6e"
down_revision = ("fd61facec777", "f179009904e7")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
