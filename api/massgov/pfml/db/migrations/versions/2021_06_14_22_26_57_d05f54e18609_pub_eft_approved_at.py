"""pub eft approved at

Revision ID: d05f54e18609
Revises: 13eb397da2f3
Create Date: 2021-06-14 22:26:57.006317

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d05f54e18609"
down_revision = "13eb397da2f3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "pub_eft", sa.Column("prenote_approved_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("pub_eft", "prenote_approved_at")
    # ### end Alembic commands ###