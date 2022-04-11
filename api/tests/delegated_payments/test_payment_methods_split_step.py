import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.payment_methods_split_step as payment_split
from massgov.pfml.db.models.employees import PaymentMethod, State
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory

# A few miscellaneous states that won't be cleaned up
misc_states = [State.DELEGATED_PAYMENT_COMPLETE, State.DELEGATED_PAYMENT_PUB_TRANSACTION_EFT_SENT]


@pytest.fixture
def payment_split_step(initialize_factories_session, test_db_session):
    return payment_split.PaymentMethodsSplitStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    )


def test_split_payment_methods(payment_split_step, test_db_session):
    for _ in range(5):
        DelegatedPaymentFactory(
            test_db_session, payment_method=PaymentMethod.ACH
        ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_VALIDATED)

        DelegatedPaymentFactory(
            test_db_session, payment_method=PaymentMethod.CHECK
        ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_VALIDATED)

        for misc_state in misc_states:
            DelegatedPaymentFactory(
                test_db_session, payment_method=PaymentMethod.CHECK
            ).get_or_create_payment_with_state(misc_state)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)
    assert state_log_counts[State.DELEGATED_PAYMENT_VALIDATED.state_description] == 10

    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5

    # Run the step
    payment_split_step.run()
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert (
        state_log_counts[State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT.state_description] == 5
    )
    assert (
        state_log_counts[State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_CHECK.state_description]
        == 5
    )

    # The miscellaneous state should still be unaffected
    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5


def test_cleanup_states_rollback(payment_split_step, test_db_session):
    test_db_session.begin_nested()
    for _ in range(5):
        DelegatedPaymentFactory(
            test_db_session, payment_method=PaymentMethod.ACH
        ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_VALIDATED)

        DelegatedPaymentFactory(
            test_db_session, payment_method=PaymentMethod.CHECK
        ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_VALIDATED)

        DelegatedPaymentFactory(
            test_db_session, payment_method=PaymentMethod.DEBIT
        ).get_or_create_payment_with_state(State.DELEGATED_PAYMENT_VALIDATED)

        for misc_state in misc_states:
            DelegatedPaymentFactory(test_db_session).get_or_create_payment_with_state(misc_state)

    test_db_session.commit()  # It will rollback to this DB state
    test_db_session.begin_nested()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)
    assert state_log_counts[State.DELEGATED_PAYMENT_VALIDATED.state_description] == 15

    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5

    with pytest.raises(Exception, match="Unexpected payment method found"):
        payment_split_step.run()

    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    # no change in count for misc and DELEGATED_PAYMENT_VALIDATED
    assert state_log_counts[State.DELEGATED_PAYMENT_VALIDATED.state_description] == 15

    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5
