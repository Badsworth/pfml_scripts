"""fineos writeback details primary key

Revision ID: 8d22338060aa
Revises: 7e4cd8f28ddc
Create Date: 2021-06-02 16:43:50.175900

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8d22338060aa"
down_revision = "7e4cd8f28ddc"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "fineos_writeback_details",
        sa.Column("fineos_writeback_details_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.add_column(
        "fineos_writeback_details",
        sa.Column("writeback_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.drop_constraint("fineos_writeback_details_pkey", "fineos_writeback_details", type_="primary")
    op.create_primary_key(
        "fineos_writeback_details_pkey", "fineos_writeback_details", ["fineos_writeback_details_id"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fineos_writeback_details_pkey", "fineos_writeback_details", type_="primary")
    op.drop_column("fineos_writeback_details", "writeback_sent_at")
    op.drop_column("fineos_writeback_details", "fineos_writeback_details_id")
    op.create_primary_key(
        "fineos_writeback_details_pkey", "fineos_writeback_details", ["payment_id"]
    )
    # ### end Alembic commands ###
