"""PUB-71: Add payment transaction type

Revision ID: 69d14fefa414
Revises: b6f8c3f3b282
Create Date: 2021-03-11 18:13:17.391907

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "69d14fefa414"
down_revision = "b6f8c3f3b282"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_payment_transaction_type",
        sa.Column("payment_transaction_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payment_transaction_type_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("payment_transaction_type_id"),
    )
    op.add_column("payment", sa.Column("payment_transaction_type_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "payment_payment_transaction_type_fkey",
        "payment",
        "lk_payment_transaction_type",
        ["payment_transaction_type_id"],
        ["payment_transaction_type_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("payment_payment_transaction_type_fkey", "payment", type_="foreignkey")
    op.drop_column("payment", "payment_transaction_type_id")
    op.drop_table("lk_payment_transaction_type")
    # ### end Alembic commands ###
