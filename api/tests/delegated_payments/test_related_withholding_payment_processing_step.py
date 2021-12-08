import datetime
from typing import List, Optional

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_fineos_related_payment_processing as withholding_payments_process
from massgov.pfml.db.models.employees import Flow, Payment, PaymentTransactionType, State, StateLog
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    LinkSplitPayment,
)
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


@pytest.fixture
def related_withholding_payment_step(
    initialize_factories_session, test_db_session, test_db_other_session
):
    return withholding_payments_process.RelatedPaymentsProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def test_withholding_payment_methods(related_withholding_payment_step, test_db_session):

    claim = DelegatedPaymentFactory(test_db_session).get_or_create_claim()
    import_log = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STANDARD,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.50,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
        amount=10.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.STATE_WITHHOLDING_READY_FOR_PROCESSING)

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
        amount=15.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 1
    )

    # Run the step
    related_withholding_payment_step.run()

    state_log_counts = state_log_util.get_state_counts(test_db_session)

    # Expect same results as before running step
    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 1
    )


def test_withholding_payment_methods1(related_withholding_payment_step, test_db_session):

    claim = DelegatedPaymentFactory(test_db_session).get_or_create_claim()
    import_log = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STANDARD,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.50,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STANDARD,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.50,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
        amount=10.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.STATE_WITHHOLDING_READY_FOR_PROCESSING)

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STATE_TAX_WITHHOLDING,
        amount=10.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.STATE_WITHHOLDING_READY_FOR_PROCESSING)

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
        amount=15.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING)

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
        amount=15.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 2

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 2

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 2
    )

    # Run the step
    federal_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING,
        db_session=test_db_session,
    )
    state_state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.STATE_WITHHOLDING_READY_FOR_PROCESSING,
        db_session=test_db_session,
    )

    payment_container = []
    for federal_state_log in federal_state_logs:
        payment_container.append(federal_state_log.payment)

    for state_state_log in state_state_logs:
        payment_container.append(state_state_log.payment)

    for payment in payment_container:

        if payment.claim is None:
            raise Exception("Claim not found for withholding payment id: %s ", payment.payment_id)

        primary_payment_records: List[Payment] = (
            test_db_session.query(Payment)
            .filter(Payment.claim_id == payment.claim_id)
            .filter(Payment.period_start_date == payment.period_start_date)
            .filter(Payment.period_end_date == payment.period_end_date)
            .filter(Payment.payment_date == payment.payment_date)
            .filter(
                Payment.payment_transaction_type_id
                == PaymentTransactionType.STANDARD.payment_transaction_type_id
            )
            .filter(Payment.fineos_extract_import_log_id == payment.fineos_extract_import_log_id)
            .all()
        )
        if len(primary_payment_records) > 1:

            end_state = (
                State.STATE_WITHHOLDING_PENDING_AUDIT
                if (
                    payment.payment_transaction_type_id
                    == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                )
                else State.FEDERAL_WITHHOLDING_PENDING_AUDIT
            )
            message = "Duplicate records found for the payment."

            state_log_util.create_finished_state_log(
                end_state=end_state,
                outcome=state_log_util.build_outcome(message),
                associated_model=payment,
                db_session=test_db_session,
            )

            message = "Duplicate primay payment records found for the withholding record."
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
                outcome=state_log_util.build_outcome(message),
                associated_model=payment,
                db_session=test_db_session,
            )
            import_log1 = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()
            writeback_details = FineosWritebackDetails(
                payment=payment,
                transaction_status_id=FineosWritebackTransactionStatus.WITHHOLDING_ERROR.transaction_status_id,
                import_log_id=import_log1.import_log_id,
            )
            test_db_session.add(writeback_details)
        else:
            primary_payment_record = primary_payment_records[0].payment_id
            if primary_payment_record == "":
                raise Exception(
                    f"Primary payment id not found for withholding payment id: {payment.payment_id}"
                )

            #  if primary is in error state set withholding in error and don't enter in link table.
            payment_id = primary_payment_record
            related_payment_id = payment.payment_id
            link_payment = LinkSplitPayment()
            link_payment.payment_id = payment_id
            link_payment.related_payment_id = related_payment_id
            test_db_session.add(link_payment)

            #  If primary payment is has any validation error set withholidng state to error
            payment_state_log: Optional[StateLog] = state_log_util.get_latest_state_log_in_flow(
                primary_payment_records[0], Flow.DELEGATED_PAYMENT, test_db_session
            )
            if payment_state_log is None:
                raise Exception(
                    "State log record not found for the primary payment id: %s",
                    primary_payment_records[0].payment_id,
                )
            if (
                payment_state_log.end_state_id
                != State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_id
            ):
                end_state = (
                    State.STATE_WITHHOLDING_ERROR
                    if (
                        payment.payment_transaction_type_id
                        == PaymentTransactionType.STATE_TAX_WITHHOLDING.payment_transaction_type_id
                    )
                    else State.FEDERAL_WITHHOLDING_ERROR
                )
                outcome = state_log_util.build_outcome("Primay payment has an error")
                state_log_util.create_finished_state_log(
                    associated_model=payment,
                    end_state=end_state,
                    outcome=outcome,
                    db_session=test_db_session,
                )
                message = "Duplicate primay payment records found for the withholding record."
                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
                    outcome=state_log_util.build_outcome(message),
                    associated_model=payment,
                    db_session=test_db_session,
                )
                import_log2 = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()
                writeback_details = FineosWritebackDetails(
                    payment=payment,
                    transaction_status_id=FineosWritebackTransactionStatus.WITHHOLDING_ERROR.transaction_status_id,
                    import_log_id=import_log2.import_log_id,
                )
                test_db_session.add(writeback_details)

    state_log_counts = state_log_util.get_state_counts(test_db_session)
    for sc in state_log_counts:
        print(sc)

    assert state_log_counts[State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_description] == 4

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 2
    )
