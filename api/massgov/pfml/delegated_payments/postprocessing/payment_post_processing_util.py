import enum
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from functools import total_ordering
from typing import Any, Dict, List, Optional, Set, Tuple

import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Claim,
    LatestStateLog,
    Payment,
    PaymentDetails,
    PaymentTransactionType,
    State,
    StateLog,
)

logger = massgov.pfml.util.logging.get_logger(__name__)

DATE_FORMAT = "%Y-%m-%d"


class PostProcessingMetrics(str, enum.Enum):
    # General metrics
    PAYMENTS_PROCESSED_COUNT = "payments_processed_count"
    PAYMENTS_FAILED_VALIDATION_COUNT = "payments_failed_validation_count"
    PAYMENTS_PASSED_VALIDATION_COUNT = "payments_passed_valdiation_count"
    # Metrics specific to the payment cap check
    PAYMENT_CAP_PAYMENT_ERROR_COUNT = "payment_cap_payment_error_count"
    PAYMENT_CAP_PAYMENT_ACCEPTED_COUNT = "payment_cap_payment_accepted_count"

    PAYMENT_SKIPPED_FOR_CAP_ADHOC_COUNT = "payment_excluded_for_cap_adhoc_count"

    PAYMENT_DETAIL_MISSING_COUNT = "payment_detail_missing_count"

    # Metrics specific to the in review processor
    PAYMENT_LEAVE_PLAN_IN_REVIEW_COUNT = "payment_leave_plan_in_review"


@total_ordering  # Handles supporting sort with just __eq__ and __lt__
@dataclass
class PaymentContainer:
    """
    Container for group a payment with its validation container
    """

    payment: Payment

    pay_periods_over_cap: List[Tuple["PayPeriodGroup", PaymentDetails]] = field(
        init=False, default_factory=list
    )

    payment_distribution: Optional[Dict["PayPeriodGroup", List[PaymentDetails]]] = None

    maximum_weekly_audit_report_msg: Optional[str] = None
    maximum_weekly_full_details_msg: Optional[str] = None

    def __post_init__(self) -> None:
        self.validation_container = payments_util.ValidationContainer(str(self.payment.payment_id))

    def _get_sort_key(self) -> Any:
        # Sorting is done based on
        # the earliest payment period start date
        # For ties, rely on when the absence case was created
        # If still tied, sort based on the payment's I value
        # which is guaranteed to be unique and will keep sorting consistent
        # (Plus the I value is incrementing in FINEOS, so makes some sense to use)
        return (
            self.payment.period_start_date,
            self.payment.absence_case_creation_date,
            self.payment.fineos_pei_i_value,
        )

    def __eq__(self, other):
        return self._get_sort_key() == other._get_sort_key()

    def __lt__(self, other):
        return self._get_sort_key() < other._get_sort_key()

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

    def get_payment_log_record(self) -> Dict[str, Any]:
        record: Dict[str, Any] = {}

        maximum_weekly_benefits_info: Dict[str, Any] = {}

        if self.payment_distribution:
            payment_distribution_info: Dict[str, Any] = {}
            for pay_period, details in self.payment_distribution.items():
                pay_period_str = str(pay_period)
                if pay_period_str not in payment_distribution_info:
                    payment_distribution_info[pay_period_str] = []

                for detail in details:
                    payment_distribution_info[pay_period_str].append(detail.for_json())

            maximum_weekly_benefits_info["payment_distribution"] = payment_distribution_info

        pay_periods_over_cap_info = []
        for pay_period, _ in self.pay_periods_over_cap:
            pay_periods_over_cap_info.append(str(pay_period))
        maximum_weekly_benefits_info["pay_periods_over_cap"] = pay_periods_over_cap_info

        record["maximum_weekly_benefits"] = maximum_weekly_benefits_info

        return record


@dataclass
class PaymentDetailsGroup:
    """
    Container class for group a payment and payment details
    that are associated with a single week. May not contain
    every payment detail record associated with the payment
    if certain pay periods of a payment overlap with other weeks.
    """

    payment: Payment
    payment_details: List[PaymentDetails] = field(default_factory=list)


