"""Add mfa_delivery_preference_updated_by to User model

Revision ID: 3561b8166511
Revises: e7c39d5b58be
Create Date: 2021-12-14 23:56:59.199653

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3561b8166511"
down_revision = "e7c39d5b58be"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lk_mfa_delivery_preference_updated_by",
        sa.Column(
            "mfa_delivery_preference_updated_by_id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("mfa_delivery_preference_updated_by_description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("mfa_delivery_preference_updated_by_id"),
    )
    op.add_column(
        "user", sa.Column("mfa_delivery_preference_updated_by_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "user_mfa_delivery_preference_updated_by_id_fkey",
        "user",
        "lk_mfa_delivery_preference_updated_by",
        ["mfa_delivery_preference_updated_by_id"],
        ["mfa_delivery_preference_updated_by_id"],
    )


def downgrade():
    op.drop_constraint(
        "user_mfa_delivery_preference_updated_by_id_fkey", "user", type_="foreignkey"
    )
    op.drop_column("user", "mfa_delivery_preference_updated_by_id")
    op.drop_table("lk_mfa_delivery_preference_updated_by")
