import enum

import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class Upload1099DocumentsStep(Step):
    class Metrics(str, enum.Enum):
        DOCUMENT_COUNT = "document_count"
        DOCUMENT_ERROR = "document_errors"

    def run_step(self) -> None:
        self._upload_1099_documents()

    def _upload_1099_documents(self) -> None:
        logger.info("1099 Documents - Upload 1099 Documents Step")
