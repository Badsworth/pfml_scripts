"""Add Absence Period database tables and columns

Revision ID: 60c62cce24ea
Revises: aa54e512ffb7
Create Date: 2021-06-28 15:45:11.755512

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "60c62cce24ea"
down_revision = "aa54e512ffb7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_leave_request_decision",
        sa.Column("leave_request_decision_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("leave_request_decision_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("leave_request_decision_id"),
    )
    op.create_table(
        "absence_period",
        sa.Column("absence_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fineos_absence_period_id", sa.Integer(), nullable=False),
        sa.Column("fineos_leave_request_id", sa.Integer(), nullable=True),
        sa.Column("absence_period_start_date", sa.Date(), nullable=False),
        sa.Column("absence_period_end_date", sa.Date(), nullable=False),
        sa.Column("leave_request_decision_id", sa.Integer(), nullable=False),
        sa.Column("is_id_proofed", sa.Boolean(), nullable=True),
        sa.Column("claim_type_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claim.claim_id"],),
        sa.ForeignKeyConstraint(["claim_type_id"], ["lk_claim_type.claim_type_id"],),
        sa.ForeignKeyConstraint(
            ["leave_request_decision_id"], ["lk_leave_request_decision.leave_request_decision_id"],
        ),
        sa.PrimaryKeyConstraint("absence_period_id"),
    )
    op.create_index(
        op.f("ix_absence_period_claim_id"), "absence_period", ["claim_id"], unique=False
    )
    op.create_index(
        op.f("ix_absence_period_fineos_absence_period_id"),
        "absence_period",
        ["fineos_absence_period_id"],
        unique=True,
    )
    op.add_column(
        "payment", sa.Column("leave_request_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_payment_absence_period_leave_request_id_absence_period_id",
        "payment",
        "absence_period",
        ["leave_request_id"],
        ["absence_period_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "fk_payment_absence_period_leave_request_id_absence_period_id",
        "payment",
        type_="foreignkey",
    )
    op.drop_column("payment", "leave_request_id")
    op.drop_index(op.f("ix_absence_period_fineos_absence_period_id"), table_name="absence_period")
    op.drop_index(op.f("ix_absence_period_claim_id"), table_name="absence_period")
    op.drop_table("absence_period")
    op.drop_table("lk_leave_request_decision")
    # ### end Alembic commands ###
