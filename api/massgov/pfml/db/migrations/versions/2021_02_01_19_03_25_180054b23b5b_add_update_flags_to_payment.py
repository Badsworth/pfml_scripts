"""Add update flags to payment

Revision ID: 180054b23b5b
Revises: 2fbc25c28b0e
Create Date: 2021-02-01 19:03:25.293115

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "180054b23b5b"
down_revision = "2fbc25c28b0e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "payment",
        sa.Column("has_address_update", sa.Boolean(), server_default="FALSE", nullable=False),
    )
    op.add_column(
        "payment", sa.Column("has_eft_update", sa.Boolean(), server_default="FALSE", nullable=False)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("payment", "has_eft_update")
    op.drop_column("payment", "has_address_update")
    # ### end Alembic commands ###
