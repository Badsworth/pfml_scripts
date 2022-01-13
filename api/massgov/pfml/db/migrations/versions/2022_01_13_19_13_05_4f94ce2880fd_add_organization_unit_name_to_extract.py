"""Add organization unit name to extract

Revision ID: 4f94ce2880fd
Revises: cc08f804cd01
Create Date: 2021-11-23 19:13:05.567899

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4f94ce2880fd"
down_revision = "7d30434c59db"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "fineos_extract_vbi_requested_absence_som",
        sa.Column("orgunit_name", sa.Text(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("fineos_extract_vbi_requested_absence_som", "orgunit_name")
    # ### end Alembic commands ###