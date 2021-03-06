"""Add relationship qualifier lookup and attribute

Revision ID: 045543f6292e
Revises: 918ba8aceb3b
Create Date: 2020-05-19 23:08:00.414189

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "045543f6292e"
down_revision = "918ba8aceb3b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_relationship_qualifier",
        sa.Column("relationship_qualifier", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("relationship_qualifier_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("relationship_qualifier"),
    )
    op.add_column("application", sa.Column("relationship_qualifier", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_relationship_qualifier",
        "application",
        "lk_relationship_qualifier",
        ["relationship_qualifier"],
        ["relationship_qualifier"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_relationship_qualifier", "application", type_="foreignkey")
    op.drop_column("application", "relationship_qualifier")
    op.drop_table("lk_relationship_qualifier")
    # ### end Alembic commands ###
