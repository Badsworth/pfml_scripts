"""Add foreign key from claim table to employer table

Revision ID: cd94e1c1a5f8
Revises: 0b0d119901b6
Create Date: 2021-02-04 21:14:04.331728

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "cd94e1c1a5f8"
down_revision = "0b0d119901b6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, "claim", "employer", ["employer_id"], ["employer_id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "claim", type_="foreignkey")  # type: ignore
    # ### end Alembic commands ###
