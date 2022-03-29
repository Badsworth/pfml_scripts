#!/usr/bin/python3
#
# ECS task to import DOR data from S3 to PostgreSQL (RDS).
#
import argparse
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import boto3
from sqlalchemy.orm.session import Session

import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.util.batch.log
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.newrelic.events
from massgov.pfml import db
from massgov.pfml.db.models.base import uuid_gen
from massgov.pfml.db.models.employees import (
    Employee,
    EmployeePushToFineosQueue,
    Employer,
    EmployerPushToFineosQueue,
    WagesAndContributions,
)
from massgov.pfml.dor.importer.dor_file_formats import (
    EMPLOYER_PENDING_FILING_RESPONSE_FILE_A_ROW_LENGTH,
    EMPLOYER_PENDING_FILING_RESPONSE_FILE_B_ROW_LENGTH,
    EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_A,
    EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_B,
    ParsedEmployeeLine,
    ParsedEmployerLine,
    WageKey,
)
from massgov.pfml.dor.importer.import_dor import (
    PROCESSED_FOLDER,
    Capturer,
    ImportException,
    ImportReport,
    ImportRunReport,
)
from massgov.pfml.dor.importer.paths import get_exempt_employer_files_to_process
from massgov.pfml.dor.pending_filing.pending_filing_response import (
    bulk_save,
    decrypter_factory,
    filter_add_memory_usage,
    get_decrypted_file_stream,
    get_wage_composite_key,
    handle_import_exception,
    is_valid_employer_fein,
    move_file_to_processed,
)
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.encryption import Crypt

logger = logging.get_logger("massgov.pfml.dor.importer.import_exempt_dor")

aws_ssm = boto3.client("ssm", region_name="us-east-1")

# TODO get these from environment variables
DFML_RECEIVED_FOLDER = "dfml/received/"
DFML_PROCESSED_FOLDER = "dfml/processed/"

EMPLOYEE_LINE_LIMIT = 25000

# DOR has a 'magic date' of 12/31/9999 if employer has no exemptions.
exemption_date = datetime.strptime("12/31/9999", "%m/%d/%Y").date()


@dataclass
class Configuration:
    file_path: str

    def __init__(self, input_args: List[str]):
        parser = argparse.ArgumentParser(description="Process DOR Exempt Employers file")

        parser.add_argument("--responsefile", help="Path to DORDUADFML file to process.")

        args = parser.parse_args(input_args)
        self.file_path = args.responsefile

        if args.responsefile is None:
            raise Exception("Response file is required.")


@background_task("dor-import-exempt")
def main():
    config = Configuration(sys.argv[1:])
    logger.info("Starting dor-import-exempt with config", extra=asdict(config))

    report = ImportRunReport(start=datetime.now().isoformat())

    with db.session_scope(db.init(), close=True) as db_session:
        try:
            file_list: list[str] = list()
            file_list.append(config.file_path)

            decrypt_files = os.getenv("DECRYPT") == "true"
            import_reports = process_exempt_employer_files(file_list, decrypt_files, db_session)
            report.imports = import_reports
            report.message = "files imported"

        except ImportException as ie:
            report.end = datetime.now().isoformat()
            message = str(ie)
            report.message = message
            logger.error(message, extra={"report": asdict(report)})
            sys.exit(1)
        except Exception as e:
            report.end = datetime.now().isoformat()
            message = f"Unexpected error during import run: {type(e)} -- {e}"
            report.message = message
            logger.error(message, extra={"report": asdict(report)})
            sys.exit(1)

        report.end = datetime.now().isoformat()
        logger.info("Finished import run", extra={"report": asdict(report)})


