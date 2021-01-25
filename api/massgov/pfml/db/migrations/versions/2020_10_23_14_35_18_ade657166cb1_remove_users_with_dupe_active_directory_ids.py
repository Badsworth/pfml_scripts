""" Remove Users with duplicate active_directory_id values

Revision ID: ade657166cb1
Revises: 3c7f53532558
Create Date: 2020-10-23 14:35:18.762918

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ade657166cb1"
down_revision = "3c7f53532558"
branch_labels = None
depends_on = None


def upgrade():
    duplicate_user_ids_query = """
    SELECT user_id
        FROM "user" u1
        INNER JOIN
            (SELECT MIN(ctid) as ctid, active_directory_id
               FROM "user"
               GROUP BY active_directory_id
               HAVING COUNT(user_id) > 1
            ) u2
        ON u1.active_directory_id = u2.active_directory_id
        AND u1.ctid <> u2.ctid
    """

    op.execute(
        f"""
        DELETE FROM link_user_role lur
            USING ({duplicate_user_ids_query}) u
            WHERE lur.user_id = u.user_id
    """
    )

    op.execute(
        f"""
        DELETE FROM link_user_leave_administrator lula
            USING ({duplicate_user_ids_query}) u
            WHERE lula.user_id = u.user_id
    """
    )

    op.execute(
        f"""
        DELETE FROM "user" u1
            USING ({duplicate_user_ids_query}) u2
            WHERE u1.user_id = u2.user_id
    """
    )


def downgrade():
    # One-way migration. User records are irreversibly destroyed.
    pass
