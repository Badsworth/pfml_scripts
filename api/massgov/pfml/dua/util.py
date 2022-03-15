import csv
import re
from typing import Any, Dict, List

from sqlalchemy.dialects.postgresql import insert

import massgov.pfml.db as db
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import ReferenceFile
from massgov.pfml.dua.config import DUAMoveItConfig, DUATransferConfig
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_from_sftp_to_s3_and_archive_files,
)


def convert_dict_with_csv_keys_to_db_keys(
    csv_data: Dict[str, Any], csv_columns: Dict[str, str]
) -> Dict[str, Any]:
    # Load empty strings as empty values.
    return {csv_columns[k]: "" if v == "" else v for k, v in csv_data.items()}


def load_rows_from_file_path(
    file_location: str, db_session: db.Session, csv_columns: Dict[str, str], insert_table: Any
) -> Dict[str, Any]:

    total_row_count = 0
    inserted_row_count = 0

    # filter out duplicate rows in same file
    unique_rows = set()
    rows_to_insert = []

    # Load to database.
    with file_util.open_stream(file_location) as file:
        for row in csv.DictReader(file):
            total_row_count += 1

            row_values = tuple(row.values())
            if row_values not in unique_rows:
                db_data = convert_dict_with_csv_keys_to_db_keys(row, csv_columns)
                db_data["created_at"] = utcnow()
                unique_rows.add(tuple(row.values()))
                rows_to_insert.append(db_data)

        result = db_session.execute(
            insert(insert_table.__table__).on_conflict_do_nothing().values(rows_to_insert)
        )
        inserted_row_count += result.rowcount

    db_session.commit()

    final_count = {"total_row_count": total_row_count, "inserted_row_count": inserted_row_count}

    return final_count


def download_files_from_moveit(
    db_session: db.Session,
    transfer_config: DUATransferConfig,
    moveit_config: DUAMoveItConfig,
    file_name: str,
    reference_file_type_id: int,
) -> List[ReferenceFile]:
    sftp_transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=transfer_config.base_path,
        source_dir=moveit_config.moveit_inbound_path,
        archive_dir=moveit_config.moveit_archive_path,
        dest_dir=transfer_config.pending_directory_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
        regex_filter=re.compile(file_name),
    )

    copied_reference_files = copy_from_sftp_to_s3_and_archive_files(
        sftp_transfer_config, db_session
    )
    for ref_file in copied_reference_files:
        ref_file.reference_file_type_id = reference_file_type_id

    # Commit the ReferenceFile changes to the database.
    db_session.commit()

    return copied_reference_files