@background_task("dor-import-exempt")
def handler() -> None:
    """ECS task main method."""
    logger.addFilter(filter_add_memory_usage)

    report = ImportRunReport(start=datetime.now().isoformat())

    try:
        folder_path = os.environ["FOLDER_PATH"]
        logger.info("Starting import run", extra={"folder_path": folder_path})
        import_files = get_exempt_employer_files_to_process(folder_path)

        if not import_files:
            logger.info("no files found to import")
            report.message = "no files found to import"
        else:
            decrypt_files = os.getenv("DECRYPT") == "true"
            import_reports = process_exempt_employer_files(import_files, decrypt_files)

            report.imports = import_reports
            report.message = "files imported"

        report.end = datetime.now().isoformat()
        logger.info("Finished import run", extra={"report": asdict(report)})
    except ImportException as ie:
        report.end = datetime.now().isoformat()
        message = str(ie)
        report.message = message
        logger.error(message, extra={"report": asdict(report)})
        sys.exit(1)
    except Exception as e:
        report.end = datetime.now().isoformat()
        message = f"Unexpected error during import run: {type(e)} -- {e}"
        report.message = message
        logger.error(message, extra={"report": asdict(report)})
        sys.exit(1)


def process_exempt_employer_files(
    import_files: List[str],
    decrypt_files: bool,
    optional_db_session: Optional[Session] = None,
    optional_decrypter: Optional[Crypt] = None,
    optional_s3: Optional[boto3.Session] = None,
) -> List[ImportReport]:
    try:
        import_reports: List[ImportReport] = []

        s3 = optional_s3
        if not s3:
            s3 = boto3.client("s3")

        decrypter = optional_decrypter
        if not decrypter:
            decrypter = decrypter_factory(decrypt_files)

        # Initialize the database
        db_session_raw = optional_db_session
        if not db_session_raw:
            db_session_raw = db.init(sync_lookups=True)

        with db.session_scope(db_session_raw) as db_session:

            # process each batch
            for employer_file in import_files:
                logger.info("Processing import file", extra={"employer_file": employer_file})

                import_report = process_exempt_employer_import(
                    db_session, employer_file, decrypter, s3
                )
                import_reports.append(import_report)
    except ImportException as ie:
        raise ie
    except Exception as e:
        raise ImportException("Unexpected error importing batches", type(e).__name__)

    return import_reports


def process_exempt_employer_import(
    db_session: Session,
    employer_file_path: str,
    decrypter: Crypt,
    s3: boto3.Session,
) -> ImportReport:
    logger.info("Starting to process files")
    report = ImportReport(
        start=datetime.now().isoformat(), status="in progress", employer_file=employer_file_path
    )

    report.sample_employers_line_lengths = {}
    report.parsed_employers_exception_line_nums = []

    report_log_entry = massgov.pfml.util.batch.log.create_log_entry(
        db_session, "DOR_EXEMPT", "Exempt Employers", report
    )

    db_session.refresh(report_log_entry)

    try:
        parsed_employers_count = 0

        # If an employer file is given, parse and import
        if employer_file_path:
            employers, employees = parse_exempt_employer_file(
                employer_file_path, decrypter, report, db_session
            )
            parsed_employers_count = len(employers)
            parsed_employees_count = len(employees)

            import_employers(db_session, employers, report, report_log_entry.import_log_id)

            import_employees_and_wage_data(
                db_session, employees, dict(), report, report_log_entry.import_log_id
            )

        # finalize report
        report.parsed_employers_count = parsed_employers_count
        report.parsed_employees_info_count = parsed_employees_count
        report.status = "success"
        report.end = datetime.now().isoformat()
        massgov.pfml.util.batch.log.update_log_entry(
            db_session, report_log_entry, "success", report
        )

        logger.info("Sample Employer line lengths: %s", repr(report.sample_employers_line_lengths))

        # move file to processed folder unless explicitly told not to.
        if os.getenv("RETAIN_RECEIVED_FILES") is None:
            if file_util.is_s3_path(employer_file_path):
                move_file_to_processed(PROCESSED_FOLDER, employer_file_path, s3)

    except Exception as e:
        handle_import_exception(e, db_session, report_log_entry, report)

    return report


