import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class Merge1099Step(Step):
    def run_step(self) -> None:
        self._merge_1099()

    def _merge_1099(self) -> None:
        logger.info("1099 Documents - Merge 1099 Documents Step")
