"""nullable_content_type_table

Revision ID: 458af2d103eb
Revises: 3765c13fe7e6
Create Date: 2021-10-21 16:48:11.138836

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "458af2d103eb"
down_revision = "3765c13fe7e6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("document", "content_type_id", existing_type=sa.INTEGER(), nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # This is not reversible since there is no default value
    # ### end Alembic commands ###
