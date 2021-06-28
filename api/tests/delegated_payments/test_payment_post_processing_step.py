import random
from datetime import date, timedelta
from decimal import Decimal

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import Flow, State
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory, PaymentFactory
from massgov.pfml.db.models.payments import FineosWritebackDetails, FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.payment_post_processing_step import (
    EmployeePaymentGroup,
    PaymentContainer,
    PaymentPostProcessingStep,
    PaymentTransactionType,
)

###
# Note that the maximum weekly benefit cap for these tests is set to $850.00 in:
# api/massgov/pfml/db/models/payments.py::sync_maximum_weekly_benefit_amount
###


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


def _create_payment_container(
    employee,
    amount,
    db_session,
    start_date=None,
    end_date=None,
    has_processed_state=False,
    has_errored_state=False,
    is_adhoc_payment=False,
    payment_transaction_type=PaymentTransactionType.STANDARD,
):
    if not start_date:
        start_date = date(2021, 1, 1)
    if not end_date:
        end_date = date(2021, 1, 7)

    claim = ClaimFactory.create(employee=employee)
    payment = PaymentFactory.create(
        claim=claim,
        amount=amount,
        period_start_date=start_date,
        period_end_date=end_date,
        is_adhoc_payment=is_adhoc_payment,
        payment_transaction_type_id=payment_transaction_type.payment_transaction_type_id,
    )

    if has_processed_state:
        state = random.choice(list(payments_util.Constants.PAID_STATES))
    elif has_errored_state:
        state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    else:
        state = State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK

    state_log_util.create_finished_state_log(
        payment, state, state_log_util.build_outcome("MESSAGE"), db_session
    )

    return PaymentContainer(payment, payments_util.ValidationContainer(str(payment.payment_id)))


def _create_employee_payment_group(prior_amounts, current_amounts):
    # Note, the amounts all come in as strings and are converted
    # to decimals. This is to maintain the accuracy as Decimal(100.10)
    # ends up less accurate than Decimal("100.10") as the float gets rounded
    # first. This method takes in strings rather than decimals to avoid verbosity:
    # eg. [Decimal("100.00"), Decimal("100.00"), Decimal("100.00")]
    # vs.
    # ["100.00", "100.00", "100.00"]
    employee = EmployeeFactory.create()
    claim = ClaimFactory.create(employee=employee)
    group = EmployeePaymentGroup(employee.employee_id)

    for amount in prior_amounts:
        payment = PaymentFactory.create(claim=claim, amount=Decimal(amount))
        group.prior_payments.append(payment)

    for amount in current_amounts:
        payment = PaymentFactory.create(claim=claim, amount=Decimal(amount))
        validation_container = payments_util.ValidationContainer(str(payment.payment_id))
        group.current_payments.append(PaymentContainer(payment, validation_container))

    return group


def _validate_amounts_not_selected(group, expected_chosen_amounts):
    # Iterate over the list of payment containers
    # and figure out which payments errored. Any that
    # did not error, add to a list and make sure it matches
    # the list of actually chosen amounts

    actual_amounts_chosen = []
    for payment_container in group.current_payments:
        amount = payment_container.payment.amount
        if payment_container.validation_container.has_validation_issues():
            actual_amounts_chosen.append(str(amount))

    assert sorted(actual_amounts_chosen) == sorted(expected_chosen_amounts)


def test_get_maximum_amount_for_period(payment_post_processing_step):
    # For dates used, the maximum for a week is $850.00. Weeks are rounded up (eg. 8 days = 2 weeks)

    # Period is all contained in one day
    amount = payment_post_processing_step._get_maximum_amount_for_period(
        date(2021, 1, 1), date(2021, 1, 1)
    )
    assert amount == Decimal("850.00")

    # Period is part of one week
    amount = payment_post_processing_step._get_maximum_amount_for_period(
        date(2021, 1, 1), date(2021, 1, 4)
    )
    assert amount == Decimal("850.00")

    # Period is exactly a week
    amount = payment_post_processing_step._get_maximum_amount_for_period(
        date(2021, 1, 1), date(2021, 1, 7)
    )
    assert amount == Decimal("850.00")

    # Period is part of two weeks
    amount = payment_post_processing_step._get_maximum_amount_for_period(
        date(2021, 1, 1), date(2021, 1, 8)
    )
    assert amount == Decimal("1700.00")

    # Period is exactly two weeks
    amount = payment_post_processing_step._get_maximum_amount_for_period(
        date(2021, 1, 1), date(2021, 1, 14)
    )
    assert amount == Decimal("1700.00")

    # Period is part of three weeks
    amount = payment_post_processing_step._get_maximum_amount_for_period(
        date(2021, 1, 1), date(2021, 1, 15)
    )
    assert amount == Decimal("2550.00")

    # Period is exactly three weeks
    amount = payment_post_processing_step._get_maximum_amount_for_period(
        date(2021, 1, 1), date(2021, 1, 21)
    )
    assert amount == Decimal("2550.00")


