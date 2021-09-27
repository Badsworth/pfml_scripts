import uuid
from typing import Dict, List, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import State
from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    stage_payment_audit_report_details,
)
from massgov.pfml.delegated_payments.postprocessing.dua_dia_reductions_processor import (
    DuaDiaReductionsProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.in_review_processor import InReviewProcessor
from massgov.pfml.delegated_payments.postprocessing.maximum_weekly_benefits_processor import (
    MaximumWeeklyBenefitsStepProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PaymentContainer,
    PostProcessingMetrics,
    make_payment_log,
)
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PaymentPostProcessingStep(Step):
    """
    This step runs after our payment extract step and
    handles any post-processing on payments, that is, any
    validation rules that need to be run for a payment across
    a wider swath of data (eg. comparing all payments for a claimant)
    """

    Metrics = PostProcessingMetrics

    def run_step(self):
        """
        Grabs all payments in the awaiting state, and runs
        various validation rules on them. If any issue
        is encountered, the validation container attached to the
        payment will be updated accordingly. All validation rules
        run even if a payment has errored in a prior step so that
        all issues can be communicated in the eventual error report.
        """

        try:
            payment_containers = self._get_payments_awaiting_post_processing_validation()

            # Run processing on payments
            self._process_payments(payment_containers)

            # After all validations are run, move states of the payments
            self._handle_state_transition(payment_containers)
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

    def _process_payments(self, payment_containers: List[PaymentContainer]) -> None:
        self._process_payments_individually(payment_containers)
        self._process_payments_across_employee(payment_containers)

    def _process_payments_individually(self, payment_containers: List[PaymentContainer]) -> None:
        """Post process payments individually"""
        dua_dia_processor = DuaDiaReductionsProcessor(self)
        in_review_processor = InReviewProcessor(self)

        for payment_container in payment_containers:
            dua_dia_processor.process(payment_container.payment)
            in_review_processor.process(payment_container)

    def _process_payments_across_employee(self, payment_containers: List[PaymentContainer]) -> None:
        """Post process payments grouped by employee"""
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
            maximum_weekly_processor.process(employee, payment_containers)

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
