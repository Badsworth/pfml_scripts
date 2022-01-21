"""Repurposing the verifications table

Revision ID: 666884c2433c
Revises: fd7cd789a4a1
Create Date: 2021-01-14 21:12:35.950401

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "666884c2433c"
down_revision = "fd7cd789a4a1"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "verification", sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False)
    )
    op.add_column(
        "verification", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False)
    )
    op.add_column(
        "verification",
        sa.Column("verification_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # type: ignore
    )
    op.drop_column("verification", "email_address")
    op.drop_column("verification", "verified_at")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "verification",
        sa.Column(
            "verified_at", postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "verification", sa.Column("email_address", sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.drop_column("verification", "verification_metadata")
    op.drop_column("verification", "updated_at")
    op.drop_column("verification", "created_at")
    # ### end Alembic commands ###