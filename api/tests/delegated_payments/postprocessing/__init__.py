import random
from datetime import date, timedelta

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
from massgov.pfml.db.models.employees import PaymentTransactionType, State
from massgov.pfml.db.models.factories import ClaimFactory, PaymentDetailsFactory, PaymentFactory
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PaymentContainer,
)


def _create_legacy_payment_container(
    employee,
    amount,
    db_session,
    start_date=None,
    end_date=None,
    has_processed_state=False,
    has_errored_state=False,
    is_adhoc_payment=False,
    later_failed=False,
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
        payment,
        state,
        state_log_util.build_outcome(f"Payment set to {state.state_description}"),
        db_session,
    )

    # To represent a payment that succeeded and then failed with the bank
    if has_processed_state and later_failed:
        state_log_util.create_finished_state_log(
            payment,
            State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            state_log_util.build_outcome("Payment later failed with the bank"),
            db_session,
        )

    return PaymentContainer(payment)


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

    if not claim:
        claim = ClaimFactory.create(employee=employee)
    payment = PaymentFactory.create(
        claim=claim,
        amount=amount,
        period_start_date=start_date,
        period_end_date=end_date,
        is_adhoc_payment=is_adhoc_payment,
        payment_transaction_type_id=payment_transaction_type.payment_transaction_type_id,
    )

    if not skip_pay_periods:
        for payment_period in payment_periods:
            payment_period.payment_id = payment.payment_id

    if has_processed_state:
        state = random.choice(list(payments_util.Constants.PAID_STATES))
    elif has_errored_state:
        state = State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT
    elif is_overpayment:
        state = State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT
    else:
        state = State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK

    state_log_util.create_finished_state_log(
        payment,
        state,
        state_log_util.build_outcome(f"Payment set to {state.state_description}"),
        db_session,
    )

    # To represent a payment that succeeded and then failed with the bank
    if has_processed_state and later_failed:
        state_log_util.create_finished_state_log(
            payment,
            State.DELEGATED_PAYMENT_ERROR_FROM_BANK,
            state_log_util.build_outcome("Payment later failed with the bank"),
            db_session,
        )

    db_session.commit()
    return PaymentContainer(payment)
