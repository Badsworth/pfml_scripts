import os
import uuid
from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import State
from massgov.pfml.db.models.payments import (
    FineosWritebackDetails,
    FineosWritebackTransactionStatus,
    MaximumWeeklyBenefitAmount,
    PaymentAuditReportType,
)
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    stage_payment_audit_report_details,
)
from massgov.pfml.delegated_payments.postprocessing.maximum_weekly_benefits_processor import (
    MaximumWeeklyBenefitsStepProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    EmployeePaymentGroup,
    PaymentContainer,
    PostProcessingMetrics,
    determine_best_payments_under_cap,
    format_dates,
    get_all_paid_payments_associated_with_employee,
    get_date_tuple,
    make_payment_log,
    sum_payments,
)
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.util.datetime import get_period_in_weeks

logger = massgov.pfml.util.logging.get_logger(__name__)


class PaymentPostProcessingStep(Step):
    """
    This step runs after our payment extract step and
    handles any post-processing on payments, that is, any
    validation rules that need to be run for a payment across
    a wider swath of data (eg. comparing all payments for a claimant)
    """

    use_new_maximum_weekly_logic: bool = False

    Metrics = PostProcessingMetrics

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

        weeks = get_period_in_weeks(start_date, end_date)

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
        self.use_new_maximum_weekly_logic = (
            os.environ.get("USE_NEW_MAXIMUM_WEEKLY_LOGIC", "0") == "1"
        )

        try:
            payment_containers = self._get_payments_awaiting_post_processing_validation()

            # Run validations that process payments
            # by group them under a single employee
            self._process_payments_across_employee(payment_containers)

            # After all validations are run, move states of the payments
            if self.use_new_maximum_weekly_logic:
                self._handle_state_transition(payment_containers)
            else:
                self._move_payments_to_new_state(payment_containers)

            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            logger.exception("Error during payment post processing step")
            raise

    def _get_payments_awaiting_post_processing_validation(self) -> List[PaymentContainer]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
            db_session=self.db_session,
        )

        payment_containers = []
        for state_log in state_logs:
            self.increment(self.Metrics.PAYMENTS_PROCESSED_COUNT)
            payment_containers.append(PaymentContainer(state_log.payment))

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

        maximum_weekly_processor = MaximumWeeklyBenefitsStepProcessor(self)
        # Run various validation rules on these groups
        for employee_id, payment_containers in employee_to_containers.items():
            # Employee ID was useful for grouping, but we want the employee itself
            employee = payment_containers[0].payment.claim.employee
            logger.info(
                "Processing %i payments in batch for employee ID %s",
                len(payment_containers),
                employee_id,
            )
            # Validate that payments aren't exceeding a maximum cap
            if self.use_new_maximum_weekly_logic:
                maximum_weekly_processor.process(employee, payment_containers)
            else:
                self._validate_payments_not_exceeding_cap(employee_id, payment_containers)

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
        prior_payments = get_all_paid_payments_associated_with_employee(
            employee_id, current_payment_ids, self.db_session
        )

        # group the payments by start+end period. We only care about the periods
        # for the new payments from this batch
        # Create a dictionary that maps from a tuple of start/end dates to a a tuple
        # of prior_payments + current payment containers. These are contained in classes
        # to preserve simple names
        date_range_to_payments: Dict[Tuple[date, date], EmployeePaymentGroup] = {}
        for payment_container in payment_containers:
            # Adhoc payments do not factor into the calculation, and both
            # automatically pass the maximum weekly cap rule and don't cause
            # other payments to fail that rule.
            if payment_container.payment.is_adhoc_payment:
                logger.info(
                    "Payment %s is an adhoc payment and will not factor into the maximum weekly cap calculation.",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(False),
                )
                continue

            date_tuple = get_date_tuple(payment_container.payment)

            if date_tuple not in date_range_to_payments:
                date_range_to_payments[date_tuple] = EmployeePaymentGroup(employee_id)

            date_range_to_payments[date_tuple].current_payments.append(payment_container)

        # For any prior payments that have the same leave periods, add them to the list as well
        for prior_payment in prior_payments:
            date_tuple = get_date_tuple(prior_payment.payment)

            if date_tuple in date_range_to_payments:
                date_range_to_payments[date_tuple].prior_payments.append(prior_payment.payment)

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
        if sum_payments(prior_payment_sum, current_payment_containers) <= max_amount:
            # Increment the counter for each accepted payment
            for _ in current_payment_containers:
                self.increment(self.Metrics.PAYMENT_CAP_ALL_ACCEPTED_COUNT)
            return

        accepted_payment_containers = determine_best_payments_under_cap(
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
                msg = f"This payment for ${payment_container.payment.amount} exceeded the maximum amount allowable (${max_amount}) for a claimant for the pay period of {format_dates(period_start, period_end)}."

                if payment_group.prior_payments:
                    prior_payment_msgs = []
                    for prior_payment in payment_group.prior_payments:
                        prior_payment_msgs.append(make_payment_log(prior_payment, True))

                    msg += f" We previously paid {', '.join(prior_payment_msgs)}."

                if accepted_payment_containers:
                    accepted_payment_msgs = []
                    for accepted_payment in accepted_payment_containers:
                        accepted_payment_msgs.append(
                            make_payment_log(accepted_payment.payment, True)
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
                    "Payment %s failed a validation rule",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(True),
                )

                # Add it to the state for being put in the payment error report
                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_PAYMENT_ADD_TO_PAYMENT_ERROR_REPORT,
                    outcome=state_log_util.build_outcome(
                        "Payment failed post-processing validation",
                        payment_container.validation_container,
                    ),
                    associated_model=payment_container.payment,
                    db_session=self.db_session,
                )

                self._manage_pei_writeback_state(payment_container)

            # Otherwise it is ready for address validation
            else:
                self.increment(self.Metrics.PAYMENTS_PASSED_VALIDATION_COUNT)
                logger.info(
                    "Payment %s passed all validation rules",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(False),
                )

                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
                    outcome=state_log_util.build_outcome(
                        "Success", payment_container.validation_container
                    ),
                    associated_model=payment_container.payment,
                    db_session=self.db_session,
                )

    def _manage_pei_writeback_state(self, payment_container: PaymentContainer) -> None:
        # Add it to a state for getting put in a PEI writeback
        # to indicate that the payment errored to anyone looking in FINEOS
        # This is in flow DELEGATED_PEI_WRITEBACK
        state_log_util.create_finished_state_log(
            end_state=State.DELEGATED_ADD_TO_FINEOS_WRITEBACK,
            outcome=state_log_util.build_outcome(
                "Payment failed post-processing validation", payment_container.validation_container
            ),
            associated_model=payment_container.payment,
            db_session=self.db_session,
        )

        transaction_status = None
        reasons = payment_container.validation_container.get_reasons()
        if payments_util.ValidationReason.PAYMENT_EXCEEDS_PAY_PERIOD_CAP in reasons:
            transaction_status = FineosWritebackTransactionStatus.TOTAL_BENEFITS_OVER_CAP
        else:
            raise Exception(
                "No transaction status configured for any validation issue %s for payment %s"
                % (reasons, make_payment_log(payment_container.payment))
            )

        writeback_details = FineosWritebackDetails(
            payment=payment_container.payment,
            transaction_status_id=transaction_status.transaction_status_id,
            import_log_id=cast(int, self.get_import_log_id()),
        )
        self.db_session.add(writeback_details)

    def _handle_state_transition(self, payment_containers: List[PaymentContainer]) -> None:
        for payment_container in payment_containers:

            # Create a payment log to track what was done
            payments_util.create_payment_log(
                payment_container.payment,
                self.get_import_log_id(),
                self.db_session,
                payment_container.get_payment_log_record(),
            )
            maximum_weekly_audit_msg = payment_container.maximum_weekly_audit_report_msg

            # If it has issues, add an audit log report
            if maximum_weekly_audit_msg:
                stage_payment_audit_report_details(
                    payment_container.payment,
                    PaymentAuditReportType.MAX_WEEKLY_BENEFITS,
                    maximum_weekly_audit_msg,
                    self.get_import_log_id(),
                    self.db_session,
                )

                self.increment(self.Metrics.PAYMENTS_FAILED_VALIDATION_COUNT)
                logger.info(
                    "Payment %s failed a validation rule, creating audit report details",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(),
                )

            else:
                self.increment(self.Metrics.PAYMENTS_PASSED_VALIDATION_COUNT)

                logger.info(
                    "Payment %s passed all validation rules",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(),
                )

            additional_outcome_details = {}
            if payment_container.maximum_weekly_full_details_msg:
                additional_outcome_details[
                    "maximum_weekly_details"
                ] = payment_container.maximum_weekly_full_details_msg

            # Always allow it past this step, we simply add info for the audit report here.
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
                outcome=state_log_util.build_outcome(
                    "Completed post processing",
                    validation_container=None,
                    **additional_outcome_details,
                ),
                associated_model=payment_container.payment,
                db_session=self.db_session,
            )
