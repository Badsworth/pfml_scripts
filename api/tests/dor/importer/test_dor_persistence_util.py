import uuid
from datetime import date

import pytest
from sqlalchemy.orm.exc import NoResultFound

import massgov.pfml.dor.importer.lib.dor_persistence_util as util

# every test in here requires real resources
pytestmark = pytest.mark.integration

# === test helper functions empty returns and exception raises ===


def test_get_employee_by_ssn(test_db_session):
    employee_row = util.get_employee_by_ssn(test_db_session, "000-00-0000")

    assert employee_row is None


def test_get_wages_and_contributions_by_employee_id_and_filling_period(test_db_session):
    wage_row = util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, uuid.uuid4(), date.today()
    )

    assert wage_row is None


def test_get_employer_by_fein(test_db_session):
    employer_row = util.get_employer_by_fein(test_db_session, "00-000000000")

    assert employer_row is None


def test_get_employer_address(test_db_session):
    with pytest.raises(NoResultFound):
        util.get_employer_address(test_db_session, uuid.uuid4())


def test_get_address(test_db_session):
    with pytest.raises(NoResultFound):
        util.get_address(test_db_session, uuid.uuid4())


def test_get_business_address_type(test_db_session):
    with pytest.raises(NoResultFound):
        util.get_business_address_type(test_db_session)


def test_find_state(test_db_session):
    with pytest.raises(NoResultFound):
        util.find_state(test_db_session, "MA")


def test_find_country(test_db_session):
    with pytest.raises(NoResultFound):
        util.find_country(test_db_session, "US")
