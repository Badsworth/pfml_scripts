import os

import requests

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import Pfml1099Batch
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)
PDF_API_HOST = os.environ.get("PDF_API_HOST")


class Merge1099Step(Step):
    def run_step(self) -> None:
        self._merge_1099_documents()

    def _merge_1099_documents(self) -> None:
        logger.info("1099 Documents - Merge 1099 Documents Step")

        if app.get_config().enable_generate_1099_pdf:
            logger.info("Merge 1099 Pdf flag is enabled")
            records = self.get_batches_records()

            for record in records:
                self.merge_documents(record)
        else:
            logger.info("Merge 1099 Pdf flag is not enabled")

    def get_batches_records(self):
        return self.db_session.query(Pfml1099Batch).all()

    def merge_documents(self, record) -> None:
        pdfApiUrl = f"{PDF_API_HOST}/api/pdf/merge"

        try:
            mergeDto = {"batchId": str(record.pfml_1099_batch_id), "numOfRecords": 250}

            response = requests.post(
                pdfApiUrl,
                json=mergeDto,
                verify=False,
                headers={"Content-type": "application/json", "Accept": "application/json"},
            )

            logger.info(response)
        except requests.exceptions.RequestException as error:
            logger.error(error)
