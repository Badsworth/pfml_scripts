"""Add MFA delivery preference to User

Revision ID: 84a75d6c3739
Revises: a8f826a20319
Create Date: 2021-11-03 23:38:16.757925

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "84a75d6c3739"
down_revision = "a8f826a20319"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lk_mfa_delivery_preference",
        sa.Column("mfa_delivery_preference_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mfa_delivery_preference_description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("mfa_delivery_preference_id"),
    )
    op.add_column("user", sa.Column("mfa_delivery_preference_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "user_mfa_delivery_preference_id_fkey",
        "user",
        "lk_mfa_delivery_preference",
        ["mfa_delivery_preference_id"],
        ["mfa_delivery_preference_id"],
    )


def downgrade():
    op.drop_constraint("user_mfa_delivery_preference_id_fkey", "user", type_="foreignkey")
    op.drop_column("user", "mfa_delivery_preference_id")
    op.drop_table("lk_mfa_delivery_preference")
