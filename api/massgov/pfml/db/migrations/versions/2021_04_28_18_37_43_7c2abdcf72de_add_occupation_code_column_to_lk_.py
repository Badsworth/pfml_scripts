"""add occupation_code column to lk_occupation

Revision ID: 7c2abdcf72de
Revises: f179009904e7
Create Date: 2021-04-28 18:37:43.676535

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7c2abdcf72de"
down_revision = "f179009904e7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lk_occupation", sa.Column("occupation_code", sa.Integer(), nullable=True))
    op.create_unique_constraint("lk_occupation_code_key", "lk_occupation", ["occupation_code"])
    op.add_column("application", sa.Column("job_title", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("lk_occupation", "occupation_code")
    op.drop_column("application", "job_title")
