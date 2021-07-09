"""Clear consented_to_data_sharing column

Revision ID: aa54e512ffb7
Revises: d22e41db247f
Create Date: 2021-06-22 16:31:25.207935

"""
from alembic import op

revision = "aa54e512ffb7"
down_revision = "d22e41db247f"
branch_labels = None
depends_on = None


def upgrade():
    # Clear the consented_to_data_sharing column for claimants.
    # Claimants will be prompted to re-consent (with new language) upon logging in.
    op.execute(
        # Join with the link_user_role table to determine which users are claimants.
        # All claimants either have no role, or a role_id of 1 ("User").
        # Other users include Leave Admins and the FINEOS user.
        """
        WITH claimants AS (
            SELECT u.user_id
            FROM "user" u
            LEFT OUTER JOIN "link_user_role" ur ON u.user_id = ur.user_id
            WHERE (ur.role_id IS NULL OR ur.role_id = 1)
        )
        UPDATE "user" u
        SET consented_to_data_sharing = FALSE
        FROM claimants c
        WHERE u.user_id = c.user_id
        """
    )


def downgrade():
    pass