def import_employers(
    db_session: Session,
    employers: List[ParsedEmployerLine],
    report: ImportReport,
    import_log_entry_id: int,
) -> None:
    """Import employers into db"""
    logger.info("Importing employers")

    # 1 - Stage employers for creation and update

    # Get all employers in DB
    existing_employer_reference_models = dor_persistence_util.get_all_employers_fein(db_session)

    fein_to_existing_employer_reference_models: Dict[str, Optional[Employer]] = {
        employer.employer_fein: employer for employer in existing_employer_reference_models
    }

    logger.info("Found employers in db: %i", len(existing_employer_reference_models))

    not_found_employer_info_list = []
    found_employer_info_list = []
    additional_employer_wage_rows = []

    staged_not_found_employer_ssns = set()
    for employer_info in employers:
        if not is_valid_employer_fein(employer_info, report):
            continue

        fein = employer_info["fein"]

        if fein in staged_not_found_employer_ssns:
            # this means there is more than one line for the same employer
            # add it to the found list for later possible update processing
            found_employer_info_list.append(employer_info)
            additional_employer_wage_rows.append(employer_info)
            continue

        if fein not in fein_to_existing_employer_reference_models:
            not_found_employer_info_list.append(employer_info)
            staged_not_found_employer_ssns.add(fein)
        else:
            found_employer_info_list.append(employer_info)

    # 2 - Create employers
    fein_to_new_employer_id = {}
    for emp in not_found_employer_info_list:
        fein_to_new_employer_id[emp["fein"]] = uuid_gen()

    employer_models_to_create = list(
        map(
            lambda employer_info: dor_persistence_util.dict_to_employer(
                employer_info, import_log_entry_id, fein_to_new_employer_id[employer_info["fein"]]
            ),
            not_found_employer_info_list,
        )
    )

    logger.info("Creating new employers: %i", len(employer_models_to_create))

    bulk_save(db_session, employer_models_to_create, "Employers")

    # Enqueue newly created employers for push to FINEOS
    employer_insert_logs_to_create = list(
        map(
            lambda employer: EmployerPushToFineosQueue(
                employer_id=employer.employer_id,
                action="INSERT",
                family_exemption=True,
                medical_exemption=True,
                exemption_cease_date=exemption_date,
            ),
            employer_models_to_create,
        )
    )
    bulk_save(db_session, employer_insert_logs_to_create, "Employer Insert Logs")

    # 3 - Update existing employers
    found_employer_info_to_update_list = []

    for employer_info in found_employer_info_list:
        fein = employer_info["fein"]

        # this means the employer already exists in this file and do not reprocess
        if fein in fein_to_new_employer_id:
            continue

        # this means the same employer was created previously in the current import run
        # fetch the existing employer for an update check
        if fein not in fein_to_existing_employer_reference_models:
            recently_created_existing_employer = dor_persistence_util.get_employer_by_fein(
                db_session, fein
            )
            fein_to_existing_employer_reference_models[fein] = recently_created_existing_employer

        existing_employer = fein_to_existing_employer_reference_models[fein]
        if existing_employer is None:
            logger.warning(
                "Expected existing employer not found {}".format(employer_info["account_key"])
            )
            continue

        _employer = fein_to_existing_employer_reference_models[fein]
        if _employer is not None:
            found_employer_info_to_update_list.append(employer_info)

    logger.info("Employers to update: %i", len(found_employer_info_to_update_list))

    if len(found_employer_info_to_update_list) > 0:
        logger.info(
            "Batch committing employer updates: %i", len(found_employer_info_to_update_list)
        )
        db_session.commit()

    report.updated_employers_count += len(found_employer_info_to_update_list)
    logger.info("Done - Updating employers: %i", len(found_employer_info_to_update_list))

    # 7 - Done
    logger.info(
        "Finished importing employers",
        extra={
            "created_employers_count": report.created_employers_count,
            "updated_employers_count": report.updated_employers_count,
        },
    )


