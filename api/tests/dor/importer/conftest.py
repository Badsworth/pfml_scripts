#
# Helpers and fixtures for pytest.
#

import pytest

from massgov.pfml.db.models.factories import EmployerOnlyDORDataFactory


@pytest.fixture
def employers(initialize_factories_session):
    employer1 = EmployerOnlyDORDataFactory.create(
        account_key="44100000001", employer_fein="100000001", employer_name="Boone PLC"
    )
    employer2 = EmployerOnlyDORDataFactory.create(
        account_key="44100000002", employer_fein="100000002", employer_name="Gould, Brown & Miller",
    )
    employer3 = EmployerOnlyDORDataFactory.create(
        account_key="44100000003", employer_fein="100000003", employer_name="Stephens LLC"
    )
    return employer1, employer2, employer3
