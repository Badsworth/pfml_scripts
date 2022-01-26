"""API-2323: Add indexes for slowest queries

Revision ID: 5eed6252f2a3
Revises: 4f94ce2880fd
Create Date: 2022-01-19 17:05:54.426580

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5eed6252f2a3"
down_revision = "4f94ce2880fd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_absence_period_fineos_leave_request_id"),
        "absence_period",
        ["fineos_leave_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_details_payment_id"), "payment_details", ["payment_id"], unique=False
    )
    op.create_index(op.f("ix_state_log_end_state_id"), "state_log", ["end_state_id"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_state_log_end_state_id"), table_name="state_log")
    op.drop_index(op.f("ix_payment_details_payment_id"), table_name="payment_details")
    op.drop_index(op.f("ix_absence_period_fineos_leave_request_id"), table_name="absence_period")
    # ### end Alembic commands ###