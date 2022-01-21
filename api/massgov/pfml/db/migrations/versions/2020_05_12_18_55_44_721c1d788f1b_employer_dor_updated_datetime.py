"""employer dor updated datetime

Revision ID: 721c1d788f1b
Revises: 066044391b6f
Create Date: 2020-05-12 18:55:44.383523

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "721c1d788f1b"
down_revision = "79e1405a1b3e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "employer",
        "dor_updated_date",
        existing_type=sa.DATE(),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "employer",
        "dor_updated_date",
        existing_type=sa.DateTime(),
        type_=sa.DATE(),
        existing_nullable=True,
    )
    # ### end Alembic commands ###