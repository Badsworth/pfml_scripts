"""Set employee_id value on claims records

Revision ID: 89b58b9c6d17
Revises: a113c523fedf
Create Date: 2021-05-04 20:43:15.784837

"""
import datetime
import math

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import bindparam

import massgov.pfml.util.logging


logger = massgov.pfml.util.logging.get_logger(__name__)
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
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    employees = sa.Table(
        "employee",
        sa.MetaData(),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tax_identifier_id", postgresql.UUID(as_uuid=True), nullable=False),
    )

    # Unique log identifier for this invocation of the migration
    migration_tag = f"set_employee_id_on_claims-{datetime.datetime.now()}"

    # First get all claims that have a null employee_id
    null_employee_claims_query = connection.execute(
        sa.select([claims.c.claim_id]).where(claims.c.employee_id == None)  # noqa: E711
    )
    null_employee_claim_ids = set([row.claim_id for row in null_employee_claims_query.fetchall()])

    logger.info(
        f"Starting run of set employee id on claims migration",
        extra={
            "migration_tag": migration_tag,
            "total_null_employee_claims": len(null_employee_claim_ids),
        }
    )

    # Then lookup all applications for those claims and the corresponding tax identifier ids
    applications_claims_and_tax_identifier_query = connection.execute(
        sa.select(
            [
                applications.c.application_id,
                applications.c.claim_id,
                applications.c.tax_identifier_id,
            ]
        ).where(applications.c.claim_id.in_(null_employee_claim_ids))
    )

    # Build a mapping of all tax identifier ids to claim ids
    tax_identifier_ids_to_claim_ids = {
        row.tax_identifier_id: row.claim_id
        for row in applications_claims_and_tax_identifier_query.fetchall()
    }
    tax_identifier_ids = set(
        [tax_identifier_id for tax_identifier_id in tax_identifier_ids_to_claim_ids]
    )

    # Build a mapping of all tax identifier ids to employee ids
    tax_identifier_ids_to_employees_query = connection.execute(
        sa.select([employees.c.tax_identifier_id, employees.c.employee_id]).where(
            employees.c.tax_identifier_id.in_(tax_identifier_ids)
        )
    )
    tax_identifier_ids_to_employees = {
        row.tax_identifier_id: row.employee_id
        for row in tax_identifier_ids_to_employees_query.fetchall()
    }

    # Use the tax identifier ids -> employees and tax identifier ids -> claims mappings to update
    # the claims tables with correct employee_ids
    bulk_update_params = []
    for tax_identifier_id in tax_identifier_ids_to_employees:
        claim_id = tax_identifier_ids_to_claim_ids[tax_identifier_id]
        employee_id = tax_identifier_ids_to_employees[tax_identifier_id]
        bulk_update_params.append({"claim_id": claim_id, "employee_id": employee_id})

    batch_size = 500
    total_batches = math.ceil(len(bulk_update_params) / batch_size)
    current_batch = 0

    bulk_update_statement = (
        claims.update()
        .where(claims.c.claim_id == bindparam("_claim_id"))
        .values({"employee_id": bindparam("employee_id")})
    )

    while current_batch < total_batches:
        connection.execute(
            bulk_update_statement,
            bulk_update_params[current_batch * batch_size : (current_batch + 1) * batch_size],
        )
        current_batch += 1

    null_employee_claims_query = connection.execute(
        sa.select([claims.c.claim_id]).where(claims.c.employee_id == None)  # noqa: E711
    )
    null_employee_claim_ids = set([row.claim_id for row in null_employee_claims_query.fetchall()])

    logger.info(
        f"Finished run of set employee id on claims migration",
        extra={
            "migration_tag": migration_tag,
            "total_null_employee_claims": len(null_employee_claim_ids),
        }
    )


def downgrade():
    pass
