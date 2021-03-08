import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.state_cleanup_step as state_cleanup_step
from massgov.pfml.db.models.employees import State, StateLog
from massgov.pfml.db.models.factories import PaymentFactory

# A few miscellaneous states that won't be cleaned up
misc_states = [
    State.DELEGATED_PAYMENT_COMPLETE,
    State.DELEGATED_PAYMENT_PUB_ERROR_REPORT_SENT,
    State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT,
]


def create_payment_in_state(state, test_db_session):
    payment = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        end_state=state,
        outcome=state_log_util.build_outcome("Success"),
        associated_model=payment,
        db_session=test_db_session,
    )


def test_cleanup_states(initialize_factories_session, test_db_session):
    for _ in range(5):
        for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
            create_payment_in_state(audit_state, test_db_session)

        for misc_state in misc_states:
            create_payment_in_state(misc_state, test_db_session)
    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)
    for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
        assert state_log_counts[audit_state.state_description] == 5

    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5

    # Run the step
    state_cleanup_step.cleanup_states(test_db_session)
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    # We shouldn't find any of the prior audit states as they've been moved
    for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
        assert audit_state not in state_log_counts

    # The miscellaneous state should be unaffected
    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5

    # Every audit state should have been moved to the expected error state
    assert state_log_counts[state_cleanup_step.ERROR_STATE.state_description] == 5 * len(
        payments_util.Constants.REJECT_FILE_PENDING_STATES
    )


def test_cleanup_states_rollback(initialize_factories_session, test_db_session):
    for _ in range(5):
        for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
            create_payment_in_state(audit_state, test_db_session)

        for misc_state in misc_states:
            create_payment_in_state(misc_state, test_db_session)

    # This process delibertely won't handle unassociated state logs, so we'll
    # error it by creating one.
    state_log_util.create_state_log_without_associated_model(
        end_state=payments_util.Constants.REJECT_FILE_PENDING_STATES[0],
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        outcome=state_log_util.build_outcome("Success"),
        db_session=test_db_session,
    )
    test_db_session.commit()  # It will rollback to this DB state

    state_log_counts = state_log_util.get_state_counts(test_db_session)
    total_state_logs = test_db_session.query(StateLog).count()

    with pytest.raises(
        Exception, match="A state log was found without a payment in the cleanup job"
    ):
        state_cleanup_step.cleanup_states(test_db_session)

    # None of the state logs should have changed
    state_log_counts_after = state_log_util.get_state_counts(test_db_session)
    total_state_logs_after = test_db_session.query(StateLog).count()
    assert state_log_counts == state_log_counts_after
    assert total_state_logs == total_state_logs_after
