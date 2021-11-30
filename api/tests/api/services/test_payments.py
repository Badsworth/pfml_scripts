from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.sql.expression import null

import massgov.pfml.api.services.payments as payment_services
from massgov.pfml.db.models.employees import PaymentTransactionType
from massgov.pfml.db.models.factories import ImportLogFactory, PaymentFactory
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory


# Run `initialize_factories_session` for all tests,
# so that it doesn't need to be manually included
@pytest.fixture(autouse=True)
def setup_factories(initialize_factories_session):
    return


def test_get_payments_from_db_dedups_pei_i_value(test_db_session):
    import_log_1 = ImportLogFactory.create()
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_extract_import_log_id=import_log_1.import_log_id,
        fineos_pei_i_value="9999",
    )
    claim = payment_factory.get_or_create_claim()
    payment = payment_factory.get_or_create_payment()

    import_log_2 = ImportLogFactory.create()
    payment2 = PaymentFactory.create(
        claim=claim,
        fineos_extract_import_log=import_log_2,
        fineos_pei_i_value="9999",
        payment_transaction_type=payment.payment_transaction_type,
    )

    assert import_log_2.import_log_id > import_log_1.import_log_id

    payment_containers = payment_services.get_payments_from_db(test_db_session, claim.claim_id)

    assert len(payment_containers) == 1
    assert payment_containers[0].payment.payment_id == payment2.payment_id
    assert payment_containers[0].payment.fineos_extract_import_log == import_log_2
    assert payment_containers[0].payment.fineos_pei_i_value == "9999"


def test_get_payments_from_db_filters_payments_with_flag(test_db_session):
    import_log_1 = ImportLogFactory.create()
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_pei_i_value="1000",
        fineos_extract_import_log_id=import_log_1.import_log_id,
    )
    claim = payment_factory.get_or_create_claim()
    payment = payment_factory.get_or_create_payment()

    import_log_2 = ImportLogFactory.create()

    assert import_log_2.import_log_id > import_log_1.import_log_id

    # This payment has a higher import log id
    # with a matching i value but won't be returned by
    # the query because exclude_from_payment_status is True
    PaymentFactory.create(
        claim=claim,
        fineos_extract_import_log=import_log_2,
        fineos_pei_i_value="1000",
        payment_transaction_type=payment.payment_transaction_type,
        exclude_from_payment_status=True,
    )

    payment_containers = payment_services.get_payments_from_db(test_db_session, claim.claim_id)
    assert len(payment_containers) == 1

    assert payment_containers[0].payment.payment_id == payment.payment_id
    assert payment_containers[0].payment.fineos_extract_import_log_id == import_log_1.import_log_id
    assert payment_containers[0].payment.fineos_pei_i_value == "1000"


def test_get_payments_from_db_allows_multiple_pei_i_values(test_db_session):
    import_log_1 = ImportLogFactory.create()
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_extract_import_log_id=import_log_1.import_log_id,
        fineos_pei_i_value="2000",
    )
    claim = payment_factory.get_or_create_claim()
    payment = payment_factory.get_or_create_payment()

    import_log_2 = ImportLogFactory.create()
    payment2 = PaymentFactory.create(
        claim=claim,
        fineos_extract_import_log=import_log_2,
        fineos_pei_i_value="1000",
        payment_transaction_type=payment.payment_transaction_type,
    )

    payment_containers = payment_services.get_payments_from_db(test_db_session, claim.claim_id)

    assert len(payment_containers) == 2

    assert payment_containers[0].payment.payment_id == payment2.payment_id
    assert payment_containers[0].payment.fineos_extract_import_log == import_log_2
    assert payment_containers[0].payment.fineos_pei_i_value == "1000"

    assert payment_containers[1].payment.payment_id == payment.payment_id
    assert payment_containers[1].payment.fineos_extract_import_log == import_log_1
    assert payment_containers[1].payment.fineos_pei_i_value == "2000"


def test_consolidate_successors_simple(test_db_session):
    # Verify this works in the simple case. A few payments
    # without any overlapping pay periods.

    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session, period_start_date=date(2021, 11, 1), period_end_date=date(2021, 11, 7)
    )

    payment_containers.append(
        payment_services.PaymentContainer(payment_factory.get_or_create_payment())
    )
    payment_containers.append(
        payment_services.PaymentContainer(payment_factory.create_related_payment(weeks_later=1))
    )
    payment_containers.append(
        payment_services.PaymentContainer(payment_factory.create_related_payment(weeks_later=2))
    )

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)
    consolidated_payment_containers.sort()

    # Nothing is filtered, we just end up with what we sent in
    # Nothing is filtered, we just end up with what we sent in
    assert len(consolidated_payment_containers) == 3
    for i in range(3):
        assert (
            payment_containers[i].payment.payment_id
            == consolidated_payment_containers[i].payment.payment_id
        )


