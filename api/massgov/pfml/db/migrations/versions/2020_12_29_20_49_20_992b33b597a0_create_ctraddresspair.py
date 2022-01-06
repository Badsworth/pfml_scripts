"""Create CtrAddressPair

Revision ID: 992b33b597a0
Revises: d6d53b34006c
Create Date: 2020-12-29 20:49:20.152638

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "992b33b597a0"
down_revision = "d6d53b34006c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "link_ctr_address_pair",
        sa.Column("fineos_address_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ctr_address_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["ctr_address_id"], ["address.address_id"],),
        sa.ForeignKeyConstraint(["fineos_address_id"], ["address.address_id"],),
        sa.PrimaryKeyConstraint("fineos_address_id"),
        sa.UniqueConstraint("fineos_address_id"),
    )
    op.create_index(
        op.f("ix_link_ctr_address_pair_ctr_address_id"),
        "link_ctr_address_pair",
        ["ctr_address_id"],
        unique=False,
    )
    op.add_column(
        "employee", sa.Column("ctr_address_pair_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index(
        op.f("ix_employee_ctr_address_pair_id"), "employee", ["ctr_address_pair_id"], unique=False
    )
    op.create_foreign_key(
        "employee_ctr_address_pair_id_fkey",
        "employee",
        "link_ctr_address_pair",
        ["ctr_address_pair_id"],
        ["fineos_address_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("employee_ctr_address_pair_id_fkey", "employee", type_="foreignkey")
    op.drop_index(op.f("ix_employee_ctr_address_pair_id"), table_name="employee")
    op.drop_column("employee", "ctr_address_pair_id")
    op.drop_index(
        op.f("ix_link_ctr_address_pair_ctr_address_id"), table_name="link_ctr_address_pair"
    )
    op.drop_table("link_ctr_address_pair")
    # ### end Alembic commands ###