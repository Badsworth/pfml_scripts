"""Initial roles

Revision ID: 791abdb2ba16
Revises: 020d8108295a
Create Date: 2020-07-13 09:39:10.386003

"""
import os

from alembic import op

# revision identifiers, used by Alembic.
revision = "791abdb2ba16"
down_revision = "020d8108295a"
branch_labels = None
depends_on = None

admin_username = "pfml"
app_schema = os.getenv("DB_SCHEMA", "public")
app_role = "app"


def upgrade():
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")

    op.execute(
        f"""
    DO $$
    BEGIN
        CREATE ROLE {app_role};
        EXCEPTION WHEN DUPLICATE_OBJECT THEN
        RAISE NOTICE 'not creating role {app_role} -- it already exists';
    END
    $$;
    """
    )

    # allow admin user to act in the new role
    op.execute(f"GRANT app TO {admin_username} WITH ADMIN OPTION")

    # allow new role to access app schema
    op.execute(f"GRANT USAGE ON SCHEMA {app_schema} TO {app_role}")

    # set permissions for tables created in the future
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {app_schema} GRANT ALL ON TABLES TO {app_role}")
    # set permissions for existing tables
    op.execute(f"GRANT ALL ON ALL TABLES IN SCHEMA {app_schema} TO {app_role}")

    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {app_schema} GRANT ALL ON SEQUENCES TO {app_role}"
    )
    op.execute(f"GRANT ALL ON ALL SEQUENCES IN SCHEMA {app_schema} TO {app_role}")

    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {app_schema} GRANT ALL ON ROUTINES TO {app_role}"
    )
    op.execute(f"GRANT ALL ON ALL ROUTINES IN SCHEMA {app_schema} TO {app_role}")


def downgrade():
    op.execute(f"REASSIGN OWNED BY {app_role} TO {admin_username}")

    op.execute(f"REVOKE ALL ON SCHEMA {app_schema} FROM {app_role}")

    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {app_schema} FROM {app_role}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {app_schema} REVOKE ALL ON TABLES FROM {app_role}"
    )

    op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA {app_schema} FROM {app_role}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {app_schema} REVOKE ALL ON SEQUENCES FROM {app_role}"
    )

    op.execute(f"REVOKE ALL ON ALL ROUTINES IN SCHEMA {app_schema} FROM {app_role}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {app_schema} REVOKE ALL ON ROUTINES FROM {app_role}"
    )

    op.execute(f"DROP ROLE {app_role}")

    op.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
