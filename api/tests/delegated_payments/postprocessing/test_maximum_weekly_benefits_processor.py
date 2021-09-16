from datetime import date
from decimal import Decimal

import pytest

from massgov.pfml.db.models.employees import PaymentTransactionType
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory
from massgov.pfml.db.models.payments import MaximumWeeklyBenefitAmount
from massgov.pfml.delegated_payments.postprocessing.maximum_weekly_benefits_processor import (
    MaximumWeeklyBenefitsStepProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_step import (
    PaymentPostProcessingStep,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PayPeriodGroup,
)

from . import _create_payment_container


@pytest.fixture
def payment_post_processing_step(
    local_initialize_factories_session,
    local_test_db_session,
    local_test_db_other_session,
    monkeypatch,
):
    return PaymentPostProcessingStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


@pytest.fixture
def maximum_weekly_processor(payment_post_processing_step):
    return MaximumWeeklyBenefitsStepProcessor(payment_post_processing_step)


def validate_payment_success(payment_container):
    assert not payment_container.maximum_weekly_audit_report_msg


def validate_payment_failed(payment_container):
    assert payment_container.maximum_weekly_audit_report_msg


def test_get_maximum_amount_for_week(maximum_weekly_processor, local_test_db_session):
    # manually set the maximum weekly benefit amounts
    # If fetched from the DB they would be in descending order like so

    maximum_amounts = [
        MaximumWeeklyBenefitAmount(date(2021, 3, 1), "300.00"),
        MaximumWeeklyBenefitAmount(date(2021, 2, 1), "200.00"),
        MaximumWeeklyBenefitAmount(date(2021, 1, 1), "100.00"),
    ]
    maximum_weekly_processor.maximum_amount_for_week = maximum_amounts

    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 1, 1)) == Decimal(
        "100.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 1, 15)) == Decimal(
        "100.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 1, 31)) == Decimal(
        "100.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 2, 1)) == Decimal(
        "200.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 2, 2)) == Decimal(
        "200.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 2, 28)) == Decimal(
        "200.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 3, 1)) == Decimal(
        "300.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2021, 6, 25)) == Decimal(
        "300.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_week(date(2031, 1, 1)) == Decimal(
        "300.00"
    )

    # Will error if given a date before the earliest configured date.
    with pytest.raises(Exception, match="No maximum weekly amount configured for 2020-12-31"):
        maximum_weekly_processor._get_maximum_amount_for_week(date(2020, 12, 31))


def test_validate_payments_not_exceeding_cap(maximum_weekly_processor, local_test_db_session):
    # New payments that are being processed
    employee = EmployeeFactory.create()
    payment_container1 = _create_payment_container(
        employee, Decimal("225.00"), local_test_db_session
    )
    payment_container2 = _create_payment_container(
        employee, Decimal("225.00"), local_test_db_session
    )

    # Prior payments already processed
    _create_payment_container(
        employee, Decimal("200.00"), local_test_db_session, has_processed_state=True
    )
    _create_payment_container(
        employee, Decimal("200.00"), local_test_db_session, has_processed_state=True
    )

    # Prior payments that errored/are adhoc and aren't factored into the calculation
    _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, has_errored_state=True
    )
    _create_payment_container(
        employee,
        Decimal("500.00"),
        local_test_db_session,
        has_processed_state=True,
        is_adhoc_payment=True,
    )

    # The cap is configured to 850.00, the two new payments
    # alongside the two previously processed payments sum to exactly this
    containers = [payment_container1, payment_container2]
    maximum_weekly_processor.process(employee, containers)

    for container in containers:
        validate_payment_success(container)


def test_validate_payments_not_exceeding_cap_in_same_claim(
    maximum_weekly_processor, local_test_db_session
):
    employee = EmployeeFactory.create()
    claim = ClaimFactory.create(employee=employee)

    # Any two of these payments would go over the cap
    # but because they're all in the same claim, they
    # all are capable of passing.
    payment_container1 = _create_payment_container(
        employee,
        Decimal("850.00"),
        local_test_db_session,
        start_date=date(2021, 8, 1),  # Sunday
        claim=claim,
    )
    payment_container2 = _create_payment_container(
        employee,
        Decimal("850.00"),
        local_test_db_session,
        start_date=date(2021, 8, 2),  # Monday
        claim=claim,
    )
    payment_container3 = _create_payment_container(
        employee,
        Decimal("850.00"),
        local_test_db_session,
        start_date=date(2021, 8, 3),  # Tuesday
        claim=claim,
    )
    # Also a prior payment for the same claim
    _create_payment_container(
        employee,
        Decimal("850.00"),
        local_test_db_session,
        start_date=date(2021, 8, 1),  # Sunday
        has_processed_state=True,
        claim=claim,
    )

    # These last two payments will cause it to go over
    # the cap because they have a different claim (generated in the method)
    payment_container4 = _create_payment_container(
        employee, Decimal("850.00"), local_test_db_session, start_date=date(2021, 8, 4)  # Wednesday
    )
    payment_container5 = _create_payment_container(
        employee, Decimal("850.00"), local_test_db_session, start_date=date(2021, 8, 5)  # Thursday
    )

    successful_containers = [payment_container1, payment_container2, payment_container3]
    failed_containers = [payment_container4, payment_container5]
    maximum_weekly_processor.process(
        employee, successful_containers + failed_containers,
    )

    for container in successful_containers:
        validate_payment_success(container)

    for container in failed_containers:
        validate_payment_failed(container)


