import csv
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.dialects.postgresql import insert

import massgov.pfml.db as db
import massgov.pfml.util.batch.log as batch_log
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml.db.models.employees import (
    DuaEmployeeDemographics,
    DuaReportingUnit,
    Employee,
    EmployeeOccupation,
    EmployeePushToFineosQueue,
    Employer,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.dua.config import DUAMoveItConfig, DUATransferConfig
from massgov.pfml.util.datetime import utcnow
from massgov.pfml.util.sftp_s3_transfer import (
    SftpS3TransferConfig,
    copy_from_sftp_to_s3_and_archive_files,
)

logger = logging.get_logger(__name__)


class Metrics:
    DUA_DEMOGRAPHICS_FILE_DOWNLOADED_COUNT = "dua_demographics_file_downloaded_count"
    PENDING_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = (
        "pending_dua_demographics_reference_files_count"
    )
    SUCCESSFUL_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT = (
        "successful_dua_demographics_reference_files_count"
    )
    TOTAL_DUA_DEMOGRAPHICS_ROW_COUNT = "total_dua_demographics_row_count"
    UNSUCCESSFUL_DUA_PAYMENT_REFERENCE_FILES_COUNT = (
        "unsuccessful_dua_demographics_reference_files_count"
    )
    INSERTED_DUA_DEMOGRAPHICS_ROW_COUNT = "inserted_dua_demographics_row_count"
    OCCUPATION_ORG_UNIT_SET_COUNT = "occupation_org_unit_set_count"
    OCCUPATION_ORG_UNIT_SKIPPED_COUNT = "occupation_org_unit_skipped_count"
    MISSING_DUA_REPORTING_UNIT_COUNT = "missing_dua_reporting_unit_count"
    CREATED_EMPLOYEE_OCCUPATION_COUNT = "created_employee_occupation_count"
    DUA_REPORTING_UNIT_MISSING_FINEOS_ORG_UNIT_COUNT = (
        "dua_reporting_unit_missing_fineos_org_unit_count"
    )


class Constants:
    CUSTOMER_ID_FIELD = "FINEOS"
    EMPR_FEIN_FIELD = "FEIN"
    DOB_FIELD = "BirthDt"
    GENDER_CODE_FIELD = "GenderCd"
    OCCUPATION_CODE_FIELD = "OccupationCode"
    OCCUPATION_DESCRIPTION_FIELD = "OccupationDesc"
    EMPR_REPORTING_UNIT_NO_FIELD = "EmployerUnitNumber"

    DUA_DEMOGRAPHIC_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP = {
        CUSTOMER_ID_FIELD: "fineos_customer_number",
        DOB_FIELD: "date_of_birth",
        GENDER_CODE_FIELD: "gender_code",
        OCCUPATION_CODE_FIELD: "occupation_code",
        OCCUPATION_DESCRIPTION_FIELD: "occupation_description",
        EMPR_FEIN_FIELD: "employer_fein",
        EMPR_REPORTING_UNIT_NO_FIELD: "employer_reporting_unit_number",
    }


def download_demographics_file_from_moveit(
    db_session: db.Session,
    log_entry: batch_log.LogEntry,
    transfer_config: DUATransferConfig,
    moveit_config: DUAMoveItConfig,
) -> List[ReferenceFile]:
    sftp_transfer_config = SftpS3TransferConfig(
        s3_bucket_uri=transfer_config.base_path,
        source_dir=moveit_config.moveit_inbound_path,
        archive_dir=moveit_config.moveit_archive_path,
        dest_dir=transfer_config.pending_directory_path,
        sftp_uri=moveit_config.moveit_sftp_uri,
        ssh_key_password=moveit_config.moveit_ssh_key_password,
        ssh_key=moveit_config.moveit_ssh_key,
        regex_filter=re.compile(r"DUA_DFML_CLM_DEM_\d+.csv"),
    )

    copied_reference_files = copy_from_sftp_to_s3_and_archive_files(
        sftp_transfer_config, db_session
    )
    for ref_file in copied_reference_files:
        ref_file.reference_file_type_id = (
            ReferenceFileType.DUA_DEMOGRAPHICS_FILE.reference_file_type_id
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
        {Metrics.DUA_DEMOGRAPHICS_FILE_DOWNLOADED_COUNT: len(copied_reference_files)}
    )

    return copied_reference_files


def load_demographics_file(
    db_session: db.Session,
    ref_file: ReferenceFile,
    log_entry: batch_log.LogEntry,
    transfer_config: DUATransferConfig,
    move_files: bool = False,
) -> Tuple[int, int]:
    archive_dir = os.path.join(transfer_config.base_path, transfer_config.archive_directory_path)
    error_dir = os.path.join(transfer_config.base_path, transfer_config.error_directory_path)

    log_entry.increment(Metrics.PENDING_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT)

    total_row_count = 0
    inserted_row_count = 0

    try:
        total_row_count, inserted_row_count = _load_demographic_rows_from_file_path(
            ref_file.file_location, db_session
        )
        log_entry.increment(Metrics.SUCCESSFUL_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT)
        log_entry.increment(Metrics.TOTAL_DUA_DEMOGRAPHICS_ROW_COUNT, total_row_count)
        log_entry.increment(Metrics.INSERTED_DUA_DEMOGRAPHICS_ROW_COUNT, inserted_row_count)
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
        log_entry.increment(Metrics.UNSUCCESSFUL_DUA_PAYMENT_REFERENCE_FILES_COUNT)

        # Log exceptions but continue attempting to load other payment files into the database.
        logger.exception(
            "Failed to load new DUA payments to database from file",
            extra={
                "file_location": ref_file.file_location,
                "reference_file_id": ref_file.reference_file_id,
            },
        )

    return total_row_count, inserted_row_count


def set_employee_occupation_from_demographic_data(
    db_session: db.Session,
    log_entry: batch_log.LogEntry,
    after_created_at: Optional[datetime] = None,
) -> None:
    if not after_created_at:
        after_created_at = datetime.min

    # Load latest records for Employee+Employer pair, optionally filtered to
    # records after created_at
    demographic_data = (
        db_session.query(DuaEmployeeDemographics)
        .filter(DuaEmployeeDemographics.created_at >= after_created_at)
        .distinct(
            DuaEmployeeDemographics.fineos_customer_number, DuaEmployeeDemographics.employer_fein
        )
        .order_by(
            DuaEmployeeDemographics.fineos_customer_number,
            DuaEmployeeDemographics.employer_fein,
            DuaEmployeeDemographics.created_at.desc(),
        )
    ).yield_per(1000)

    for row in demographic_data:
        fineos_customer_number = row.fineos_customer_number
        employer_reporting_unit_number = row.employer_reporting_unit_number
        employer_fein = row.employer_fein

        log_attributes = {
            "employee_fineos_customer_number": fineos_customer_number,
            "dua_employee_demographics_id": row.dua_employee_demographics_id,
            "dua_reporting_unit_number": employer_reporting_unit_number,
        }

        # we *should* always have fineos_customer_number given this is how DUA
        # identifies employees in the return file and a missing FEIN would seem
        # very unlikely, but just in case...
        if not fineos_customer_number or not employer_fein:
            logger.warning(
                "Employee FINEOS customer number or Employer FEIN missing. Skipping.",
                extra=log_attributes,
            )
            continue

        existing_employee = (
            db_session.query(Employee).filter(
                Employee.fineos_customer_number == fineos_customer_number
            )
        ).one_or_none()

        existing_employer = (
            db_session.query(Employer).filter(Employer.employer_fein == employer_fein)
        ).one_or_none()

        if not existing_employee:
            logger.warning("No matching employee found", extra=log_attributes)
            continue

        log_attributes["employee_id"] = existing_employee.employee_id

        if not existing_employer:
            logger.warning("No matching employer found for employee", extra=log_attributes)
            continue

        log_attributes["employer_id"] = existing_employer.employer_id

        employee_occupations = (
            db_session.query(EmployeeOccupation).filter(
                EmployeeOccupation.employee_id == existing_employee.employee_id,
                EmployeeOccupation.employer_id == existing_employer.employer_id,
            )
        ).all()

        found_reporting_unit = (
            db_session.query(DuaReportingUnit).filter(
                DuaReportingUnit.dua_id == employer_reporting_unit_number
            )
        ).one_or_none()

        if not found_reporting_unit:
            logger.warning("No matching DUA Reporting Unit found", extra=log_attributes)
            log_entry.increment(Metrics.MISSING_DUA_REPORTING_UNIT_COUNT)
            continue

        if not found_reporting_unit.organization_unit_id:
            logger.warning(
                "DUA Reporting Unit has no FINEOS Org Unit associated", extra=log_attributes
            )
            log_entry.increment(Metrics.DUA_REPORTING_UNIT_MISSING_FINEOS_ORG_UNIT_COUNT)
            continue

        # Create an EmployeeOccupation if it doesn't exist
        if len(employee_occupations) == 0:
            employee_occupation = EmployeeOccupation()
            employee_occupation.employee_id = existing_employee.employee_id
            employee_occupation.organization_unit_id = found_reporting_unit.organization_unit_id
            employee_occupation.employer_id = existing_employer.employer_id

            db_session.add(employee_occupation)

            log_entry.increment(Metrics.CREATED_EMPLOYEE_OCCUPATION_COUNT)
        else:
            # this should only ever be 1, although multiple are technically supported
            for occupation in employee_occupations:
                # do not act on records with an organization_unit_id already set
                if not occupation.organization_unit_id:
                    log_entry.increment(Metrics.OCCUPATION_ORG_UNIT_SET_COUNT)
                    occupation.organization_unit_id = found_reporting_unit.organization_unit_id
                    db_session.add(
                        EmployeePushToFineosQueue(
                            employee_id=existing_employee.employee_id,
                            employer_id=existing_employer.employer_id,
                            action="UPDATE_NEW_EMPLOYER",
                        )
                    )
                else:
                    log_entry.increment(Metrics.OCCUPATION_ORG_UNIT_SKIPPED_COUNT)

    db_session.commit()


def _convert_dict_with_csv_keys_to_db_keys(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    # Load empty strings as empty values.
    return {
        Constants.DUA_DEMOGRAPHIC_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP[k]: "" if v == "" else v
        for k, v in csv_data.items()
    }


def _load_demographic_rows_from_file_path(
    file_location: str, db_session: db.Session,
) -> Tuple[int, int]:
    total_row_count = 0
    inserted_row_count = 0

    # filter out duplicate rows in same file
    unique_rows = set()
    rows_to_insert = []

    logger.info("Load demographic rows started", extra={"file_location": file_location})

    # Load to database.
    with file_util.open_stream(file_location) as file:
        for row in csv.DictReader(file):
            total_row_count += 1

            row_values = tuple(row.values())
            if row_values not in unique_rows:
                db_data = _convert_dict_with_csv_keys_to_db_keys(row)
                db_data["created_at"] = utcnow()
                unique_rows.add(tuple(row.values()))
                rows_to_insert.append(db_data)

        result = db_session.execute(
            insert(DuaEmployeeDemographics.__table__)
            .on_conflict_do_nothing()
            .values(rows_to_insert)
        )
        inserted_row_count += result.rowcount

    db_session.commit()
    logger.info(
        "Load demographic rows finished",
        extra={
            "file_location": file_location,
            "total_row_count": total_row_count,
            "inserted_row_count": inserted_row_count,
        },
    )

    return total_row_count, inserted_row_count