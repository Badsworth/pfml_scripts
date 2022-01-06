"""Add has_mailing_address to Application model

Revision ID: 37f1504f1b9f
Revises: f1720ed9d6e6
Create Date: 2020-09-24 20:52:48.277216

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "37f1504f1b9f"
down_revision = "f1720ed9d6e6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("application", sa.Column("has_mailing_address", sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("application", "has_mailing_address")
    # ### end Alembic commands ###