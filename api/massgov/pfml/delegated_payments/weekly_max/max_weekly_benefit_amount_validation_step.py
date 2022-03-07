import uuid
from typing import Dict, List, cast

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import State
from massgov.pfml.db.models.payments import FineosWritebackTransactionStatus
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PaymentContainer,
    make_payment_log,
)
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.delegated_payments.util.fineos_writeback_util import (
    create_payment_finished_state_log_with_writeback,
)
from massgov.pfml.delegated_payments.weekly_max.max_weekly_benefit_amount_util import (
    MaxWeeklyBenefitAmountMetrics,
)
from massgov.pfml.delegated_payments.weekly_max.maximum_weekly_benefits_processor import (
    MaximumWeeklyBenefitsStepProcessor,
)

logger = logging.get_logger(__name__)


class MaxWeeklyBenefitAmountValidationStep(Step):
    Metrics = MaxWeeklyBenefitAmountMetrics

    def run_step(self) -> None:
        payments_containers = self._get_payments_awaiting_max_weekly_benefit_amount_validation()
        self._process_max_weekly_benefit_amount_by_employee(payments_containers)
        self._handle_state_transition(payments_containers)

    def _get_payments_awaiting_max_weekly_benefit_amount_validation(self) -> List[PaymentContainer]:
        state_logs = state_log_util.get_all_latest_state_logs_in_end_state(
            associated_class=state_log_util.AssociatedClass.PAYMENT,
            end_state=State.PAYMENT_READY_FOR_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION,
            db_session=self.db_session,
        )

        payment_containers = []
        for state_log in state_logs:
            self.increment(self.Metrics.PAYMENTS_PROCESSED_COUNT)
            payment_containers.append(PaymentContainer(state_log.payment))

        return payment_containers

    def _process_max_weekly_benefit_amount_by_employee(
        self, payment_containers: List[PaymentContainer]
    ) -> None:
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
            payments_util.create_payment_log(
                payment_container.payment,
                self.get_import_log_id(),
                self.db_session,
                payment_container.get_payment_log_record(),
            )

            maximum_weekly_audit_msg = payment_container.maximum_weekly_audit_report_msg

            if maximum_weekly_audit_msg:
                maximum_weekly_full_details_msg = payment_container.maximum_weekly_full_details_msg

                self.increment(self.Metrics.PAYMENTS_FAILED_VALIDATION_COUNT)
                logger.info(
                    "Payment %s failed max weekly benefits amount validation rule, adding to error log",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(
                        state=State.PAYMENT_FAILED_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION
                    ),
                )

                additional_outcome_details = {}
                if maximum_weekly_full_details_msg:
                    additional_outcome_details[
                        "maximum_weekly_details"
                    ] = maximum_weekly_full_details_msg

                outcome = state_log_util.build_outcome(
                    maximum_weekly_audit_msg,
                    validation_container=None,
                    **additional_outcome_details,
                )

                create_payment_finished_state_log_with_writeback(
                    payment=payment_container.payment,
                    payment_end_state=State.PAYMENT_FAILED_MAX_WEEKLY_BENEFIT_AMOUNT_VALIDATION,
                    payment_outcome=outcome,
                    writeback_transaction_status=FineosWritebackTransactionStatus.WEEKLY_BENEFITS_AMOUNT_EXCEEDS_850,
                    writeback_outcome=outcome,
                    db_session=self.db_session,
                    import_log_id=self.get_import_log_id(),
                )

            else:
                self.increment(self.Metrics.PAYMENTS_PASSED_VALIDATION_COUNT)

                logger.info(
                    "Payment %s passed max weekly benefit amount validation rules",
                    make_payment_log(payment_container.payment),
                    extra=payment_container.get_traceable_details(
                        state=State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK
                    ),
                )

                state_log_util.create_finished_state_log(
                    end_state=State.DELEGATED_PAYMENT_POST_PROCESSING_CHECK,
                    outcome=state_log_util.build_outcome(
                        "Completed max weekly benefit amount validation", validation_container=None
                    ),
                    associated_model=payment_container.payment,
                    db_session=self.db_session,
                )
