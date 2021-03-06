"""Add payee fullname to Payment

Revision ID: 3cf07191b8d6
Revises: b9e3f491eba2
Create Date: 2022-03-11 16:37:45.033605

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3cf07191b8d6"
down_revision = "b9e3f491eba2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("payment", sa.Column("payee_name", sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("payment", "payee_name")
    # ### end Alembic commands ###
