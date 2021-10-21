"""nullable_content_type_table

Revision ID: a560e0d2e432
Revises: 175e38fc50d0
Create Date: 2021-10-21 16:14:32.119306

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a560e0d2e432"
down_revision = "175e38fc50d0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("document", "document_type_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column(
        "dua_employee_demographics",
        "fineos_customer_number",
        existing_type=sa.TEXT(),
        nullable=True,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "dua_employee_demographics",
        "fineos_customer_number",
        existing_type=sa.TEXT(),
        nullable=False,
    )
    # this is not revertable since there is no default value for the column
    # ### end Alembic commands ###
