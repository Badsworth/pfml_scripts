"""Remove flow from state_log and latest_state_log

Revision ID: bef7e8d6100b
Revises: a5144960536f
Create Date: 2020-12-23 19:02:51.162093

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bef7e8d6100b"
down_revision = "a5144960536f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("latest_state_log_flow_id_fkey", "latest_state_log", type_="foreignkey")
    op.drop_column("latest_state_log", "flow_id")
    op.drop_constraint("state_log_flow_id_fkey", "state_log", type_="foreignkey")
    op.drop_column("state_log", "flow_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "state_log", sa.Column("flow_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_foreign_key(
        "state_log_flow_id_fkey", "state_log", "lk_flow", ["flow_id"], ["flow_id"]
    )
    op.add_column(
        "latest_state_log", sa.Column("flow_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_foreign_key(
        "latest_state_log_flow_id_fkey", "latest_state_log", "lk_flow", ["flow_id"], ["flow_id"]
    )
    # ### end Alembic commands ###
