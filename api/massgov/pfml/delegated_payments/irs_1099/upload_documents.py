import enum
import os
from datetime import datetime
from typing import Optional

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


class FineosUploadStatus(str, enum.Enum):
    # Default value when a 1099 record is created
    NEW = "New"
    # When a 1099 record is in the process to be uploaded to Fineos API
    IN_PROGRESS = "In Progress"
    # When a 1099 record was successfully uploaded to Fineos API
    SUCCESS = "Success"
    # When a 1099 record failed to be uploaded to Fineos API
    FAILED = "Failed"
    # When a 1099 record is skipped for reprinting process
    SKIPPED = "Skipped"


class Upload1099DocumentsStep(Step):
    class Metrics(str, enum.Enum):
        DOCUMENT_COUNT = "document_count"
        DOCUMENT_ERROR = "document_errors"
        DOCUMENT_SKIP = "document_skips"

    def run_step(self) -> None:
        self._upload_1099_documents()

    def _upload_1099_documents(self) -> None:
        logger.info("1099 Documents - Upload 1099 Documents Step")

        if pfml_1099_util.is_upload_1099_pdf_enabled():
            logger.info("Upload 1099 Pdf flag is enabled")
            batch = pfml_1099_util.get_current_1099_batch(self.db_session)
            if batch is None:
                return

            document_type = self._get_document_type()
            fineos = massgov.pfml.fineos.create_client()
            temp_limit_to = pfml_1099_util.get_upload_max_files_to_fineos()
            temp_con = 1

            while temp_con <= temp_limit_to:
                record1099: Optional[Pfml1099] = pfml_1099_util.get_1099_record(
                    self.db_session, FineosUploadStatus.NEW, str(batch.pfml_1099_batch_id)
                )

                if record1099 is None:
                    logger.warning("No more pfml 1099 records found.")
                    break

                if (
                    record1099.s3_location is None
                    or len(record1099.s3_location) == 0
                    or record1099.s3_location == "NULL"
                ):
                    logger.warning(
                        f"Pfml 1099 record with id {record1099.pfml_1099_id} cannot be upload to FIneos API because it was not successfully generated."
                    )
                    self.update_status(record1099, FineosUploadStatus.FAILED)
                    self.increment(self.Metrics.DOCUMENT_ERROR)
                    continue

                ## reprinting
                if batch.correction_ind is True and record1099.correction_ind is False:
                    self.update_status(record1099, FineosUploadStatus.SKIPPED)
                    self.increment(self.Metrics.DOCUMENT_SKIP)
                    continue

                self.update_status(record1099, FineosUploadStatus.IN_PROGRESS)
                current_retry = 0

                try:
                    document_path = os.path.join(
                        payments_config.get_s3_config().pfml_1099_document_archive_path,
                        record1099.s3_location,
                    )
                    document_name = record1099.s3_location.split("/")[3]
                    self._upload_document(
                        fineos,
                        document_path,
                        document_name,
                        document_type,
                        record1099,
                        current_retry,
                    )
                    self.update_status(record1099, FineosUploadStatus.SUCCESS)
                    self.increment(self.Metrics.DOCUMENT_COUNT)
                    temp_con = temp_con + 1
                except Exception as error:
                    logger.error(
                        f"Pfml 1099 record with id {record1099.pfml_1099_id} generated the error: {error}"
                    )
                    self.update_status(record1099, FineosUploadStatus.FAILED)
                    self.increment(self.Metrics.DOCUMENT_ERROR)
        else:
            logger.info("Upload 1099 Pdf flag is not enabled")

    def _upload_document(
        self,
        fineos: AbstractFINEOSClient,
        document_path: str,
        file_name: str,
        document_type: str,
        record: Pfml1099,
        current_retry: int,
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
                self._retry_upload_document(
                    fineos, document_path, file_name, document_type, record, current_retry
                )
        except Exception:
            logger.exception("Upload 1099 exception.")
            self._retry_upload_document(
                fineos, document_path, file_name, document_type, record, current_retry
            )

    def _get_document_content(self, document_path: str) -> bytes:
        logger.info(f"Getting file content: {document_path}")
        return file_util.open_stream(document_path, "rb").read()

    def _get_document_type(self) -> str:
        return DocumentType.IRS_1099G_TAX_FORM_FOR_CLAIMANTS.document_type_description

    def update_status(self, record: Pfml1099, status: FineosUploadStatus) -> None:
        record.fineos_status = status
        self.db_session.commit()

    def _retry_upload_document(
        self,
        fineos: AbstractFINEOSClient,
        document_path: str,
        file_name: str,
        document_type: str,
        record: Pfml1099,
        current_retry: int,
    ) -> None:
        current_retry += 1

        if current_retry <= 1:
            logger.info(f"RETRY ({current_retry}) to upload document {file_name} to Fineos Api.")
            self._upload_document(
                fineos, document_path, file_name, document_type, record, current_retry
            )
        else:
            logger.info("No more RETRY allowed to Fineos Api.")
