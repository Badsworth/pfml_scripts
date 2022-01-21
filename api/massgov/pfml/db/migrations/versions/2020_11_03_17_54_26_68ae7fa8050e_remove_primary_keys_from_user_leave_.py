"""remove primary keys from user_leave_administrator table

Revision ID: 68ae7fa8050e
Revises: ac77dfa6613a
Create Date: 2020-11-03 17:54:26.647158

"""
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "68ae7fa8050e"
down_revision = "ac77dfa6613a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(
        "ALTER TABLE link_user_leave_administrator DROP CONSTRAINT link_user_leave_administrator_pkey"
    )
    op.add_column(
        "link_user_leave_administrator",
        sa.Column("user_leave_administrator_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    connection = op.get_bind()
    t_lula = sa.Table(
        "link_user_leave_administrator",
        sa.MetaData(),
        sa.Column("user_leave_administrator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("fineos_web_id", sa.Text()),
    )
    results = connection.execute(
        sa.select([t_lula.c.user_id, t_lula.c.employer_id, t_lula.c.fineos_web_id])
    ).fetchall()
    # Iterate over all selected data tuples.
    for user_id, employer_id, fineos_web_id in results:
        connection.execute(
            t_lula.update()
            .where(
                sa.and_(
                    t_lula.c.user_id == user_id,
                    t_lula.c.employer_id == employer_id,
                    t_lula.c.fineos_web_id == fineos_web_id,
                )
            )
            .values(user_leave_administrator_id=uuid.uuid4())
        )

    op.alter_column("link_user_leave_administrator", "user_leave_administrator_id", nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("link_user_leave_administrator", "user_leave_administrator_id")
    op.execute(
        "ALTER TABLE link_user_leave_administrator ADD CONSTRAINT link_user_leave_administrator_pkey PRIMARY KEY (user_id, employer_id)"
    )
    # ### end Alembic commands ###