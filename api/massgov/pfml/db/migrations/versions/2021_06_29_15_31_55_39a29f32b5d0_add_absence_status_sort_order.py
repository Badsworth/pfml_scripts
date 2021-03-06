"""add absence status sort order

Revision ID: 39a29f32b5d0
Revises: 60c62cce24ea
Create Date: 2021-06-29 15:31:55.892015

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "39a29f32b5d0"
down_revision = "60c62cce24ea"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "lk_absence_status",
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("lk_absence_status", "sort_order")
    # ### end Alembic commands ###
