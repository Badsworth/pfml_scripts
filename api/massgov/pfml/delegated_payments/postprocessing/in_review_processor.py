import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.delegated_payments.abstract_step_processor import AbstractStepProcessor
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    stage_payment_audit_report_details,
)
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PaymentContainer,
    PostProcessingMetrics,
    make_payment_log,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


class InReviewProcessor(AbstractStepProcessor):
    Metrics = PostProcessingMetrics

    def process(self, payment_container: PaymentContainer) -> None:
        if payment_container.payment.leave_request_decision == "In Review":
            logger.info(
                "Payment %s has an in review leave plan",
                make_payment_log,
                extra=payment_container.get_traceable_details(),
            )
            self.increment(self.Metrics.PAYMENT_LEAVE_PLAN_IN_REVIEW_COUNT)

            stage_payment_audit_report_details(
                payment_container.payment,
                PaymentAuditReportType.LEAVE_PLAN_IN_REVIEW,
                "Leave Plan is still In Review",
                self.get_import_log_id(),
                self.db_session,
            )
