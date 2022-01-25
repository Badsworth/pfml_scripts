"""Include Timestamps in Employee and Employer Fineos Queue Tables

Revision ID: 7356c1084235
Revises: 6e9178463c6d
Create Date: 2021-10-12 21:37:50.080556

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7356c1084235"
down_revision = "6e9178463c6d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "employee_push_to_fineos_queue",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "employee_push_to_fineos_queue",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_employee_push_to_fineos_queue_employee_id"),
        "employee_push_to_fineos_queue",
        ["employee_id"],
        unique=False,
    )
    op.add_column(
        "employer_push_to_fineos_queue",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "employer_push_to_fineos_queue",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("employer_push_to_fineos_queue", "updated_at")
    op.drop_column("employer_push_to_fineos_queue", "created_at")
    op.drop_index(
        op.f("ix_employee_push_to_fineos_queue_employee_id"),
        table_name="employee_push_to_fineos_queue",
    )
    op.drop_column("employee_push_to_fineos_queue", "updated_at")
    op.drop_column("employee_push_to_fineos_queue", "created_at")
    # ### end Alembic commands ###