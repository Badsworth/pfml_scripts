import os
import pathlib
import re
import tempfile
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import Field

import massgov.pfml.util.batch.log as batch_log
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    Employee,
    ReferenceFile,
    ReferenceFileType,
    TaxIdentifier,
)
from massgov.pfml.dua.config import DUAMoveItConfig
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.pydantic import PydanticBaseSettings
from massgov.pfml.util.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_to_sftp_and_archive_s3_files,
)

logger = logging.get_logger(__name__)


class Metrics(str, Enum):
    EMPLOYEES_TOTAL_COUNT = "employees_total_count"
    DUA_DEMOGRAPHICS_FILE_UPLOADED_COUNT = "dua_demographics_file_uploaded_count"
    PENDING_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = "pending_dua_demographics_files_count"
    SUCCESSFUL_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = "successful_dua_demographics_files_count"
    UNSUCCESSFUL_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = (
        "unsuccessful_dua_demographics_files_count"
    )


class Constants:
    # DUA_DFML_EMP_YYYYMMDD.csv
    FILE_PREFIX = "DFML_DUA_CLM_DEM_"

    # S3 bucket names
    S3_DFML_ARCHIVE_PATH = "dua/dfml/archive"
    S3_DFML_INBOUND_PATH = "dua/dfml/inbound"
    S3_DFML_OUTBOUND_PATH = "dua/dfml/outbound"
    S3_DFML_ERROR_PATH = "dua/dfml/error"

    FINEOS_CUSTOMER_NUMBER = "FINEOS Customer ID"
    SSN = "SSN"

    EMPLOYEE_LIST_FIELDS = [
        FINEOS_CUSTOMER_NUMBER,
        SSN,
    ]


class DuaEmployeeRequestConfig(PydanticBaseSettings):
    s3_bucket_uri: str = Field(..., env="S3_BUCKET")
    s3_dfml_archive_directory_path: str = Constants.S3_DFML_ARCHIVE_PATH
    s3_dfml_outbound_directory_path: str = Constants.S3_DFML_OUTBOUND_PATH
    s3_dfml_error_directory_path: str = Constants.S3_DFML_ERROR_PATH


def get_s3_config() -> DuaEmployeeRequestConfig:
    return DuaEmployeeRequestConfig()


def get_moveit_config() -> DUAMoveItConfig:
    return DUAMoveItConfig()


def get_employees_for_outbound(db_session: db.Session) -> List[Employee]:
    return (
        db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(Employee.tax_identifier_id == TaxIdentifier.tax_identifier_id)
        .all()
    )


def _format_employees_for_outbound(employees: List[Employee]) -> List[Dict[str, Any]]:
    formatted_employees = []
    for employee in employees:
        fineos_customer_number = employee.fineos_customer_number
        ssn = employee.tax_identifier_id
        formatted_employees.append(
            {Constants.FINEOS_CUSTOMER_NUMBER: fineos_customer_number, Constants.SSN: ssn}
        )
    return formatted_employees


def _write_employees_to_tempfile(employees: List[Dict]) -> pathlib.Path:
    _, filepath = tempfile.mkstemp()
    return file_util.create_csv_from_list(employees, Constants.EMPLOYEE_LIST_FIELDS, filepath)


def generate_and_upload_dua_employee_update_file(
    db_session: db.Session, log_entry: batch_log.LogEntry
) -> str:
    s3_config = get_s3_config()

    employees = get_employees_for_outbound(db_session)
    employee_info = _format_employees_for_outbound(employees)

    tempfile_path = _write_employees_to_tempfile(employee_info)
    log_entry.set_metrics({Metrics.EMPLOYEES_TOTAL_COUNT: len(employee_info)})

    file_name = f"{Constants.FILE_PREFIX}{datetime.now().strftime('%Y%m%d')}.csv"
    s3_dest = os.path.join(
        s3_config.s3_bucket_uri, s3_config.s3_dfml_outbound_directory_path, file_name
    )
    file_util.upload_to_s3(str(tempfile_path), s3_dest)
    reference_file = ReferenceFile(
        file_location=str(s3_dest),
        reference_file_type_id=ReferenceFileType.DUA_DEMOGRAPHICS_REQUEST_FILE.reference_file_type_id,
    )
    db_session.add(reference_file)
    db_session.commit()
    return s3_dest


def copy_dua_files_from_s3_to_moveit(
    db_session: db.Session, log_entry: batch_log.LogEntry
) -> List[ReferenceFile]:
    s3_config = get_s3_config()
    moveit_config = get_moveit_config()

    transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=s3_config.s3_bucket_uri,
        source_dir=s3_config.s3_dfml_outbound_directory_path,
        archive_dir=s3_config.s3_dfml_archive_directory_path,
        dest_dir=moveit_config.moveit_outbound_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
        regex_filter=re.compile(r"DFML_DUA_CLM_DEM_\d+.csv"),
    )

    copied_reference_files = copy_to_sftp_and_archive_s3_files(transfer_config, db_session)
    for ref_file in copied_reference_files:
        ref_file.reference_file_type_id = (
            ReferenceFileType.DUA_DEMOGRAPHICS_REQUEST_FILE.reference_file_type_id
        )

    # Commit the ReferenceFile changes to the database.
    db_session.commit()

    if len(copied_reference_files) == 0:
        logger.info("No new demographics file were detected in the SFTP server.")
    else:
        logger.info(
            "New demographics files were detected in the SFTP server.",
            extra={"reference_file_count": len(copied_reference_files)},
        )

    log_entry.set_metrics(
        {Metrics.DUA_DEMOGRAPHICS_FILE_UPLOADED_COUNT: len(copied_reference_files)}
    )

    return copied_reference_files


@background_task("dua-generate-and-send-employee-request-file")
def main():
    with db.session_scope(db.init(), close=True) as db_session, db.session_scope(
        db.init(), close=True
    ) as log_entry_db_session:
        with LogEntry(
            log_entry_db_session, "DUA generate-and-send-employee-request-file"
        ) as log_entry:
            generate_and_upload_dua_employee_update_file(db_session, log_entry)
            copy_dua_files_from_s3_to_moveit(db_session, log_entry)
