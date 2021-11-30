import pytest

import massgov.pfml.delegated_payments.irs_1099.populate_refunds as populate_refunds
from massgov.pfml.delegated_payments.mock.irs_1099_factory import Pfml1099Factory


@pytest.fixture
def populate_refunds_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return populate_refunds.PopulateRefundsStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_populate_refunds(populate_refunds_step, local_test_db_session):

    # Create batch records for test
    Pfml1099Factory(db_session=local_test_db_session).get_or_create_batch()

    # Run the step
    populate_refunds_step.run()
