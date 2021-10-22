import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulateRefundsStep(Step):
    def run_step(self) -> None:
        self._populate_refunds()

    def _populate_refunds(self) -> None:
        logger.info("1099 Documents - Populate Refunds Step")
