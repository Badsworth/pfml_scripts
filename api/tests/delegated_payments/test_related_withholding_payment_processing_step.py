import datetime

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_fineos_related_payment_processing as withholding_payments_process
from massgov.pfml.db.models.employees import PaymentTransactionType, State
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus
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

    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 1
    )


def test_withholding_payments_without_primary_payment(
    related_withholding_payment_step, test_db_session
):

    claim = DelegatedPaymentFactory(test_db_session).get_or_create_claim()
    import_log = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()

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

    # Get the counts after running
    related_withholding_payment_step.run()

    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT.state_description] == 1

    assert state_log_counts[State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT.state_description] == 1


def test_withholding_payments_with_multiple_primary_payment(
    related_withholding_payment_step, test_db_session
):

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
        payment_transaction_type=PaymentTransactionType.FEDERAL_TAX_WITHHOLDING,
        amount=15.50,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 2
    )

    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    # Run the step
    related_withholding_payment_step.run()

    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.STATE_WITHHOLDING_ORPHANED_PENDING_AUDIT.state_description] == 1

    assert state_log_counts[State.FEDERAL_WITHHOLDING_ORPHANED_PENDING_AUDIT.state_description] == 1


def test_withholding_payments_with_restartable_primary_payment(
    related_withholding_payment_step, test_db_session
):

    claim = DelegatedPaymentFactory(test_db_session).get_or_create_claim()
    import_log = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()

    payment = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STANDARD,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.50,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE
    )

    DelegatedPaymentFactory(test_db_session, payment=payment).get_or_create_payment_with_writeback(
        FineosWritebackTransactionStatus.BANK_PROCESSING_ERROR
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

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT_RESTARTABLE.state_description
        ]
        == 1
    )

    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    # Run the step
    withholding_payments_process.RelatedPaymentsProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    ).run()

    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.STATE_WITHHOLDING_ERROR_RESTARTABLE.state_description] == 1

    assert state_log_counts[State.FEDERAL_WITHHOLDING_ERROR_RESTARTABLE.state_description] == 1


def test_withholding_payments_with_non_restartable_primary_payment(
    related_withholding_payment_step, test_db_session
):

    claim = DelegatedPaymentFactory(test_db_session).get_or_create_claim()
    import_log = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()

    payment = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.STANDARD,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
        amount=100.50,
    ).get_or_create_payment_with_state(State.PAYMENT_FAILED_ADDRESS_VALIDATION)

    DelegatedPaymentFactory(test_db_session, payment=payment).get_or_create_payment_with_writeback(
        FineosWritebackTransactionStatus.ADDRESS_VALIDATION_ERROR
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

    assert state_log_counts[State.PAYMENT_FAILED_ADDRESS_VALIDATION.state_description] == 1

    assert state_log_counts[State.FEDERAL_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    assert state_log_counts[State.STATE_WITHHOLDING_READY_FOR_PROCESSING.state_description] == 1

    # Run the step
    withholding_payments_process.RelatedPaymentsProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_session
    ).run()
    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert state_log_counts[State.STATE_WITHHOLDING_ERROR.state_description] == 1

    assert state_log_counts[State.FEDERAL_WITHHOLDING_ERROR.state_description] == 1


def test_employer_reimbursement_payment(
    related_withholding_payment_step, test_db_session, monkeypatch
):
    monkeypatch.setenv("ENABLE_EMPLOYER_REIMBURSEMENT_PAYMENTS", "1")
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
        amount=500,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
        amount=350,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert (
        state_log_counts[State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING.state_description] == 1
    )

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 1
    )

    # Run the step
    related_withholding_payment_step.run()

    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert (
        state_log_counts[State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING.state_description] == 1
    )

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 1
    )


def test_employer_reimbursement_payment_without_primary_payment(
    related_withholding_payment_step, test_db_session, monkeypatch
):
    monkeypatch.setenv("ENABLE_EMPLOYER_REIMBURSEMENT_PAYMENTS", "1")
    claim = DelegatedPaymentFactory(test_db_session).get_or_create_claim()
    import_log = DelegatedPaymentFactory(test_db_session).get_or_create_import_log()

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
        amount=350,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert (
        state_log_counts[State.EMPLOYER_REIMBURSEMENT_READY_FOR_PROCESSING.state_description] == 1
    )

    # Run the step
    related_withholding_payment_step.run()

    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)

    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 1
    )


def test_sync_primary_to_related_payments(
    related_withholding_payment_step, test_db_session, monkeypatch
):
    monkeypatch.setenv("ENABLE_EMPLOYER_REIMBURSEMENT_PAYMENTS", "1")
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
        amount=500,
    ).get_or_create_payment_with_state(
        State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
    )

    DelegatedPaymentFactory(
        test_db_session,
        claim=claim,
        import_log=import_log,
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
        amount=350,
        period_start_date=datetime.date(2021, 3, 17),
        period_end_date=datetime.date(2021, 3, 24),
        payment_date=datetime.date(2021, 3, 25),
    ).get_or_create_payment_with_state(State.PAYMENT_FAILED_ADDRESS_VALIDATION)

    test_db_session.commit()

    # Get the counts before running
    state_log_counts = state_log_util.get_state_counts(test_db_session)
    assert (
        state_log_counts[
            State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING.state_description
        ]
        == 1
    )

    assert state_log_counts[State.PAYMENT_FAILED_ADDRESS_VALIDATION.state_description] == 1
    # Run the step
    related_withholding_payment_step.run()

    # Get the counts after running
    state_log_counts = state_log_util.get_state_counts(test_db_session)
    assert state_log_counts[State.DELEGATED_PAYMENT_CASCADED_ERROR.state_description] == 1

    assert state_log_counts[State.PAYMENT_FAILED_ADDRESS_VALIDATION.state_description] == 1
