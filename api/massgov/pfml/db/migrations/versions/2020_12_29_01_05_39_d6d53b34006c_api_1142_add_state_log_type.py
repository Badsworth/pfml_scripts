"""API-1142: Add state log type

Revision ID: d6d53b34006c
Revises: 3a27e33dfbda
Create Date: 2020-12-29 01:05:39.107342

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d6d53b34006c"
down_revision = "3a27e33dfbda"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("state_log", sa.Column("associated_type", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_state_log_associated_type"), "state_log", ["associated_type"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_state_log_associated_type"), table_name="state_log")
    op.drop_column("state_log", "associated_type")
    # ### end Alembic commands ###