class PaymentScenario(str, enum.Enum):
    PREVIOUS_PAYMENT = "Previous Payments"
    CURRENT_PAYABLE_PAYMENT = "Current Payable Payments"
    UNPAYABLE_PAYMENT = "Unpayable Payments"


@dataclass
class PayPeriodGroup:
    """
    Class to represent and contain information about a
    pay period (defined as the 7 day period Sun -> Sat).
    Will contain all payment information, including the
    pay period level information for a payment that overlaps
    for a given claimant.

    Most notably, contains all information for:
    * Prior Payments -> Payments from prior runs + overpayments
    * "Payable" payments -> Payments from the current batch that are deemed payable
    * "Unpayable" payments -> Payments from the current batch that would go
                              over the cap for a given week (not necessarily "this" week)
    """

    start_date: date
    end_date: date
    maximum_weekly_amount: Decimal = Decimal("0.00")

    amount_previously_paid: Decimal = Decimal("0.00")  # Sum of all prior payments
    amount_paid_from_this_batch: Decimal = Decimal(
        0
    )  # Sum of all payments from current batch that can be paid
    amount_unpayable_from_this_batch: Decimal = Decimal("0.00")

    previously_paid_payment_details: Dict[uuid.UUID, PaymentDetailsGroup] = field(
        default_factory=dict
    )
    payable_payment_details: Dict[uuid.UUID, PaymentDetailsGroup] = field(default_factory=dict)
    unpayable_payment_details: Dict[uuid.UUID, PaymentDetailsGroup] = field(default_factory=dict)

    absence_case_ids: Set[str] = field(default_factory=set)

    def __hash__(self):
        # Hash for pay_period group equivalency is based only on start/end date.
        return hash((self.start_date, self.end_date))

    def __repr__(self):
        return f"{self.start_date} -> {self.end_date}"

    def __str__(self):
        return self.__repr__()

    def get_total_amount(self) -> Decimal:
        return self.amount_previously_paid + self.amount_paid_from_this_batch

    def get_amount_available_in_pay_period(self) -> Decimal:
        return max(Decimal("0.00"), self.maximum_weekly_amount - self.get_total_amount())

    def add_payment_from_details(
        self, payment_details: PaymentDetails, payment_scenario: PaymentScenario
    ) -> None:
        amount = payment_details.amount
        payment = payment_details.payment
        self.absence_case_ids.add(str(payment.claim.fineos_absence_id))

        details_to_update = None
        if payment_scenario == PaymentScenario.PREVIOUS_PAYMENT:
            self.amount_previously_paid += amount
            details_to_update = self.previously_paid_payment_details
        elif payment_scenario == PaymentScenario.CURRENT_PAYABLE_PAYMENT:
            self.amount_paid_from_this_batch += amount
            details_to_update = self.payable_payment_details
        else:
            self.amount_unpayable_from_this_batch += amount
            details_to_update = self.unpayable_payment_details

        if payment.payment_id not in details_to_update:
            details_to_update[payment.payment_id] = PaymentDetailsGroup(payment)

        details_to_update[payment.payment_id].payment_details.append(payment_details)


#################
# Helper Methods
#################


def get_all_paid_payments_associated_with_employee(
    employee_id: uuid.UUID, current_payment_ids: List[uuid.UUID], db_session: db.Session
) -> List[PaymentContainer]:

    # Get all payment IDs of payments associated with the same employee
    # That aren't the payments we're attempting to validate, that are
    # standard payments (eg. no cancellations, overpayments, etc.) that are
    # not adhoc payments (adhoc payments don't factor into the calculation whatsoever)
    subquery = (
        db_session.query(Payment.payment_id)
        .join(Claim)
        .filter(
            Claim.employee_id == employee_id,
            Payment.payment_transaction_type_id
            == PaymentTransactionType.STANDARD.payment_transaction_type_id,
            Payment.payment_id.notin_(current_payment_ids),
            Payment.is_adhoc_payment != True,  # noqa: E712
        )
    )

    # For the payment IDs fetched above, look for any payments
    # that we have sent to PUB or have returned as paid
    # Payments that errored after sending to PUB will be excluded
    # as they're moved to a separate end state
    payments = (
        db_session.query(Payment)
        .join(StateLog)
        .join(LatestStateLog)
        .filter(
            Payment.payment_id.in_(subquery),
            StateLog.end_state_id.in_(payments_util.Constants.PAID_STATE_IDS),
        )
        .all()
    )

    containers = []
    for payment in payments:
        containers.append(PaymentContainer(payment))

    return containers