def import_employees(
    db_session: Session,
    employee_info_list: List[ParsedEmployeeLine],
    employee_ssns_to_id_created_in_current_import_run: Dict[str, uuid.UUID],
    ssn_to_existing_employee_model: Dict[str, Employee],
    report: ImportReport,
    import_log_entry_id: int,
) -> None:
    """Create or update employees data in the db"""
    logger.info("Start import of employees import - lines: %i", len(employee_info_list))

    # 1 - Stage employee info for creation
    logger.info("Staging employee info for creation")

    not_found_employee_info_list = list(
        filter(
            lambda employee: (
                employee["employee_ssn"] not in employee_ssns_to_id_created_in_current_import_run
                and employee["employee_ssn"] not in ssn_to_existing_employee_model
            ),
            employee_info_list,
        )
    )

    ssn_to_new_tax_id = {}
    ssn_to_new_employee_id = {}

    # look up if any existing ssns exist
    maybe_previously_created_ssns = list(
        map(lambda emp: emp["employee_ssn"], not_found_employee_info_list)
    )

    previously_created_tax_ids = dor_persistence_util.get_tax_ids(
        db_session, maybe_previously_created_ssns
    )

    for emp in not_found_employee_info_list:
        found = None
        for tax_id in previously_created_tax_ids:
            if tax_id.tax_identifier == emp["employee_ssn"]:
                found = tax_id

        ssn_to_new_employee_id[emp["employee_ssn"]] = uuid_gen()

        # If a tax identifier does not already exists, create a UUID
        # Else use the found one.
        if not found:
            ssn_to_new_tax_id[emp["employee_ssn"]] = uuid_gen()
        else:
            ssn_to_new_tax_id[emp["employee_ssn"]] = found.tax_identifier_id
            logger.info(
                "Not creating tax identifier because it already exists - {}".format(
                    found.tax_identifier_id
                ),
                extra={"tax_identifier_id": found.tax_identifier_id},
            )

    logger.info(
        "Done - Staging employee and wage info for creation. Employees staged for creation: %i",
        len(ssn_to_new_tax_id),
    )

    # 2 - Create tax ids for new employees
    tax_id_models_to_create = []
    for ssn in ssn_to_new_employee_id:
        tax_id_is_found = False
        for tax_id in previously_created_tax_ids:
            if tax_id.tax_identifier == ssn:
                tax_id_is_found = True

        if not tax_id_is_found:
            tax_id_models_to_create.append(
                dor_persistence_util.tax_id_from_dict(ssn_to_new_tax_id[ssn], ssn)
            )

    logger.info("Creating new tax ids: %i", len(tax_id_models_to_create))

    bulk_save(db_session, tax_id_models_to_create, "Tax Ids")

    logger.info("Done - Creating new tax ids: %i", len(tax_id_models_to_create))

    # 3 - Create new employees
    employee_models_to_create = []
    employee_ssns_staged_for_creation_in_current_loop = set()
    employee_insert_logs_to_create = []

    for employee_info in not_found_employee_info_list:
        ssn = employee_info["employee_ssn"]

        # since there are multiple rows with the same employee information ignore all but the first one
        if ssn in employee_ssns_staged_for_creation_in_current_loop:
            continue

        new_employee_id = ssn_to_new_employee_id[ssn]
        new_employee = dor_persistence_util.dict_to_employee(
            employee_info, import_log_entry_id, new_employee_id, ssn_to_new_tax_id[ssn]
        )
        employee_models_to_create.append(new_employee)
        # Enqueue newly created employee for push to FINEOS
        employee_insert_logs_to_create.append(
            EmployeePushToFineosQueue(employee_id=new_employee.employee_id, action="INSERT")
        )

        employee_ssns_staged_for_creation_in_current_loop.add(ssn)
        employee_ssns_to_id_created_in_current_import_run[ssn] = new_employee_id

    # Store log entries for new employees
    bulk_save(db_session, employee_insert_logs_to_create, "Employee Insert Logs")

    logger.info("Creating new employees: %i", len(employee_models_to_create))

    bulk_save(db_session, employee_models_to_create, "Employees")

    db_session.commit()

    report.created_employees_count += len(employee_models_to_create)

    logger.info("Done - Creating new employees: %i", len(employee_models_to_create))


