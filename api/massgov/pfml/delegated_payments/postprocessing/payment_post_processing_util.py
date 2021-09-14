import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Tuple, cast

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Payment

logger = massgov.pfml.util.logging.get_logger(__name__)

DATE_FORMAT = "%Y-%m-%d"


@dataclass
class PaymentContainer:
    """
    Container for group a payment with its validation container
    """

    payment: Payment
    validation_container: payments_util.ValidationContainer

    def get_traceable_details(
        self, add_validation_issues: bool = False
    ) -> Dict[str, Optional[Any]]:
        # For logging purposes, this returns useful, traceable details

        details = payments_util.get_traceable_payment_details(self.payment)

        # This is just the reason codes, the details of the validation
        # container can potentially contain PII which we do not want to log.
        if add_validation_issues:
            details["validation_issues"] = self.validation_container.get_reasons()

        return details


@dataclass
class EmployeePaymentGroup:
    employee_id: uuid.UUID
    prior_payments: List[Payment] = field(default_factory=list)
    current_payments: List[PaymentContainer] = field(default_factory=list)


def _sum_payments(
    prior_payment_sum: Decimal, current_payment_containers: Iterable[PaymentContainer]
) -> Decimal:
    current_sum = sum(
        (
            Decimal(payment_container.payment.amount)
            for payment_container in current_payment_containers
        ),
        Decimal(0.00),
    )
    return prior_payment_sum + current_sum


def _determine_best_payments_under_cap(
    prior_payment_sum: Decimal,
    max_amount: Decimal,
    current_payment_containers: List[PaymentContainer],
) -> Iterable[PaymentContainer]:
    # We want to track the "best" scenario, that is, the one that maximizes
    # the amount of money a claimant gets paid that doesn't exceed the cap
    best_amount = prior_payment_sum
    best_accepted_payments: Iterable[PaymentContainer] = []

    # We want to try every combination of payments that don't sum to
    # more than the cap. We'll start with combinations of 1 record, then 2 and so on
    for combination_len in range(1, len(current_payment_containers) + 1):
        payment_combinations = combinations(current_payment_containers, combination_len)

        for payment_combination in payment_combinations:
            payment_sum = _sum_payments(prior_payment_sum, payment_combination)

            # If the sum is under the cap + more than the prior best
            # We want to set the payment_sum
            if payment_sum <= max_amount and payment_sum > best_amount:
                best_amount = payment_sum
                best_accepted_payments = payment_combination

    return best_accepted_payments


def _make_payment_log(payment: Payment, include_amount: bool = False) -> str:
    log_message = f"C={payment.fineos_pei_c_value},I={payment.fineos_pei_i_value},AbsenceCaseId={payment.claim.fineos_absence_id}"
    if include_amount:
        log_message += f",Amount={payment.amount}"

    return f"[{log_message}]"


def _format_dates(date_start: date, date_end: date) -> str:
    date_start_str = date_start.strftime(DATE_FORMAT)
    date_end_str = date_end.strftime(DATE_FORMAT)

    return f"[{date_start_str} - {date_end_str}]"


def _get_date_tuple(payment: Payment) -> Tuple[date, date]:
    return (cast(date, payment.period_start_date), cast(date, payment.period_end_date))
