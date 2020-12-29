"""Make latest_state_log.state_log_id non-nullable

Revision ID: 3a27e33dfbda
Revises: bde264ac357c
Create Date: 2020-12-28 17:18:59.662955

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3a27e33dfbda"
down_revision = "bde264ac357c"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "latest_state_log", "state_log_id", existing_type=postgresql.UUID(), nullable=False
    )


def downgrade():
    op.alter_column(
        "latest_state_log", "state_log_id", existing_type=postgresql.UUID(), nullable=True
    )
