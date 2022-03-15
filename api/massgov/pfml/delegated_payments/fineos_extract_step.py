import enum
import os
import pathlib
import tempfile
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

import massgov.pfml.delegated_payments.delegated_config as payments_config
import massgov.pfml.delegated_payments.delegated_payments_util as payments_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import LkReferenceFileType, ReferenceFile, ReferenceFileType
from massgov.pfml.delegated_payments.step import Step
from massgov.pfml.util.collections.dict import make_keys_lowercase
from massgov.pfml.util.csv import download_and_parse_csv

logger = logging.get_logger(__name__)


@dataclass
class ExtractConfig:
    extracts: List[payments_util.FineosExtract]
    reference_file_type: LkReferenceFileType
    source_folder_s3_config_key: str


CLAIMANT_EXTRACT_CONFIG = ExtractConfig(
    payments_util.CLAIMANT_EXTRACT_FILES,
    ReferenceFileType.FINEOS_CLAIMANT_EXTRACT,
    "fineos_data_export_path",
)

PAYMENT_EXTRACT_CONFIG = ExtractConfig(
    payments_util.PAYMENT_EXTRACT_FILES,
    ReferenceFileType.FINEOS_PAYMENT_EXTRACT,
    "fineos_data_export_path",
)

PAYMENT_RECONCILIATION_EXTRACT_CONFIG = ExtractConfig(
    payments_util.PAYMENT_RECONCILIATION_EXTRACT_FILES,
    ReferenceFileType.FINEOS_PAYMENT_RECONCILIATION_EXTRACT,
    "fineos_adhoc_data_export_path",
)

IAWW_EXTRACT_CONFIG = ExtractConfig(
    payments_util.IAWW_EXTRACT_FILES,
    ReferenceFileType.FINEOS_IAWW_EXTRACT,
    "fineos_data_export_path",
)

REQUEST_1099_EXTRACT_CONFIG = ExtractConfig(
    payments_util.REQUEST_1099_EXTRACT_FILES,
    ReferenceFileType.FINEOS_1099_DATA_EXTRACT,
    "fineos_data_export_path",
)


class ExtractData:
    s3_locations: List[str]
    date_str: str
    extract_config: ExtractConfig
    extract_path_mapping: Dict[str, payments_util.FineosExtract]

    reference_file: ReferenceFile

    def __init__(
        self,
        s3_locations: List[str],
        date_str: str,
        extract_config: ExtractConfig,
    ):
        self.s3_locations = s3_locations
        self.date_str = date_str
        self.extract_config = extract_config
        self.extract_path_mapping = {}

        for s3_location in s3_locations:
            for extract in extract_config.extracts:
                if s3_location.endswith(extract.file_name):
                    self.extract_path_mapping[s3_location] = extract

        self.reference_file = ReferenceFile(
            file_location=os.path.join(
                payments_config.get_s3_config().pfml_fineos_extract_archive_path,
                payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
                self.date_str,
            ),
            reference_file_type_id=extract_config.reference_file_type.reference_file_type_id,
            reference_file_id=uuid.uuid4(),
        )
        logger.info("Intialized extract data: %s", self.reference_file.file_location)

    def validate(self, validate_all_files: bool = True) -> None:
        if validate_all_files and len(self.extract_config.extracts) != len(
            self.extract_path_mapping
        ):
            expected_file_names = [extract.file_name for extract in self.extract_config.extracts]
            error_msg = (
                f"Expected to find files {expected_file_names}, but found {self.s3_locations}"
            )
            raise Exception(error_msg)


