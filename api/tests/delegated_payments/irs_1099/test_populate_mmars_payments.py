import pytest

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.delegated_payments.irs_1099.populate_mmars_payments as populate_mmars_payments
from massgov.pfml.db.models import factories
from massgov.pfml.db.models.payments import MmarsPaymentData
from massgov.pfml.delegated_payments.mock.irs_1099_factory import Pfml1099Factory


@pytest.fixture
def populate_mmars_payments_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return populate_mmars_payments.PopulateMmarsPaymentsStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_populate_mmars_payments(populate_mmars_payments_step, local_test_db_session):

    # Create batch records for test
    batch = Pfml1099Factory(db_session=local_test_db_session).get_or_create_batch()

    # Add 9 payments.
    for i in range(1, 10):
        _mmars_payment_factory(i, local_test_db_session)

    # Run the step
    populate_mmars_payments_step.run()
    after_payment_counts = pfml_1099_util.get_mmars_payment_counts(local_test_db_session)

    # We should have 9 payments
    assert after_payment_counts[batch.pfml_1099_batch_id] == 9


def test_get_mmars_payments_no_batch_for_employee(
    local_initialize_factories_session, local_test_db_session
):
    employee_id = "a9c98c3f-eaaf-4f68-9a03-13561537c023"
    batch = pfml_1099_util.get_last_1099_batch_for_employee(local_test_db_session, employee_id)
    assert batch is None


def _mmars_payment_factory(pub_individual_id, test_db_session) -> MmarsPaymentData:
    employee = factories.EmployeeFactory.create(
        ctr_vendor_customer_code="VC00012011" + str(pub_individual_id)
    )
    employer = factories.EmployerFactory.create()
    factories.WagesAndContributionsFactory.create(employer=employer, employee=employee)

    payment = factories.MmarsPaymentDataFactory(
        vendor_customer_code="VC00012011" + str(pub_individual_id)
    )

    return payment
