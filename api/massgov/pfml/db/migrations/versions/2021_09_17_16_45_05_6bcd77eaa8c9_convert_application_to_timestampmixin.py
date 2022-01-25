"""Convert application to TimestampMixin

Revision ID: 6bcd77eaa8c9
Revises: d54ca8c8eccb
Create Date: 2021-09-17 16:45:05.608325

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6bcd77eaa8c9"
down_revision = "d54ca8c8eccb"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "application",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "application",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.execute("UPDATE application SET created_at = start_time, updated_at = updated_time")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("application", "updated_at")
    op.drop_column("application", "created_at")
    # ### end Alembic commands ###