class FineosExtractStep(Step):
    extract_config: ExtractConfig
    active_extract_data: Optional[ExtractData]
    active_extract_data_date_str: Optional[str]

    class Metrics(str, enum.Enum):
        FINEOS_PREFIX = "fineos_prefix"
        ARCHIVE_PATH = "archive_path"
        FILE_TYPE = "file_type"
        RECORDS_PROCESSED_COUNT = "records_processed_count"

    def __init__(
        self,
        db_session: db.Session,
        log_entry_db_session: db.Session,
        extract_config: ExtractConfig,
    ) -> None:
        super().__init__(db_session=db_session, log_entry_db_session=log_entry_db_session)
        self.extract_config = extract_config
        self.active_extract_data = None
        self.active_extract_data_date_str = None

    def get_import_type(self) -> str:
        """Use the reference file type description for an import log type distinction"""
        return self.extract_config.reference_file_type.reference_file_type_description

    def run_step(self) -> None:
        logger.info(
            "Starting processing of %s files",
            self.extract_config.reference_file_type.reference_file_type_description,
        )
        self.set_metrics(
            {
                self.Metrics.FILE_TYPE: self.extract_config.reference_file_type.reference_file_type_description
            }
        )

        with tempfile.TemporaryDirectory() as download_directory:
            self.process_extracts(pathlib.Path(download_directory))

        logger.info(
            "Successfully consumed FINEOS extract data for %s",
            self.extract_config.reference_file_type.reference_file_type_description,
        )

    def cleanup_on_failure(self) -> None:
        logger.exception(
            "Error processing %s extract files in date_group: %s",
            self.extract_config.reference_file_type.reference_file_type_description,
            self.active_extract_data_date_str,
            extra={"date_group": self.active_extract_data_date_str},
        )
        if self.active_extract_data:
            # Move the files to the error directory
            # Note we don't create the reference file
            # because if it errors again, we don't want to hit
            # an issue with the reference file location unique key
            self.move_files_from_received_to_out_dir(
                self.active_extract_data,
                payments_util.Constants.S3_INBOUND_ERROR_DIR,
                create_reference_file=False,
            )
            self.active_extract_data = None

    def process_extracts(self, download_directory: pathlib.Path) -> None:
        data_by_date = self._move_files_from_fineos_to_received()

        previously_processed_date = set()

        if bool(data_by_date):
            latest_date_str = sorted(data_by_date.keys())[-1]

        for date_str, s3_file_locations in data_by_date.items():

            logger.info(
                "Processing files in date group: %s", date_str, extra={"date_group": date_str}
            )
            is_latest_extract = date_str == latest_date_str

            extract_data = ExtractData(
                s3_file_locations,
                date_str,
                self.extract_config,
            )
            self.active_extract_data = extract_data
            self.active_extract_data_date_str = date_str

            # We'll only validate all files present for the latest
            # extract that we're going to actually store to the DB
            extract_data.validate(validate_all_files=is_latest_extract)

            if not is_latest_extract:
                self.move_files_from_received_to_out_dir(
                    extract_data, payments_util.Constants.S3_INBOUND_SKIPPED_DIR
                )
                logger.info(
                    "Successfully skipped claimant extract files in date group: %s",
                    date_str,
                    extra={"date_group": date_str},
                )
                continue

            if (
                date_str in previously_processed_date
                or payments_util.payment_extract_reference_file_exists_by_date_group(
                    self.db_session, date_str, self.extract_config.reference_file_type
                )
            ):
                logger.warning(
                    "Found existing ReferenceFile record for date group in /processed folder: %s",
                    date_str,
                    extra={"date_group": date_str},
                )
                previously_processed_date.add(date_str)
                continue

            self.set_metrics({self.Metrics.FINEOS_PREFIX: date_str})
            self._download_and_index_data(extract_data, str(download_directory))
            self.move_files_from_received_to_out_dir(
                extract_data, payments_util.Constants.S3_INBOUND_PROCESSED_DIR
            )
            logger.info(
                "Processed extract files for %s now in %s",
                self.extract_config.reference_file_type.reference_file_type_description,
                extract_data.reference_file.file_location,
            )

            self.active_extract_data = None
            self.active_extract_data_date_str = None

    def _move_files_from_fineos_to_received(self) -> Dict[str, List[str]]:
        expected_file_names = [extract.file_name for extract in self.extract_config.extracts]

        payments_util.copy_fineos_data_to_archival_bucket(
            self.db_session,
            expected_file_names,
            self.extract_config.reference_file_type,
            self.extract_config.source_folder_s3_config_key,
            allow_missing=True,  # We'll check later
        )
        data_by_date = payments_util.group_s3_files_by_date(expected_file_names)

        logger.info("Dates in /received folder: %s", ", ".join(data_by_date.keys()))

        return data_by_date

    def move_files_from_received_to_out_dir(
        self, extract_data: ExtractData, directory_name: str, create_reference_file: bool = True
    ) -> None:
        # Effectively, this method will move a file of path:
        # s3://bucket/path/to/received/2020-01-01-11-30-00-file.csv
        # to
        # s3://bucket/path/to/skipped/2020-01-01-11-30-00-payment-extract/2020-01-01-11-30-00-file.csv
        date_group_folder = payments_util.get_date_group_folder_name(
            extract_data.date_str, self.extract_config.reference_file_type
        )

        for file_path, extract in extract_data.extract_path_mapping.items():
            new_path = file_path.replace(
                payments_util.Constants.S3_INBOUND_RECEIVED_DIR,
                f"{directory_name}/{date_group_folder}",
            )

            logger.info("Moving %s file from %s to %s", extract.file_name, file_path, new_path)
            file_util.rename_file(file_path, new_path)

        original_file_location = extract_data.reference_file.file_location
        new_file_location = original_file_location.replace(
            payments_util.Constants.S3_INBOUND_RECEIVED_DIR, directory_name
        ).replace(extract_data.date_str, date_group_folder)
        logger.info(
            "Updated reference file location from %s to %s",
            original_file_location,
            new_file_location,
        )
        extract_data.reference_file.file_location = new_file_location
        if create_reference_file:
            self.db_session.add(extract_data.reference_file)

        logger.info("Successfully moved files to %s folder", directory_name)
        self.set_metrics({self.Metrics.ARCHIVE_PATH: new_file_location})

    def _download_and_index_data(self, extract_data: ExtractData, download_directory: str) -> None:
        for file_location, extract in extract_data.extract_path_mapping.items():
            records = download_and_parse_csv(file_location, download_directory)

            logger.info(
                "Storing extract data from %s to %s with reference_file_id %s and import_log_id %s",
                file_location,
                extract.table.__name__,
                extract_data.reference_file.reference_file_id,
                self.get_import_log_id(),
            )

            unconfigured_columns = []

            for i, record in enumerate(records):
                lower_key_record = make_keys_lowercase(record)

                if i == 0:
                    # Verify that the expected columns are present
                    payments_util.validate_columns_present(lower_key_record, extract)

                    # Check if there are any fields that don't have a matching
                    # column in the table model
                    unconfigured_columns = payments_util.get_unconfigured_fineos_columns(
                        lower_key_record, extract.table
                    )
                    if len(unconfigured_columns) > 0:
                        logger.warning(
                            "Unconfigured columns in FINEOS extract.",
                            extra={
                                "extract.table.__name__": extract.table.__name__,
                                "fields": ",".join(unconfigured_columns),
                            },
                        )

                staging_table_instance = payments_util.create_staging_table_instance(
                    lower_key_record,
                    extract.table,
                    extract_data.reference_file,
                    self.get_import_log_id(),
                    # These were already logged when we checked the first record earlier,
                    # so we don't need to log them again.
                    ignore_properties=unconfigured_columns,
                )
                self.db_session.add(staging_table_instance)
                self.increment(self.Metrics.RECORDS_PROCESSED_COUNT)