def import_wage_data(
    db_session: Session,
    wage_info_list: List,
    account_key_to_employer_id_map: Dict[str, uuid.UUID],
    employee_ssns_to_id_created_in_current_import_run: Dict[str, uuid.UUID],
    ssn_to_existing_employee_model: Dict[str, Employee],
    report: ImportReport,
    import_log_entry_id: int,
) -> None:
    # 1 - Create new wage data
    # For employees just created in the current run, we can avoid checking for existing wage rows
    wage_info_list_for_creation = list(
        filter(
            lambda wage_info: wage_info["employee_ssn"]
            in employee_ssns_to_id_created_in_current_import_run,
            wage_info_list,
        )
    )

    wages_contributions_models_to_create = []
    for employee_info in wage_info_list_for_creation:
        if account_key_to_employer_id_map.get(employee_info["account_key"], None) is None:
            report.skipped_wages_count += 1
            continue

        # Check if we just created the employee. If we did, get the employee_id, else it must already exist
        employee_id = None
        if (
            employee_ssns_to_id_created_in_current_import_run.get(
                employee_info["employee_ssn"], None
            )
            is not None
        ):
            employee_id = employee_ssns_to_id_created_in_current_import_run[
                employee_info["employee_ssn"]
            ]
        else:
            employee_id = ssn_to_existing_employee_model[employee_info["employee_ssn"]].employee_id

        wages_contributions_models_to_create.append(
            dor_persistence_util.dict_to_wages_and_contributions(
                employee_info,
                employee_id,
                account_key_to_employer_id_map[employee_info["account_key"]],
                import_log_entry_id,
            )
        )

    logger.info("Creating new wage information: %i", len(wages_contributions_models_to_create))

    bulk_save(db_session, wages_contributions_models_to_create, "Employee Wages", commit=True)

    report.created_wages_and_contributions_count += len(wages_contributions_models_to_create)

    logger.info(
        "Done - Creating new wage information: %i", len(wages_contributions_models_to_create)
    )

    # 2. Create wage rows for existing employees

    # Get the list of wages to check (any rows with employees not created in current run)
    wage_info_list_to_create_or_update = list(
        filter(
            lambda wage_info: wage_info["employee_ssn"]
            not in employee_ssns_to_id_created_in_current_import_run,
            wage_info_list,
        )
    )

    wage_data_total = len(wage_info_list_to_create_or_update)
    logger.info("Wage data for existing employees - total lines to check: %i", wage_data_total)

    # Stage existing wage rows for create or update check
    logger.info(
        "Fetching existing wage rows for create or update check - existing employees: %i",
        len(ssn_to_existing_employee_model),
    )

    existing_employee_ids = set()
    for employee_model in ssn_to_existing_employee_model.values():
        existing_employee_ids.add(employee_model.employee_id)

    existing_wages = []
    if len(existing_employee_ids) > 0:
        existing_wages = dor_persistence_util.get_wages_and_contributions_by_employee_ids(
            db_session, list(existing_employee_ids)
        )

    employer_employee_filing_period_to_wage_model: Dict[WageKey, Any] = {}
    for existing_wage in existing_wages:
        key = get_wage_composite_key(
            existing_wage.employer_id, existing_wage.employee_id, existing_wage.filing_period
        )
        employer_employee_filing_period_to_wage_model[key] = existing_wage

    logger.info(
        "Done - Fetching existing wage rows for create or update check - existing employees: %i, existing wage rows: %i",
        len(ssn_to_existing_employee_model),
        len(existing_wages),
    )

    # Create or update wage lines for existing employees
    wages_contributions_models_existing_employees_to_create: List[WagesAndContributions] = []

    count = 0
    updated_count = 0
    unmodified_count = 0

    for wage_info in wage_info_list_to_create_or_update:
        count += 1

        account_key = wage_info["account_key"]
        filing_period = wage_info["filing_period"]
        ssn = wage_info["employee_ssn"]

        employer_id = account_key_to_employer_id_map.get(account_key, None)
        if employer_id is None:
            logger.warning(
                "Attempted to save a wage row for unknown employer: %s",
                account_key,
                extra={"account_key": account_key},
            )
            continue

        existing_employee = ssn_to_existing_employee_model.get(ssn, None)
        if existing_employee is None:
            logger.warning(
                "Attempted to save a wage row for unknown employee: %s",
                account_key,
                extra={"account_key": account_key},
            )
            continue

        existing_wage_composite_key = get_wage_composite_key(
            employer_id, existing_employee.employee_id, filing_period
        )
        existing_wage = employer_employee_filing_period_to_wage_model.get(
            existing_wage_composite_key, None
        )

        if existing_wage is None:
            wage_model = dor_persistence_util.dict_to_wages_and_contributions(
                wage_info, existing_employee.employee_id, employer_id, import_log_entry_id
            )
            wages_contributions_models_existing_employees_to_create.append(wage_model)

        if count % 10000 == 0:
            logger.info(
                "Wage data for existing employees - count: %i/%i (%.1f%%), updated: %i , unmodified: %i, collected for creation: %i",
                count,
                wage_data_total,
                100.0 * count / wage_data_total,
                updated_count,
                unmodified_count,
                len(wages_contributions_models_existing_employees_to_create),
            )

    logger.info(
        "Creating new wage information for existing employees: %i",
        len(wages_contributions_models_existing_employees_to_create),
    )

    bulk_save(
        db_session,
        wages_contributions_models_existing_employees_to_create,
        "Employee Wages",
        commit=True,
    )

    report.created_wages_and_contributions_count += len(
        wages_contributions_models_existing_employees_to_create
    )

    logger.info(
        "Done - Creating new wage information for existing employees: %i",
        len(wages_contributions_models_existing_employees_to_create),
    )


