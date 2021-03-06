"""add relationship between applications that were split

Revision ID: 028f08735753
Revises: bb297dde715e
Create Date: 2022-03-03 16:29:43.516695

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "028f08735753"
down_revision = "bb297dde715e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "application",
        sa.Column("split_from_application_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_application_split_from_application_id"),
        "application",
        ["split_from_application_id"],
        unique=False,
    )
    op.create_foreign_key(
        "split_from_application_id_fkey",
        "application",
        "application",
        ["split_from_application_id"],
        ["application_id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("split_from_application_id_fkey", "application", type_="foreignkey")
    op.drop_index(op.f("ix_application_split_from_application_id"), table_name="application")
    op.drop_column("application", "split_from_application_id")
    # ### end Alembic commands ###
