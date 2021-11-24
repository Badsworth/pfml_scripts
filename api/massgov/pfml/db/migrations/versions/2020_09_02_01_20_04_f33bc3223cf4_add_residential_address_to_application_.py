"""Add residential address to application model

Revision ID: f33bc3223cf4
Revises: d7fa5074cea9
Create Date: 2020-09-02 01:20:04.752938

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f33bc3223cf4"
down_revision = "d7fa5074cea9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "application",
        sa.Column("residential_address_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        None, "application", "address", ["residential_address_id"], ["address_id"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "application", type_="foreignkey")  # type: ignore
    op.drop_column("application", "residential_address_id")
    # ### end Alembic commands ###
