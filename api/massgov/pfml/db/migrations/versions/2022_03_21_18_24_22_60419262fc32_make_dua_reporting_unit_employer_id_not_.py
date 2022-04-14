"""Make dua_reporting_unit employer_id not nullable

Revision ID: 60419262fc32
Revises: 4bd14f975de1
Create Date: 2022-03-21 18:24:22.660121

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "60419262fc32"
down_revision = "4bd14f975de1"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "dua_reporting_unit", "employer_id", existing_type=postgresql.UUID(), nullable=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "dua_reporting_unit", "employer_id", existing_type=postgresql.UUID(), nullable=True
    )
    # ### end Alembic commands ###
