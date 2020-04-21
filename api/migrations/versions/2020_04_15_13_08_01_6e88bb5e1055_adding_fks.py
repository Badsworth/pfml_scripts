"""adding fks

Revision ID: 6e88bb5e1055
Revises: 2183ff9d3cd7
Create Date: 2020-04-15 13:08:01.461851

"""
import sqlalchemy as sa  # noqa: F401
from alembic import op

# revision identifiers, used by Alembic.
revision = "6e88bb5e1055"
down_revision = "2183ff9d3cd7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(
        None, "wage_and_contribution_id", "employee", ["employee_id"], ["employee_id"]
    )
    op.create_foreign_key(
        None, "wage_and_contribution_id", "employer", ["employer_id"], ["employer_id"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "wage_and_contribution_id", type_="foreignkey")
    op.drop_constraint(None, "wage_and_contribution_id", type_="foreignkey")
    # ### end Alembic commands ###
