"""Remove experian_address_pair_id

Revision ID: 2341094462d0
Revises: 973ae2445d15
Create Date: 2021-09-28 17:07:30.453563

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2341094462d0"
down_revision = "973ae2445d15"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_employee_experian_address_pair_id", table_name="employee")
    op.drop_constraint("fk_employee_link_experian_address_pair", "employee", type_="foreignkey")
    op.drop_column("employee", "experian_address_pair_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "employee",
        sa.Column(
            "experian_address_pair_id", postgresql.UUID(), autoincrement=False, nullable=True
        ),
    )
    op.create_foreign_key(
        "fk_employee_link_experian_address_pair",
        "employee",
        "link_experian_address_pair",
        ["experian_address_pair_id"],
        ["fineos_address_id"],
    )
    op.create_index(
        "ix_employee_experian_address_pair_id",
        "employee",
        ["experian_address_pair_id"],
        unique=False,
    )
    # ### end Alembic commands ###
