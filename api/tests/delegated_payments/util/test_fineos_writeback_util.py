import massgov.pfml.api.util.state_log_util as state_log_util
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.db.models.factories import PaymentFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.db.models.state import Flow, State
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    create_payment_finished_state_log_with_writeback,
    stage_payment_fineos_writeback,
)


def test_stage_payment_fineos_writeback(test_db_session, initialize_factories_session):
    transaction_status = FineosWritebackTransactionStatus.PAID
    import_log_id = 1
    outcome_message = "Test"

    import_log = ImportLog(import_log_id=import_log_id)
    test_db_session.add(import_log)

    # standard usage
    payment = PaymentFactory.create()
    stage_payment_fineos_writeback(
        payment=payment,
        writeback_transaction_status=transaction_status,
        outcome=state_log_util.build_outcome(outcome_message),
        db_session=test_db_session,
        import_log_id=import_log_id,
    )

    assert_writeback(payment, transaction_status, outcome_message, test_db_session, import_log_id)

    # no outcome
    payment_2 = PaymentFactory.create()
    stage_payment_fineos_writeback(
        payment=payment_2,
        writeback_transaction_status=transaction_status,
        db_session=test_db_session,
        import_log_id=import_log_id,
    )

    assert_writeback(
        payment_2,
        transaction_status,
        transaction_status.transaction_status_description,
        test_db_session,
        import_log_id,
    )


def test_create_payment_finished_state_log_with_writeback(
    test_db_session, initialize_factories_session
):
    transaction_status = FineosWritebackTransactionStatus.PAID
    import_log_id = 1
    outcome_message = "Test"

    import_log = ImportLog(import_log_id=import_log_id)
    test_db_session.add(import_log)

    payment = PaymentFactory.create()
    create_payment_finished_state_log_with_writeback(
        payment=payment,
        payment_end_state=State.DELEGATED_PAYMENT_COMPLETE,
        payment_outcome=state_log_util.build_outcome(outcome_message),
        writeback_transaction_status=transaction_status,
        writeback_outcome=state_log_util.build_outcome(outcome_message),
        db_session=test_db_session,
        import_log_id=import_log_id,
    )

    assert_writeback(payment, transaction_status, outcome_message, test_db_session, import_log_id)

    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, test_db_session
    )
    assert payment_flow_log.end_state_id == State.DELEGATED_PAYMENT_COMPLETE.state_id
    assert payment_flow_log.import_log_id == import_log_id
    assert payment_flow_log.outcome["message"] == outcome_message


def assert_writeback(payment, transaction_status, outcome_message, db_session, import_log_id):
    writeback_detail = (
        db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert writeback_detail
    assert writeback_detail.transaction_status_id == transaction_status.transaction_status_id

    writeback_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, db_session
    )
    assert writeback_flow_log.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id
    assert writeback_flow_log.import_log_id == import_log_id
    assert writeback_flow_log.outcome["message"] == outcome_message
