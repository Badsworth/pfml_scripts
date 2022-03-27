"""Corrects phone numbers that are just a +

Revision ID: dcb69fd878da
Revises: 669cb17688dd
Create Date: 2022-03-10 20:19:21.181852

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "dcb69fd878da"
down_revision = "669cb17688dd"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE employee SET phone_number = NULL WHERE phone_number = '+'")
    op.execute("UPDATE employee SET cell_phone_number = NULL WHERE cell_phone_number = '+'")


def downgrade():
    # No-op. Don't reintroduce bad data on downgrade!
    pass
