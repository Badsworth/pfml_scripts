"""remove leave_type_id column and table

Revision ID: 3df6e9ccf48f
Revises: c911058236e6
Create Date: 2021-05-17 19:46:20.302757

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3df6e9ccf48f"
down_revision = "4180916e9815"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("application_leave_type_fkey", "application", type_="foreignkey")
    op.drop_column("application", "leave_type_id")
    op.drop_table("lk_leave_type")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_leave_type",
        sa.Column("leave_type_id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("leave_type_description", sa.TEXT(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("leave_type_id", name="lk_leave_type_pkey"),
    )
    op.add_column(
        "application", sa.Column("leave_type_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_foreign_key(
        "application_leave_type_fkey",
        "application",
        "lk_leave_type",
        ["leave_type_id"],
        ["leave_type_id"],
    )
    # ### end Alembic commands ###
