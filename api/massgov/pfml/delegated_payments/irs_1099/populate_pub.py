import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulatePubStep(Step):
    def run_step(self) -> None:
        self._populate_pub()

    def _populate_pub(self) -> None:
        logger.info("1099 Documents - Populate Pub Step")
