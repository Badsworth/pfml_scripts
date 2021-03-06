"""Add application gender and fineos gender description

Revision ID: 8e477b802405
Revises: ec33b25714f2
Create Date: 2021-05-12 13:06:25.989335

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8e477b802405"
down_revision = "4180916e9815"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("application", sa.Column("gender_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "application_gender_id_fkey", "application", "lk_gender", ["gender_id"], ["gender_id"]
    )
    op.add_column("lk_gender", sa.Column("fineos_gender_description", sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("lk_gender", "fineos_gender_description")
    op.drop_constraint("application_gender_id_fkey", "application", type_="foreignkey")
    op.drop_column("application", "gender_id")
    # ### end Alembic commands ###
