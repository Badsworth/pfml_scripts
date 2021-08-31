"""create_index_dia_reduction_payment_fineos_customer_number_board_no

Revision ID: cceaf8646052
Revises: f9c23f61707e
Create Date: 2021-08-18 19:25:43.274659

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "cceaf8646052"
down_revision = "c6d26b935c2c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_dia_reduction_payment_fineos_customer_number_board_no",
        "dia_reduction_payment",
        ["fineos_customer_number", "board_no"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_dia_reduction_payment_fineos_customer_number_board_no"),
        table_name="dia_reduction_payment",
    )
