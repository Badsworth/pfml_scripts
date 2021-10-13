import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class GeneratePub1220filingStep(Step):
    def run_step(self) -> None:
        self._generate_pub_1220_filing()

    def _generate_pub_1220_filing(self) -> None:
        logger.info("1099 Documents - Generate Pub 1220 filing Step")
