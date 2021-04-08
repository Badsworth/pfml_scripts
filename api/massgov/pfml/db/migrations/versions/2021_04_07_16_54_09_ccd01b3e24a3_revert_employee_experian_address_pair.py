"""revert employee experian_address_pair

Revision ID: ccd01b3e24a3
Revises: b3c55c26e2d3
Create Date: 2021-04-07 16:54:09.207432

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ccd01b3e24a3"
down_revision = "b3c55c26e2d3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "employee",
        sa.Column("experian_address_pair_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_employee_experian_address_pair_id"),
        "employee",
        ["experian_address_pair_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_employee_link_experian_address_pair",
        "employee",
        "link_experian_address_pair",
        ["experian_address_pair_id"],
        ["fineos_address_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_employee_link_experian_address_pair", "employee", type_="foreignkey")
    op.drop_index(op.f("ix_employee_experian_address_pair_id"), table_name="employee")
    op.drop_column("employee", "experian_address_pair_id")
    # ### end Alembic commands ###
