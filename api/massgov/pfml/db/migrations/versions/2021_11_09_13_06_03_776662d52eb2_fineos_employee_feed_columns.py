"""fineos employee feed columns

Revision ID: 776662d52eb2
Revises: 952219694811
Create Date: 2021-11-09 13:06:03.866635

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "776662d52eb2"
down_revision = "952219694811"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "fineos_extract_employee_feed", sa.Column("effectivefrom", sa.Text(), nullable=True)
    )
    op.add_column(
        "fineos_extract_employee_feed", sa.Column("effectiveto", sa.Text(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("fineos_extract_employee_feed", "effectiveto")
    op.drop_column("fineos_extract_employee_feed", "effectivefrom")
    # ### end Alembic commands ###