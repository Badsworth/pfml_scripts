"""API-659: Index C and I values in payments

Revision ID: 521da22e3f61
Revises: f1d2e7bf289b
Create Date: 2020-12-15 16:38:54.928292

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "521da22e3f61"
down_revision = "f1d2e7bf289b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_payment_fineos_pei_c_value"), "payment", ["fineos_pei_c_value"], unique=False
    )
    op.create_index(
        op.f("ix_payment_fineos_pei_i_value"), "payment", ["fineos_pei_i_value"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_payment_fineos_pei_i_value"), table_name="payment")
    op.drop_index(op.f("ix_payment_fineos_pei_c_value"), table_name="payment")
    # ### end Alembic commands ###
