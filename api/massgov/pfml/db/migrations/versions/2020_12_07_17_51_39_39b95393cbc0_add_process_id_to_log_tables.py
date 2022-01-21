"""Add process id to log tables

Revision ID: 39b95393cbc0
Revises: e69963f23515
Create Date: 2020-12-07 17:51:39.698266

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "39b95393cbc0"
down_revision = "e69963f23515"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("employee_log", sa.Column("process_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_employee_log_process_id"), "employee_log", ["process_id"], unique=False
    )
    op.add_column("employer_log", sa.Column("process_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_employer_log_process_id"), "employer_log", ["process_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_employer_log_process_id"), table_name="employer_log")
    op.drop_column("employer_log", "process_id")
    op.drop_index(op.f("ix_employee_log_process_id"), table_name="employee_log")
    op.drop_column("employee_log", "process_id")
    # ### end Alembic commands ###