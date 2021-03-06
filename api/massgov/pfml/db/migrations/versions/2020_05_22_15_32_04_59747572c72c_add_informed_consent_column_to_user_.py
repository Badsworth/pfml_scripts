"""add informed consent column to user table

Revision ID: 59747572c72c
Revises: 918ba8aceb3b
Create Date: 2020-05-22 15:32:04.122246

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "59747572c72c"
down_revision = "eeaec8bc17c0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column(
            "consented_to_data_sharing", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "consented_to_data_sharing")
    # ### end Alembic commands ###