def test_validate_payments_not_exceeding_cap(payment_post_processing_step, local_test_db_session):
    employee = EmployeeFactory.create()

    # New payments that are being processed
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

    # Prior payments that errored and aren't factored into the calculation
    _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, has_errored_state=True
    )
    _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, has_errored_state=True
    )

    # The cap is configured to 850.00, the two new payments
    # alongside the two previously processed payments sum to exactly this
    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id, [payment_container1, payment_container2]
    )

    # Both new payments worked without issue
    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()

    # Make another payment that'll push it over the cap
    payment_container3 = _create_payment_container(employee, Decimal("0.01"), local_test_db_session)
    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id, [payment_container1, payment_container2, payment_container3]
    )

    # Only the smallest one fails
    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()
    assert payment_container3.validation_container.has_validation_issues()


def test_validate_payments_not_exceeding_cap_adhoc_payments(
    payment_post_processing_step, local_test_db_session
):
    employee = EmployeeFactory.create()

    # New payments that are being processed, but are all adhoc
    # Will all be accepted
    payment_container1 = _create_payment_container(
        employee, Decimal("5000.00"), local_test_db_session, is_adhoc_payment=True
    )
    payment_container2 = _create_payment_container(
        employee, Decimal("5000.00"), local_test_db_session, is_adhoc_payment=True
    )
    # Not adhoc, will still be accepted as they sum to less than the cap
    payment_container3 = _create_payment_container(
        employee, Decimal("425.00"), local_test_db_session, is_adhoc_payment=False
    )
    payment_container4 = _create_payment_container(
        employee, Decimal("425.00"), local_test_db_session, is_adhoc_payment=False
    )

    # Prior adhoc payments don't factor into the calculation either
    _create_payment_container(
        employee,
        Decimal("850.00"),
        local_test_db_session,
        has_processed_state=True,
        is_adhoc_payment=True,
    )

    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id,
        [payment_container1, payment_container2, payment_container3, payment_container4],
    )

    # None of the payments failed, as adhoc payments don't factor into the calculation
    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()
    assert not payment_container3.validation_container.has_validation_issues()
    assert not payment_container4.validation_container.has_validation_issues()

    # Note adding one more non-adhoc payment will still cause something to fail.
    payment_container5 = _create_payment_container(
        employee, Decimal("1.00"), local_test_db_session, is_adhoc_payment=False
    )

    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id,
        [
            payment_container1,
            payment_container2,
            payment_container3,
            payment_container4,
            payment_container5,
        ],
    )

    # The smallest one fails validation.
    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()
    assert not payment_container3.validation_container.has_validation_issues()
    assert not payment_container4.validation_container.has_validation_issues()
    assert payment_container5.validation_container.has_validation_issues()


def test_get_all_active_payments_associated_with_employee(
    payment_post_processing_step, local_test_db_session
):
    # This test shows that it doesn't need to be the latest state for a payment
    # for us to find the prior payments, just so long as they were sent to PUB at some point

    employee = EmployeeFactory.create()
    # New payment are being processed
    payment_container = _create_payment_container(
        employee, Decimal("225.00"), local_test_db_session
    )

    prior_payment_container = _create_payment_container(
        employee, Decimal("800.00"), local_test_db_session, has_processed_state=True
    )

    # Add another state log
    state_log_util.create_finished_state_log(
        prior_payment_container.payment,
        State.DELEGATED_PAYMENT_COMPLETE,
        state_log_util.build_outcome("MESSAGE"),
        local_test_db_session,
    )

    active_payments = payment_post_processing_step._get_all_active_payments_associated_with_employee(
        employee.employee_id, [payment_container.payment.payment_id]
    )
    assert len(active_payments) == 1
    assert active_payments[0].payment_id == prior_payment_container.payment.payment_id


