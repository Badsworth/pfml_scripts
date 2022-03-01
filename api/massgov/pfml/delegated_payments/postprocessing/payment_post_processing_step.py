from typing import List

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import State
from massgov.pfml.delegated_payments.postprocessing.dor_fineos_employee_name_mismatch_processor import (
    DORFineosEmployeeNameMismatchProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.dua_dia_reductions_processor import (
    DuaDiaReductionsProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.fineos_total_leave_duration_processor import (
    FineosTotalLeaveDurationProcessor,
)
from massgov.pfml.delegated_payments.postprocessing.payment_date_mismatch_processor import (
    PaymentDateMismatchProcessor,
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
        payment_containers = self._get_payments_awaiting_post_processing_validation()

        # Run processing on payments
        self._process_payments(payment_containers)

        # After all validations are run, move states of the payments
        self._handle_state_transition(payment_containers)

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
        """Post process payments individually"""
        dua_dia_processor = DuaDiaReductionsProcessor(self)
        name_mismatch_processor = DORFineosEmployeeNameMismatchProcessor(self)
        payment_date_mismatch_processor = PaymentDateMismatchProcessor(self)
        leave_duration_processor = FineosTotalLeaveDurationProcessor(self)

        for payment_container in payment_containers:
            dua_dia_processor.process(payment_container.payment)
            name_mismatch_processor.process(payment_container.payment)
            payment_date_mismatch_processor.process(payment_container.payment)
            leave_duration_processor.process(payment_container.payment)

    def _handle_state_transition(self, payment_containers: List[PaymentContainer]) -> None:
        for payment_container in payment_containers:

            # Create a payment log to track what was done
            payments_util.create_payment_log(
                payment_container.payment,
                self.get_import_log_id(),
                self.db_session,
                payment_container.get_payment_log_record(),
            )

            logger.info(
                "Payment post-processing complete for %s",
                make_payment_log(payment_container.payment),
                extra=payment_container.get_traceable_details(
                    state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING
                ),
            )

            # We simply add info for the audit report here without erroring
            state_log_util.create_finished_state_log(
                end_state=State.DELEGATED_PAYMENT_STAGED_FOR_PAYMENT_AUDIT_REPORT_SAMPLING,
                outcome=state_log_util.build_outcome(
                    "Completed post processing", validation_container=None,
                ),
                associated_model=payment_container.payment,
                db_session=self.db_session,
            )
