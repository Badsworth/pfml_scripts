from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, cast

import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Employee, PaymentDetails
from massgov.pfml.db.models.payments import MaximumWeeklyBenefitAmount
from massgov.pfml.delegated_payments.abstract_step_processor import AbstractStepProcessor
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    MaximumWeeklyBenefitsAuditMessageBuilder,
    PaymentContainer,
    PaymentScenario,
    PayPeriodGroup,
    PostProcessingMetrics,
    get_all_overpayments_associated_with_employee,
    get_all_paid_payments_associated_with_employee,
    make_payment_log,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


class MaximumWeeklyBenefitsStepProcessor(AbstractStepProcessor):
    """
    Mass limits the maximum amount we can pay a claimant in a given period. For example,
    in 2021, this limit is $850 The regulations detail the process for how this changes:
    https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXXII/Chapter175M/Section3

    See https://lwd.atlassian.net/wiki/spaces/API/pages/1885372428/Maximum+Weekly+Benefits+Logic
    for details on this algorithm, how it works, and why we do what we do.
    """

    maximum_amount_for_week: Optional[List[MaximumWeeklyBenefitAmount]] = None

    Metrics = PostProcessingMetrics

    def process(self, employee: Employee, payment_containers: List[PaymentContainer]) -> None:
        """
        This method updates the payment containers'
        audit_report_maximum_weekly_msg message if
        the payment would go over the maximum weekly cap
        """
        current_payment_ids = [
            payment_container.payment.payment_id for payment_container in payment_containers
        ]

        prior_payments = get_all_paid_payments_associated_with_employee(
            employee.employee_id, current_payment_ids, self.db_session
        )

        # Overpayments are effectively just prior payments (generally negative), so just add them
        # to the list of prior payments for the purposes of the calculation.
        overpayments = get_all_overpayments_associated_with_employee(
            employee.employee_id, self.db_session
        )
        prior_payments.extend(overpayments)

        # Filter out previously errored payments + adhoc payments
        payment_containers_to_process = self._filter_payments_from_maximum_weekly_processing(
            payment_containers
        )

        # Determine the relevant pay_periods
        # and adds prior payments to those pay_periods
        pay_periods = self._initialize_payment_pay_periods(
            payment_containers_to_process, prior_payments
        )

        # Process all of the payments and determine which
        # payments go over the maximum weekly cap.
        payment_containers_over_cap = self._determine_payments_over_cap(
            payment_containers_to_process, pay_periods
        )

        # Now we know which payments are/are not payable. For the
        # non-payable ones, process those payments and add an error msg
        for errored_payment_container in payment_containers_over_cap:
            msg_builder = MaximumWeeklyBenefitsAuditMessageBuilder(errored_payment_container)
            errored_payment_container.maximum_weekly_audit_report_msg = (
                msg_builder.build_simple_msg()
            )
            errored_payment_container.maximum_weekly_full_details_msg = (
                msg_builder.build_complex_msg()
            )

    def _filter_payments_from_maximum_weekly_processing(
        self, payment_containers: List[PaymentContainer],
    ) -> List[PaymentContainer]:
        payment_containers_to_process = []

        for payment_container in payment_containers:
            # Adhoc payments do not factor into the calculation, and both
            # automatically pass the maximum weekly cap rule and don't cause
            # other payments to fail that rule.
            if payment_container.payment.is_adhoc_payment:
                logger.info(
                    "Payment %s is an adhoc payment and will not factor into the maximum weekly cap calculation.",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(),
                )
                self.increment(self.Metrics.PAYMENT_SKIPPED_FOR_CAP_ADHOC_COUNT)

            else:
                payment_containers_to_process.append(payment_container)

        payment_containers_to_process.sort()
        return payment_containers_to_process

    def _get_maximum_amount_for_week(self, start_date: date) -> Decimal:
        # Determine the maximum amount allowed for a given week
        # Cache the result from the DB and use that for processing.

        if not self.maximum_amount_for_week:
            results = (
                self.db_session.query(MaximumWeeklyBenefitAmount)
                .order_by(MaximumWeeklyBenefitAmount.effective_date.desc())
                .all()
            )
            self.maximum_amount_for_week = results

        # Find the closest maximum weekly amount that comes before the payments start date
        for record in self.maximum_amount_for_week:
            if record.effective_date <= start_date:
                return record.maximum_weekly_benefit_amount

        raise Exception("No maximum weekly amount configured for %s" % str(start_date))

    def _initialize_payment_pay_periods(
        self, payment_containers: List[PaymentContainer], prior_payments: List[PaymentContainer]
    ) -> List[PayPeriodGroup]:
        """
        Pre-compute all the pay_periods (7 day ranges) that we are going to need to check.
        For each payment, we need a 7-day pay_periods corresponding to every 7-day period
        that overlaps for even one day with the pay period that starts on a Sunday.
        """

        pay_periods = self._determine_pay_periods_for_payments(payment_containers)

        for prior_payment in prior_payments:
            # We don't care about whether the payment is payable
            # Historical payments may have gone over their caps
            # prior to us launching this feature.
            payment_distribution = self._get_payment_details_per_pay_period(
                prior_payment, pay_periods
            )
            prior_payment.payment_distribution = payment_distribution

            for pay_period, payment_details in payment_distribution.items():
                for payment_detail in payment_details:
                    pay_period.add_payment_from_details(
                        payment_detail, PaymentScenario.PREVIOUS_PAYMENT
                    )

        return pay_periods

    def _determine_pay_periods_for_payments(
        self, payment_containers: List[PaymentContainer]
    ) -> List[PayPeriodGroup]:
        """
        For each payment, we want any 7-day period that starts with a Sunday
        and that overlaps with the payments we are actively processing.
        """
        pay_periods = set()
        for payment_container in payment_containers:
            date_iter = cast(date, payment_container.payment.period_start_date) - timedelta(days=6)

            while date_iter <= cast(date, payment_container.payment.period_end_date):
                start_date, end_date = date_iter, date_iter + timedelta(days=6)

                # We only want 7-day periods beginning with Sunday which is weekday 6:
                # https://docs.python.org/3/library/datetime.html#datetime.date.weekday
                if start_date.weekday() == 6:
                    pay_period = PayPeriodGroup(start_date, end_date)
                    # pay_period is hashed on just the dates.
                    if pay_period not in pay_periods:
                        # Determine the maximum for the week
                        pay_period.maximum_weekly_amount = self._get_maximum_amount_for_week(
                            pay_period.start_date
                        )
                        pay_periods.add(pay_period)

                date_iter = date_iter + timedelta(days=1)

        return sorted(pay_periods, key=lambda pay_period: pay_period.start_date)

    def _determine_payments_over_cap(
        self,
        payment_containers_to_process: List[PaymentContainer],
        pay_periods: List[PayPeriodGroup],
    ) -> List[PaymentContainer]:
        """
        Process all current payments and determine which of them go over the maximum weekly cap
        """
        payment_containers_over_cap = []
        for payment_container in payment_containers_to_process:
            # Get how much each payment would contribute per pay_period
            payment_distribution = self._get_payment_details_per_pay_period(
                payment_container, pay_periods, validate_payment_details=True
            )
            payment_container.payment_distribution = payment_distribution

            absence_case_id = payment_container.payment.claim.fineos_absence_id

            # Check all pay_periods if we could pay the amount
            is_payable = True
            for pay_period, payment_details in payment_distribution.items():
                for payment_detail in payment_details:
                    # We do not check if a payment is over the cap
                    # for a given week if the payments are all from one claim
                    # FINEOS calculates maximum amount differently than we do here
                    # so can potentially put two separate payments in one week
                    # that are under the cap when you look at a claim as a whole (which we can't see).
                    if (
                        absence_case_id not in pay_period.absence_case_ids
                        and pay_period.get_amount_available_in_pay_period() < payment_detail.amount
                    ):
                        is_payable = False
                        payment_container.pay_periods_over_cap.append((pay_period, payment_detail))

            # If the payment didn't go over the cap
            # Add the payment to the list of payable payments
            # and add the amount
            if is_payable:
                self.increment(self.Metrics.PAYMENT_CAP_PAYMENT_ACCEPTED_COUNT)
                payment_scenario = PaymentScenario.CURRENT_PAYABLE_PAYMENT
                logger.info(
                    "Payment %s passed the maximum weekly check",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(),
                )

            else:
                self.increment(self.Metrics.PAYMENT_CAP_PAYMENT_ERROR_COUNT)
                payment_containers_over_cap.append(payment_container)
                payment_scenario = PaymentScenario.UNPAYABLE_PAYMENT
                logger.info(
                    "Payment %s failed the maximum weekly check",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(),
                )

            for pay_period, payment_details in payment_distribution.items():
                for payment_detail in payment_details:
                    pay_period.add_payment_from_details(payment_detail, payment_scenario)

        return payment_containers_over_cap

    def _get_payment_details_per_pay_period(
        self,
        payment_container: PaymentContainer,
        pay_periods: List[PayPeriodGroup],
        validate_payment_details: bool = False,
    ) -> Dict[PayPeriodGroup, List[PaymentDetails]]:
        pay_period_to_details: Dict[PayPeriodGroup, List[PaymentDetails]] = {}

        payment_details_added = 0
        for pay_period in pay_periods:
            for payment_detail in payment_container.payment.payment_details:
                if (
                    pay_period.start_date
                    <= cast(date, payment_detail.period_start_date)
                    <= pay_period.end_date
                ):
                    if pay_period not in pay_period_to_details:
                        pay_period_to_details[pay_period] = []

                    pay_period_to_details[pay_period].append(payment_detail)
                    payment_details_added += 1

        payment_details_len = len(payment_container.payment.payment_details)

        # Every type of payment we work with should have the payment
        # details object set, but if it isn't and we're not working
        # with a current payment (where we set the validate parameter)
        # we just want to log a warning and update a metric accordingly.
        if payment_details_len == 0:
            self.increment(self.Metrics.PAYMENT_DETAIL_MISSING_COUNT)
            logger.warning(
                "Payment details for payment %s missing.",
                make_payment_log(payment_container.payment),
            )

            if validate_payment_details:
                raise Exception(
                    "Current payment %s is missing payment details info which is required."
                    % make_payment_log(payment_container.payment)
                )

        # We only pass in validate_payment_details for current payments
        # as we expect older payments to not necessarily overlap entirely
        # with the payments we're processing
        if validate_payment_details and payment_details_added != payment_details_len:
            raise Exception(
                "Payment %s only had %i of %i payment details map to pay periods %s."
                % (
                    make_payment_log(payment_container.payment),
                    payment_details_added,
                    payment_details_len,
                    pay_periods,
                )
            )

        return pay_period_to_details
