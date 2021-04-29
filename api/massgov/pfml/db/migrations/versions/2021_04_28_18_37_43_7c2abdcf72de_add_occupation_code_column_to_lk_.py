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
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("lk_occupation", sa.Column("occupation_code", sa.Integer(), nullable=True))

    op.create_unique_constraint(
        "lk_occupation_code_key", "lk_occupation", ["occupation_code"]
    )
    op.create_table(
        "lk_occupation_title",
        sa.Column("occupation_title_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("occupation_id", sa.Integer(), nullable=True),
        sa.Column("occupation_title_code", sa.Integer(), nullable=True),
        sa.Column("occupation_title_description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["occupation_id"], ["lk_occupation.occupation_id"],),
        sa.PrimaryKeyConstraint("occupation_title_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("lk_occupation_title")
    op.drop_column("lk_occupation", "occupation_code")
    # ### end Alembic commands ###
