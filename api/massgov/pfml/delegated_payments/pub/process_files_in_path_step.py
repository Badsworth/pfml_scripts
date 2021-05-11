#
# Abstract class ProcessFilesInPathStep for processing a directory of received files.
#

import abc
import os.path
from typing import Any, Dict, Optional, cast

import massgov.pfml.util.files
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import (
    LkPubErrorType,
    Payment,
    PubEft,
    PubError,
    ReferenceFile,
)
from massgov.pfml.delegated_payments import delegated_payments_util
from massgov.pfml.delegated_payments.step import Step

logger = massgov.pfml.util.logging.get_logger(__name__)


class ProcessFilesInPathStep(Step, metaclass=abc.ABCMeta):
    """Abstract class to process a directory of received files."""

    base_path: str
    received_path: str
    processed_path: str
    error_path: str
    reference_file: ReferenceFile
    more_files_to_process: bool

    def __init__(
        self,
        db_session: massgov.pfml.db.Session,
        log_entry_db_session: massgov.pfml.db.Session,
        base_path: str,
    ) -> None:
        """Constructor."""
        self.base_path = base_path
        self.compute_paths_from_base_path()
        self.more_files_to_process = True

        super().__init__(db_session, log_entry_db_session)

    def run_step(self) -> None:
        """List incoming directory and process the first file."""
        s3_objects = massgov.pfml.util.files.list_files(self.received_path)
        s3_objects.sort()

        logger.info("found files in %s: %s", self.received_path, s3_objects)

        if s3_objects:
            file = s3_objects.pop(0)
            path = os.path.join(self.received_path, file)
            self.set_metrics({"input_path": path})
            self.process_file(path)

        self.more_files_to_process = s3_objects != []

    def have_more_files_to_process(self) -> bool:
        """Determine if there are more incoming files to process.

        If this returns True, the caller may call run() again to process the next file.
        """
        return self.more_files_to_process

    def compute_paths_from_base_path(self) -> None:
        """Compute the subdirectory paths for received, processed, and error files."""
        date_folder = delegated_payments_util.get_date_folder()

        self.received_path = os.path.join(
            self.base_path, delegated_payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
        )
        self.processed_path = os.path.join(
            self.base_path, date_folder, delegated_payments_util.Constants.S3_INBOUND_PROCESSED_DIR,
        )
        self.error_path = os.path.join(
            self.base_path, date_folder, delegated_payments_util.Constants.S3_INBOUND_ERROR_DIR,
        )

    @abc.abstractmethod
    def process_file(self, path):
        """Parse a single file in the received path."""
        pass

    def add_pub_error(
        self,
        pub_error_type: LkPubErrorType,
        message: str,
        line_number: int,
        raw_data: str,
        type_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        payment: Optional[Payment] = None,
        pub_eft: Optional[PubEft] = None,
    ) -> PubError:
        if self.get_import_log_id() is None:
            raise Exception("object has no log entry set")

        pub_error = PubError(
            pub_error_type_id=pub_error_type.pub_error_type_id,
            message=message,
            line_number=line_number,
            type_code=type_code,
            raw_data=raw_data,
            details=details or {},
            import_log_id=cast(int, self.get_import_log_id()),
            reference_file_id=self.reference_file.reference_file_id,
        )

        if payment is not None:
            pub_error.payment_id = payment.payment_id

        if pub_eft is not None:
            pub_error.pub_eft_id = pub_eft.pub_eft_id

        self.db_session.add(pub_error)

        return pub_error