def test_validate_payments_not_exceeding_cap_many_overlap(
    maximum_weekly_processor, local_test_db_session
):
    employee = EmployeeFactory.create()

    # First four payments are all capable of being
    # paid without issue
    payment_container1 = _create_payment_container(
        employee, Decimal("461.54"), local_test_db_session, start_date=date(2021, 6, 22)  # Tuesday
    )
    payment_container2 = _create_payment_container(
        employee, Decimal("461.54"), local_test_db_session, start_date=date(2021, 6, 29)  # Tuesday
    )
    payment_container3 = _create_payment_container(
        employee, Decimal("461.54"), local_test_db_session, start_date=date(2021, 7, 6)  # Tuesday
    )
    payment_container4 = _create_payment_container(
        employee, Decimal("461.54"), local_test_db_session, start_date=date(2021, 7, 13)  # Tuesday
    )

    # These last two payments will cause it to go over
    # the cap because payments above are counted first
    # for the weeks they overlap
    payment_container5 = _create_payment_container(
        employee, Decimal("850.00"), local_test_db_session, start_date=date(2021, 7, 2)  # Saturday
    )
    payment_container6 = _create_payment_container(
        employee, Decimal("850.00"), local_test_db_session, start_date=date(2021, 7, 9)  # Saturday
    )

    successful_containers = [
        payment_container1,
        payment_container2,
        payment_container3,
        payment_container4,
    ]
    failed_containers = [payment_container5, payment_container6]
    maximum_weekly_processor.process(
        employee, successful_containers + failed_containers,
    )

    for container in successful_containers:
        validate_payment_success(container)

    for container in failed_containers:
        validate_payment_failed(container)


def test_validate_payments_not_exceeding_cap_adhoc(maximum_weekly_processor, local_test_db_session):
    employee = EmployeeFactory.create()

    # New payments that are being processed, but are all adhoc
    # Will all be accepted as the validation is skipped for them
    payment_container1 = _create_payment_container(
        employee,
        Decimal("5000.00"),
        local_test_db_session,
        is_adhoc_payment=True,
        start_date=date(2021, 8, 1),  # Sunday
    )
    payment_container2 = _create_payment_container(
        employee,
        Decimal("5000.00"),
        local_test_db_session,
        is_adhoc_payment=True,
        start_date=date(2021, 8, 1),  # Sunday
    )
    # Not adhoc, will still be accepted as they sum to less than the cap
    payment_container3 = _create_payment_container(
        employee,
        Decimal("425.00"),
        local_test_db_session,
        is_adhoc_payment=False,
        start_date=date(2021, 8, 1),  # Sunday
    )
    payment_container4 = _create_payment_container(
        employee,
        Decimal("425.00"),
        local_test_db_session,
        is_adhoc_payment=False,
        start_date=date(2021, 8, 1),  # Sunday
    )

    # Prior adhoc payments don't factor into the calculation either
    _create_payment_container(
        employee,
        Decimal("850.00"),
        local_test_db_session,
        has_processed_state=True,
        is_adhoc_payment=True,
        start_date=date(2021, 8, 1),  # Sunday
    )

    containers = [payment_container1, payment_container2, payment_container3, payment_container4]
    maximum_weekly_processor.process(
        employee, containers,
    )
    for container in containers:
        validate_payment_success(container)


def test_validate_payments_not_exceeding_cap_for_multiweek_payments(
    maximum_weekly_processor, local_test_db_session
):
    # Several 2-week payments that overlap one week each
    # Note the totals shown below are divided evenly to each week
    employee = EmployeeFactory.create()

    # $400.00 a week for 4 weeks
    payment_container1 = _create_payment_container(
        employee,
        Decimal("1600.00"),
        local_test_db_session,
        periods=4,
        start_date=date(2021, 8, 1),  # Sunday
    )

    # $400.00 a week for 4 weeks, overlapping for 2 with the above
    payment_container2 = _create_payment_container(
        employee,
        Decimal("1600.00"),
        local_test_db_session,
        periods=4,
        start_date=date(2021, 8, 15),  # Sunday
    )

    # $400.00 a week for 4 weeks, overlaps the 4th week of the first payment
    # and 3 weeks of the second payment, which causes it to go over the cap and fail
    payment_container3 = _create_payment_container(
        employee,
        Decimal("1600.00"),
        local_test_db_session,
        periods=4,
        start_date=date(2021, 8, 22),  # Sunday
    )

    _create_payment_container(
        employee,
        Decimal("50.00"),
        local_test_db_session,
        start_date=date(2021, 8, 22),  # Sunday
        has_processed_state=True,
    )

    containers = [payment_container1, payment_container2, payment_container3]
    maximum_weekly_processor.process(
        employee, containers,
    )
    validate_payment_success(payment_container1)
    validate_payment_success(payment_container2)
    validate_payment_failed(payment_container3)


