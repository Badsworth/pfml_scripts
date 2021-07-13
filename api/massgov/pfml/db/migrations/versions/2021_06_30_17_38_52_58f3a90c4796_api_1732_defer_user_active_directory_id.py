"""API-1732: defer User.active_directory_id

Revision ID: 58f3a90c4796
Revises: 39a29f32b5d0
Create Date: 2021-06-30 17:38:52.731932

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "58f3a90c4796"
down_revision = "95239ae3de15"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DROP TRIGGER copy_activedirectoryid_to_subid ON "user";

        DROP FUNCTION IF EXISTS copyToSubId();

        UPDATE "user" SET sub_id=active_directory_id
        WHERE sub_id IS NULL AND active_directory_id IS NOT NULL;
        """
    )


def downgrade():
    pass