def import_employees_and_wage_data(
    db_session: Session,
    employee_and_wage_info_list: List[ParsedEmployeeLine],
    employee_ssns_created_in_current_import_run: Dict[str, uuid.UUID],
    report: ImportReport,
    import_log_entry_id: int,
) -> None:
    # 1 - Create account key to existing employer id reference map
    account_keys = {employee_info["account_key"] for employee_info in employee_and_wage_info_list}
    account_key_to_employer_id_map = dor_persistence_util.get_employers_by_account_key(
        db_session, account_keys
    )

    # 2 - Create existing employee reference maps
    logger.info(
        "Create existing employee reference maps, checking lines: %i",
        len(employee_and_wage_info_list),
    )

    incoming_ssns = set()
    for employee_and_wage_info in employee_and_wage_info_list:
        incoming_ssns.add(employee_and_wage_info["employee_ssn"])

    ssns_to_check_in_db = list(
        filter(lambda ssn: ssn not in employee_ssns_created_in_current_import_run, incoming_ssns)
    )

    existing_employee_models = dor_persistence_util.get_employees_by_ssn(
        db_session, ssns_to_check_in_db
    )

    ssn_to_existing_employee_model = {}
    for employee in existing_employee_models:
        if employee.tax_identifier is not None:
            ssn_to_existing_employee_model[employee.tax_identifier.tax_identifier] = employee

    logger.info(
        "Done - Create existing employee reference maps - checked ssns: %i, existing employees matched: %i",
        len(ssns_to_check_in_db),
        len(existing_employee_models),
    )

    # 3 - Import employees
    import_employees(
        db_session,
        employee_and_wage_info_list,
        employee_ssns_created_in_current_import_run,
        ssn_to_existing_employee_model,
        report,
        import_log_entry_id,
    )

    # 4 - Import wages
    import_wage_data(
        db_session,
        employee_and_wage_info_list,
        account_key_to_employer_id_map,
        employee_ssns_created_in_current_import_run,
        ssn_to_existing_employee_model,
        report,
        import_log_entry_id,
    )


