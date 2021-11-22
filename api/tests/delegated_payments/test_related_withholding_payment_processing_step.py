import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_fineos_related_payment_processing as withholding_payments_process
from massgov.pfml.db.models.employees import State
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory

misc_states = [
    State.STATE_WITHHOLDING_READY_FOR_PROCESSING,
    State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING,
    State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
]


@pytest.fixture
def related_withholding_payment_step(initialize_factories_session, test_db_session, test_db_other_session):
    return withholding_payments_process.RelatedPaymentsProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_split_payment_methods(related_withholding_payment_step, test_db_session):
    for misc_state in misc_states:
        DelegatedPaymentFactory(
            test_db_session
        ).get_or_create_payment_with_state(misc_state)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description] == 1

    # Run the step
    related_withholding_payment_step.run()
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    # Expect 2 writeback records after process
    assert (
        state_log_counts[State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_description] == 2
    )
    assert (
        state_log_counts[State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description]
        == 1
    )
