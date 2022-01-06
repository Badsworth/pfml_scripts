"""add non null fields to employees

Revision ID: 240cc1d6ea5e
Revises: 918ba8aceb3b
Create Date: 2020-05-26 18:03:27.900372

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "240cc1d6ea5e"
down_revision = "59747572c72c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("employee", "first_name", existing_type=sa.TEXT(), nullable=False)
    op.alter_column("employee", "last_name", existing_type=sa.TEXT(), nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("employee", "last_name", existing_type=sa.TEXT(), nullable=True)
    op.alter_column("employee", "first_name", existing_type=sa.TEXT(), nullable=True)
    # ### end Alembic commands ###