def parse_exempt_employer_file(
    employer_file_path: str,
    decrypter: Crypt,
    report: ImportReport,
    db_session: Session,
) -> Tuple[List, List]:
    """Parse employer file"""
    logger.info(
        "Start parsing exempt employer file",
        extra={"employer_file_path": employer_file_path},
    )
    employers = []
    employees = []

    employer_uuids: Dict[str, str] = dict()

    decrypt_files = os.getenv("DECRYPT") == "true"

    invalid_employer_key_line_nums = []
    line_count = 0

    last_employer_account_key = ""
    last_employer_filing_period: Optional[date] = None

    if decrypt_files:
        employer_capturer = Capturer(line_offset=0)
        decrypter.set_on_data(employer_capturer)
        get_decrypted_file_stream(employer_file_path, decrypter)

        for row in employer_capturer.lines:
            if not row:  # skip empty end of file lines
                continue

            line_count = line_count + 1

            if row.startswith("A"):
                try:
                    employer = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_A.parse_line(row)

                    line_length = len(row.strip("\n\r"))
                    if line_length != EMPLOYER_PENDING_FILING_RESPONSE_FILE_A_ROW_LENGTH:
                        logger.warning(
                            "Incorrect employer line length - Line {0}, employer name: {1}, line length: {2}".format(
                                line_count, employer["fstrEmployerName"], line_length
                            )
                        )
                        report.invalid_employer_lines_count += 1

                    last_employer_filing_period = datetime.strptime(
                        employer["fdtmQuarterYear"], "%Y%m%d"
                    ).date()
                    last_employer_account_key = employer_uuids.get(employer["fstrEmployerID"], "")

                    if last_employer_account_key == "":
                        existing_employer = dor_persistence_util.get_employer_by_fein(
                            db_session, employer["fstrEmployerID"]
                        )
                        if (
                            existing_employer is not None
                            and existing_employer.account_key is not None
                        ):
                            employer_uuids[
                                employer["fstrEmployerID"]
                            ] = existing_employer.account_key
                        else:
                            employer_uuids[employer["fstrEmployerID"]] = "exempt_employer_" + str(
                                uuid_gen()
                            )
                        last_employer_account_key = employer_uuids[employer["fstrEmployerID"]]

                    family_exemption = True
                    medical_exemption = True

                    transformed_dict = {
                        "fein": employer["fstrEmployerID"],
                        "employer_name": employer["fstrEmployerName"],
                        "filing_period": last_employer_filing_period,
                        "total_pfml_contribution": employer["fcurEmployeeWages"],
                        "employer_dba": employer["fstrEmployerName"],
                        "account_key": last_employer_account_key,
                        "family_exemption": family_exemption,
                        "medical_exemption": medical_exemption,
                        "exemption_commence_date": exemption_date,
                        "exemption_cease_date": exemption_date,
                        "updated_date": None,
                        "employer_address_state": None,
                        "employer_address_city": None,
                        "employer_address_zip": None,
                        "employer_address_country": None,
                        "employer_address_street": None,
                    }
                    employers.append(transformed_dict)
                except Exception as e:
                    logger.exception(e)
                    report.parsed_employers_exception_line_nums.append(line_count)

            if row.startswith("B"):
                try:
                    employee = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_B.parse_line(row)

                    if len(row.strip("\n\r")) != EMPLOYER_PENDING_FILING_RESPONSE_FILE_B_ROW_LENGTH:
                        employee = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_B.parse_line(row)
                        invalid_employer_key_line_nums.append("Line {0}".format(line_count))
                        continue

                    employee = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_B.parse_line(row)
                    transformed_dict = {
                        "account_key": last_employer_account_key,
                        "filing_period": last_employer_filing_period,
                        "employee_first_name": employee["fstrFirstName"],
                        "employee_last_name": employee["fstrLastName"],
                        "employee_ssn": employee["fstrID"],
                        "independent_contractor": False,
                        "opt_in": False,
                        "employee_qtr_wages": employee["fcurQuarterWages"],
                        "employee_ytd_wages": 0,
                        "employee_medical": 0,
                        "employer_medical": 0,
                        "employee_family": 0,
                        "employer_family": 0,
                    }

                    employees.append(transformed_dict)
                except Exception as e:
                    logger.exception(e)
    else:

        for row in get_decrypted_file_stream(employer_file_path, decrypter):
            if not row:  # skip empty end of file lines
                continue

            try:
                row = row.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                pass

            line_count = line_count + 1

            if row.startswith("A"):
                if len(row.strip("\n\r")) != EMPLOYER_PENDING_FILING_RESPONSE_FILE_A_ROW_LENGTH:
                    employer = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_A.parse_line(row)
                    invalid_employer_key_line_nums.append(
                        "Line {0}, account key: {1}".format(
                            line_count, employer["fstrEmployerName"]
                        )
                    )
                    continue

                employer = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_A.parse_line(row)
                last_employer_filing_period = datetime.strptime(
                    employer["fdtmQuarterYear"], "%Y%m%d"
                ).date()
                last_employer_account_key = employer_uuids.get(employer["fstrEmployerID"], "")

                if last_employer_account_key == "":
                    existing_employer = dor_persistence_util.get_employer_by_fein(
                        db_session, employer["fstrEmployerID"]
                    )
                    if existing_employer is not None and existing_employer.account_key is not None:
                        employer_uuids[employer["fstrEmployerID"]] = existing_employer.account_key
                    else:
                        employer_uuids[employer["fstrEmployerID"]] = "exempt_employer_" + str(
                            uuid_gen()
                        )
                    last_employer_account_key = employer_uuids[employer["fstrEmployerID"]]

                family_exemption = True
                medical_exemption = True

                transformed_dict = {
                    "fein": employer["fstrEmployerID"],
                    "employer_name": employer["fstrEmployerName"],
                    "filing_period": last_employer_filing_period,
                    "total_pfml_contribution": employer["fcurEmployeeWages"],
                    "employer_dba": employer["fstrEmployerName"],
                    "account_key": last_employer_account_key,
                    "family_exemption": family_exemption,
                    "medical_exemption": medical_exemption,
                    "exemption_commence_date": exemption_date,
                    "exemption_cease_date": exemption_date,
                    "updated_date": None,
                    "employer_address_state": None,
                    "employer_address_city": None,
                    "employer_address_zip": None,
                    "employer_address_country": None,
                    "employer_address_street": None,
                }
                employers.append(transformed_dict)

            if row.startswith("B"):
                if len(row.strip("\n\r")) != EMPLOYER_PENDING_FILING_RESPONSE_FILE_B_ROW_LENGTH:
                    employee = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_B.parse_line(row)
                    invalid_employer_key_line_nums.append("Line {0}".format(line_count))
                    continue

                employee = EMPLOYER_PENDING_FILING_RESPONSE_FILE_FORMAT_B.parse_line(row)
                transformed_dict = {
                    "account_key": last_employer_account_key,
                    "filing_period": last_employer_filing_period,
                    "employee_first_name": employee["fstrFirstName"],
                    "employee_last_name": employee["fstrLastName"],
                    "employee_ssn": employee["fstrID"],
                    "independent_contractor": False,
                    "opt_in": False,
                    "employee_ytd_wages": 0,
                    "employee_qtr_wages": employee["fcurQuarterWages"],
                    "employee_medical": 0,
                    "employer_medical": 0,
                    "employee_family": 0,
                    "employer_family": 0,
                }

                employees.append(transformed_dict)

    logger.info(
        "Finished parsing employer file",
        extra={
            "employer_file_path": employer_file_path,
            "invalid_parsed_employers": repr(invalid_employer_key_line_nums),
            "valid_parsed_employers": len(employers),
            "valid_parsed_employees": len(employees),
        },
    )
    return employers, employees


if __name__ == "__main__":
    handler()
