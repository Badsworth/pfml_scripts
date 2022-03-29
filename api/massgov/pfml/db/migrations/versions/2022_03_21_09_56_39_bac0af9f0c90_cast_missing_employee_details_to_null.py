"""Cast missing Employee details to NULL

Revision ID: bac0af9f0c90
Revises: 3bca32005f0e
Create Date: 2022-03-21 09:56:39.107158

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "bac0af9f0c90"
down_revision = "3bca32005f0e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE employee SET email_address = NULL WHERE email_address = ''")

    op.execute("UPDATE employee_occupation SET job_title = NULL WHERE job_title = ''")
    op.execute(
        "UPDATE employee_occupation SET employment_status = NULL WHERE employment_status = ''"
    )
    op.execute("UPDATE employee_occupation SET manager_id = NULL WHERE manager_id = ''")
    op.execute("UPDATE employee_occupation SET worksite_id = NULL WHERE worksite_id = ''")
    op.execute(
        "UPDATE employee_occupation SET occupation_qualifier = NULL WHERE occupation_qualifier = ''"
    )


def downgrade():
    pass
