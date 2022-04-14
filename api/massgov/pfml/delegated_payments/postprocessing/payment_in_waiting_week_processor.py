import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import Claim, Payment
from massgov.pfml.db.models.payments import PaymentAuditReportType
from massgov.pfml.delegated_payments.abstract_step_processor import AbstractStepProcessor
from massgov.pfml.delegated_payments.audit.delegated_payment_audit_util import (
    get_payment_in_waiting_week_status,
    stage_payment_audit_report_details,
)
from massgov.pfml.delegated_payments.delegated_payments_util import get_traceable_payment_details
from massgov.pfml.delegated_payments.postprocessing.payment_post_processing_util import (
    PostProcessingMetrics,
)
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PaymentInWaitingWeekProcessor(AbstractStepProcessor):
    Metrics = PostProcessingMetrics

    def __init__(self, step: Step) -> None:
        super().__init__(step)

    def process(self, payment: Payment) -> None:
        extra = get_traceable_payment_details(payment)
        claim: Claim = payment.claim

        payment_in_waiting_week_status = get_payment_in_waiting_week_status(
            payment, self.db_session
        )
        extra = {**extra, payment_in_waiting_week_status: payment_in_waiting_week_status}
        if payment_in_waiting_week_status == "":
            logger.info(
                "Payment date was not in the waiting week for the claim",
                extra=extra,
            )
            self.increment(self.Metrics.PAYMENT_NOT_IN_WAITING_WEEK_COUNT)
            return

        self.increment(self.Metrics.PAYMENT_IN_WAITING_WEEK_COUNT)
        logger.info(
            "Payment date was in the waiting week for the claim, adding notes to the audit report.",
            extra=extra,
        )

        message = f"Payment period start date: {payment.period_start_date}.  Claim start date: {claim.absence_period_start_date}. Payment in waiting week status: {payment_in_waiting_week_status}"
        stage_payment_audit_report_details(
            payment,
            PaymentAuditReportType.WAITING_WEEK,
            message,
            self.get_import_log_id(),
            self.db_session,
        )
