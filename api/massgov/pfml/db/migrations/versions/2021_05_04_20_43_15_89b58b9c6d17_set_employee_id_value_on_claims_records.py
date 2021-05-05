"""Set employee_id value on claims records

Revision ID: 89b58b9c6d17
Revises: a113c523fedf
Create Date: 2021-05-04 20:43:15.784837

"""
import math

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import bindparam


# revision identifiers, used by Alembic.
revision = "89b58b9c6d17"
down_revision = "a113c523fedf"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    applications = sa.Table(
        "application",
        sa.MetaData(),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tax_identifier_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    claims = sa.Table(
        "claim",
        sa.MetaData(),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    employees = sa.Table(
        "employee",
        sa.MetaData(),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tax_identifier_id", postgresql.UUID(as_uuid=True), nullable=False),
    )

    null_employee_claims = connection.execute(sa.select([claims.c.claim_id]).where(claims.c.employee_id==None)).fetchall()
    null_employee_claim_ids = set([row.claim_id for row in null_employee_claims])

    applications_claims_and_tax_identifier_ids = connection.execute(
        sa.select([
            applications.c.application_id,
            applications.c.claim_id,
            applications.c.tax_identifier_id,
        ]).where(applications.c.claim_id.in_(null_employee_claim_ids))
    ).fetchall()

    tax_identifier_ids_to_claim_ids = {
        row.tax_identifier_id: row.claim_id
        for row in applications_claims_and_tax_identifier_ids
    }

    tax_identifier_ids = set(
        [row.tax_identifier_id for row in applications_claims_and_tax_identifier_ids]
    )

    tax_identifier_ids_to_employees_results = connection.execute(
        sa.select([
            employees.c.tax_identifier_id, employees.c.employee_id
        ]).where(
            employees.c.tax_identifier_id.in_(tax_identifier_ids)
        )
    ).fetchall()

    tax_identifier_ids_to_employees = {
        row.tax_identifier_id: row.employee_id
        for row in tax_identifier_ids_to_employees_results
    }

    bulk_update_params = []

    for tax_identifier_id in tax_identifier_ids_to_employees:
        claim_id = tax_identifier_ids_to_claim_ids[tax_identifier_id]
        employee_id = tax_identifier_ids_to_employees[tax_identifier_id]
        bulk_update_params.append({'claim_id': claim_id, 'employee_id': employee_id})

    batch_size = 500
    total_batches = math.ceil(len(bulk_update_params) / batch_size)
    current_batch = 0

    stmt = claims.update().where(
        claims.c.claim_id == bindparam('_claim_id')
    ).values(
        {
            'employee_id': bindparam('employee_id'),
        }
    )

    while current_batch < total_batches:
        connection.execute(
            stmt,
            bulk_update_params[current_batch * batch_size: (current_batch + 1) * batch_size]
        )
        current_batch += 1
    """
    while current_batch < total_batches:
        try:
            connection.bulk_update_mappings(bulk_update_params[current_batch * batch_size: (current_batch + 1) * batch_size])
        except:
            pass
        finally:
            current_batch += 1
    """
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # drop claims where source is employee_id
    # drop claims source
    pass
    # ### end Alembic commands ###
