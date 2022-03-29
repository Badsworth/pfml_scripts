from datetime import date
from decimal import Decimal

import pytest

from massgov.pfml.db.models.applications import BenefitsMetrics
from massgov.pfml.db.models.employees import PaymentTransactionType
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PayPeriodGroup,
)
from massgov.pfml.delegated_payments.weekly_max.max_weekly_benefit_amount_validation_step import (
    MaxWeeklyBenefitAmountValidationStep,
)
from massgov.pfml.delegated_payments.weekly_max.maximum_weekly_benefits_processor import (
    MaximumWeeklyBenefitsStepProcessor,
)
from tests.delegated_payments.postprocessing import (
    _create_absence_periods,
    _create_payment_container,
)


@pytest.fixture
def max_weekly_benefit_amount_validation_step(
    local_initialize_factories_session, local_test_db_session, local_test_db_other_session
):
    return MaxWeeklyBenefitAmountValidationStep(
        db_session=local_test_db_session, log_entry_db_session=local_test_db_other_session
    )


@pytest.fixture
def maximum_weekly_processor(max_weekly_benefit_amount_validation_step):
    return MaximumWeeklyBenefitsStepProcessor(max_weekly_benefit_amount_validation_step)


def validate_payment_success(payment_container):
    payment_container.get_payment_log_record()
    assert not payment_container.maximum_weekly_audit_report_msg


def validate_payment_failed(payment_container):
    assert payment_container.maximum_weekly_audit_report_msg


def test_get_maximum_amount_for_week(maximum_weekly_processor, local_test_db_session):
    # manually set the maximum weekly benefit amounts
    # If fetched from the DB they would be in descending order like so

    maximum_amounts = [
        BenefitsMetrics(date(2021, 3, 1), "468.75", "300.00"),
        BenefitsMetrics(date(2021, 2, 1), "312.50", "200.00"),
        BenefitsMetrics(date(2021, 1, 1), "156.25", "100.00"),
    ]
    maximum_weekly_processor.benefits_metrics_cache = maximum_amounts

    assert maximum_weekly_processor._get_maximum_amount_for_start_date(date(2021, 1, 1)) == Decimal(
        "100.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(
        date(2021, 1, 15)
    ) == Decimal("100.00")
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(
        date(2021, 1, 31)
    ) == Decimal("100.00")
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(date(2021, 2, 1)) == Decimal(
        "200.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(date(2021, 2, 2)) == Decimal(
        "200.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(
        date(2021, 2, 28)
    ) == Decimal("200.00")
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(date(2021, 3, 1)) == Decimal(
        "300.00"
    )
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(
        date(2021, 6, 25)
    ) == Decimal("300.00")
    assert maximum_weekly_processor._get_maximum_amount_for_start_date(date(2031, 1, 1)) == Decimal(
        "300.00"
    )

    # Will error if given a date before the earliest configured date.
    with pytest.raises(Exception, match="No maximum weekly amount configured for 2020-12-31"):
        maximum_weekly_processor._get_maximum_amount_for_start_date(date(2020, 12, 31))


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

    # The successful containers will work on their own
    maximum_weekly_processor.process(employee, successful_containers)

    for container in successful_containers:
        validate_payment_success(container)

    # But if you run them with another claim, now they all need
    # to meet the rule and they start failing
    maximum_weekly_processor.process(employee, successful_containers + failed_containers)

    for container in successful_containers + failed_containers:
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
    maximum_weekly_processor.process(employee, successful_containers + failed_containers)

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
    maximum_weekly_processor.process(employee, containers)
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
    maximum_weekly_processor.process(employee, containers)
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


