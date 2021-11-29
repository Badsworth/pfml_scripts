import pytest

import massgov.pfml.delegated_payments.irs_1099.populate_1099 as populate_1099
from massgov.pfml.delegated_payments.mock.irs_1099_factory import Pfml1099Factory


@pytest.fixture
def populate_1099_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return populate_1099.Populate1099Step(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_populate_1099(populate_1099_step, local_test_db_session):

    # Create batch records for test
    Pfml1099Factory(db_session=local_test_db_session).get_or_create_batch()

    # Run the step
    populate_1099_step.run()
