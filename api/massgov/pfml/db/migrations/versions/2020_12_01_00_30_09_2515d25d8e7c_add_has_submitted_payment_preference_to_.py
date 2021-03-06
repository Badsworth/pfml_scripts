"""Add has_submitted_payment_preference to Application

Revision ID: 2515d25d8e7c
Revises: 1e28741cdbd3
Create Date: 2020-12-01 00:30:09.397452

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2515d25d8e7c"
down_revision = "7393f844246f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "application", sa.Column("has_submitted_payment_preference", sa.Boolean(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("application", "has_submitted_payment_preference")
    # ### end Alembic commands ###
