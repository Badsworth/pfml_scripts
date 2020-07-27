"""Add column application.employer_fein

Revision ID: 89e55ef4d333
Revises: b695fa114a27
Create Date: 2020-07-24 12:19:13.711324

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "89e55ef4d333"
down_revision = "b695fa114a27"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("application", sa.Column("employer_fein", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("application", "employer_fein")
