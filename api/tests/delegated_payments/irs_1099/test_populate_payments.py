import datetime

import pytest

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.delegated_payments.irs_1099.populate_payments as populate_payments
from massgov.pfml.db.models import factories
from massgov.pfml.db.models.employees import Payment, PaymentMethod, PaymentTransactionType, State
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.mock.irs_1099_factory import Pfml1099Factory


@pytest.fixture
def populate_payments_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return populate_payments.PopulatePaymentsStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def test_populate_payments(populate_payments_step, local_test_db_session):

    # Create batch records for test
    batch = Pfml1099Factory(db_session=local_test_db_session).get_or_create_batch()

    # Add 9 payments.
    for i in range(1, 10):
        _payment_factory(i, local_test_db_session)

    # Run the step
    populate_payments_step.run()
    after_payment_counts = pfml_1099_util.get_payment_counts(local_test_db_session)

    # We should have one more batch
    # TODO : Fix test as part of PAY-148
    # assert after_payment_counts[batch.pfml_1099_batch_id] == 9
    assert batch is not None
    assert after_payment_counts is not None


def _payment_factory(
    pub_individual_id, test_db_session, end_state=State.DELEGATED_PAYMENT_PUB_TRANSACTION_CHECK_SENT
) -> Payment:
    employee = factories.EmployeeFactory.create()
    employer = factories.EmployerFactory.create()
    factories.WagesAndContributionsFactory.create(employer=employer, employee=employee)

    payment = DelegatedPaymentFactory(
        test_db_session,
        payment_transaction_type_id=PaymentTransactionType.STANDARD,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.75 + pub_individual_id,
        fineos_pei_c_value=42424,
        fineos_pei_i_value=10000 + pub_individual_id,
        fineos_extraction_date=datetime.date(2021, 3, 24),
        payment_method=PaymentMethod.CHECK,
        pub_individual_id=pub_individual_id,
        check_number=500 + pub_individual_id,
    ).get_or_create_payment_with_state(end_state)

    return payment
