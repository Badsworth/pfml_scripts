import datetime

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_fineos_related_payment_post_processing as withholding_payments_process
from massgov.pfml.db.models.employees import PaymentTransactionType, State
from massgov.pfml.db.models.factories import ClaimFactory
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


@pytest.fixture
def related_withholding_payment_post_processing_step(
    initialize_factories_session, test_db_session, test_db_other_session
):

    return withholding_payments_process.RelatedPaymentsPostProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


def test_withholding_payment_methods(
    related_withholding_payment_post_processing_step, test_db_session, test_db_other_session
):
    claim = ClaimFactory.create()

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
        amount=10.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.STATE_WITHHOLDING_SEND_FUNDS)

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
        amount=10.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_SEND_FUNDS)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.FEDERAL_WITHHOLDING_SEND_FUNDS.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_SEND_FUNDS.state_description] == 1

    related_withholding_payment_post_processing_step.run()
    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.FEDERAL_WITHHOLDING_FUNDS_SENT.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_FUNDS_SENT.state_description] == 1
