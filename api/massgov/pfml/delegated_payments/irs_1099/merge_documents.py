import massgov.pfml.util.logging
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.db.models.payments import Pfml1099Batch
import requests

logger = massgov.pfml.util.logging.get_logger(__name__)


class Merge1099Step(Step):
    def run_step(self) -> None:
        self._merge_1099_documents()

    def _merge_1099_documents(self) -> None:
        logger.info("1099 Documents - Merge 1099 Documents Step")
        records = self.get_batches_records()

        for record in records:
            self.merge_documents(record)

    def get_batches_records(self):
        return self.db_session.query(Pfml1099Batch).all()

    def merge_documents(self, record) -> None:
        pdfApiUrl = "http://mass-pfml-pdf-api:5001/api/pdf/merge"

        try:
            mergeDto = {
                "batchId": str(record.pfml_1099_batch_id),
                "numOfRecords" : 250
            }

            response = requests.post(
                pdfApiUrl, 
                json=mergeDto, 
                verify=False, 
                headers = {
                    'Content-type': 'application/json',
                    'Accept': 'application/json'
                }
            )

            logger.info(response)
        except requests.exceptions.RequestException as error:
            logger.error(error)
