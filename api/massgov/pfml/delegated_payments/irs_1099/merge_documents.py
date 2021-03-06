import enum

import requests

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class Merge1099Step(Step):
    class Metrics(str, enum.Enum):
        DOCUMENT_COUNT = "document_count"
        DOCUMENT_ERROR = "document_errors"

    def run_step(self) -> None:
        self.pdfApiEndpoint = pfml_1099_util.get_pdf_api_merge_endpoint()
        self._merge_1099_documents()

    def _merge_1099_documents(self) -> None:
        logger.info("1099 Documents - Merge 1099 Documents Step")

        if pfml_1099_util.is_merge_1099_pdf_enabled():
            logger.info("Merge 1099 Pdf flag is enabled")
            batch_id = self.get_1099_batch_id()
            self.merge_document(batch_id, self.pdfApiEndpoint)
        else:
            logger.info("Merge 1099 Pdf flag is not enabled")

    def get_1099_batch_id(self):
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        return str(batch.pfml_1099_batch_id)

    def merge_document(self, batchId: str, url: str) -> None:
        mergeDto = {"batchId": batchId, "numOfRecords": 250}

        try:
            response = requests.post(
                url,
                json=mergeDto,
                headers={"Content-type": "application/json", "Accept": "application/json"},
            )

            if response.ok:
                logger.info(f"Pdfs were successfully merged for batchId: {batchId}")
                self.increment(self.Metrics.DOCUMENT_COUNT)
            else:
                logger.error(response.json())
                self.increment(self.Metrics.DOCUMENT_ERROR)
        except requests.exceptions.RequestException as error:
            logger.error(error)
            raise Exception("Api error to merge Pdf.")
