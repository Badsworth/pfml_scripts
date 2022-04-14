import pytest

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
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


def test_get_refunds_no_batch_for_employee(
    local_initialize_factories_session, local_test_db_session
):
    employee_id = "a9c98c3f-eaaf-4f68-9a03-13561537c023"
    batch = pfml_1099_util.get_last_1099_batch_for_employee(local_test_db_session, employee_id)
    assert batch is None
