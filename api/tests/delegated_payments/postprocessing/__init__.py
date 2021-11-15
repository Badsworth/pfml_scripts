import random
from datetime import date, timedelta

from massgov.pfml.db.models.employees import PaymentTransactionType, SharedPaymentConstants, State
from massgov.pfml.db.models.factories import PaymentDetailsFactory
from massgov.pfml.delegated_payments.mock.delegated_payments_factory import DelegatedPaymentFactory
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PaymentContainer,
)


def _create_payment_periods(total_amount, start_date, periods, length_of_period):
    amount_per_period = total_amount / periods

    payment_periods = []
    for _ in range(periods):
        end_date = start_date + timedelta(length_of_period - 1)

        payment_period = PaymentDetailsFactory.create(
            amount=amount_per_period, period_start_date=start_date, period_end_date=end_date,
        )
        payment_periods.append(payment_period)

        # Increment after as it starts on the first period's day
        start_date = start_date + timedelta(length_of_period)

    return payment_periods


def _create_payment_container(
    employee,
    amount,
    db_session,
    start_date=None,
    periods=1,
    length_of_period=7,
    skip_pay_periods=False,
    has_processed_state=False,
    has_errored_state=False,
    is_adhoc_payment=False,
    is_overpayment=False,
    later_failed=False,
    payment_transaction_type=PaymentTransactionType.STANDARD,
    claim=None,
):

    if not start_date:
        # We use this day because it's a Sunday that starts on the 1st so easier to conceptualize
        start_date = date(2021, 8, 1)

    if not skip_pay_periods:
        payment_periods = _create_payment_periods(amount, start_date, periods, length_of_period)
        end_date = payment_periods[-1].period_end_date
    else:
        end_date = start_date + timedelta(length_of_period - 1)

    factory = DelegatedPaymentFactory(
        db_session,
        employee=employee,
        claim=claim,
        payment_transaction_type=payment_transaction_type,
        amount=amount,
        period_start_date=start_date,
        period_end_date=end_date,
        is_adhoc_payment=is_adhoc_payment,
        payment_transaction_type_id=payment_transaction_type.payment_transaction_type_id,
        fineos_employee_first_name=employee.first_name,
        fineos_employee_last_name=employee.last_name,
    )
    payment = factory.get_or_create_payment()

    if not skip_pay_periods:
        for payment_period in payment_periods:
            payment_period.payment_id = payment.payment_id

    if has_processed_state:
        state = random.choice(list(SharedPaymentConstants.PAID_STATES))
    elif has_errored_state:
        state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    elif is_overpayment:
        state = State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    else:
        state = State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK

    factory.get_or_create_payment_with_state(state)

    # To represent a payment that succeeded and then failed with the bank
    if has_processed_state and later_failed:
        factory.get_or_create_payment_with_state(State.DELEGATED_PAYMENT_ERROR_FROM_BANK)

    # db_session.commit()
    return PaymentContainer(payment)
