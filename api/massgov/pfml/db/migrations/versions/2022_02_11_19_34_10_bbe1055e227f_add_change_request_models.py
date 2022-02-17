"""add change request models

Revision ID: bbe1055e227f
Revises: fc466567a4db
Create Date: 2022-02-11 19:34:10.959194

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "bbe1055e227f"
down_revision = "fc466567a4db"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_change_request_type",
        sa.Column("change_request_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("change_request_type_description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("change_request_type_id"),
    )
    op.create_table(
        "change_request",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("change_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("change_request_type_id", sa.Integer(), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("submitted_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["change_request_type_id"], ["lk_change_request_type.change_request_type_id"],
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claim.claim_id"],),
        sa.PrimaryKeyConstraint("change_request_id"),
    )
    op.create_index(
        op.f("ix_change_request_claim_id"), "change_request", ["claim_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_change_request_claim_id"), table_name="change_request")
    op.drop_table("change_request")
    op.drop_table("lk_change_request_type")
    # ### end Alembic commands ###