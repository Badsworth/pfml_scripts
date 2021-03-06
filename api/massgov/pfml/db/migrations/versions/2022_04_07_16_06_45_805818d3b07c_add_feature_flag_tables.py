"""Add feature flag tables

Revision ID: 805818d3b07c
Revises: 3fbc57dc3880
Create Date: 2022-04-07 16:06:45.068482

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "805818d3b07c"
down_revision = "3fbc57dc3880"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_feature_flag",
        sa.Column("feature_flag_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("default_enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("feature_flag_id"),
    )
    op.create_table(
        "feature_flag_value",
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
        sa.Column("email_address", sa.Text(), nullable=False),
        sa.Column("sub_id", sa.Text(), nullable=False),
        sa.Column("family_name", sa.Text(), nullable=False),
        sa.Column("given_name", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("feature_flag_value_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feature_flag_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["feature_flag_id"],
            ["lk_feature_flag.feature_flag_id"],
        ),
        sa.PrimaryKeyConstraint("feature_flag_value_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("feature_flag_value")
    op.drop_table("lk_feature_flag")
    # ### end Alembic commands ###
