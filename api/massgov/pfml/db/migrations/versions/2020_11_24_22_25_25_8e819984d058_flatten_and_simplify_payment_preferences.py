"""Flatten and simplify payment preferences

Revision ID: 8e819984d058
Revises: 4a77e100b58c
Create Date: 2020-11-24 22:25:33.914686

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8e819984d058"
down_revision = "a33179b41e77"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_bank_account_type",
        sa.Column("bank_account_type_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bank_account_type_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("bank_account_type_id"),
    )
    op.create_table(
        "lk_payment_method",
        sa.Column("payment_method_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("payment_method_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("payment_method_id"),
    )
    op.add_column(
        "application",
        sa.Column("payment_preference_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("bank_account_type_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("payment_method_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "payment_information", sa.Column("payment_method_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "application_payment_preference_payment_id_fkey",
        "application",
        "application_payment_preference",
        ["payment_preference_id"],
        ["payment_pref_id"],
    )
    op.create_foreign_key(
        "application_payment_preference_payment_method_id_fkey",
        "application_payment_preference",
        "lk_payment_method",
        ["payment_method_id"],
        ["payment_method_id"],
    )
    op.create_foreign_key(
        "application_payment_preference_bank_account_type_id_fkey",
        "application_payment_preference",
        "lk_bank_account_type",
        ["bank_account_type_id"],
        ["bank_account_type_id"],
    )
    op.create_foreign_key(
        "payment_information_payment_method_id_fkey",
        "payment_information",
        "lk_payment_method",
        ["payment_method_id"],
        ["payment_method_id"],
    )
    op.drop_index(
        "ix_application_payment_preference_application_id",
        table_name="application_payment_preference",
    )
    op.drop_constraint(
        "payment_information_payment_type_fkey", "payment_information", type_="foreignkey"
    )
    op.drop_constraint(
        "application_payment_preference_payment_type_fkey",
        "application_payment_preference",
        type_="foreignkey",
    )
    op.drop_constraint(
        "application_payment_preference_application_id_fkey",
        "application_payment_preference",
        type_="foreignkey",
    )
    op.drop_column("application_payment_preference", "is_default")
    op.drop_column("application_payment_preference", "application_id")
    op.drop_column("application_payment_preference", "type_of_account")
    op.drop_column("application_payment_preference", "name_in_check")
    op.drop_column("application_payment_preference", "payment_type_id")
    op.drop_column("application_payment_preference", "description")
    op.drop_column("application_payment_preference", "account_name")
    op.drop_column("payment_information", "payment_type_id")
    op.drop_table("lk_payment_type")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "lk_payment_type",
        sa.Column("payment_type_id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("payment_type_description", sa.TEXT(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("payment_type_id", name="lk_payment_type_pkey"),
    )
    op.add_column(
        "payment_information",
        sa.Column("payment_type_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("account_name", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("description", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("payment_type_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("name_in_check", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("type_of_account", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("application_id", postgresql.UUID(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "application_payment_preference",
        sa.Column("is_default", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "payment_information_payment_type_fkey",
        "payment_information",
        "lk_payment_type",
        ["payment_type_id"],
        ["payment_type_id"],
    )
    op.create_foreign_key(
        "application_payment_preference_payment_type_fkey",
        "application_payment_preference",
        "lk_payment_type",
        ["payment_type_id"],
        ["payment_type_id"],
    )
    op.create_foreign_key(
        "application_payment_preference_application_id_fkey",
        "application_payment_preference",
        "application",
        ["application_id"],
        ["application_id"],
    )
    op.create_index(
        "ix_application_payment_preference_application_id",
        "application_payment_preference",
        ["application_id"],
        unique=False,
    )
    op.drop_constraint(
        "payment_information_payment_method_id_fkey", "payment_information", type_="foreignkey"
    )
    op.drop_constraint(
        "application_payment_preference_payment_method_id_fkey",
        "application_payment_preference",
        type_="foreignkey",
    )
    op.drop_constraint(
        "application_payment_preference_bank_account_type_id_fkey",
        "application_payment_preference",
        type_="foreignkey",
    )
    op.drop_constraint(
        "application_payment_preference_payment_id_fkey", "application", type_="foreignkey"
    )
    op.drop_column("payment_information", "payment_method_id")
    op.drop_column("application_payment_preference", "payment_method_id")
    op.drop_column("application_payment_preference", "bank_account_type_id")
    op.drop_column("application", "payment_preference_id")
    op.drop_table("lk_payment_method")
    op.drop_table("lk_bank_account_type")
    # ### end Alembic commands ###