def test_consolidate_successors_multiple_payments_in_period(test_db_session):
    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session, period_start_date=date(2021, 11, 1), period_end_date=date(2021, 11, 7)
    )

    # The other payments we create have the same pay period, but all end up in the final list
    payment_containers.append(
        payment_services.PaymentContainer(payment_factory.get_or_create_payment())
    )
    payment_containers.append(
        payment_services.PaymentContainer(payment_factory.create_related_payment(weeks_later=0))
    )
    payment_containers.append(
        payment_services.PaymentContainer(payment_factory.create_related_payment(weeks_later=0))
    )

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)
    consolidated_payment_containers.sort()

    # Nothing is filtered, we just end up with what we sent in
    assert len(consolidated_payment_containers) == 3
    for i in range(3):
        assert (
            payment_containers[i].payment.payment_id
            == consolidated_payment_containers[i].payment.payment_id
        )


def test_consolidate_successors_single_lineage(test_db_session):
    """
    This tests the scenario where a payment gets replaced twice.
    That means we receive the following payment records for it.

    First Batch:
      * Original Payment

    Second Batch:
      * Cancellation of Original Payment
      * Successor Payment

    Third Batch:
      * Cancellation of Successor Payment
      * Another Successor Payment

    Payments in each batch have the same import log ID.
    """
    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        amount=Decimal("500.00"),
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
    )

    # The original payment
    original_payment = payment_factory.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment))

    # Reissue the payments, getting a cancellation and new reduced payment
    original_cancellation, first_successor_payment = payment_factory.create_reissued_payments(
        amount=Decimal("400.00")
    )
    payment_containers.append(payment_services.PaymentContainer(original_cancellation))
    payment_containers.append(payment_services.PaymentContainer(first_successor_payment))

    # Reissue the payments again, with another reduction
    successor_cancellation, final_successor_payment = payment_factory.create_reissued_payments(
        reissuing_payment=first_successor_payment, amount=Decimal("300.00")
    )
    payment_containers.append(payment_services.PaymentContainer(successor_cancellation))
    payment_containers.append(payment_services.PaymentContainer(final_successor_payment))

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)

    # The payment returned is just the final one
    assert len(consolidated_payment_containers) == 1
    assert (
        final_successor_payment.payment_id == consolidated_payment_containers[0].payment.payment_id
    )

    # TODO - validate the lineage created


def test_consolidate_successors_double_lineage(test_db_session):
    """
    Two separate payments, both replaced.

    First Batch:
      * Original Payment1
      * Original Payment2

    Second Batch:
      * Cancellation of Original Payment1
      * Successor Payment1
      * Cancellation of Original Payment2
      * Successor Payment2

    Payments in each batch have the same import log ID.
    """
    payment_containers = []
    payment_factory1 = DelegatedPaymentFactory(
        test_db_session,
        amount=Decimal("500.00"),
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
    )

    payment_factory2 = DelegatedPaymentFactory(
        test_db_session,
        claim=payment_factory1.claim,
        employee=payment_factory1.employee,
        amount=Decimal("300.00"),
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
    )

    # The original payments (Note, they have different import log IDs)
    original_payment1 = payment_factory1.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment1))

    original_payment2 = payment_factory2.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment2))

    # Both originals are replaced
    original_cancellation1, original_successor1 = payment_factory1.create_reissued_payments()
    payment_containers.append(payment_services.PaymentContainer(original_cancellation1))
    payment_containers.append(payment_services.PaymentContainer(original_successor1))
    original_cancellation2, original_successor2 = payment_factory2.create_reissued_payments()
    payment_containers.append(payment_services.PaymentContainer(original_cancellation2))
    payment_containers.append(payment_services.PaymentContainer(original_successor2))

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)
    consolidated_payment_containers.sort()

    # We should have gotten back two separate payments, the successor
    # from each of the two lineages.
    assert len(consolidated_payment_containers) == 2
    assert original_successor1.payment_id == consolidated_payment_containers[0].payment.payment_id
    assert original_successor2.payment_id == consolidated_payment_containers[1].payment.payment_id


