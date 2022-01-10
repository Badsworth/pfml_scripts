import enum

import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class PopulateWithholdingsStep(Step):
    class Metrics(str, enum.Enum):
        WITHHOLDING_COUNT = "withholding_count"

    def run_step(self) -> None:
        self._populate_withholdings()

    def _populate_withholdings(self) -> None:
        logger.info("1099 Documents - Populate Withholdings Step")
