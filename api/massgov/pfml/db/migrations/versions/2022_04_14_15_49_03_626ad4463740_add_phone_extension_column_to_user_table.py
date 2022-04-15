"""add phone_extension column to user table

Revision ID: 626ad4463740
Revises: 02f64a649015
Create Date: 2022-04-14 15:49:03.034856

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "626ad4463740"
down_revision = "02f64a649015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("phone_extension", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("user", "phone_extension")
