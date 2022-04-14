"""first_name last_name and phone_number to user

Revision ID: 02f64a649015
Revises: c7425fa3402e
Create Date: 2022-04-13 18:11:07.690678

"""
import sqlalchemy as sa
from alembic import op

revision = "02f64a649015"
down_revision = "c7425fa3402e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("first_name", sa.Text(), nullable=True))
    op.add_column("user", sa.Column("last_name", sa.Text(), nullable=True))
    op.add_column("user", sa.Column("phone_number", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("user", "first_name")
    op.drop_column("user", "last_name")
    op.drop_column("user", "phone_number")
