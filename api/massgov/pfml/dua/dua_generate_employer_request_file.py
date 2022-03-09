import os
import pathlib
import re
import tempfile
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import massgov.pfml.util.batch.log as batch_log
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Employer, ReferenceFile, ReferenceFileType
from massgov.pfml.dua.config import get_moveit_config, get_transfer_config
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_to_sftp_and_archive_s3_files,
)

logger = logging.get_logger(__name__)


class Constants:
    employer_id_key = "FINEOS Employer ID"
    employer_ein_key = "Employer EIN"


class Metrics(str, Enum):
    EMPLOYERS_TOTAL_COUNT = "employers_total_count"
    DUA_EMPLOYERS_FILES_UPLOADED_COUNT = "dua_employers_files_uploaded_count"


@background_task("dua-generate-and-send-employers-request-file")
def main():
    with db.session_scope(db.init(), close=True) as db_session, db.session_scope(
        db.init(), close=True
    ) as log_entry_db_session:
        with LogEntry(
            log_entry_db_session, "DUA generate-and-send-employers-request-file"
        ) as log_entry:
            generate_and_upload_dua_employers_update_file(db_session, log_entry)
            copy_dua_files_from_s3_to_moveit(db_session, log_entry)


def generate_and_upload_dua_employers_update_file(
    db_session: db.Session, log_entry: batch_log.LogEntry
) -> str:
    transfer_config = get_transfer_config()

    raw_employers = get_employers_for_outbound(db_session)
    employers = _format_employers_for_outbound(raw_employers)

    log_entry.set_metrics({Metrics.EMPLOYERS_TOTAL_COUNT: len(employers)})

    tempfile_path = _write_employers_to_tempfile(employers)
    # DFML_DUA_EMP_YYYYmmDDHHMM.csv
    file_name = f"DFML_DUA_EMP_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
    s3_dest = os.path.join(
        transfer_config.base_path, transfer_config.outbound_directory_path, file_name
    )
    file_util.upload_file(str(tempfile_path), s3_dest)

    reference_file = ReferenceFile(
        file_location=str(s3_dest),
        reference_file_type_id=ReferenceFileType.DUA_EMPLOYERS_REQUEST_FILE.reference_file_type_id,
    )
    db_session.add(reference_file)
    db_session.commit()
    return s3_dest


def copy_dua_files_from_s3_to_moveit(
    db_session: db.Session, log_entry: batch_log.LogEntry
) -> List[ReferenceFile]:
    transfer_config = get_transfer_config()
    moveit_config = get_moveit_config()

    sftp_s3_transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=transfer_config.base_path,
        source_dir=transfer_config.outbound_directory_path,
        archive_dir=transfer_config.archive_directory_path,
        dest_dir=moveit_config.moveit_outbound_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
        regex_filter=re.compile(r"DFML_DUA_EMP_\d+.csv"),
    )

    copied_reference_files = copy_to_sftp_and_archive_s3_files(sftp_s3_transfer_config, db_session)
    for ref_file in copied_reference_files:
        ref_file.reference_file_type_id = (
            ReferenceFileType.DUA_EMPLOYERS_REQUEST_FILE.reference_file_type_id
        )
    db_session.commit()

    if len(copied_reference_files) == 0:
        logger.info("No new employers request files were detected in S3.")
    else:
        logger.info(
            "New employers request files were detected in S3.",
            extra={"reference_file_count": len(copied_reference_files)},
        )

    log_entry.set_metrics({Metrics.DUA_EMPLOYERS_FILES_UPLOADED_COUNT: len(copied_reference_files)})

    return copied_reference_files


def get_employers_for_outbound(db_session: db.Session) -> List[Employer]:
    return db_session.query(Employer).filter(Employer.fineos_employer_id.isnot(None)).all()


def _format_employers_for_outbound(employers: List[Employer]) -> List[Dict[str, Any]]:
    formatted_employers = []
    for employer in employers:
        fineos_employer_id = employer.fineos_employer_id
        tax_id = employer.employer_fein

        if not (fineos_employer_id and tax_id):
            logger.warning(
                "Employer missing required information. Skipping.",
                extra={
                    "employer_id": employer.employer_id,
                    "has_fineos_employer_id": bool(fineos_employer_id),
                    "has_tax_id": bool(tax_id),
                },
            )
            continue

        formatted_employers.append(
            {
                Constants.employer_id_key: fineos_employer_id,
                Constants.employer_ein_key: employer.employer_fein.to_unformatted_str().replace("-", ""),
            }
        )
    return formatted_employers


def _write_employers_to_tempfile(employers: List[Dict]) -> pathlib.Path:
    _, filepath = tempfile.mkstemp()
    return file_util.create_csv_from_list(
        employers, [Constants.employer_id_key, Constants.employer_ein_key], filepath
    )
