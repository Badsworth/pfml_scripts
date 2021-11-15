"""change request_json column to JSONB from JSON

Revision ID: 60115085565a
Revises: fc752a00f212
Create Date: 2021-06-28 15:41:13.292823

"""

from alembic import op
from sqlalchemy import orm

# revision identifiers, used by Alembic.
revision = "60115085565a"
down_revision = "fc752a00f212"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    upgrade_sql = "ALTER TABLE notification ALTER COLUMN request_json TYPE JSONB USING ((request_json #>> '{}')::JSONB);"

    session.execute(upgrade_sql)

    session.commit()


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    downgrade_sql = "ALTER TABLE notification ALTER COLUMN request_json TYPE JSON USING ((request_json #>> '{}')::JSON);"

    session.execute(downgrade_sql)

    session.commit()
