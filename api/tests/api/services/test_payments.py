import logging  # noqa: B1
from datetime import date
from decimal import Decimal

import pytest
from freezegun.api import freeze_time
from sqlalchemy.sql.expression import null

import massgov.pfml.api.services.payments as payment_services
from massgov.pfml.api.services.payments_services_util import WRITEBACK_SCENARIOS_MAPPER
from massgov.pfml.db.models.employees import PaymentMethod, PaymentTransactionType
from massgov.pfml.db.models.factories import ImportLogFactory, PaymentFactory
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus
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
        disb_method_id=PaymentMethod.ACH.payment_method_id,
    )

    assert import_log_2.import_log_id > import_log_1.import_log_id

    payment_containers, legacy_containers = payment_services.get_payments_from_db(
        test_db_session, claim.claim_id
    )

    assert len(payment_containers) == 1
    assert payment_containers[0].payment.payment_id == payment2.payment_id
    assert payment_containers[0].payment.fineos_extract_import_log == import_log_2
    assert payment_containers[0].payment.fineos_pei_i_value == "9999"

    assert len(legacy_containers) == 0


def test_get_payments_from_db_filters_payments_with_flag(test_db_session):
    import_log_1 = ImportLogFactory.create()
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_pei_i_value="1000",
        fineos_extract_import_log_id=import_log_1.import_log_id,
        payment_method=PaymentMethod.ACH,
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
        disb_method_id=PaymentMethod.ACH.payment_method_id,
    )

    payment_containers, legacy_containers = payment_services.get_payments_from_db(
        test_db_session, claim.claim_id
    )
    assert len(payment_containers) == 1
    assert len(legacy_containers) == 0

    assert payment_containers[0].payment.payment_id == payment.payment_id
    assert payment_containers[0].payment.fineos_extract_import_log_id == import_log_1.import_log_id
    assert payment_containers[0].payment.fineos_pei_i_value == "1000"


def test_get_payments_from_db_allows_multiple_pei_i_values(test_db_session):
    import_log_1 = ImportLogFactory.create()
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        fineos_extract_import_log_id=import_log_1.import_log_id,
        fineos_pei_i_value="2000",
        payment_method=PaymentMethod.ACH,
    )
    claim = payment_factory.get_or_create_claim()
    payment = payment_factory.get_or_create_payment()

    import_log_2 = ImportLogFactory.create()
    payment2 = PaymentFactory.create(
        claim=claim,
        fineos_extract_import_log=import_log_2,
        fineos_pei_i_value="1000",
        payment_transaction_type=payment.payment_transaction_type,
        disb_method_id=PaymentMethod.ACH.payment_method_id,
    )

    payment_containers, legacy_containers = payment_services.get_payments_from_db(
        test_db_session, claim.claim_id
    )

    assert len(payment_containers) == 2
    assert len(legacy_containers) == 0

    assert payment_containers[0].payment.payment_id == payment2.payment_id
    assert payment_containers[0].payment.fineos_extract_import_log == import_log_2
    assert payment_containers[0].payment.fineos_pei_i_value == "1000"

    assert payment_containers[1].payment.payment_id == payment.payment_id
    assert payment_containers[1].payment.fineos_extract_import_log == import_log_1
    assert payment_containers[1].payment.fineos_pei_i_value == "2000"


def test_get_payments_from_db_legacy_payments_separated(test_db_session):
    payment_factory = DelegatedPaymentFactory(test_db_session, payment_method=PaymentMethod.ACH)
    claim = payment_factory.get_or_create_claim()
    payment_pub = payment_factory.get_or_create_payment()

    legacy_payment_factory = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,  # Same claim
        payment_transaction_type=PaymentTransactionType.STANDARD_LEGACY_MMARS,
        payment_method=PaymentMethod.ACH,
    )
    payment_legacy = legacy_payment_factory.get_or_create_payment()

    payment_containers, legacy_containers = payment_services.get_payments_from_db(
        test_db_session, claim.claim_id
    )

    assert len(payment_containers) == 1
    assert len(legacy_containers) == 1

    assert payment_containers[0].payment.payment_id == payment_pub.payment_id
    assert legacy_containers[0].payment.payment_id == payment_legacy.payment_id


