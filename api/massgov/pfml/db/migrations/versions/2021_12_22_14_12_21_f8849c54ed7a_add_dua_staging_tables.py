"""Add DUA staging tables

Revision ID: f8849c54ed7a
Revises: 1caaec619dd3
Create Date: 2021-12-22 14:12:21.369063

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f8849c54ed7a"
down_revision = "1caaec619dd3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "dua_employer_data",
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
        sa.Column("dua_employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fineos_employer_id", sa.Text(), nullable=False),
        sa.Column("dba", sa.Text(), nullable=True),
        sa.Column("attention", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column("address_line_1", sa.Text(), nullable=True),
        sa.Column("address_line_2", sa.Text(), nullable=True),
        sa.Column("address_city", sa.Text(), nullable=True),
        sa.Column("address_zip_code", sa.Text(), nullable=True),
        sa.Column("address_state", sa.Text(), nullable=True),
        sa.Column("naics_code", sa.Text(), nullable=True),
        sa.Column("naics_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("dua_employer_id"),
        sa.UniqueConstraint(
            "fineos_employer_id",
            "dba",
            "attention",
            "email",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "address_city",
            "address_zip_code",
            "address_state",
            "naics_code",
            "naics_description",
            name="uix_dua_employer",
        ),
    )
    op.create_table(
        "dua_reporting_unit_data",
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
        sa.Column("dua_reporting_unit_data_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fineos_employer_id", sa.Text(), nullable=False),
        sa.Column("dua_id", sa.Text(), nullable=True),
        sa.Column("dba", sa.Text(), nullable=True),
        sa.Column("attention", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column("address_line_1", sa.Text(), nullable=True),
        sa.Column("address_line_2", sa.Text(), nullable=True),
        sa.Column("address_city", sa.Text(), nullable=True),
        sa.Column("address_zip_code", sa.Text(), nullable=True),
        sa.Column("address_state", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("dua_reporting_unit_data_id"),
        sa.UniqueConstraint(
            "fineos_employer_id",
            "dua_id",
            "dba",
            "attention",
            "email",
            "phone_number",
            "address_line_1",
            "address_line_2",
            "address_city",
            "address_zip_code",
            "address_state",
            name="uix_dua_reporting_unit_data",
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("dua_reporting_unit_data")
    op.drop_table("dua_employer_data")
    # ### end Alembic commands ###
