import enum
import os
from typing import Any, Dict, List, Optional

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import LkReferenceFileType, ReferenceFile
from massgov.pfml.delegated_payments.delegated_payments_util import FineosExtract
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.util.collections.dict import make_keys_lowercase
from massgov.pfml.util.csv import CSVSourceWrapper

logger = logging.get_logger(__name__)


class BackfillFineosExtractStep(Step):
    """
    Step to backfill a FINEOS extract dataset to
    the corresponding FINEOS Extract staging table.

    Note this has a few assumptions:
    1. The file you're backfilling is a part of
       a reference file that has multiple files
       associated with it that all relate to each other.
    2. The files this one is associated with
       have been processed for a while and you
       want to retroactively associate old FINEOS
       extracts with them - that is, attach
       a file to the other files we processed for
       a given day.
    3. The file you're backfilling isn't a full
       snapshot (if it were, a backfill shouldn't be needed)
    """

    reference_file_type: LkReferenceFileType
    fineos_extract: FineosExtract

    fineos_extract_path: str

    class Metrics(str, enum.Enum):
        RECORDS_PROCESSED_COUNT = "records_processed_count"

        TOTAL_REFERENCE_FILE_COUNT = "total_reference_file_count"
        PROCESSED_REFERENCE_FILE_COUNT = "processed_reference_file_count"
        SKIPPED_REFERENCE_FILE_COUNT = "skipped_reference_file_count"
        NO_DATE_STR_REFERENCE_FILE_COUNT = "no_date_str_reference_file_count"
        FILE_NOT_FOUND_IN_FINEOS_COUNT = "file_not_found_in_fineos_count"
        SUCCESSFUL_REFERENCE_FILE_COUNT = "successful_reference_file_count"

    def __init__(
        self,
        db_session: db.Session,
        log_entry_db_session: db.Session,
        reference_file_type: LkReferenceFileType,
        fineos_extract: FineosExtract,
    ) -> None:
        self.reference_file_type = reference_file_type
        self.fineos_extract = fineos_extract

        s3_config = payments_config.get_s3_config()
        self.fineos_extract_path = s3_config.fineos_data_export_path

        super().__init__(db_session, log_entry_db_session)

    def run_step(self) -> None:

        reference_files = self.get_reference_files()

        logger.info(
            "Found %s reference files to process for backfill",
            len(reference_files),
            extra=self.get_extra(),
        )
        self.set_metrics({self.Metrics.TOTAL_REFERENCE_FILE_COUNT: len(reference_files)})

        for reference_file in reference_files:
            self.process_reference_file(reference_file)
            self.increment(self.Metrics.PROCESSED_REFERENCE_FILE_COUNT)
            # Commit for every file backfilled
            self.db_session.commit()

    def get_reference_files(self) -> List[ReferenceFile]:
        """
        Get reference files that:
        1. Are of the configured type
        2. Their IDs aren't already present in the table we are backfilling
        """

        # Get the reference file IDs we've already processed
        #
        reference_file_ids_already_processed = self.db_session.query(
            self.fineos_extract.table.reference_file_id
        ).all()

        reference_files = (
            self.db_session.query(ReferenceFile)
            .filter(
                ReferenceFile.reference_file_type_id
                == self.reference_file_type.reference_file_type_id
            )
            .filter(ReferenceFile.reference_file_id.notin_(reference_file_ids_already_processed))
            .all()
        )

        reference_files.sort(key=lambda reference_file: reference_file.file_location)

        return reference_files

    def process_reference_file(self, reference_file: ReferenceFile) -> None:
        # The reference file location will look like this:
        # s3://<bucket>/cps/extracts/processed/2022-03-10-14-50-44-payment-extract
        # The timestamp prefix is based on the same one that FINEOS
        # had so we can use that to build the FINEOS path.
        extra = self.get_extra(reference_file)
        logger.info("Processing reference file for backfill", extra=extra)

        if payments_util.Constants.S3_INBOUND_PROCESSED_DIR not in reference_file.file_location:
            logger.info("Skipping reference file as it's not in a processed directory", extra=extra)
            self.increment(self.Metrics.SKIPPED_REFERENCE_FILE_COUNT)
            return

        date_group_str = payments_util.get_date_group_str_from_path(reference_file.file_location)
        if not date_group_str:
            logger.warning(
                "Cannot process reference file as it does not contain a valid date for processing",
                extra=extra,
            )
            self.increment(self.Metrics.NO_DATE_STR_REFERENCE_FILE_COUNT)
            return

        # Build the FINEOS file path which will look like:
        # s3://<fineos bucket + initial path>/2022-03-10-14-50-44/2022-03-10-14-50-44-<filename>
        expected_filename = f"{date_group_str}-{self.fineos_extract.file_name}"
        fineos_dir = os.path.join(self.fineos_extract_path, date_group_str)

        if expected_filename not in file_util.list_files(fineos_dir):
            # There were a few times in lower environments
            # where we renamed and reprocessed FINEOS extracts
            # so it's expected that at least a few files will
            # not be found in the FINEOS bucket as a result
            extra["fineos_directory"] = fineos_dir
            logger.warning(
                "Cannot backfill reference file, file not found in FINEOS S3", extra=extra
            )
            self.increment(self.Metrics.FILE_NOT_FOUND_IN_FINEOS_COUNT)
            return

        # Read the file and write the rows to the DB
        fineos_path = os.path.join(fineos_dir, expected_filename)
        csv_reader = CSVSourceWrapper(fineos_path)

        date_group_processed_count_key = f"{date_group_str}_RECORDS_PROCESSED_COUNT"
        unconfigured_columns = []
        for i, record in enumerate(csv_reader):

            if i == 0:
                lower_key_record = make_keys_lowercase(record)
                # Verify that the expected columns are present
                payments_util.validate_columns_present(lower_key_record, self.fineos_extract)

                unconfigured_columns = payments_util.get_unconfigured_fineos_columns(
                    lower_key_record,
                    self.fineos_extract.table,
                )

                if len(unconfigured_columns) > 0:
                    unconfigured_extra = {"fields": ",".join(unconfigured_columns)} | extra
                    logger.warning(
                        "Unconfigured columns in FINEOS extract", extra=unconfigured_extra
                    )

            staging_table_instance = payments_util.create_staging_table_instance(
                data=record,
                db_cls=self.fineos_extract.table,
                ref_file=reference_file,
                ignore_properties=unconfigured_columns,
            )
            self.db_session.add(staging_table_instance)
            self.increment(self.Metrics.RECORDS_PROCESSED_COUNT)
            self.increment(date_group_processed_count_key)

        self.increment(self.Metrics.SUCCESSFUL_REFERENCE_FILE_COUNT)

    def get_extra(self, reference_file: Optional[ReferenceFile] = None) -> Dict[str, Any]:
        extra = {
            "reference_file_type": self.reference_file_type,
            "file_name": self.fineos_extract.file_name,
            "table_name": self.fineos_extract.table.__name__,
        }
        if reference_file:
            extra["reference_file_id"] = reference_file.reference_file_id
            extra["reference_file_location"] = reference_file.file_location

        return extra
