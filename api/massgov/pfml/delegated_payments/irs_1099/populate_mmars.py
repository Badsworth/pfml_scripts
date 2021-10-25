import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulateMmarsStep(Step):
    def run_step(self) -> None:
        self._populate_mmars()

    def _populate_mmars(self) -> None:
        logger.info("1099 Documents - Populate Mmars Step")