def test_validate_payments_not_exceeding_cap_multiple_claims(
    maximum_weekly_processor, local_test_db_session
):
    # This is validating a problem found in https://lwd.atlassian.net/browse/API-2245
    # Before, the logic was letting all payments after
    # the first auto-pass the validation if they were in the
    # same claim + week, which isn't correct.
    employee = EmployeeFactory.create()
    claim1 = ClaimFactory.create(employee=employee)
    claim2 = ClaimFactory.create(employee=employee)

    # Claim 1
    _create_payment_container(
        employee,
        Decimal("100.00"),
        local_test_db_session,
        has_processed_state=True,
        claim=claim1,
        start_date=date(2021, 12, 19),
        length_of_period=1,
    )

    payment_container1 = _create_payment_container(
        employee,
        Decimal("700.00"),
        local_test_db_session,
        claim=claim1,
        start_date=date(2021, 12, 20),
        length_of_period=7,
    )

    # Claim 2
    _create_payment_container(
        employee,
        Decimal("125.00"),
        local_test_db_session,
        has_processed_state=True,
        claim=claim2,
        start_date=date(2021, 12, 19),
        length_of_period=1,
    )

    payment_container2 = _create_payment_container(
        employee,
        Decimal("725.00"),
        local_test_db_session,
        claim=claim2,
        start_date=date(2021, 12, 20),
        length_of_period=7,
    )

    # Run the logic
    # Because $225.00 was paid previously
    # both payments are expected to fail validation
    maximum_weekly_processor.process(employee, [payment_container1, payment_container2])

    validate_payment_failed(payment_container1)
    validate_payment_failed(payment_container2)


def test_validate_payments_use_correct_maximum_benefit(
    maximum_weekly_processor, local_test_db_session
):
    # payments in 2022 for claims starting in 2022 have a maximum payment of $1084.31,
    # so this should be paid in full
    employee = EmployeeFactory.create()
    payment_container1 = _create_payment_container(
        employee, Decimal("750"), local_test_db_session, start_date=date(2022, 1, 14)
    )
    payment_container2 = _create_payment_container(
        employee, Decimal("250"), local_test_db_session, start_date=date(2022, 1, 14)
    )
    maximum_weekly_processor.process(employee, [payment_container1, payment_container2])
    validate_payment_success(payment_container1)

    # payments in 2022 for absence periods starting in 2021 have a maximum payment of $850,
    # so the second payment should be reduced
    employee2 = EmployeeFactory.create()
    claim3 = ClaimFactory.create(employee=employee2)
    payment_container3 = _create_payment_container(
        employee2,
        Decimal("750"),
        local_test_db_session,
        start_date=date(2022, 1, 14),
        claim=claim3,
        add_single_absence_period=False,
    )
    _create_absence_periods(
        claim3,
        payment_container3.payment.fineos_leave_request_id,
        absence_period_start_date=date(2021, 12, 2),
    )

    claim4 = ClaimFactory.create(employee=employee2)
    payment_container4 = _create_payment_container(
        employee2,
        Decimal("250"),
        local_test_db_session,
        start_date=date(2022, 1, 14),
        claim=claim4,
        add_single_absence_period=False,
    )
    _create_absence_periods(
        claim4,
        payment_container4.payment.fineos_leave_request_id,
        absence_period_start_date=date(2021, 12, 17),
    )

    maximum_weekly_processor.process(employee2, [payment_container3, payment_container4])
    validate_payment_success(payment_container3)
    validate_payment_failed(payment_container4)

    # when payments are for claims in different years, the higher maximum amount applies,
    # so this should be paid in full
    employee3 = EmployeeFactory.create()
    claim5 = ClaimFactory.create(employee=employee3)

    payment_container5 = _create_payment_container(
        employee3,
        Decimal("750"),
        local_test_db_session,
        start_date=date(2022, 1, 14),
        claim=claim5,
        add_single_absence_period=False,
    )
    _create_absence_periods(
        claim5,
        payment_container5.payment.fineos_leave_request_id,
        absence_period_start_date=date(2022, 1, 7),
    )

    maximum_weekly_processor.process(employee, [payment_container5])
    validate_payment_success(payment_container5)

    claim6 = ClaimFactory.create(employee=employee3)
    payment_container6 = _create_payment_container(
        employee3,
        Decimal("250"),
        local_test_db_session,
        start_date=date(2022, 1, 14),
        claim=claim6,
        add_single_absence_period=False,
    )
    _create_absence_periods(
        claim6,
        payment_container6.payment.fineos_leave_request_id,
        absence_period_start_date=date(2021, 12, 10),
    )

    maximum_weekly_processor.process(employee3, [payment_container6])
    validate_payment_success(payment_container6)

    # Multiple absence periods spanning the year, only earliest is used
    employee4 = EmployeeFactory.create()
    claim7 = ClaimFactory.create(employee=employee4)

    payment_container7 = _create_payment_container(
        employee4,
        Decimal("900"),
        local_test_db_session,
        start_date=date(2022, 1, 14),
        claim=claim7,
        add_single_absence_period=False,
    )
    _create_absence_periods(
        claim7,
        payment_container7.payment.fineos_leave_request_id,
        absence_period_start_date=date(2021, 12, 7),
    )
    _create_absence_periods(
        claim7,
        payment_container7.payment.fineos_leave_request_id,
        absence_period_start_date=date(2022, 1, 7),
    )

    claim8 = ClaimFactory.create(employee=employee4)
    payment_container8 = _create_payment_container(
        employee4,
        Decimal("100"),
        local_test_db_session,
        start_date=date(2022, 1, 14),
        claim=claim8,
        add_single_absence_period=False,
    )
    _create_absence_periods(
        claim8,
        payment_container8.payment.fineos_leave_request_id,
        absence_period_start_date=date(2021, 12, 7),
    )

    maximum_weekly_processor.process(employee4, [payment_container7, payment_container8])

    validate_payment_failed(payment_container7)
    validate_payment_success(payment_container8)


