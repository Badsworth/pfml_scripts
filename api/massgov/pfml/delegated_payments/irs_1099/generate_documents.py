import enum
import math
from typing import List, Optional

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
            batch_id = self.get_1099_batch_id()
            records = self.get_records(batch_id)

            # Determine the maximum number of 1099s to generate in this run
            generate_max = pfml_1099_util.get_generate_1099_max_files()
            generate_limit = generate_max
            records_len = len(records)
            if generate_max > records_len:
                generate_limit = records_len

            # Determine how many have already been generated so that we start at the right subbatch
            generated = pfml_1099_util.get_1099_generated_count(self.db_session, batchId=batch_id)

            if records_len > 0:
                max_records_in_subbatch = 250
                con_subbatch = math.ceil(generated / max_records_in_subbatch) + 1
                con = 1

                for i in range(generate_limit):
                    try:
                        batch_folder = f"Batch-{batch_id}"
                        sub_batch_folder = f"Sub-batch-{con_subbatch}"
                        s3_location = (
                            f"{batch_folder}/Forms/{sub_batch_folder}/{records[i].pfml_1099_id}.pdf"
                        )
                        self.generate_document(
                            records[i], sub_batch_folder, self.pdfApiEndpoint, s3_location
                        )
                        con += 1

                        if con > max_records_in_subbatch:
                            con = 1
                            con_subbatch += 1
                    except (Exception) as error:
                        logger.error(error)

        else:
            logger.info("Generate 1099 Pdf flag is not enabled")

    def get_1099_batch_id(self) -> str:
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        return str(batch.pfml_1099_batch_id)

    def get_records(self, batch_id: str) -> List[Pfml1099]:
        return pfml_1099_util.get_1099_records_to_generate(self.db_session, batchId=batch_id)

    def generate_document(
        self, record: Pfml1099, sub_batch: str, url: str, s3_location: str
    ) -> None:
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
                "name": f"{sub_batch}/{record.first_name} {record.last_name}",
                "address": record.address_line_1,
                "address2": record.address_line_2,
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
                record.s3_location = s3_location
                self.db_session.commit()
                logger.info("Pdf was successfully generated.")
                self.increment(self.Metrics.DOCUMENT_COUNT)
            else:
                logger.error(response.json())
                self.increment(self.Metrics.DOCUMENT_ERROR)
        except requests.exceptions.RequestException as error:
            raise error
