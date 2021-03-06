"""Add ssn fein max attempts

Revision ID: 3fbc57dc3880
Revises: e294fb147db0
Create Date: 2022-04-05 14:18:10.329237

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3fbc57dc3880"
down_revision = "e294fb147db0"
branch_labels = None
depends_on = None


def upgrade():
    # Manually added server_default="0"
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "application", sa.Column("nbr_of_retries", sa.Integer(), nullable=False, server_default="0")
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("application", "nbr_of_retries")
    # ### end Alembic commands ###
