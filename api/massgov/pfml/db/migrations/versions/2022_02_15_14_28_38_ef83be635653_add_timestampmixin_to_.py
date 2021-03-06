"""Add TimestampMixin to UserLeaveAdministratorOrgUnit

Revision ID: ef83be635653
Revises: 1c912d1c655c
Create Date: 2022-02-15 14:28:38.632371

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ef83be635653"
down_revision = "1c912d1c655c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "link_user_leave_administrator_org_unit",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "link_user_leave_administrator_org_unit",
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
    op.drop_column("link_user_leave_administrator_org_unit", "updated_at")
    op.drop_column("link_user_leave_administrator_org_unit", "created_at")
    # ### end Alembic commands ###