def get_all_overpayments_associated_with_employee(
    employee_id: uuid.UUID, db_session: db.Session
) -> List[PaymentContainer]:
    # Query to grab all overpayments for a claimant
    # that are either standard Overpayments OR Overpayment Adjustments
    # (Excludes recovery scenarios that represent claimant paying back an overpayment)
    subquery = (
        db_session.query(Payment.payment_id)
        .join(Claim)
        .filter(
            Claim.employee_id == employee_id,
            Payment.payment_transaction_type_id
            == PaymentTransactionType.OVERPAYMENT.payment_transaction_type_id,
        )
    )

    overpayments = (
        db_session.query(Payment)
        .join(StateLog)
        .filter(
            Payment.payment_id.in_(subquery),
            StateLog.end_state_id == State.DELEGATED_PAYMENT_PROCESSED_OVERPAYMENT.state_id,
        )
        .all()
    )

    overpayment_containers = []
    for overpayment in overpayments:
        overpayment_containers.append(PaymentContainer(overpayment))

    return overpayment_containers


def make_payment_log(payment: Payment, include_amount: bool = False) -> str:
    log_message = f"C={payment.fineos_pei_c_value},I={payment.fineos_pei_i_value},AbsenceCaseId={payment.claim.fineos_absence_id}"
    if include_amount:
        log_message += f",Amount={payment.amount}"

    return f"[{log_message}]"


def get_reduction_amount(payment_amount: Decimal, amount_available: Decimal) -> Decimal:
    if amount_available >= payment_amount:
        return Decimal(0)
    else:
        return payment_amount - amount_available


def make_payment_detail_log(
    payment_detail: PaymentDetails, amount_available: Optional[Decimal] = None
) -> str:
    msg = f"[StartDate={payment_detail.period_start_date},EndDate={payment_detail.period_end_date},Amount=${payment_detail.amount}]"

    if amount_available is not None:
        reduction_amount = get_reduction_amount(payment_detail.amount, amount_available)
        if reduction_amount == Decimal(0):
            msg += " does not require a reduction for this pay period."
        else:
            msg += f" is over the cap by ${reduction_amount}"

    return msg


