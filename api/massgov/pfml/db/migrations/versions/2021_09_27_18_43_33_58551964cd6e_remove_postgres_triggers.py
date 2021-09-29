"""Remove postgres triggers

Revision ID: 58551964cd6e
Revises: b99a1f6a0679
Create Date: 2021-09-27 18:43:33.726489

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "58551964cd6e"
down_revision = "b99a1f6a0679"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TRIGGER IF EXISTS after_employee_insert on employee;")
    op.execute("DROP TRIGGER IF EXISTS after_employee_update on employee;")
    op.execute("DROP TRIGGER IF EXISTS after_employee_delete on employee;")
    op.execute("DROP FUNCTION IF EXISTS audit_employee_func CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS after_employer_insert on employer;")
    op.execute("DROP TRIGGER IF EXISTS after_employer_update on employer;")
    op.execute("DROP TRIGGER IF EXISTS after_employer_delete on employer;")
    op.execute("DROP FUNCTION IF EXISTS audit_employer_func CASCADE;")


def downgrade():
    pass
