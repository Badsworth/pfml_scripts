#
# Tests for massgov.pfml.db.handle_error.
#

import psycopg2
import pytest
import sqlalchemy

import massgov.pfml.db.handle_error
from massgov.pfml.db.models.employees import TaxIdentifier


def test_sqlalchemy_event_handle_error():
    psycopg2_exception = psycopg2.errors.UniqueViolation(
        'duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"\n'
        "DETAIL:  Key (tax_identifier)=(999000999) already exists.\n"
    )
    sqlalchemy_exception = sqlalchemy.exc.IntegrityError("UPDATE ...", (), psycopg2_exception)

    context = sqlalchemy.engine.ExceptionContext()
    context.original_exception = psycopg2_exception
    context.sqlalchemy_exception = sqlalchemy_exception

    massgov.pfml.db.handle_error.sqlalchemy_event_handle_error(context)

    assert repr(psycopg2_exception) == (
        "UniqueViolation("
        "'duplicate key value violates unique constraint \"tax_identifier_tax_identifier_key\"')"
    )
    assert repr(sqlalchemy_exception) == (
        "IntegrityError('(psycopg2.errors.UniqueViolation)"
        ' duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"\')'
    )


def test_exception_is_cleaned(test_db_session):
    t1 = TaxIdentifier(tax_identifier="999009999")
    t2 = TaxIdentifier(tax_identifier="999009999")
    test_db_session.add(t1)
    test_db_session.add(t2)

    with pytest.raises(sqlalchemy.exc.IntegrityError) as exc_info:
        test_db_session.commit()
    assert exc_info.value.args == (
        "(psycopg2.errors.UniqueViolation) duplicate key value violates unique "
        'constraint "tax_identifier_tax_identifier_key"',
    )
    assert type(exc_info.value.orig) == psycopg2.errors.UniqueViolation
    assert exc_info.value.orig.args == (
        'duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"',
    )
