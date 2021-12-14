import enum
import os
from datetime import datetime
from typing import List, Optional

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.irs_1099.pfml_1099_util as pfml_1099_util
import massgov.pfml.fineos
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.db.models.applications import DocumentType
from massgov.pfml.db.models.payments import Pfml1099
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.fineos.client import AbstractFINEOSClient

logger = massgov.pfml.util.logging.get_logger(__name__)


class Upload1099DocumentsStep(Step):
    class Metrics(str, enum.Enum):
        DOCUMENT_COUNT = "document_count"
        DOCUMENT_ERROR = "document_errors"

    def run_step(self) -> None:
        self._upload_1099_documents()

    def _upload_1099_documents(self) -> None:
        logger.info("1099 Documents - Upload 1099 Documents Step")

        if pfml_1099_util.is_upload_1099_pdf_enabled():
            logger.info("Upload 1099 Pdf flag is enabled")
            document_type = self._get_document_type()
            batch_id = self._get_batch_id()
            directory_path = self._get_1099_documents_directory(batch_id)
            sub_directories = self._get_1099_sub_batches(directory_path)
            fineos = massgov.pfml.fineos.create_client()
            temp_limit_to = 10
            temp_con = 0

            for sub_directory in sub_directories:
                sub_directory_path = os.path.join(directory_path, sub_directory)
                documents = self._get_1099_documents_in_sub_batch(sub_directory_path)

                for document in documents:
                    temp_con = temp_con + 1

                    if temp_con <= temp_limit_to:
                        document_path = os.path.join(directory_path, sub_directory, document)
                        document_id = document.split("_")[0]
                        record1099: Optional[Pfml1099] = pfml_1099_util.get_1099_record(
                            self.db_session, document_id
                        )

                        if record1099 is None:
                            logger.error(f"No pfml 1099 record found for id: {document_id}")
                        else:
                            try:
                                self._upload_document(
                                    fineos, document_path, document, document_type, record1099
                                )
                            except (Exception) as error:
                                logger.error(error)
                    else:
                        temp_con = 0
                        break

        else:
            logger.info("Upload 1099 Pdf flag is not enabled")

    def _get_batch_id(self) -> str:
        batch = pfml_1099_util.get_current_1099_batch(self.db_session)

        if batch is None:
            logger.error("No current batch exists. This should never happen.")
            raise Exception("Batch cannot be empty at this point.")

        return str(batch.pfml_1099_batch_id)

    def _get_1099_documents_directory(self, batch_id: str) -> str:
        directory = payments_config.get_s3_config().pfml_1099_document_archive_path.replace(
            "[id]", batch_id
        )
        logger.info(directory)
        return directory

    def _get_1099_sub_batches(self, directory: str) -> List[str]:
        sub_directories = file_util.list_files(directory)
        logger.info(f"{len(sub_directories)} sub directories found.")
        return sub_directories

    def _get_1099_documents_in_sub_batch(self, sub_directory_path: str) -> List[str]:
        documents = file_util.list_files(sub_directory_path)
        logger.info(f"{len(documents)} 1099 forms found in sub directory {sub_directory_path}.")
        return documents

    def _upload_document(
        self,
        fineos: AbstractFINEOSClient,
        document_path: str,
        file_name: str,
        document_type: str,
        record: Pfml1099,
    ) -> None:
        file = self._get_document_content(document_path)

        data = {
            "dmsDocId": file_name,
            "fileExtension": "." + file_name.split(".")[1],
            "docProperties": {
                "title": file_name,
                "description": file_name,
                "receivedDate": str(datetime.now().isoformat()),
                "partyClassId": record.c,
                "partyIndexId": record.i,
                "managedReqId": 0,
                "status": "Completed",
                "fineosDocType": document_type,
                "dmsDocType": document_type,
            },
        }

        try:
            response = fineos.upload_document_to_dms(file_name, file, data)

            if response.status_code == 200:
                logger.info(f"File {file_name} was successfully uploaded to Fineos Api.")
            else:
                logger.error(f"Error when uploading file {file_name} to Fineos Api.")
        except (Exception) as error:
            raise error

    def _get_document_content(self, document_path: str) -> bytes:
        logger.info(f"Getting file content: {document_path}")
        return open(document_path, "rb").read()

    def _get_document_type(self) -> str:
        return DocumentType.IRS_1099G_TAX_FORM_FOR_CLAIMANTS.document_type_description
