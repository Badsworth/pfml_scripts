from datetime import date
from decimal import Decimal

import pytest

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import State
from massgov.pfml.db.models.factories import ClaimFactory, EmployeeFactory, PaymentFactory
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
    initialize_factories_session, test_db_session, test_db_other_session, monkeypatch
):
    return PaymentPostProcessingStep(
        db_session=test_db_session, log_entry_db_session=test_db_other_session
    )


def _create_payment_container(
    employee,
    amount,
    db_session,
    start_date=None,
    end_date=None,
    has_processed_state=False,
    has_errored_state=False,
    payment_transaction_type=PaymentTransactionType.STANDARD,
):
    if not start_date:
        start_date = date(2021, 1, 1)
    if not end_date:
        end_date = date(2021, 1, 8)

    claim = ClaimFactory.create(employee=employee)
    payment = PaymentFactory.create(
        claim=claim,
        amount=amount,
        period_start_date=start_date,
        period_end_date=end_date,
        payment_transaction_type_id=payment_transaction_type.payment_transaction_type_id,
    )

    if has_processed_state:
        state = State.DELEGATED_PAYMENT_FINEOS_WRITEBACK_CHECK_SENT
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


def test_validate_payments_not_exceeding_cap(payment_post_processing_step, test_db_session):
    employee = EmployeeFactory.create()

    # New payments that are being processed
    payment_container1 = _create_payment_container(employee, Decimal("225.00"), test_db_session)
    payment_container2 = _create_payment_container(employee, Decimal("225.00"), test_db_session)

    # Prior payments already processed
    _create_payment_container(
        employee, Decimal("200.00"), test_db_session, has_processed_state=True
    )
    _create_payment_container(
        employee, Decimal("200.00"), test_db_session, has_processed_state=True
    )

    # Prior payments that errored and aren't factored into the calculation
    _create_payment_container(employee, Decimal("500.00"), test_db_session, has_errored_state=True)
    _create_payment_container(employee, Decimal("500.00"), test_db_session, has_errored_state=True)

    # The cap is configured to 850.00, the two new payments
    # alongside the two previously processed payments sum to exactly this
    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id, [payment_container1, payment_container2]
    )

    # Both new payments worked without issue
    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()

    # Make another payment that'll push it over the cap
    payment_container3 = _create_payment_container(employee, Decimal("0.01"), test_db_session)
    payment_post_processing_step._validate_payments_not_exceeding_cap(
        employee.employee_id, [payment_container1, payment_container2, payment_container3]
    )

    # Only the smallest one fails
    assert not payment_container1.validation_container.has_validation_issues()
    assert not payment_container2.validation_container.has_validation_issues()
    assert payment_container3.validation_container.has_validation_issues()


def test_validate_payments_not_exceeding_cap_multiple_pay_periods(
    payment_post_processing_step, test_db_session
):
    employee = EmployeeFactory.create()

    # No prior payments exist, only processing new ones in this test

    # Now lets create more payments for the same claimant, but another pay period
    payment_container1 = _create_payment_container(
        employee,
        Decimal("800.00"),
        test_db_session,
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 8),
    )
    payment_container2 = _create_payment_container(
        employee,
        Decimal("800.00"),
        test_db_session,
        start_date=date(2021, 2, 1),
        end_date=date(2021, 2, 8),
    )
    payment_container3 = _create_payment_container(
        employee,
        Decimal("800.00"),
        test_db_session,
        start_date=date(2021, 3, 1),
        end_date=date(2021, 3, 8),
    )
    payment_container4 = _create_payment_container(
        employee,
        Decimal("1200.00"),
        test_db_session,
        start_date=date(2021, 4, 1),
        end_date=date(2021, 4, 8),
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


def test_validate_payments_not_exceeding_cap_other_payment_types(
    payment_post_processing_step, test_db_session
):
    employee = EmployeeFactory.create()

    # New payments that are being processed, sum exactly to cap
    # and will be accepted
    payment_container1 = _create_payment_container(employee, Decimal("425.00"), test_db_session)
    payment_container2 = _create_payment_container(employee, Decimal("425.00"), test_db_session)

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
            employee, Decimal("850.00"), test_db_session, payment_transaction_type=payment_type
        )
        _create_payment_container(
            employee,
            Decimal("850.00"),
            test_db_session,
            payment_transaction_type=payment_type,
            has_processed_state=True,
        )
        _create_payment_container(
            employee,
            Decimal("850.00"),
            test_db_session,
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


def test_validate_payment_cap_for_period(payment_post_processing_step, test_db_session):
    """
    This test validates that the logic for choosing payments to pay is correct.
    """
    start_date = date(2021, 1, 1)
    end_date = date(2021, 1, 8)
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


def test_run_step_payment_cap(payment_post_processing_step, test_db_session):
    # Sanity test to show payments are filtered by employee ID
    # and old payments from other employees aren't picked up
    # when doing the payment cap processing logic

    # Create an employee with 4 new payments
    # and one old payment that sum to the cap
    employee1 = EmployeeFactory.create()
    _create_payment_container(employee1, Decimal("200.00"), test_db_session)
    _create_payment_container(employee1, Decimal("200.00"), test_db_session)
    _create_payment_container(employee1, Decimal("200.00"), test_db_session)
    _create_payment_container(employee1, Decimal("200.00"), test_db_session)

    _create_payment_container(
        employee1, Decimal("50.00"), test_db_session, has_processed_state=True
    )

    # Create old payments for other employees
    employee2 = EmployeeFactory.create()
    employee3 = EmployeeFactory.create()
    employee4 = EmployeeFactory.create()
    _create_payment_container(
        employee2, Decimal("850.00"), test_db_session, has_processed_state=True
    )
    _create_payment_container(
        employee3, Decimal("850.00"), test_db_session, has_processed_state=True
    )
    _create_payment_container(
        employee4, Decimal("850.00"), test_db_session, has_processed_state=True
    )

    payment_post_processing_step.run_step()

    # All 4 payments should have been moved to the success state
    state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
        associated_class=state_log_util.AssociatedClass.PAYMENT,
        end_state=State.PAYMENT_READY_FOR_ADDRESS_VALIDATION,
        db_session=test_db_session,
    )

    assert len(state_logs) == 4
