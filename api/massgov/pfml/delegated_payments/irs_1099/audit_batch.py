import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class AuditBatchStep(Step):
    def run_step(self) -> None:
        self._audit_batch()

    def _audit_batch(self) -> None:
        logger.info("1099 Documents - Audit Batch Step")
