import os

import requests

import massgov.pfml.api.app as app
import massgov.pfml.util.logging
from massgov.pfml.db.models.payments import Pfml1099
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)
PDF_API_HOST = os.environ.get("PDF_API_HOST")


class Generate1099DocumentsStep(Step):
    def run_step(self) -> None:
        self._generate_1099_documents()

    def _generate_1099_documents(self) -> None:
        logger.info("1099 Documents - Generate 1099 Documents Step")

        if app.get_config().enable_generate_1099_pdf:
            logger.info("Generate 1099 Pdf flag is enabled")
            records = self.get_payment_records()

            for record in records:
                self.generate_document(record)
        else:
            logger.info("Generate 1099 Pdf flag is not enabled")

    def get_payment_records(self):
        return self.db_session.query(Pfml1099).all()

    def generate_document(self, record) -> None:
        pdfApiUrl = f"{PDF_API_HOST}/api/pdf/generate"

        try:
            documentDto = {
                "batchId": str(record.pfml_1099_batch_id),
                "year": record.tax_year,
                "corrected": record.correction_ind,
                "paymentAmount": str(record.gross_payments),
                "socialNumber": "***-**-0001",
                "federalTaxesWithheld": str(record.federal_tax_withholdings),
                "stateTaxesWithheld": str(record.state_tax_withholdings),
                "repayments": str(record.overpayment_repayments),
                "name": f"{record.first_name} {record.last_name}",
                "address": record.address_line_1,
                "city": record.city,
                "state": record.state,
                "zipCode": record.zip,
                "accountNumber": None,
            }

            response = requests.post(
                pdfApiUrl,
                json=documentDto,
                verify=False,
                headers={"Content-type": "application/json", "Accept": "application/json"},
            )

            logger.info(response)
        except requests.exceptions.RequestException as error:
            logger.error(error)