@dataclass
class MaximumWeeklyBenefitsAuditMessageBuilder:
    """
    Utility class for building the audit message
    for the maximum weekly check. Separated into
    another class to minimize the complexity of the
    core logic for checking.
    """

    payment_container: PaymentContainer

    lines: List[str] = field(init=False, default_factory=list)

    def build_simple_msg(self) -> str:
        self.lines = []  # Empty the lines
        self._add_absence_case_ids()
        self._add_blank_line()
        self._add_pay_period_info_header()
        self._add_simple_pay_period_info()

        return "\n".join(self.lines)

    def build_complex_msg(self) -> str:
        self.lines = []  # Empty the lines
        self._add_header()
        self._add_blank_line()
        self._add_absence_case_ids()
        self._add_blank_line()

        self._add_pay_period_info_header()
        self._add_all_pay_period_info()

        return "\n".join(self.lines)

    def _add_line(self, line: str, is_indented: bool = False) -> None:
        if is_indented:
            line = "\t" + line
        self.lines.append(line)

    def _add_blank_line(self) -> None:
        self.lines.append("")

    def _add_separator_line(self) -> None:
        self.lines.append("-" * 50)

    def _add_header(self) -> None:
        msg = f"This payment for {make_payment_log(self.payment_container.payment, True)} exceeded the maximum amount allowable for a 7-day period."
        self._add_line(msg)

    def _add_absence_case_ids(self) -> None:
        relevant_absence_case_ids = set()
        for pay_period, _ in self.payment_container.pay_periods_over_cap:
            relevant_absence_case_ids.update(pay_period.absence_case_ids)
        # Don't include the absence case of the payment itself
        if self.payment_container.payment.claim.fineos_absence_id in relevant_absence_case_ids:
            relevant_absence_case_ids.remove(self.payment_container.payment.claim.fineos_absence_id)

        msg = f"The payment overlapped with the following other claim(s): {','.join(relevant_absence_case_ids)}"
        self._add_line(msg)

    def _add_pay_period_info_header(self) -> None:
        msg = "It exceeded the cap for the following weeks + pay periods:"
        self._add_line(msg)

    def _add_all_pay_period_info(self) -> None:
        if self.payment_container.payment_distribution:
            for pay_period in self.payment_container.payment_distribution.keys():
                self._add_pay_period_overview(pay_period, False)

                self._add_pay_period_info(pay_period, PaymentScenario.PREVIOUS_PAYMENT)
                self._add_pay_period_info(pay_period, PaymentScenario.CURRENT_PAYABLE_PAYMENT)
                self._add_pay_period_info(pay_period, PaymentScenario.UNPAYABLE_PAYMENT)
        else:
            # Should not be possible, just making the type checker happy
            logger.error(
                "No pay_periods found for payment %s",
                make_payment_log(self.payment_container.payment),
            )

    def _add_simple_pay_period_info(self) -> None:
        # The audit report's simple message only details weeks/pay periods
        # that were over the cap, so we can just iterate over the ones we know are over
        if self.payment_container.pay_periods_over_cap:
            for pay_period, _ in self.payment_container.pay_periods_over_cap:
                self._add_pay_period_overview(pay_period, True)
        else:
            # Should not be possible, just making the type checker happy
            logger.error(
                "No pay_periods found for payment %s",
                make_payment_log(self.payment_container.payment),
            )

    def _add_pay_period_overview(self, pay_period: PayPeriodGroup, is_simple_format: bool) -> None:
        self._add_separator_line()
        pay_period_overview_msg = f"{pay_period}: Amount already paid=${pay_period.get_total_amount()}; AmountAvailable=${pay_period.get_amount_available_in_pay_period()}"

        # The simple format consolidates all of the info about
        # the amount a payment is over the cap into the overview message
        if is_simple_format:
            details_to_process = pay_period.unpayable_payment_details
            amount_available = pay_period.get_amount_available_in_pay_period()

            amount_attempting_to_pay = Decimal("0.00")
            for payment_detail_group in details_to_process.values():
                if (
                    payment_detail_group.payment.payment_id
                    != self.payment_container.payment.payment_id
                ):
                    continue

                for payment_details in payment_detail_group.payment_details:
                    amount_attempting_to_pay += payment_details.amount

            reduction_amount = get_reduction_amount(amount_attempting_to_pay, amount_available)
            pay_period_overview_msg += f"; Over the cap by ${reduction_amount}"

        self._add_line(pay_period_overview_msg)

        self._add_blank_line()

    def _add_pay_period_info(
        self, pay_period: PayPeriodGroup, payment_scenario: PaymentScenario
    ) -> None:
        amount_available = None  # We only want this for the unpayable scenario

        if payment_scenario == PaymentScenario.PREVIOUS_PAYMENT:
            details_to_process = pay_period.previously_paid_payment_details
            amount_paid_for_scenario = pay_period.amount_previously_paid
        elif payment_scenario == PaymentScenario.CURRENT_PAYABLE_PAYMENT:
            details_to_process = pay_period.payable_payment_details
            amount_paid_for_scenario = pay_period.amount_paid_from_this_batch
        else:
            details_to_process = pay_period.unpayable_payment_details
            amount_paid_for_scenario = pay_period.amount_unpayable_from_this_batch
            amount_available = pay_period.get_amount_available_in_pay_period()

        if not details_to_process:
            return

        else:
            pay_period_msg = f"{payment_scenario} (${amount_paid_for_scenario} total):"
            self._add_line(pay_period_msg)

            for payment_detail_group in details_to_process.values():
                payment_msg = f"{make_payment_log(payment_detail_group.payment)} with the following relevant pay periods:"
                self._add_line(payment_msg)

                for payment_details in payment_detail_group.payment_details:
                    payment_detail_msg = make_payment_detail_log(payment_details, amount_available)
                    self._add_line(payment_detail_msg, is_indented=True)

        self._add_blank_line()
