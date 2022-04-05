"""update employee table

Revision ID: e294fb147db0
Revises: b9e3f491eba2
Create Date: 2022-03-17 15:42:06.448985

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e294fb147db0"
down_revision = "60419262fc32"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("employee", sa.Column("mass_id_number", sa.Text(), nullable=True))
    op.add_column("employee", sa.Column("out_of_state_id_number", sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("employee", "out_of_state_id_number")
    op.drop_column("employee", "mass_id_number")
    # ### end Alembic commands ###
