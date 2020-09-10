"""application user_id required

Revision ID: 438401d159b6
Revises: b1b0ff11c961
Create Date: 2020-09-03 17:01:12.636684

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "438401d159b6"
down_revision = "b1b0ff11c961"
branch_labels = None
depends_on = None


def upgrade():
    # Remove any applications from earlier testing that were not associated with a user_id.
    op.execute("DELETE FROM application WHERE user_id IS NULL")
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("application", "user_id", existing_type=postgresql.UUID(), nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("application", "user_id", existing_type=postgresql.UUID(), nullable=True)
    # ### end Alembic commands ###
