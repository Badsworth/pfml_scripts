import pytest

import massgov.pfml.fineos
import massgov.pfml.fineos.employers as fineos_employers
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
