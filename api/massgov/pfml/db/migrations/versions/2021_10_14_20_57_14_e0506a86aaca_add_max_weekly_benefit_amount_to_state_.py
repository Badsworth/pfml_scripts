"""add max weekly benefit amount to state metric table

Revision ID: e0506a86aaca
Revises: 2236f00cf4e7
Create Date: 2021-10-14 20:57:14.637159

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e0506a86aaca"
down_revision = "2236f00cf4e7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "state_metric", sa.Column("maximum_weekly_benefit_amount", sa.Numeric(), nullable=True)
    )
    op.execute("UPDATE state_metric SET maximum_weekly_benefit_amount = 850")
    op.alter_column("state_metric", "maximum_weekly_benefit_amount", nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("state_metric", "maximum_weekly_benefit_amount")
    # ### end Alembic commands ###