def test_validate_payments_not_exceeding_cap_multiple_pay_periods(
    payment_post_processing_step, local_test_db_session
):
    employee = EmployeeFactory.create()

    # No prior payments exist, only processing new ones in this test

    # Now lets create more payments for the same claimant, but another pay period
    payment_container1 = _create_payment_container(
        employee,
        Decimal("800.00"),
        local_test_db_session,
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 7),
    )
    payment_container2 = _create_payment_container(
        employee,
        Decimal("800.00"),
        local_test_db_session,
        start_date=date(2021, 2, 1),
        end_date=date(2021, 2, 7),
    )
    payment_container3 = _create_payment_container(
        employee,
        Decimal("800.00"),
        local_test_db_session,
        start_date=date(2021, 3, 1),
        end_date=date(2021, 3, 7),
    )
    payment_container4 = _create_payment_container(
        employee,
        Decimal("1200.00"),
        local_test_db_session,
        start_date=date(2021, 4, 1),
        end_date=date(2021, 4, 7),
    )

    # Send all of the payments. Only the last one will fail
    # as it is over the cap by itself.
    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id,
        [payment_container1, payment_container2, payment_container3, payment_container4],
    )

    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()
    assert not payment_container3.validation_container.has_validation_issues()
    assert payment_container4.validation_container.has_validation_issues()


def test_validate_payments_not_exceeding_cap_multiweek_pay_periods(
    payment_post_processing_step, local_test_db_session
):
    # Pay periods can be for more than one week, and the cap
    # is a maximum per week. A pay period of of more than one week
    # should allow a cap equal to maximum_per_week * weeks. Weeks
    # are always rounded up (eg. 8 days = 2 weeks
    employee = EmployeeFactory.create()
    start_date = date(2021, 1, 1)
    end_date_start = date(2021, 1, 2)  # Weeks will be 2, 8, 15... days long

    # Show that
    for i in range(1, 10):
        end_date = end_date_start + timedelta(days=7 * (i - 1))
        payment_container1 = _create_payment_container(
            employee,
            Decimal("850.00") * Decimal(i),
            local_test_db_session,
            start_date=start_date,
            end_date=end_date,
        )
        # Also create a second container for exactly $0.01 that'll fail
        # as it pushes it just over the cap.
        payment_container2 = _create_payment_container(
            employee,
            Decimal("0.01"),
            local_test_db_session,
            start_date=start_date,
            end_date=end_date,
        )
        payment_post_processing_step._validate_payments_not_exceeding_cap(
            employee.employee_id, [payment_container1, payment_container2],
        )
        assert not payment_container1.validation_container.has_validation_issues()
        assert payment_container2.validation_container.has_validation_issues()


def test_validate_payments_not_exceeding_cap_other_payment_types(
    payment_post_processing_step, local_test_db_session
):
    employee = EmployeeFactory.create()

    # New payments that are being processed, sum exactly to cap
    # and will be accepted
    payment_container1 = _create_payment_container(
        employee, Decimal("425.00"), local_test_db_session
    )
    payment_container2 = _create_payment_container(
        employee, Decimal("425.00"), local_test_db_session
    )

    # Other payments of non-standard types. Despite all of these
    # existing, none of them will have any effect on the above payments
    # being successfully accepted.
    other_payment_types = [
        PaymentTransactionType.ZERO_DOLLAR,
        PaymentTransactionType.OVERPAYMENT,
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
        )
        _create_payment_container(
            employee,
            Decimal("850.00"),
            local_test_db_session,
            payment_transaction_type=payment_type,
            has_processed_state=True,
        )
        _create_payment_container(
            employee,
            Decimal("850.00"),
            local_test_db_session,
            payment_transaction_type=payment_type,
            has_errored_state=True,
        )

    # Run the logic
    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id, [payment_container1, payment_container2]
    )

    # Both new payments worked without issue, none of the other types
    # caused any sort of interference
    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()


