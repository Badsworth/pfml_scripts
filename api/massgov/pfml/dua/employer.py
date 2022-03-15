import os
from typing import List, Tuple

import massgov.pfml.db as db
import massgov.pfml.util.batch.log as batch_log
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.dua import DuaEmployer
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.dua.config import DUAMoveItConfig, DUATransferConfig
from massgov.pfml.dua.constants import Constants, Metrics
from massgov.pfml.dua.util import download_files_from_moveit, load_rows_from_file_path

logger = logging.get_logger(__name__)


def download_employer_file_from_moveit(
    db_session: db.Session,
    log_entry: batch_log.LogEntry,
    transfer_config: DUATransferConfig,
    moveit_config: DUAMoveItConfig,
) -> List[ReferenceFile]:

    file_name = r"DUA_DFML_EMP_\d+.csv"
    reference_file_type_id = ReferenceFileType.DUA_EMPLOYER_FILE.reference_file_type_id

    copied_reference_files = download_files_from_moveit(
        db_session, transfer_config, moveit_config, file_name, reference_file_type_id
    )

    if len(copied_reference_files) == 0:
        logger.info("No new Employer file were detected in the SFTP server.")
    else:
        logger.info(
            "New Employer files were detected in the SFTP server.",
            extra={"reference_file_count": len(copied_reference_files)},
        )

    log_entry.set_metrics({Metrics.DUA_EMPLOYER_FILE_DOWNLOADED_COUNT: len(copied_reference_files)})

    return copied_reference_files


def load_employer_file(
    db_session: db.Session,
    ref_file: ReferenceFile,
    log_entry: batch_log.LogEntry,
    transfer_config: DUATransferConfig,
    move_files: bool = False,
) -> Tuple[int, int]:
    archive_dir = os.path.join(transfer_config.base_path, transfer_config.archive_directory_path)
    error_dir = os.path.join(transfer_config.base_path, transfer_config.error_directory_path)

    log_entry.increment(Metrics.PENDING_DUA_EMPLOYER_REFERENCE_FILES_COUNT)

    total_row_count = 0
    inserted_row_count = 0

    try:
        total_row_count, inserted_row_count = _load_employer_rows_from_file_path(
            ref_file.file_location, db_session
        )
        log_entry.increment(Metrics.SUCCESSFUL_DUA_EMPLOYER_REFERENCE_FILES_COUNT)
        log_entry.increment(Metrics.TOTAL_DUA_EMPLOYER_ROW_COUNT, total_row_count)
        log_entry.increment(Metrics.INSERTED_DUA_EMPLOYER_ROW_COUNT, inserted_row_count)
        if move_files:
            filename = os.path.basename(ref_file.file_location)
            dest_path = os.path.join(archive_dir, filename)
            file_util.rename_file(ref_file.file_location, dest_path)
            ref_file.file_location = dest_path

        db_session.commit()
    except Exception:
        if move_files:
            # Move to error directory and update ReferenceFile.
            filename = os.path.basename(ref_file.file_location)
            dest_path = os.path.join(error_dir, filename)
            file_util.rename_file(ref_file.file_location, dest_path)
            ref_file.file_location = dest_path

        db_session.commit()
        log_entry.increment(Metrics.UNSUCCESSFUL_DUA_EMPLOYER_REFERENCE_FILES_COUNT)

        # Log exceptions but continue attempting to load other payment files into the database.
        logger.exception(
            "Failed to load new DUA employer to database from file",
            extra={
                "file_location": ref_file.file_location,
                "reference_file_id": ref_file.reference_file_id,
            },
        )

    return total_row_count, inserted_row_count


def _load_employer_rows_from_file_path(
    file_location: str, db_session: db.Session
) -> Tuple[int, int]:

    logger.info("Load Employer rows started", extra={"file_location": file_location})

    # Load to database.
    result = load_rows_from_file_path(
        file_location,
        db_session,
        Constants.DUA_EMPLOYER_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP,
        DuaEmployer,
    )

    logger.info("Load Employer rows finished", extra={"file_location": file_location, **result})

    return result["total_row_count"], result["inserted_row_count"]