def test_validate_payments_with_employer_reimbursement(
    maximum_weekly_processor, local_test_db_session
):
    employee = EmployeeFactory.create()

    # Create two payments, one standard
    # payment and one employer reimbursement
    employer_reimbursement_payment = _create_payment_container(
        employee,
        Decimal("100.00"),
        local_test_db_session,
        start_date=date(2021, 8, 1),
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,  # Sunday
    )

    # This is effectively a $700 payment because
    # the $100 from the employer reimbursement will be subtracted
    # during processing
    standard_payment = _create_payment_container(
        employee,
        Decimal("800.00"),
        local_test_db_session,
        start_date=date(2021, 8, 1),
        employer_reimbursement_amount=Decimal("-100.00"),  # Sunday
    )

    maximum_weekly_processor.process(employee, [employer_reimbursement_payment, standard_payment])

    validate_payment_success(employer_reimbursement_payment)
    validate_payment_success(standard_payment)

    # Also test a scenario where the payments
    # are still over the cap.
    employee2 = EmployeeFactory.create()

    employer_reimbursement_payment2 = _create_payment_container(
        employee2,
        Decimal("100.00"),
        local_test_db_session,
        start_date=date(2021, 8, 1),
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,  # Sunday
    )

    # This is effectively a $800 payment because
    # the $100 from the employer reimbursement will be subtracted
    # during processing
    standard_payment2 = _create_payment_container(
        employee2,
        Decimal("900.00"),
        local_test_db_session,
        start_date=date(2021, 8, 1),
        employer_reimbursement_amount=Decimal("-100.00"),  # Sunday
    )

    maximum_weekly_processor.process(
        employee2, [employer_reimbursement_payment2, standard_payment2]
    )

    validate_payment_success(employer_reimbursement_payment2)
    validate_payment_failed(standard_payment2)

    # Just show that adhoc payments still get to
    # go through even if they're employer reimbursements
    employee3 = EmployeeFactory.create()

    employer_reimbursement_payment3 = _create_payment_container(
        employee3,
        Decimal("1000.00"),
        local_test_db_session,
        is_adhoc_payment=True,
        start_date=date(2021, 8, 1),
        payment_transaction_type=PaymentTransactionType.EMPLOYER_REIMBURSEMENT,  # Sunday
    )

    # This is effectively a $800 payment because
    # the $100 from the employer reimbursement will be subtracted
    # during processing
    standard_payment3 = _create_payment_container(
        employee3,
        Decimal("9000.00"),
        local_test_db_session,
        is_adhoc_payment=True,
        start_date=date(2021, 8, 1),
        employer_reimbursement_amount=Decimal("-100.00"),  # Sunday
    )

    maximum_weekly_processor.process(
        employee2, [employer_reimbursement_payment3, standard_payment3]
    )

    validate_payment_success(employer_reimbursement_payment3)
    validate_payment_success(standard_payment3)
