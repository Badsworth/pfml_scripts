"""PUB-230: Add absence case creation date

Revision ID: f9b52efbafd9
Revises: d05f54e18609
Create Date: 2021-06-17 14:13:16.292514

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f9b52efbafd9"
down_revision = "d05f54e18609"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("payment", sa.Column("absence_case_creation_date", sa.Date(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("payment", "absence_case_creation_date")
    # ### end Alembic commands ###
