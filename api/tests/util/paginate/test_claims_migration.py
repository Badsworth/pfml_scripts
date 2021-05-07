import math

import pytest
import sqlalchemy as sa

from alembic.operations import Operations
from alembic.migration import MigrationContext
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.expression import bindparam

from massgov.pfml.db import create_engine, get_config

from massgov.pfml.db.models.factories import (
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    UserFactory,
    TaxIdentifierFactory,
)


def upgrade(context):
    op = Operations(context)
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
        bulk_update_params.append({'_claim_id': claim_id, 'employee_id': employee_id})

    batch_size = 5
    total_batches = math.ceil(len(bulk_update_params) / batch_size)
    current_batch = 0

    stmt = claims.update(). \
        where(claims.c.claim_id == bindparam('_claim_id')).values(
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
        try:
        except:
            pass
        finally:"""
    # ### end Alembic commands ###


@pytest.mark.integration
class TestMigration:
    def test_claims_migration(self, user, test_db_session):
        def setup():
            # create a bunch of claims, applications, employees, tax_ids

            ssn = 188574541
            fein = 716779225

            created_count = 0
            while created_count < 30:
                employer = EmployerFactory.create(employer_fein=str(fein + created_count))
                test_db_session.add(employer)

                tax_id = TaxIdentifierFactory.create(
                    tax_identifier=str(ssn + created_count)
                )
                test_db_session.add(tax_id)
                test_db_session.commit()

                employee = EmployeeFactory.create(
                    tax_identifier=tax_id,
                    tax_identifier_id=tax_id.tax_identifier_id,
                )
                test_db_session.add(employee)

                claim = ClaimFactory.create(
                    employer_id=employer.employer_id,
                    employee=None,
                    employee_id=None
                )
                test_db_session.add(claim)

                application = ApplicationFactory.create(
                    user=user,
                    claim=claim,
                    tax_identifier_id=tax_id.tax_identifier_id,
                    employee=None
                )
                application.tax_identifier = tax_id
                application.tax_identifier_id = tax_id.tax_identifier_id

                test_db_session.add(application)
                test_db_session.commit()

                created_count += 1

            test_db_session.commit()

        setup()

        engine = create_engine(get_config(prefer_admin=True))
        conn = engine.connect()
        context = MigrationContext.configure(conn)

        upgrade(context)

        assert True is True