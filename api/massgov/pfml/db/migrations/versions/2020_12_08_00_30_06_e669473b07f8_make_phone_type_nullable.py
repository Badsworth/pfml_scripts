"""make phone_type nullable

Revision ID: e669473b07f8
Revises: 39b95393cbc0
Create Date: 2020-12-08 00:30:06.209738

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e669473b07f8"
down_revision = "39b95393cbc0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("phone", "phone_type_id", existing_type=sa.INTEGER(), nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("phone", "phone_type_id", existing_type=sa.INTEGER(), nullable=False)
    # ### end Alembic commands ###
