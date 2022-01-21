"""Migrate employee and employer log to new tables

Revision ID: 6e9178463c6d
Revises: fa3b00015aba
Create Date: 2021-09-22 14:41:19.056562

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6e9178463c6d"
down_revision = "fa3b00015aba"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "employee_push_to_fineos_queue",
        sa.Column(
            "employee_push_to_fineos_queue_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("employee_id", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.Column("action", sa.Text(), nullable=True),
        sa.Column("modified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("process_id", sa.Integer(), nullable=True),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("employee_push_to_fineos_queue_id"),
    )
    op.create_index(
        op.f("ix_employee_push_to_fineos_queue_action"),
        "employee_push_to_fineos_queue",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_push_to_fineos_queue_employer_id"),
        "employee_push_to_fineos_queue",
        ["employer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employee_push_to_fineos_queue_process_id"),
        "employee_push_to_fineos_queue",
        ["process_id"],
        unique=False,
    )
    op.create_table(
        "employer_push_to_fineos_queue",
        sa.Column(
            "employer_push_to_fineos_queue_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=True),
        sa.Column("modified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("process_id", sa.Integer(), nullable=True),
        sa.Column("family_exemption", sa.Boolean(), nullable=True),
        sa.Column("medical_exemption", sa.Boolean(), nullable=True),
        sa.Column("exemption_commence_date", sa.Date(), nullable=True),
        sa.Column("exemption_cease_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("employer_push_to_fineos_queue_id"),
    )
    op.create_index(
        op.f("ix_employer_push_to_fineos_queue_action"),
        "employer_push_to_fineos_queue",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employer_push_to_fineos_queue_employer_id"),
        "employer_push_to_fineos_queue",
        ["employer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employer_push_to_fineos_queue_process_id"),
        "employer_push_to_fineos_queue",
        ["process_id"],
        unique=False,
    )

    op.execute(
        "INSERT INTO employee_push_to_fineos_queue (employee_push_to_fineos_queue_id, employee_id, action, modified_at, process_id, employer_id) SELECT employee_log_id, employee_id, action, modified_at, process_id, employer_id FROM employee_log;"
    )
    op.execute(
        "INSERT INTO employer_push_to_fineos_queue (employer_push_to_fineos_queue_id, employer_id, action, modified_at, process_id, family_exemption, medical_exemption, exemption_commence_date, exemption_cease_date) SELECT employer_log_id, employer_id, action, modified_at, process_id, family_exemption, medical_exemption, exemption_commence_date, exemption_cease_date FROM employer_log;"
    )

    op.drop_index("ix_employee_log_action", table_name="employee_log")
    op.drop_index("ix_employee_log_employee_id", table_name="employee_log")
    op.drop_index("ix_employee_log_employer_id", table_name="employee_log")
    op.drop_index("ix_employee_log_process_id", table_name="employee_log")
    op.drop_table("employee_log")
    op.drop_index("ix_employer_log_action", table_name="employer_log")
    op.drop_index("ix_employer_log_employer_id", table_name="employer_log")
    op.drop_index("ix_employer_log_process_id", table_name="employer_log")
    op.drop_table("employer_log")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "employer_log",
        sa.Column("employer_log_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("employer_id", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.Column("action", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "modified_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True
        ),
        sa.Column("process_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("family_exemption", sa.Boolean(), nullable=True),
        sa.Column("medical_exemption", sa.Boolean(), nullable=True),
        sa.Column("exemption_commence_date", sa.Date(), nullable=True),
        sa.Column("exemption_cease_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("employer_log_id", name="employer_log_pkey"),
    )
    op.create_index("ix_employer_log_process_id", "employer_log", ["process_id"], unique=False)
    op.create_index("ix_employer_log_employer_id", "employer_log", ["employer_id"], unique=False)
    op.create_index("ix_employer_log_action", "employer_log", ["action"], unique=False)
    op.create_table(
        "employee_log",
        sa.Column("employee_log_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("employee_id", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.Column("action", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "modified_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True
        ),
        sa.Column("process_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("employer_id", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("employee_log_id", name="employee_log_pkey"),
    )
    op.create_index("ix_employee_log_process_id", "employee_log", ["process_id"], unique=False)
    op.create_index("ix_employee_log_employer_id", "employee_log", ["employer_id"], unique=False)
    op.create_index("ix_employee_log_employee_id", "employee_log", ["employee_id"], unique=False)
    op.create_index("ix_employee_log_action", "employee_log", ["action"], unique=False)

    op.execute(
        "INSERT INTO employee_log (employee_log_id, employee_id, action, modified_at, process_id, employer_id) SELECT employee_push_to_fineos_queue_id, employee_id, action, modified_at, process_id, employer_id FROM employee_push_to_fineos_queue;"
    )
    op.execute(
        "INSERT INTO employer_log (employer_log_id, employer_id, action, modified_at, process_id, family_exemption, medical_exemption, exemption_commence_date, exemption_cease_date) SELECT employer_push_to_fineos_queue_id, employer_id, action, modified_at, process_id, family_exemption, medical_exemption, exemption_commence_date, exemption_cease_date FROM employer_push_to_fineos_queue;"
    )

    op.drop_index(
        op.f("ix_employer_push_to_fineos_queue_process_id"),
        table_name="employer_push_to_fineos_queue",
    )
    op.drop_index(
        op.f("ix_employer_push_to_fineos_queue_employer_id"),
        table_name="employer_push_to_fineos_queue",
    )
    op.drop_index(
        op.f("ix_employer_push_to_fineos_queue_action"), table_name="employer_push_to_fineos_queue"
    )
    op.drop_table("employer_push_to_fineos_queue")
    op.drop_index(
        op.f("ix_employee_push_to_fineos_queue_process_id"),
        table_name="employee_push_to_fineos_queue",
    )
    op.drop_index(
        op.f("ix_employee_push_to_fineos_queue_employer_id"),
        table_name="employee_push_to_fineos_queue",
    )
    op.drop_index(
        op.f("ix_employee_push_to_fineos_queue_action"), table_name="employee_push_to_fineos_queue"
    )
    op.drop_table("employee_push_to_fineos_queue")
    # ### end Alembic commands ###