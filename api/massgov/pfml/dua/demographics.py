import os
from datetime import datetime
from typing import List, Optional, Tuple

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
from massgov.pfml.dua.constants import Constants, Metrics
from massgov.pfml.dua.util import download_files_from_moveit, load_rows_from_file_path

logger = logging.get_logger(__name__)


def download_demographics_file_from_moveit(
    db_session: db.Session,
    log_entry: batch_log.LogEntry,
    transfer_config: DUATransferConfig,
    moveit_config: DUAMoveItConfig,
) -> List[ReferenceFile]:

    file_name = r"DUA_DFML_CLM_DEM_\d+.csv"
    reference_file_type_id = ReferenceFileType.DUA_DEMOGRAPHICS_FILE.reference_file_type_id

    copied_reference_files = download_files_from_moveit(
        db_session, transfer_config, moveit_config, file_name, reference_file_type_id
    )

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
        log_entry.increment(Metrics.UNSUCCESSFUL_DUA_DEMOGRAPHICS_REFERENCE_FILES_COUNT)

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
        # some of the FEINs in the DUA data are missing their leading zeros/are
        # not 9 digits long, so to have best chance to match against our
        # Employer records (which all correctly have 9 digit FEINs) pad the left
        # with zero
        employer_fein = row.employer_fein.zfill(9)
        print(employer_fein)

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

        existing_employees = (
            db_session.query(Employee).filter(
                Employee.fineos_customer_number == fineos_customer_number
            )
        ).all()
        if len(existing_employees) > 1:
            log_attributes["employee_duplicate_count"] = len(existing_employees)
            logger.warning(
                "Duplicate employees found for fineos_customer_number. Skipping",
                extra=log_attributes,
            )
            log_entry.increment(Metrics.EMPLOYEE_SKIPPED_COUNT)
            continue
        else:
            existing_employee = existing_employees[0] if len(existing_employees) == 1 else None

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

        if found_reporting_unit.organization_unit.employer_id != existing_employer.employer_id:
            log_attributes["dua_reporting_unit_id"] = found_reporting_unit.dua_reporting_unit_id
            log_attributes["organization_unit_id"] = found_reporting_unit.organization_unit_id
            logger.warning("FINEOS Org Unit is not for same employer", extra=log_attributes)
            log_entry.increment(Metrics.DUA_REPORTING_UNIT_MISMATCHED_EMPLOYER_COUNT)
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


def _load_demographic_rows_from_file_path(
    file_location: str, db_session: db.Session
) -> Tuple[int, int]:

    logger.info("Load demographic rows started", extra={"file_location": file_location})

    # Load to database.
    result = load_rows_from_file_path(
        file_location,
        db_session,
        Constants.DUA_DEMOGRAPHIC_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP,
        DuaEmployeeDemographics,
    )

    logger.info("Load demographic rows finished", extra={"file_location": file_location, **result})

    return result["total_row_count"], result["inserted_row_count"]