def test_validate_payment_cap_for_period(payment_post_processing_step, local_test_db_session):
    """
    This test validates that the logic for choosing payments to pay is correct.
    """
    start_date = date(2021, 1, 1)
    end_date = date(2021, 1, 7)  # Exactly one week, so cap is $850
    # All values well under the cap
    group = _create_employee_payment_group(
        prior_amounts=["100.00", "100.00"], current_amounts=["100.00", "100.00"]
    )
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, [])

    # One of the two new ones won't be selected
    group = _create_employee_payment_group(
        prior_amounts=["600.00", "100.00"], current_amounts=["100.00", "100.00"]
    )
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, ["100.00"])

    # In a perfect world, the we would reject the old payment
    # as it's less efficiently packed, but we already counted it on
    # a previous day of processing.
    group = _create_employee_payment_group(
        prior_amounts=["500.00"], current_amounts=["400.00", "400.00"]
    )
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, ["400.00", "400.00"])

    # Many payments (sum to $900), only the $60 gets rejected
    group = _create_employee_payment_group(
        prior_amounts=[],
        current_amounts=["200.00", "150.00", "300.00", "75.00", "75.00", "40.00", "60.00"],
    )
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, ["60.00"])

    # All payments exceed cap.
    group = _create_employee_payment_group(prior_amounts=[], current_amounts=["1000.00", "1300.00"])
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, ["1000.00", "1300.00"])

    # The algorithm will always prefer paying fewer payments.
    # In the choice between $800+$50 or $800+$10(x5), it'll always
    # end up on the first scenario.
    group = _create_employee_payment_group(
        prior_amounts=[],
        current_amounts=["800.00", "50.00", "10.00", "10.00", "10.00", "10.00", "10.00"],
    )
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, ["10.00", "10.00", "10.00", "10.00", "10.00"])

    # It will always find the optimal even if it requires many iterations
    group = _create_employee_payment_group(
        prior_amounts=[],
        current_amounts=["800.00", "60.00", "10.00", "10.00", "10.00", "10.00", "10.00"],
    )
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, ["60.00"])

    # It will always find an optimal, even if some number of combinations
    # does not produce a result. For combinations of len=1,2,3, the $800
    # would be the only one chosen, but once we try at len=4, the rest will be
    # grouped and produce a higher value.
    group = _create_employee_payment_group(
        prior_amounts=[], current_amounts=["800.00", "201.00", "200.00", "200.00", "200.00"]
    )
    payment_post_processing_step._validate_payment_cap_for_period(start_date, end_date, group)
    _validate_amounts_not_selected(group, ["800.00"])


def test_run_step_payment_cap(payment_post_processing_step, local_test_db_session):
    # Sanity test to show payments are filtered by employee ID
    # and old payments from other employees aren't picked up
    # when doing the payment cap processing logic

    # Create an employee with 4 new payments
    # and one old payment that sum to the cap
    employee1 = EmployeeFactory.create()
    _create_payment_container(employee1, Decimal("200.00"), local_test_db_session)
    _create_payment_container(employee1, Decimal("200.00"), local_test_db_session)
    _create_payment_container(employee1, Decimal("200.00"), local_test_db_session)
    _create_payment_container(employee1, Decimal("200.00"), local_test_db_session)

    _create_payment_container(
        employee1, Decimal("50.00"), local_test_db_session, has_processed_state=True
    )

    # Create old payments for other employees
    employee2 = EmployeeFactory.create()
    employee3 = EmployeeFactory.create()
    employee4 = EmployeeFactory.create()
    _create_payment_container(
        employee2, Decimal("850.00"), local_test_db_session, has_processed_state=True
    )
    _create_payment_container(
        employee3, Decimal("850.00"), local_test_db_session, has_processed_state=True
    )
    _create_payment_container(
        employee4, Decimal("850.00"), local_test_db_session, has_processed_state=True
    )

    payment_post_processing_step.run()

    # All 4 payments should have been moved to the success state
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.PAYMENT_READY_FOR_ADDRESS_VALIDATION,
        db_session=local_test_db_session,
    )

    assert len(state_logs) == 4


def test_run_step_payment_over_cap(payment_post_processing_step, local_test_db_session):
    employee = EmployeeFactory.create()
    payment_container = _create_payment_container(
        employee, Decimal("600.00"), local_test_db_session
    )
    _create_payment_container(
        employee, Decimal("500.00"), local_test_db_session, has_processed_state=True
    )

    payment_post_processing_step.run()

    payment = payment_container.payment
    # The payment should have been added to two states in different flows
    payment_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PAYMENT, local_test_db_session
    )
    assert (
        payment_flow_log.end_state_id
        == State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT.state_id
    )
    pei_writeback_flow_log = state_log_util.get_latest_state_log_in_flow(
        payment, Flow.DELEGATED_PEI_WRITEBACK, local_test_db_session
    )
    assert pei_writeback_flow_log.end_state_id == State.DELEGATED_ADD_TO_FINEOS_WRITEBACK.state_id
    writeback_details = (
        local_test_db_session.query(FineosWritebackDetails)
        .filter(FineosWritebackDetails.payment_id == payment.payment_id)
        .one_or_none()
    )
    assert writeback_details
    assert (
        writeback_details.transaction_status_id
        == FineosWritebackTransactionStatus.TOTAL_BENEFITS_OVER_CAP.transaction_status_id
    )