def test_validate_payments_not_exceeding_cap_for_overpayments(
    maximum_weekly_processor, local_test_db_session
):
    # Two payments for the same 7-day period
    # that are at the cap on their own, however
    # there is an overpayment that offsets one of them
    # making them both payable without issue.
    employee = EmployeeFactory.create()

    payment_container1 = _create_payment_container(
        employee, Decimal("850.00"), local_test_db_session, start_date=date(2021, 8, 1)  # Sunday
    )

    payment_container2 = _create_payment_container(
        employee, Decimal("850.00"), local_test_db_session, start_date=date(2021, 8, 1)  # Sunday
    )

    _create_payment_container(
        employee,
        Decimal("-850.00"),
        local_test_db_session,
        is_overpayment=True,
        payment_transaction_type=PaymentTransactionType.OVERPAYMENT,
        start_date=date(2021, 8, 1),  # Sunday
    )
    containers = [payment_container1, payment_container2]
    maximum_weekly_processor.process(employee, containers)

    for container in containers:
        validate_payment_success(container)


def test_get_payment_details_per_pay_period_missing_payment_details(
    maximum_weekly_processor, local_test_db_session
):
    employee = EmployeeFactory.create()
    payment_container = _create_payment_container(
        employee, Decimal("225.00"), local_test_db_session, skip_pay_periods=True
    )
    pay_period_group = PayPeriodGroup(
        start_date=payment_container.payment.period_start_date,
        end_date=payment_container.payment.period_end_date,
    )
    with pytest.raises(Exception, match="is missing payment details info which is required."):
        maximum_weekly_processor._get_payment_details_per_pay_period(
            payment_container, [pay_period_group], True
        )


def test_get_payment_details_per_pay_period_not_overlapping_pay_period(
    maximum_weekly_processor, local_test_db_session
):
    # I'm not sure this is even possible with our logic,
    # but in case anything changes that could cause it,
    # this test verifies that all payment periods for a
    # current payment end up in a one of the pay period groups
    employee = EmployeeFactory.create()
    # Payment has two pay periods of 8/1 -> 8/7 and 8/8 -> 8/14
    payment_container = _create_payment_container(
        employee,
        Decimal("225.00"),
        local_test_db_session,
        start_date=date(2021, 8, 1),
        periods=2,
        length_of_period=7,
    )
    # The pay period group only overlaps with the above payment container's first pay period
    pay_period_group = PayPeriodGroup(start_date=date(2021, 8, 1), end_date=date(2021, 8, 7))
    with pytest.raises(Exception, match="only had 1 of 2 payment details map to pay periods"):
        maximum_weekly_processor._get_payment_details_per_pay_period(
            payment_container, [pay_period_group], True
        )


def test_validate_payments_not_exceeding_cap_other_payment_types(
    maximum_weekly_processor, local_test_db_session
):
    employee = EmployeeFactory.create()

    # New payments that are being processed, sum exactly to cap
    # and will be accepted
    payment_container1 = _create_payment_container(
        employee, Decimal("425.00"), local_test_db_session, start_date=date(2021, 8, 1)  # Sunday
    )
    payment_container2 = _create_payment_container(
        employee, Decimal("425.00"), local_test_db_session, start_date=date(2021, 8, 1)  # Sunday
    )

    # Other payments of non-standard types. Despite all of these
    # existing, none of them will have any effect on the above payments
    # being successfully accepted.
    other_payment_types = [
        PaymentTransactionType.ZERO_DOLLAR,
        PaymentTransactionType.CANCELLATION,
        PaymentTransactionType.UNKNOWN,
        PaymentTransactionType.EMPLOYER_REIMBURSEMENT,
    ]
    for payment_type in other_payment_types:
        # Create the payment in various other states for each of them
        _create_payment_container(
            employee,
            Decimal("850.00"),
            local_test_db_session,
            payment_transaction_type=payment_type,
            start_date=date(2021, 8, 1),  # Sunday
        )
        _create_payment_container(
            employee,
            Decimal("850.00"),
            local_test_db_session,
            payment_transaction_type=payment_type,
            has_processed_state=True,
            start_date=date(2021, 8, 1),  # Sunday
        )
        _create_payment_container(
            employee,
            Decimal("850.00"),
            local_test_db_session,
            payment_transaction_type=payment_type,
            has_errored_state=True,
            start_date=date(2021, 8, 1),  # Sunday
        )

    # Run the logic
    maximum_weekly_processor.process(employee, [payment_container1, payment_container2])

    # Both new payments worked without issue, none of the other types
    # caused any sort of interference
    validate_payment_success(payment_container1)
    validate_payment_success(payment_container2)
