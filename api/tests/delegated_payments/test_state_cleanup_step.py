import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.delegated_payments.state_cleanup_step as state_cleanup
from massgov.pfml.db.models.employees import State, StateLog
from massgov.pfml.db.models.factories import PaymentFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails

# every test in here requires real resources
pytestmark = pytest.mark.integration

# A few miscellaneous states that won't be cleaned up
misc_states = [
    State.DELEGATED_PAYMENT_COMPLETE,
    State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_EFT_SENT,
    State.DELEGATED_PAYMENT_ADD_TO_PUB_TRANSACTION_EFT,
]


@pytest.fixture
def state_cleanup_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return state_cleanup.StateCleanupStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


def create_payment_in_state(state, db_session):
    payment = PaymentFactory.create()
    state_log_util.create_finished_state_log(
        end_state=state,
        outcome=state_log_util.build_outcome("Success"),
        associated_model=payment,
        db_session=db_session,
    )


def test_cleanup_states(state_cleanup_step, local_test_db_session):
    for _ in range(5):
        for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
            create_payment_in_state(audit_state, local_test_db_session)

        for misc_state in misc_states:
            create_payment_in_state(misc_state, local_test_db_session)

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(local_test_db_session)
    for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
        assert state_log_counts[audit_state.state_description] == 5

    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5

    # Run the step
    state_cleanup_step.run()
    state_log_counts = state_log_util.get_state_counts(local_test_db_session)

    # We shouldn't find any of the prior audit states as they've been moved
    for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
        assert audit_state not in state_log_counts

    # All pending states should have been moved to the error state
    pending_payments_count = len(payments_util.Constants.REJECT_FILE_PENDING_STATES) * 5
    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_description
        ]
        == pending_payments_count
    )
    assert (
        state_log_counts[State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_description]
        == pending_payments_count
    )

    writeback_details = local_test_db_session.query(FineosWritebackDetails).all()
    assert len(writeback_details) == pending_payments_count

    # The miscellaneous state should be unaffected
    for misc_state in misc_states:
        assert state_log_counts[misc_state.state_description] == 5

    # Every audit state should have been moved to the expected error state
    assert state_log_counts[state_cleanup.ERROR_STATE.state_description] == 5 * len(
        payments_util.Constants.REJECT_FILE_PENDING_STATES
    )


def test_cleanup_states_rollback(state_cleanup_step, local_test_db_session):
    local_test_db_session.begin_nested()

    for _ in range(5):
        for audit_state in payments_util.Constants.REJECT_FILE_PENDING_STATES:
            create_payment_in_state(audit_state, local_test_db_session)

        for misc_state in misc_states:
            create_payment_in_state(misc_state, local_test_db_session)

    # This process delibertely won't handle unassociated state logs, so we'll
    # error it by creating one.
    state_log_util.create_state_log_without_associated_model(
        end_state=payments_util.Constants.REJECT_FILE_PENDING_STATES[0],
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        outcome=state_log_util.build_outcome("Success"),
        db_session=local_test_db_session,
    )
    local_test_db_session.commit()  # It will rollback to this DB state
    local_test_db_session.begin_nested()

    state_log_counts = state_log_util.get_state_counts(local_test_db_session)
    total_state_logs = local_test_db_session.query(StateLog).count()

    with pytest.raises(
        Exception, match="A state log was found without a payment in the cleanup job"
    ):
        state_cleanup_step.run()

    # None of the state logs should have changed
    state_log_counts_after = state_log_util.get_state_counts(local_test_db_session)
    total_state_logs_after = local_test_db_session.query(StateLog).count()
    assert state_log_counts == state_log_counts_after
    assert total_state_logs == total_state_logs_after
