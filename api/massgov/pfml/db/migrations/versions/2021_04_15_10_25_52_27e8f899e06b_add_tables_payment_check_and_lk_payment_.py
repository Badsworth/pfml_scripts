"""Add tables payment_check and lk_payment_check_status

Revision ID: 27e8f899e06b
Revises: 41cf51d164b7
Create Date: 2021-04-15 10:25:52.573121

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "27e8f899e06b"
down_revision = "41cf51d164b7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_payment_check_status",
        sa.Column("payment_check_status_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payment_check_status_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("payment_check_status_id"),
    )
    op.create_table(
        "payment_check",
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("check_number", sa.Integer(), nullable=False),
        sa.Column("check_posted_date", sa.Date(), nullable=True),
        sa.Column("payment_check_status_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["payment_check_status_id"], ["lk_payment_check_status.payment_check_status_id"]
        ),
        sa.ForeignKeyConstraint(["payment_id"], ["payment.payment_id"]),
        sa.PrimaryKeyConstraint("payment_id"),
    )
    op.create_index(
        op.f("ix_payment_check_check_number"), "payment_check", ["check_number"], unique=True
    )
    op.drop_index("ix_payment_check_number", table_name="payment")
    op.drop_column("payment", "check_number")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "payment", sa.Column("check_number", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_index("ix_payment_check_number", "payment", ["check_number"], unique=True)
    op.drop_index(op.f("ix_payment_check_check_number"), table_name="payment_check")
    op.drop_table("payment_check")
    op.drop_table("lk_payment_check_status")
    # ### end Alembic commands ###
