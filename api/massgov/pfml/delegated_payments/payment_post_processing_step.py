import enum
import math
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Tuple, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    Claim,
    LatestStateLog,
    Payment,
    PaymentTransactionType,
    State,
    StateLog,
)
from massgov.pfml.db.models.payments import MaximumWeeklyBenefitAmount
from massgov.pfml.delegated_payments.step import Step

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


class PaymentPostProcessingStep(Step):
    """
    This step runs after our payment extract step and
    handles any post-processing on payments, that is, any
    validation rules that need to be run for a payment across
    a wider swath of data (eg. comparing all payments for a claimant)
    """

    class Metrics(str, enum.Enum):
        # General metrics
        PAYMENTS_PROCESSED_COUNT = "payments_processed_count"
        PAYMENTS_FAILED_VALIDATION_COUNT = "payments_failed_validation_count"
        PAYMENTS_PASSED_VALIDATION_COUNT = "payments_passed_valdiation_count"
        # Metrics specific to the payment cap check
        PAYMENT_CAP_ALL_ACCEPTED_COUNT = "payment_cap_all_accepted_count"
        PAYMENT_CAP_PAYMENT_ERROR_COUNT = "payment_cap_payment_error_count"
        PAYMENT_CAP_PAYMENT_ACCEPTED_COUNT = "payment_cap_payment_accepted_count"

    def _get_maximum_amount_for_period(self, start_date: date, end_date: date) -> Decimal:
        # TODO - We haven't received guidance on how to handle pay periods
        #        that overlap a range. For example, if our effective dates
        #        were for the years 2021, 2022, 2023
        #        and we had a payment with a pay period of 2021-12-28 -> 2022-01-03
        #        we wouldn't know what to do. For now, I've implemented
        #        it to only use the start_date of the pay period at Mass' recommendation.

        result = (
            self.db_session.query(MaximumWeeklyBenefitAmount)
            .filter(MaximumWeeklyBenefitAmount.effective_date <= start_date)
            .order_by(MaximumWeeklyBenefitAmount.effective_date.desc())
            .first()
        )
        if not result:
            logger.error(
                "Maximum weekly benefit amount was not found for dates %s - %s",
                start_date,
                end_date,
            )
            raise RuntimeError(
                "No maximum weekly benefit amount configured for date %s - %s"
                % (start_date, end_date)
            )

        # The amount stored in the table is a maximum for a week, but pay periods
        # can be longer than a week. We need to scale the maximum amount up based
        # on the length of the period. This is calculated by finding the length
        # in days of the pay period, dividing by 7, and rounding up.
        period_in_days = (end_date - start_date).days
        weeks = math.ceil(period_in_days / 7.0)

        return weeks * result.maximum_weekly_benefit_amount

    def run_step(self):
        """
        Grabs all payments in the awaiting state, and runs
        various validation rules on them. If any issue
        is encountered, the validation container attached to the
        payment will be updated accordingly. All validation rules
        run even if a payment has errored in a prior step so that
        all issues can be communicated in the eventual error report.
        """
        payment_containers = self._get_payments_awaiting_post_processing_validation()

        # Run validations that process payments
        # by group them under a single employee
        self._process_payments_across_employee(payment_containers)

        # After all validations are run, move states of the payments
        self._move_payments_to_new_state(payment_containers)

    def _get_payments_awaiting_post_processing_validation(self) -> List[PaymentContainer]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
            db_session=self.db_session,
        )

        payment_containers = []
        for state_log in state_logs:
            self.increment(self.Metrics.PAYMENTS_PROCESSED_COUNT)
            payment = state_log.payment
            validation_container = payments_util.ValidationContainer(str(payment.payment_id))
            payment_containers.append(PaymentContainer(payment, validation_container))

        return payment_containers

    def _process_payments_across_employee(self, payment_containers: List[PaymentContainer]) -> None:
        # First group the payments by their employee
        employee_to_containers: Dict[uuid.UUID, List[PaymentContainer]] = {}

        for container in payment_containers:
            # Cast the employee ID because the linter thinks it's a string
            employee_id = cast(uuid.UUID, container.payment.claim.employee_id)

            if employee_id not in employee_to_containers:
                employee_to_containers[employee_id] = []

            employee_to_containers[employee_id].append(container)

        # Run various validation rules on these groups
        for employee_id, payment_containers in employee_to_containers.items():
            logger.info(
                "Processing %i payments in batch for employee ID %s",
                len(payment_containers),
                employee_id,
            )
            # Validate that payments aren't exceeding a maximum cap
            self._validate_payments_not_exceeding_cap(employee_id, payment_containers)

    def _get_all_active_payments_associated_with_employee(
        self, employee_id: uuid.UUID, current_payment_ids: Optional[List[uuid.UUID]] = None
    ) -> List[Payment]:
        if not current_payment_ids:
            current_payment_ids = []

        # Get all payment IDs of payments associated with the same employee
        # That aren't the payments we're attempting to validate, that are
        # standard payments (eg. no cancellations, overpayments, etc.)
        subquery = (
            self.db_session.query(Payment.payment_id)
            .join(Claim)
            .filter(
                Claim.employee_id == employee_id,
                Payment.payment_transaction_type_id
                == PaymentTransactionType.STANDARD.payment_transaction_type_id,
                Payment.payment_id.notin_(current_payment_ids),
            )
        )

        # For the payment IDs fetched above, grab any payments
        # that are in a non-restartable (non-error) state
        return (
            self.db_session.query(Payment)
            .join(LatestStateLog)
            .join(StateLog, LatestStateLog.state_log_id == StateLog.state_log_id)
            .filter(
                Payment.payment_id.in_(subquery),
                StateLog.end_state_id.notin_(payments_util.Constants.RESTARTABLE_PAYMENT_STATE_IDS),
            )
            .all()
        )

    def _validate_payments_not_exceeding_cap(
        self, employee_id: uuid.UUID, payment_containers: List[PaymentContainer]
    ) -> None:
        """
        Mass limits the maximum amount we can pay a claimant in a given period. For example,
        in 2021, this limit is $850 The regulations detail the process for how this changes:
        https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXXII/Chapter175M/Section3

        Find all payments associated with a claimant then group by leave period
        This can include payments that have been paid on previous days which is why
        we need more than just the payments from this batch.

        Then determine the max amount we can pay using the payments that we are actively processing
        """

        current_payment_ids = [
            payment_container.payment.payment_id for payment_container in payment_containers
        ]
        prior_payments = self._get_all_active_payments_associated_with_employee(
            employee_id, current_payment_ids
        )

        # group the payments by start+end period. We only care about the periods
        # for the new payments from this batch
        # Create a dictionary that maps from a tuple of start/end dates to a a tuple
        # of prior_payments + current payment containers. These are contained in classes
        # to preserve simple names
        date_range_to_payments: Dict[Tuple[date, date], EmployeePaymentGroup] = {}
        for payment_container in payment_containers:
            date_tuple = _get_date_tuple(payment_container.payment)

            if date_tuple not in date_range_to_payments:
                date_range_to_payments[date_tuple] = EmployeePaymentGroup(employee_id)

            date_range_to_payments[date_tuple].current_payments.append(payment_container)

        # For any prior payments that have the same leave periods, add them to the list as well
        for prior_payment in prior_payments:
            date_tuple = _get_date_tuple(prior_payment)

            if date_tuple in date_range_to_payments:
                date_range_to_payments[date_tuple].prior_payments.append(prior_payment)

        for period, payment_group in date_range_to_payments.items():
            self._validate_payment_cap_for_period(period[0], period[1], payment_group)

    def _validate_payment_cap_for_period(
        self, period_start: date, period_end: date, payment_group: EmployeePaymentGroup
    ) -> None:
        prior_payment_sum = sum(
            (Decimal(payment.amount) for payment in payment_group.prior_payments), Decimal(0.00)
        )
        current_payment_containers = payment_group.current_payments

        max_amount = self._get_maximum_amount_for_period(period_start, period_end)

        # First, a simple check, if they all sum to less than the maximum
        # we don't need to do anything complicated below
        if _sum_payments(prior_payment_sum, current_payment_containers) <= max_amount:
            # Increment the counter for each accepted payment
            for _ in current_payment_containers:
                self.increment(self.Metrics.PAYMENT_CAP_ALL_ACCEPTED_COUNT)
            return

        accepted_payment_containers = _determine_best_payments_under_cap(
            prior_payment_sum, max_amount, current_payment_containers
        )
        accepted_payment_ids = set(
            [
                payment_container.payment.payment_id
                for payment_container in accepted_payment_containers
            ]
        )

        # Now that we know the best amount and best payments, we need
        # to add a validation issue for every payment that we couldn't pick
        for payment_container in current_payment_containers:
            if payment_container.payment.payment_id not in accepted_payment_ids:
                self.increment(self.Metrics.PAYMENT_CAP_PAYMENT_ERROR_COUNT)
                msg = f"This payment exceeded the maximum amount allowable (${max_amount}) for a claimant for the pay period of {_format_dates(period_start, period_end)}."

                if payment_group.prior_payments:
                    prior_payment_msgs = []
                    for prior_payment in payment_group.prior_payments:
                        prior_payment_msgs.append(_make_payment_log(prior_payment, True))

                    msg += f" We previously paid {', '.join(prior_payment_msgs)}."

                if accepted_payment_containers:
                    accepted_payment_msgs = []
                    for accepted_payment in accepted_payment_containers:
                        accepted_payment_msgs.append(
                            _make_payment_log(accepted_payment.payment, True)
                        )

                    msg += f" We chose these payments from this batch instead {', '.join(accepted_payment_msgs)}"

                payment_container.validation_container.add_validation_issue(
                    payments_util.ValidationReason.PAYMENT_EXCEEDS_PAY_PERIOD_CAP, msg
                )
                logger.info(
                    "Payment failed validation rule by going over %s cap",
                    max_amount,
                    extra=payment_container.get_traceable_details(False),
                )

            else:
                self.increment(self.Metrics.PAYMENT_CAP_PAYMENT_ACCEPTED_COUNT)

    def _move_payments_to_new_state(self, payment_containers: List[PaymentContainer]) -> None:
        for payment_container in payment_containers:
            # If it has issues, error the payment
            if payment_container.validation_container.has_validation_issues():
                self.increment(self.Metrics.PAYMENTS_FAILED_VALIDATION_COUNT)
                logger.info(
                    "Payment %s passed all validation rules",
                    _make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(True),
                )

                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
                    outcome=state_log_util.build_outcome(
                        "Payment failed post-processing validation",
                        payment_container.validation_container,
                    ),
                    associated_model=payment_container.payment,
                    db_session=self.db_session,
                )

            # Otherwise it is ready for address validation
            else:
                self.increment(self.Metrics.PAYMENTS_PASSED_VALIDATION_COUNT)
                logger.info(
                    "Payment %s passed all validation rules",
                    _make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(False),
                )

                state_log_util.create_finished_state_log(
                    end_state=State.PAYMENT_READY_FOR_ADDRESS_VALIDATION,
                    outcome=state_log_util.build_outcome(
                        "Success", payment_container.validation_container
                    ),
                    associated_model=payment_container.payment,
                    db_session=self.db_session,
                )


###
# Utility functions outside of class
# None of these require the DB or add any metrics
###


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
