import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_fineos_payment_cancellation as processor
from massgov.pfml.db.models.employees import State, StateLog
from tests.helpers.state_log import AdditionalParams, setup_state_log


@pytest.fixture
def payment_cancellation_step(initialize_factories_session, test_db_session, test_db_other_session):
    return processor.PaymentCancellationStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_cancel_payments(
    payment_cancellation_step, test_db_session, monkeypatch, create_triggers,
):
    setup_result = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_states=[State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION,],
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="012345678",
            fineos_absence_id="NTN-01-ABS-01",
            add_claim_payment_for_employee=True,
        ),
    )

    setup_result_2 = setup_state_log(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_states=[State.PAYMENT_READY_FOR_ADDRESS_VALIDATION,],
        test_db_session=test_db_session,
        additional_params=AdditionalParams(
            fineos_customer_num="012345678",
            fineos_absence_id="NTN-01-ABS-02",
            add_claim_payment_for_employee=True,
            employee=setup_result.state_logs[0].payment.claim.employee,
        ),
    )

    assert (
        setup_result.state_logs[0].payment.claim.employee_id
        == setup_result_2.state_logs[0].payment.claim.employee_id
    )

    results_error_before = (
        test_db_session.query(StateLog)
        .filter(
            StateLog.end_state_id.in_(
                [State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id]
            ),
        )
        .all()
    )

    assert len(results_error_before) == 0

    payment_cancellation_step.run()

    results_error = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        test_db_session,
    )

    assert len(results_error) == 2

    results = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_WAITING_FOR_PAYMENT_AUDIT_RESPONSE_CANCELLATION,
        test_db_session,
    )

    assert len(results) == 0

    results_error_report = state_log_util.get_all_latest_state_logs_in_end_state(
        state_log_util.AssociatedClass.PAYMENT,
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
        test_db_session,
    )

    assert len(results_error_report) == 2
