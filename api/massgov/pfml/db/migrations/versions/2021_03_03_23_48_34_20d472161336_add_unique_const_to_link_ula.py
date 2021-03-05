"""Add unique const to link_ula

Revision ID: 20d472161336
Revises: 850ae5efc4ee
Create Date: 2021-03-03 23:48:34.411598

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20d472161336"
down_revision = "850ae5efc4ee"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "link_user_leave_administrator", ["user_id", "employer_id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "link_user_leave_administrator", type_="unique")
    # ### end Alembic commands ###
