"""Add index on employee.fineos_customer_number

Revision ID: 2ef7a3835814
Revises: 85e5ba36efd7
Create Date: 2021-11-19 16:47:17.461035

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2ef7a3835814"
down_revision = "85e5ba36efd7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_employee_fineos_customer_number"),
        "employee",
        ["fineos_customer_number"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_employee_fineos_customer_number"), table_name="employee")
    # ### end Alembic commands ###
