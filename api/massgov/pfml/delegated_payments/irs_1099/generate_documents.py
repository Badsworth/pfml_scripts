import enum
from typing import Optional

import requests

import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.util.logging
import massgov.pfml.util.pydantic.mask as mask_util
from massgov.pfml.db.models.payments import Pfml1099
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class Generate1099DocumentsStep(Step):
    class Metrics(str, enum.Enum):
        DOCUMENT_COUNT = "document_count"
        DOCUMENT_ERROR = "document_errors"

    def run_step(self) -> None:
        self.pdfApiEndpoint = pfml_1099_util.get_pdf_api_generate_endpoint()
        self._update_1099_template()
        self._generate_1099_documents()

    def _update_1099_template(self) -> None:
        url = pfml_1099_util.get_pdf_api_update_template_endpoint()
        response = requests.get(url)

        if response.ok:
            logger.info("1099 Template was successfully updated.")
        else:
            logger.error(response.json())

    def _generate_1099_documents(self) -> None:
        logger.info("1099 Documents - Generate 1099 Documents Step")

        if pfml_1099_util.is_generate_1099_pdf_enabled():
            logger.info("Generate 1099 Pdf flag is enabled")
            records = self.get_records()

            if len(records) > 0:
                max_records_in_subbatch = 250
                con_subbatch = 1
                con = 1

                for i in range(len(records)):
                    self.generate_document(
                        records[i], f"Sub-batch-{con_subbatch}", self.pdfApiEndpoint
                    )
                    con += 1

                    if con > max_records_in_subbatch:
                        con = 1
                        con_subbatch += 1

        else:
            logger.info("Generate 1099 Pdf flag is not enabled")

    def get_records(self):
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        return pfml_1099_util.get_1099_records(
            self.db_session, batchId=str(batch.pfml_1099_batch_id)
        )

    def generate_document(self, record: Pfml1099, sub_bacth: str, url: str) -> None:
        ssn: Optional[str] = pfml_1099_util.get_tax_id(
            self.db_session, str(record.tax_identifier_id)
        )
        ssn = mask_util.mask_tax_identifier(ssn)

        if ssn is None or len(ssn) == 0:
            logger.error("%s has an invalid tax identifier.", str(record.tax_identifier_id))
            return

        try:
            documentDto = {
                "id": str(record.pfml_1099_id),
                "batchId": str(record.pfml_1099_batch_id),
                "year": record.tax_year,
                "corrected": record.correction_ind,
                "paymentAmount": str(record.gross_payments),
                "socialNumber": ssn,
                "federalTaxesWithheld": str(record.federal_tax_withholdings),
                "stateTaxesWithheld": str(record.state_tax_withholdings),
                "repayments": str(record.overpayment_repayments),
                "name": f"{sub_bacth}/{record.first_name} {record.last_name}",
                "address": record.address_line_1,
                "city": record.city,
                "state": record.state,
                "zipCode": record.zip,
                "accountNumber": record.account_number,
            }

            response = requests.post(
                url,
                json=documentDto,
                headers={"Content-type": "application/json", "Accept": "application/json"},
            )

            if response.ok:
                logger.info(
                    f"Pdf was successfully generated for {record.first_name} {record.last_name}"
                )
                self.increment(self.Metrics.DOCUMENT_COUNT)
            else:
                logger.error(response.json())
                self.increment(self.Metrics.DOCUMENT_ERROR)
        except requests.exceptions.RequestException as error:
            logger.error(error)
            raise Exception("Api error to generate Pdf.")