def test_consolidate_successors_simple(test_db_session):
    # Verify this works in the simple case. A few payments
    # without any overlapping pay periods.

    payment_containers = []
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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
        test_db_session,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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
        payment_method=PaymentMethod.ACH,
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
        payment_method=PaymentMethod.ACH,
    )

    payment_factory2 = DelegatedPaymentFactory(
        test_db_session,
        claim=payment_factory1.claim,
        employee=payment_factory1.employee,
        amount=Decimal("300.00"),
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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
        test_db_session,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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
        test_db_session,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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
        payment_method=PaymentMethod.ACH,
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
        test_db_session,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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
        test_db_session,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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
        payment_method=PaymentMethod.ACH,
    )

    payment_factory2 = DelegatedPaymentFactory(
        test_db_session,
        claim=payment_factory1.claim,
        employee=payment_factory1.employee,
        amount=Decimal("300.00"),
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
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


def test_sort_amount_by_sign_then_magnitude():

    # Helper class for clearer testing
    class Item:
        def __init__(self, amount):
            self.amount = amount

        def __eq__(self, other):
            return self.amount == other.amount

    itemList = [Item(2), Item(1), Item(0), Item(-1), Item(-2)]

    itemList.sort(key=payment_services.sort_amount_by_sign_then_magnitude)
    assert itemList == [Item(-1), Item(-2), Item(0), Item(1), Item(2)]

    itemList.sort(key=payment_services.sort_amount_by_sign_then_magnitude, reverse=True)
    assert itemList == [Item(2), Item(1), Item(0), Item(-2), Item(-1)]


class TestGetPaymentDetailsAndLines:
    @pytest.fixture
    def claim_with_multiple_details(self, test_db_session):
        payment_factory = DelegatedPaymentFactory(
            test_db_session,
            amount=100,
            period_start_date=date(2021, 11, 1),
            period_end_date=date(2021, 11, 7),
            payment_method=PaymentMethod.ACH,
        )
        claim = payment_factory.get_or_create_claim()
        payment_factory.get_or_create_payment()

        payment_details_1 = payment_factory.create_payment_detail(
            amount=25, period_start_date=date(2021, 3, 1), business_net_amount=30
        )
        payment_factory.create_payment_line(payment_detail=payment_details_1, amount=25)
        payment_factory.create_payment_detail(
            amount=75, period_start_date=date(2021, 1, 1), business_net_amount=80
        )

        return claim

    @pytest.fixture
    def claim_with_multiple_lines(self, test_db_session):
        payment_factory = DelegatedPaymentFactory(
            test_db_session,
            amount=200,
            period_start_date=date(2020, 11, 1),
            period_end_date=date(2020, 11, 7),
            payment_method=PaymentMethod.ACH,
        )
        payment_factory.get_or_create_payment()
        claim = payment_factory.get_or_create_claim()

        payment_details = payment_factory.create_payment_detail(amount=100)
        payment_factory.create_payment_line(
            payment_detail=payment_details, amount=50, line_type="Positive Adjustment"
        )
        payment_factory.create_payment_line(
            payment_detail=payment_details, amount=-15, line_type="State Income Tax"
        )
        payment_factory.create_payment_line(
            payment_detail=payment_details, amount=-25, line_type="FIT Amount"
        )
        payment_factory.create_payment_line(
            payment_detail=payment_details, amount=-35, line_type="Maximum Threshold Adjustment"
        )
        payment_factory.create_payment_line(
            payment_detail=payment_details, amount=125, line_type="Auto Gross Entitlement"
        )

        return claim

    def test_multiple_details(self, test_db_session, claim_with_multiple_details):
        claim_response = payment_services.get_payments_with_status(
            test_db_session, claim_with_multiple_details
        )
        assert len(claim_response["payments"]) == 1
        assert len(claim_response["payments"][0]["payment_details"]) == 2
        assert len(claim_response["payments"][0]["payment_details"][0]["payment_lines"]) == 0
        assert len(claim_response["payments"][0]["payment_details"][1]["payment_lines"]) == 1

    def test_multiple_details_sort_order(self, test_db_session, claim_with_multiple_details):
        claim_response = payment_services.get_payments_with_status(
            test_db_session, claim_with_multiple_details
        )
        assert claim_response["payments"][0]["payment_details"][0]["net_amount"] == 75
        assert claim_response["payments"][0]["payment_details"][1]["net_amount"] == 25

    def test_multiple_details_gross_amount(self, test_db_session, claim_with_multiple_details):
        claim_response = payment_services.get_payments_with_status(
            test_db_session, claim_with_multiple_details
        )
        assert claim_response["payments"][0]["payment_details"][0]["gross_amount"] == 80
        assert claim_response["payments"][0]["payment_details"][1]["gross_amount"] == 30

    def test_multiple_details_associated_with_correct_payment_lines(
        self, test_db_session, claim_with_multiple_details
    ):
        claim_response = payment_services.get_payments_with_status(
            test_db_session, claim_with_multiple_details
        )
        assert (
            claim_response["payments"][0]["payment_details"][1]["payment_lines"][0]["amount"] == 25
        )

    def test_multiple_lines(self, test_db_session, claim_with_multiple_lines):
        claim_response = payment_services.get_payments_with_status(
            test_db_session, claim_with_multiple_lines
        )
        assert len(claim_response["payments"]) == 1
        assert len(claim_response["payments"][0]["payment_details"]) == 1
        assert len(claim_response["payments"][0]["payment_details"][0]["payment_lines"]) == 4

    def test_multiple_lines_sort_order(self, test_db_session, claim_with_multiple_lines):
        claim_response = payment_services.get_payments_with_status(
            test_db_session, claim_with_multiple_lines
        )
        payment_lines = claim_response["payments"][0]["payment_details"][0]["payment_lines"]

        assert payment_lines[1]["amount"] == 50
        assert payment_lines[2]["amount"] == -25
        assert payment_lines[3]["amount"] == -15

    def test_multiple_lines_combined_age_and_mta(self, test_db_session, claim_with_multiple_lines):
        claim_response = payment_services.get_payments_with_status(
            test_db_session, claim_with_multiple_lines
        )
        payment_lines = claim_response["payments"][0]["payment_details"][0]["payment_lines"]

        # Confirm that Auto Gross Entitlement and Max Threshold Adjustment are combined
        assert payment_lines[0]["line_type"] == "Auto Gross Entitlement"
        assert payment_lines[0]["amount"] == 125 + -35


def test_get_payments_with_status(test_db_session, caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    # Create a reiussed payment
    payment_factory1 = DelegatedPaymentFactory(
        test_db_session,
        amount=100,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
    )
    claim = payment_factory1.get_or_create_claim()

    payment1 = payment_factory1.get_or_create_payment()
    payment1_cancellation, payment1_successor = payment_factory1.create_reissued_payments(
        writeback_transaction_status=FineosWritebackTransactionStatus.PAYMENT_AUDIT_IN_PROGRESS
    )

    # Create two payments in a later pay period
    payment2a = payment_factory1.create_related_payment(
        weeks_later=1,
        amount=200,
        writeback_transaction_status=FineosWritebackTransactionStatus.PAYMENT_AUDIT_IN_PROGRESS,
    )
    payment2b = payment_factory1.create_related_payment(
        weeks_later=1,
        amount=300,
        writeback_transaction_status=FineosWritebackTransactionStatus.PAYMENT_AUDIT_IN_PROGRESS,
    )

    # Create a payment that is just cancelled (but in its own week, so returned)
    payment3 = payment_factory1.create_related_payment(weeks_later=2, amount=400)
    payment3_cancellation = payment_factory1.create_cancellation_payment(
        reissuing_payment=payment3, weeks_later=2
    )

    expected_valid_payments = [payment1_successor, payment2a, payment2b, payment3]
    filtered_payments = [payment1, payment1_cancellation, payment3_cancellation]

    payment_response = payment_services.get_payments_with_status(test_db_session, claim)

    log_dict = caplog.records[0].__dict__
    assert len(payment_response["payments"]) == len(expected_valid_payments)
    for i, expected_payment in enumerate(expected_valid_payments):
        resp_payment = payment_response["payments"][i]

        assert resp_payment["payment_id"] == expected_payment.payment_id
        assert resp_payment["period_start_date"] == expected_payment.period_start_date
        assert resp_payment["period_end_date"] == expected_payment.period_end_date

        assert log_dict[f"payment[{i}].id"] == expected_payment.payment_id
        assert log_dict[f"payment[{i}].c_value"] == expected_payment.fineos_pei_c_value
        assert log_dict[f"payment[{i}].i_value"] == expected_payment.fineos_pei_i_value
        assert (
            log_dict[f"payment[{i}].period_start_date"]
            == expected_payment.period_start_date.isoformat()
        )
        assert (
            log_dict[f"payment[{i}].period_end_date"]
            == expected_payment.period_end_date.isoformat()
        )
        assert (
            log_dict[f"payment[{i}].payment_type"]
            == expected_payment.payment_transaction_type.payment_transaction_type_description
        )
        if i != 3:
            assert (
                log_dict[f"payment[{i}].writeback_transaction_status"]
                == FineosWritebackTransactionStatus.PAYMENT_AUDIT_IN_PROGRESS.transaction_status_description
            )
            assert log_dict[f"payment[{i}].transaction_date"] is None  # Wasn't sent
            assert log_dict[f"payment[{i}].transaction_date_could_change"] is True

        # payment 3 is cancelled, so a few values are different
        if i == 3:
            assert resp_payment["status"] == payment_services.FrontendPaymentStatus.CANCELLED
            assert (
                log_dict[f"payment[{i}].status"]
                == payment_services.FrontendPaymentStatus.CANCELLED.value
            )
            assert (
                log_dict[f"payment[{i}].cancellation_event.c_value"]
                == payment3_cancellation.fineos_pei_c_value
            )
            assert (
                log_dict[f"payment[{i}].cancellation_event.i_value"]
                == payment3_cancellation.fineos_pei_i_value
            )

        else:
            assert resp_payment["status"] == payment_services.FrontendPaymentStatus.PENDING
            assert (
                log_dict[f"payment[{i}].status"]
                == payment_services.FrontendPaymentStatus.PENDING.value
            )

    for i, filtered_payment in enumerate(filtered_payments):

        assert log_dict[f"filtered_payment[{i}].id"] == filtered_payment.payment_id
        assert log_dict[f"filtered_payment[{i}].c_value"] == filtered_payment.fineos_pei_c_value
        assert log_dict[f"filtered_payment[{i}].i_value"] == filtered_payment.fineos_pei_i_value
        assert (
            log_dict[f"filtered_payment[{i}].period_start_date"]
            == filtered_payment.period_start_date.isoformat()
        )
        assert (
            log_dict[f"filtered_payment[{i}].period_end_date"]
            == filtered_payment.period_end_date.isoformat()
        )
        assert (
            log_dict[f"filtered_payment[{i}].payment_type"]
            == filtered_payment.payment_transaction_type.payment_transaction_type_description
        )

        # Payment 1 was succeeded
        if i == 0:
            assert (
                log_dict[f"filtered_payment[{i}].filter_reason"]
                == payment_services.PaymentFilterReason.HAS_SUCCESSOR
            )
            assert (
                log_dict[f"filtered_payment[{i}].successor[0].c_value"]
                == payment1_successor.fineos_pei_c_value
            )
            assert (
                log_dict[f"filtered_payment[{i}].successor[0].i_value"]
                == payment1_successor.fineos_pei_i_value
            )

        # Cancellation for Payment 1
        if i == 1:
            assert (
                log_dict[f"filtered_payment[{i}].filter_reason"]
                == payment_services.PaymentFilterReason.CANCELLATION_EVENT
            )
            assert log_dict[f"filtered_payment[{i}].cancels.c_value"] == payment1.fineos_pei_c_value
            assert log_dict[f"filtered_payment[{i}].cancels.i_value"] == payment1.fineos_pei_i_value

        # Cancellation for payment 3
        if i == 2:
            assert (
                log_dict[f"filtered_payment[{i}].filter_reason"]
                == payment_services.PaymentFilterReason.CANCELLATION_EVENT
            )
            assert log_dict[f"filtered_payment[{i}].cancels.c_value"] == payment3.fineos_pei_c_value
            assert log_dict[f"filtered_payment[{i}].cancels.i_value"] == payment3.fineos_pei_i_value

    assert log_dict["payments_returned_count"] == 4
    assert log_dict["payments_filtered_count"] == 3

    assert log_dict["payment_status_delayed_count"] == 0
    assert log_dict["payment_status_pending_count"] == 3
    assert log_dict["payment_status_sent_to_bank_count"] == 0
    assert log_dict["payment_status_cancelled_count"] == 1

    assert log_dict["payment_filtered_has_successor_count"] == 1
    assert log_dict["payment_filtered_cancellation_event_count"] == 2
    assert log_dict["payment_filtered_unknown_count"] == 0


@freeze_time("2021-12-09 12:00:00", tz_offset=5)
def test_get_payments_with_legacy_and_regular(test_db_session):
    # Create a reiussed payment for the regular one
    payment_factory = DelegatedPaymentFactory(
        test_db_session,
        amount=100,
        period_start_date=date(2021, 11, 1),
        period_end_date=date(2021, 11, 7),
        payment_method=PaymentMethod.ACH,
    )
    claim = payment_factory.get_or_create_claim()

    payment_factory.get_or_create_payment()
    _, payment_successor = payment_factory.create_reissued_payments(
        writeback_transaction_status=FineosWritebackTransactionStatus.PAYMENT_AUDIT_IN_PROGRESS
    )

    # Create a legacy payment
    legacy_send_date = date(2021, 6, 14)
    legacy_payment_factory = DelegatedPaymentFactory(
        test_db_session,
        claim=claim,  # Same claim
        payment_transaction_type=PaymentTransactionType.STANDARD_LEGACY_MMARS,
        payment_method=PaymentMethod.ACH,
        disb_check_eft_issue_date=legacy_send_date,
    )

    legacy_payment = legacy_payment_factory.get_or_create_payment()

    payment_response = payment_services.get_payments_with_status(test_db_session, claim)

    assert len(payment_response["payments"]) == 2
    validate_payment_matches(
        payment_response["payments"][0],
        payment_successor,
        status="Pending",
        expected_send_date_start=date(2021, 12, 10),
        expected_send_date_end=date(2021, 12, 12),
    )
    validate_payment_matches(
        payment_response["payments"][1],
        legacy_payment,
        status="Sent to bank",
        has_amount=True,
        sent_to_bank_date=legacy_send_date,
        expected_send_date_start=legacy_send_date,
        expected_send_date_end=legacy_send_date,
    )


def test_writeback_statuses_configured():
    """
    This test just validates that any new writebacks created are
    configured in the payment status endpoint. If you're seeing this
    test fail, and added a new writeback, you'll need to configure it.

    Likely, you've added a new error scenario, and setting the status
    to "delayed" is likely fine. If the status is a more granular version
    of an older status, consider using that one.
    """
    writeback_statuses = FineosWritebackTransactionStatus.get_all()

    unconfigured_writeback_statuses = []
    for writeback_status in writeback_statuses:
        if writeback_status.transaction_status_id not in WRITEBACK_SCENARIOS_MAPPER:
            unconfigured_writeback_statuses.append(writeback_status.transaction_status_description)

    assert (
        len(unconfigured_writeback_statuses) == 0
    ), f"The following writeback statuses need to be configured in api/massgov/pfml/api/services/payments.py::WRITEBACK_SCENARIOS: {unconfigured_writeback_statuses}"

    transaction_status_ids = set()
    for writeback_status in writeback_statuses:
        assert (
            writeback_status.transaction_status_id not in transaction_status_ids
        ), f"Writeback transaction status ID {writeback_status.transaction_status_id} is configured for two separate writeback statuses"
        transaction_status_ids.add(writeback_status.transaction_status_id)


def validate_payment_matches(
    payment_response,
    expected_payment,
    status,
    has_amount=False,
    sent_to_bank_date=None,
    expected_send_date_start=None,
    expected_send_date_end=None,
):
    # These fields never vary and are just passed through from the payment itself
    assert payment_response["payment_id"] == expected_payment.payment_id
    assert payment_response["period_start_date"] == expected_payment.period_start_date
    assert payment_response["period_end_date"] == expected_payment.period_end_date
    assert (
        payment_response["payment_method"]
        == expected_payment.disb_method.payment_method_description
    )

    # These fields vary based on different scenarios of the payment
    assert payment_response["status"] == status

    if sent_to_bank_date:
        assert payment_response["sent_to_bank_date"] == sent_to_bank_date
    else:
        assert payment_response["sent_to_bank_date"] is None

    if expected_send_date_start:
        assert payment_response["expected_send_date_start"] == expected_send_date_start
    else:
        assert payment_response["expected_send_date_start"] is None

    if expected_send_date_end:
        assert payment_response["expected_send_date_end"] == expected_send_date_end
    else:
        assert payment_response["expected_send_date_end"] is None

    if has_amount:
        assert payment_response["amount"] == expected_payment.amount
    else:
        assert payment_response["amount"] is None
