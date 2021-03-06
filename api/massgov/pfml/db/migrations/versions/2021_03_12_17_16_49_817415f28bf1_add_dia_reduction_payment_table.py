"""add dia reduction payment table

Revision ID: 817415f28bf1
Revises: 329cb33857e6
Create Date: 2021-03-12 17:16:49.354802

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "817415f28bf1"
down_revision = "329cb33857e6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "dia_reduction_payment",
        sa.Column("dia_reduction_payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("absence_case_id", sa.Text(), nullable=False),
        sa.Column("board_no", sa.Text(), nullable=True),
        sa.Column("event_id", sa.Text(), nullable=True),
        sa.Column("event_description", sa.Text(), nullable=True),
        sa.Column("eve_created_date", sa.Date(), nullable=True),
        sa.Column("event_occurrence_date", sa.Date(), nullable=True),
        sa.Column("award_id", sa.Text(), nullable=True),
        sa.Column("award_code", sa.Text(), nullable=True),
        sa.Column("award_amount", sa.Numeric(), nullable=True),
        sa.Column("award_date", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("weekly_amount", sa.Numeric(), nullable=True),
        sa.Column("award_created_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("dia_reduction_payment_id"),
    )
    op.create_table(
        "link_dia_reduction_payment_reference_file",
        sa.Column("dia_reduction_payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["dia_reduction_payment_id"], ["dia_reduction_payment.dia_reduction_payment_id"]
        ),
        sa.ForeignKeyConstraint(["reference_file_id"], ["reference_file.reference_file_id"]),
        sa.PrimaryKeyConstraint("dia_reduction_payment_id", "reference_file_id"),
    )

    # Adjust the unique index so that we coalesce all nullable fields to empty strings, 99999999
    # (for numeric), and 1788-02-06 (for dates) to ensure uniqueness across all fields.
    op.execute(
        """
        create unique index on dia_reduction_payment (
            absence_case_id,
            coalesce(board_no, ''),
            coalesce(event_id, ''),
            coalesce(event_description, ''),
            coalesce(eve_created_date, '1788-02-06'),
            coalesce(event_occurrence_date, '1788-02-06'),
            coalesce(award_id, ''),
            coalesce(award_code, ''),
            coalesce(award_amount, 99999999),
            coalesce(award_date, '1788-02-06'),
            coalesce(start_date, '1788-02-06'),
            coalesce(end_date, '1788-02-06'),
            coalesce(weekly_amount, 99999999),
            coalesce(award_created_date, '1788-02-06')
        )
    """
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("link_dia_reduction_payment_reference_file")
    op.drop_table("dia_reduction_payment")
    # ### end Alembic commands ###
