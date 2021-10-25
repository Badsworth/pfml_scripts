import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class Populate1099Step(Step):
    def run_step(self) -> None:
        self._populate_1099()

    def _populate_1099(self) -> None:
        logger.info("1099 Documents - Populate 1099 Step")
