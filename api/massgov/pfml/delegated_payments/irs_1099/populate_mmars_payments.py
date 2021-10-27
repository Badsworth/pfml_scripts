import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulateMmarsPaymentsStep(Step):
    def run_step(self) -> None:
        self._populate_mmars_payments()

    def _populate_mmars_payments(self) -> None:
        logger.info("1099 Documents - Populate Mmars Payments Step")