def test_consolidate_successors_payments_cancelled(test_db_session):
    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session, period_start_date=date(2021, 11, 1), period_end_date=date(2021, 11, 7),
    )

    # The original payment
    original_payment = payment_factory.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment))

    # Create the cancellation (the reissued payment won't be used for this test)
    original_cancellation = payment_factory.create_cancellation_payment()
    payment_containers.append(payment_services.PaymentContainer(original_cancellation))

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)

    # We should have gotten back a single payment connected to its cancellation
    assert len(consolidated_payment_containers) == 1
    assert original_payment.payment_id == consolidated_payment_containers[0].payment.payment_id

    assert consolidated_payment_containers[0].cancellation_event is not null
    assert (
        original_cancellation.payment_id
        == consolidated_payment_containers[0].cancellation_event.payment.payment_id
    )


def test_consolidate_successors_cancellations_predate_payment(test_db_session):
    # While there are multiple cancellations, they all were
    # sent before the payment in question

    # Will use below, we need an import log earlier
    # than the one made in the payment factory
    import_log_before = ImportLogFactory.create()

    payment_containers = []

    payment_factory = DelegatedPaymentFactory(
        test_db_session, period_start_date=date(2021, 11, 1), period_end_date=date(2021, 11, 7),
    )

    original_payment = payment_factory.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment))

    # Create a few cancellations like the original, but with the earlier import log
    prior_cancellation1 = payment_factory.create_cancellation_payment(import_log=import_log_before)
    prior_cancellation2 = payment_factory.create_cancellation_payment(import_log=import_log_before)
    payment_containers.append(payment_services.PaymentContainer(prior_cancellation1))
    payment_containers.append(payment_services.PaymentContainer(prior_cancellation2))

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)

    assert len(consolidated_payment_containers) == 1
    assert original_payment.payment_id == consolidated_payment_containers[0].payment.payment_id
    assert consolidated_payment_containers[0].cancellation_event is None


def test_consolidate_successors_zero_dollar(test_db_session):
    # Zero dollar payments should be returned if they're
    # the only cancellation-style event

    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_transaction_type=PaymentTransactionType.ZERO_DOLLAR,
    )
    original_payment = payment_factory.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment))

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)

    # The payment returned is a cancelled one
    assert len(consolidated_payment_containers) == 1
    assert original_payment.payment_id == consolidated_payment_containers[0].payment.payment_id
    assert consolidated_payment_containers[0].is_cancelled()


def test_consolidate_successors_zero_dollar_and_regular(test_db_session):
    # Zero dollar payments should be returned if they're
    # the only cancellation-style event, but in this case
    # we also have another regular payment

    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session, period_start_date=date(2021, 11, 1), period_end_date=date(2021, 11, 7)
    )
    original_payment = payment_factory.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment))

    # Add the zero dollar payment
    payment_containers.append(
        payment_services.PaymentContainer(
            payment_factory.create_related_payment(
                payment_transaction_type_id=PaymentTransactionType.ZERO_DOLLAR.payment_transaction_type_id
            )
        )
    )

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)

    # The payment returned is just the regular one
    assert len(consolidated_payment_containers) == 1
    assert original_payment.payment_id == consolidated_payment_containers[0].payment.payment_id
    assert not consolidated_payment_containers[0].is_cancelled()


def test_consolidate_successors_just_cancellation(test_db_session):
    """
    Show that if we just have a cancellation event and no
    regular payments, nothing ends up being returned
    """
    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session, period_start_date=date(2021, 11, 1), period_end_date=date(2021, 11, 7)
    )
    original_cancellation = payment_factory.create_cancellation_payment()
    payment_containers.append(payment_services.PaymentContainer(original_cancellation))
    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)

    assert len(consolidated_payment_containers) == 0


def test_consolidate_successors_cancelled_and_regular(test_db_session):
    # If we have a cancelled payment + uncancelled one, only the
    # uncancelled payment ends up being returned.

    payment_containers = []
    payment_factory1 = DelegatedPaymentFactory(
        test_db_session,
        amount=Decimal("500.00"),
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
    )

    payment_factory2 = DelegatedPaymentFactory(
        test_db_session,
        claim=payment_factory1.claim,
        employee=payment_factory1.employee,
        amount=Decimal("300.00"),
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
    )

    # Setup the two payments
    original_payment1 = payment_factory1.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment1))

    original_payment2 = payment_factory2.get_or_create_payment()
    payment_containers.append(payment_services.PaymentContainer(original_payment2))

    # Cancel just payment1
    original_cancellation1 = payment_factory1.create_cancellation_payment()
    payment_containers.append(payment_services.PaymentContainer(original_cancellation1))

    consolidated_payment_containers = payment_services.consolidate_successors(payment_containers)

    # Only the uncancelled payment is returned
    assert len(consolidated_payment_containers) == 1
    assert original_payment2.payment_id == consolidated_payment_containers[0].payment.payment_id
