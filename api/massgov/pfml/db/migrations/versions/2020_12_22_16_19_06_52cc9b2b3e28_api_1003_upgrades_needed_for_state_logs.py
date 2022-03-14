"""API-1003: Upgrades needed for state logs

Revision ID: 52cc9b2b3e28
Revises: 85871b949dbd
Create Date: 2020-12-22 16:19:06.868581

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "52cc9b2b3e28"
down_revision = "85871b949dbd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "latest_state_log",
        sa.Column("latest_state_log_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state_log_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("flow_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employee.employee_id"]),
        sa.ForeignKeyConstraint(["flow_id"], ["lk_flow.flow_id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.payment_id"]),
        sa.ForeignKeyConstraint(["reference_file_id"], ["reference_file.reference_file_id"]),
        sa.ForeignKeyConstraint(["state_log_id"], ["state_log.state_log_id"]),
        sa.PrimaryKeyConstraint("latest_state_log_id"),
    )
    op.create_index(
        op.f("ix_latest_state_log_employee_id"), "latest_state_log", ["employee_id"], unique=False
    )
    op.create_index(
        op.f("ix_latest_state_log_payment_id"), "latest_state_log", ["payment_id"], unique=False
    )
    op.create_index(
        op.f("ix_latest_state_log_reference_file_id"),
        "latest_state_log",
        ["reference_file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_latest_state_log_state_log_id"), "latest_state_log", ["state_log_id"], unique=False
    )
    op.add_column("state_log", sa.Column("end_state_id", sa.Integer(), nullable=True))
    op.add_column(
        "state_log", sa.Column("prev_state_log_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column("state_log", sa.Column("start_state_id", sa.Integer(), nullable=False))
    op.execute("ALTER TABLE state_log ALTER COLUMN outcome TYPE json USING (outcome::json)")
    op.alter_column(
        "state_log", "outcome", existing_type=sa.TEXT(), type_=sa.JSON(), existing_nullable=True
    )
    op.drop_index("ix_state_log_success", table_name="state_log")
    op.drop_constraint("state_log_state_id_fkey", "state_log", type_="foreignkey")
    op.create_foreign_key(
        "state_log_end_state_id_fkey", "state_log", "lk_state", ["end_state_id"], ["state_id"]
    )
    op.create_foreign_key(
        "state_log_start_state_id_fkey", "state_log", "lk_state", ["start_state_id"], ["state_id"]
    )
    op.create_foreign_key(
        "state_log_prev_state_log_id_fkey",
        "state_log",
        "state_log",
        ["prev_state_log_id"],
        ["state_log_id"],
    )
    op.drop_column("state_log", "success")
    op.drop_column("state_log", "state_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "state_log", sa.Column("state_id", sa.INTEGER(), autoincrement=False, nullable=False)
    )
    op.add_column(
        "state_log", sa.Column("success", sa.BOOLEAN(), autoincrement=False, nullable=True)
    )
    op.drop_constraint("state_log_end_state_id_fkey", "state_log", type_="foreignkey")
    op.drop_constraint("state_log_start_state_id_fkey", "state_log", type_="foreignkey")
    op.drop_constraint("state_log_prev_state_log_id_fkey", "state_log", type_="foreignkey")
    op.create_foreign_key(
        "state_log_state_id_fkey", "state_log", "lk_state", ["state_id"], ["state_id"]
    )
    op.create_index("ix_state_log_success", "state_log", ["success"], unique=False)
    op.alter_column(
        "state_log", "outcome", existing_type=sa.JSON(), type_=sa.TEXT(), existing_nullable=True
    )
    op.drop_column("state_log", "start_state_id")
    op.drop_column("state_log", "prev_state_log_id")
    op.drop_column("state_log", "end_state_id")
    op.drop_index(op.f("ix_latest_state_log_state_log_id"), table_name="latest_state_log")
    op.drop_index(op.f("ix_latest_state_log_reference_file_id"), table_name="latest_state_log")
    op.drop_index(op.f("ix_latest_state_log_payment_id"), table_name="latest_state_log")
    op.drop_index(op.f("ix_latest_state_log_employee_id"), table_name="latest_state_log")
    op.drop_table("latest_state_log")
    # ### end Alembic commands ###
