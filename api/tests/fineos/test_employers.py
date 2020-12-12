import pytest

import massgov.pfml.fineos
import massgov.pfml.fineos.employers as fineos_employers
from massgov.pfml.db.models.employees import EmployerLog
from massgov.pfml.db.models.factories import EmployerOnlyDORDataFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_load_all(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is not None


def test_load_all_missing_info(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    # this should never be the case, but just to test behavior
    employer_missing_name = EmployerOnlyDORDataFactory.create(employer_name=None)

    assert employer_missing_name.fineos_employer_id is None

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 2
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 1

    test_db_session.refresh(employer)
    test_db_session.refresh(employer_missing_name)

    assert employer.fineos_employer_id is not None
    assert employer_missing_name.fineos_employer_id is None


def test_load_all_skip_existing_fineos_employer_id(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create(fineos_employer_id=1)

    assert employer.fineos_employer_id == 1

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 0
    assert result.loaded_employers_count == 0
    assert result.errored_employers_count == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id == 1


def test_load_all_multiple(test_db_session, initialize_factories_session):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employers = EmployerOnlyDORDataFactory.create_batch(size=10)

    result = fineos_employers.load_all(test_db_session, fineos_client)

    assert result.total_employers_count == 10
    assert result.loaded_employers_count == 10
    assert result.errored_employers_count == 0

    for employer in employers:
        test_db_session.refresh(employer)
        assert employer.fineos_employer_id is not None


def test_load_updates_simple(test_db_session, initialize_factories_session, create_triggers):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    employer_log_entries = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries) == 1

    result = fineos_employers.load_updates(test_db_session, fineos_client)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is not None


def test_load_updates_multiple_log_entries_only_run_once(
    test_db_session, initialize_factories_session, create_triggers
):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employer = EmployerOnlyDORDataFactory.create()

    assert employer.fineos_employer_id is None

    # make an update
    employer.account_key = "foo"
    test_db_session.commit()

    # and ensure it was recorded in the log table
    employer_log_entries = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer.employer_id)
        .all()
    )
    assert len(employer_log_entries) == 2

    # then test
    result = fineos_employers.load_updates(test_db_session, fineos_client)

    assert result.total_employers_count == 1
    assert result.loaded_employers_count == 1
    assert result.errored_employers_count == 0

    test_db_session.refresh(employer)

    assert employer.fineos_employer_id is not None


def test_load_updates_multiple(test_db_session, initialize_factories_session, create_triggers):
    fineos_client = massgov.pfml.fineos.MockFINEOSClient()

    employers = EmployerOnlyDORDataFactory.create_batch(size=10)

    result = fineos_employers.load_updates(test_db_session, fineos_client)

    assert result.total_employers_count == 10
    assert result.loaded_employers_count == 10
    assert result.errored_employers_count == 0

    for employer in employers:
        test_db_session.refresh(employer)
        assert employer.fineos_employer_id is not None
