#!/usr/bin/python3
#
# Lambda function to import DOR data from S3 to PostgreSQL (RDS).
#

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import boto3
from sqlalchemy.orm.session import Session

import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.dor.importer.dor_file_formats import (
    EMPLOYEE_FORMAT,
    EMPLOYER_FILE_FORMAT,
    EMPLOYER_QUARTER_INFO_FORMAT,
)
from massgov.pfml.util.config import get_secret_from_env
from massgov.pfml.util.encryption import Crypt, GpgCrypt, Utf8Crypt
from massgov.pfml.util.files.file_format import FileFormat

logger = logging.get_logger("massgov.pfml.dor.importer.import_dor")

s3 = boto3.client("s3")
s3Bucket = boto3.resource("s3")
aws_ssm = boto3.client("ssm", region_name="us-east-1")


# TODO get these from environment variables
RECEIVED_FOLDER = "dor/received/"
PROCESSED_FOLDER = "dor/processed/"

EMPLOYER_FILE_PREFIX = "DORDFMLEMP_"
EMPLOYEE_FILE_PREFIX = "DORDFML_"


@dataclass
class ImportBatch:
    upload_date: str
    employer_file: str
    employee_file: str


@dataclass
class ImportReport:
    start: str = datetime.now().isoformat()
    employer_file: str = ""
    employee_file: str = ""
    parsed_employers_count: int = 0
    parsed_employers_quarter_info_count: int = 0
    parsed_employees_info_count: int = 0
    created_employers_count: int = 0
    updated_employers_count: int = 0
    unmodified_employers_count: int = 0
    created_employees_count: int = 0
    updated_employees_count: int = 0
    unmodified_employees_count: int = 0
    created_wages_and_contributions_count: int = 0
    updated_wages_and_contributions_count: int = 0
    unmodified_wages_and_contributions_count: int = 0
    status: Optional[str] = None
    end: Optional[str] = None
    updated_employer_ids: List[UUID] = field(default_factory=list)
    unmodified_employer_ids: List[UUID] = field(default_factory=list)
    updated_employee_ids: List[UUID] = field(default_factory=list)
    unmodified_employee_ids: List[UUID] = field(default_factory=list)
    updated_wages_and_contributions_ids: List[UUID] = field(default_factory=list)
    unmodified_wages_and_contributions_ids: List[UUID] = field(default_factory=list)


@dataclass
class ImportRunReport:
    start: str
    imports: List[ImportReport] = field(default_factory=list)
    end: Optional[str] = None
    message: str = ""


def handler(event=None, context=None):
    """Lambda handler function."""
    logging.init(__name__)

    folder_path = os.environ.get("FOLDER_PATH")
    decrypt_files = os.getenv("DECRYPT") == "true"

    logger.info(
        "Starting import run", extra={"folder_path": folder_path, "decrypt_files": decrypt_files}
    )

    import_batches = get_files_to_process(folder_path)
    report = ImportRunReport(start=datetime.now().isoformat())

    if not import_batches:
        logger.info("no files found to import")
        report.message = "no files found to import"
    else:
        import_reports = process_import_batches(import_batches, decrypt_files)
        report.imports = import_reports
        report.message = "files imported"

    report.end = datetime.now().isoformat()
    logger.info("Finished import run")
    return {"status": "OK", "import_type": "daily", "report": asdict(report)}


def process_import_batches(
    import_batches: List[ImportBatch],
    decrypt_files: bool,
    optional_db_session: Optional[Session] = None,
) -> List[ImportReport]:
    import_reports: List[ImportReport] = []

    # Initialize the file decrypter
    decrypter: Crypt

    if decrypt_files:
        logger.info("Setting up GPG")
        gpg_decryption_key = get_secret_from_env(aws_ssm, "GPG_DECRYPTION_KEY")
        gpg_decryption_passphrase = get_secret_from_env(aws_ssm, "GPG_DECRYPTION_KEY_PASSPHRASE")
        decrypter = GpgCrypt(gpg_decryption_key, gpg_decryption_passphrase)
    else:
        logger.info("Skipping GPG decrypter setup")
        decrypter = Utf8Crypt()

    # Initialize the database
    db_session_raw = optional_db_session
    if not db_session_raw:
        db_session_raw = db.init()

    with db.session_scope(db_session_raw) as db_session:

        # process each batch
        for import_batch in import_batches:
            logger.info(
                "processing import patch",
                extra={
                    "date": import_batch.upload_date,
                    "employer_file": import_batch.employer_file,
                    "employee_file": import_batch.employee_file,
                },
            )

            import_report = process_daily_import(
                db_session, import_batch.employer_file, import_batch.employee_file, decrypter
            )
            import_reports.append(import_report)

        return import_reports


def process_daily_import(
    db_session: Session, employer_file_path: str, employee_file_path: str, decrypter: Crypt,
) -> ImportReport:

    logger.info("Starting to process files")
    report = ImportReport(
        start=datetime.now().isoformat(),
        employer_file=employer_file_path,
        employee_file=employee_file_path,
    )

    try:
        report_log_entry = dor_persistence_util.create_import_log_entry(db_session, report)
        employers = parse_employer_file(employer_file_path, decrypter)
        employers_quarter_info, employees_info = parse_employee_file(employee_file_path, decrypter)

        parsed_employers_count = len(employers)
        parsed_employers_quarter_info_count = len(employers_quarter_info)
        parsed_employees_info_count = len(employees_info)

        logger.info(
            "Finished parsing files",
            extra={
                "employer_file": employer_file_path,
                "employee_file": employee_file_path,
                "parsed_employers_count": parsed_employers_count,
                "parsed_employers_quarter_info_count": parsed_employers_quarter_info_count,
                "parsed_employees_info_count": parsed_employees_info_count,
            },
        )

        import_to_db(
            db_session,
            employers,
            employers_quarter_info,
            employees_info,
            report,
            report_log_entry.import_log_id,
        )

        # finalize report
        report.parsed_employers_count = parsed_employers_count
        report.parsed_employers_quarter_info_count = parsed_employers_quarter_info_count
        report.parsed_employees_info_count = parsed_employees_info_count
        report.status = "success"
        report.end = datetime.now().isoformat()

        # move file to processed folder
        # move_file_to_processed(bucket, file_for_import) # TODO turn this on with invoke flag

    except Exception:
        logger.exception("Exception while processing")
        report.status = "error"
        report.end = datetime.now().isoformat()
    finally:
        logger.info("Attempting to update existing import log entry with latest report")
        dor_persistence_util.update_import_log_entry(db_session, report_log_entry, report)
        logger.info("Import log entry successfully updated")

        # TODO determine if this is still necessary now that we have db logs
        # write_report_to_s3(bucket, report)

    return report


def import_to_db(
    db_session, employers, employers_quarter_info, employees_info, report, import_log_entry_id
):
    """Process through parsed objects and persist into database"""
    logger.info("Starting import")

    account_key_to_employer_id_map = import_employers(
        db_session, employers, report, import_log_entry_id
    )
    import_employees_and_wage_data(
        db_session,
        account_key_to_employer_id_map,
        employers_quarter_info,
        employees_info,
        report,
        import_log_entry_id,
    )

    logger.info("Finished import")


def import_employers(db_session, employers, report, import_log_entry_id):
    # look through all employers
    """Import employers into db"""
    logger.info("Importing employers")

    existing_employers = dor_persistence_util.get_all_employers_fein(db_session)

    def search(fein):
        for e in existing_employers:
            if e[1] == fein:
                return e

    employer_list = list(filter(lambda employer: search(employer["fein"]) is None, employers))

    fein_to_new_employer_id = {}
    fein_to_new_address_id = {}
    for emp in employers:
        fein_to_new_employer_id[emp["fein"]] = uuid.uuid4()
        fein_to_new_address_id[emp["fein"]] = uuid.uuid4()

    employers_to_create = list(
        map(
            lambda employer_info: dor_persistence_util.dict_to_employer(
                employer_info, import_log_entry_id, fein_to_new_employer_id[employer_info["fein"]]
            ),
            employer_list,
        )
    )
    found_employers = list(filter(lambda employer: search(employer["fein"]) is not None, employers))

    employers_to_update = list(
        filter(
            lambda employer: employer["updated_date"] > search(employer["fein"]).dor_updated_date,
            found_employers,
        )
    )
    emplyers_to_not_update = list(
        filter(
            lambda employer: employer["updated_date"] <= search(employer["fein"]).dor_updated_date,
            found_employers,
        )
    )

    logger.info("employers to create: %i", len(employers_to_create))
    logger.info("employers to update: %i", len(employers_to_update))
    logger.info("employers not being updated: %i", len(emplyers_to_not_update))

    # Create employers
    db_session.bulk_save_objects(employers_to_create)
    db_session.commit()

    # Create addresses
    addresses_to_create = list(
        map(
            lambda employer_info: dor_persistence_util.dict_to_address(
                db_session, employer_info, fein_to_new_address_id[employer_info["fein"]]
            ),
            employer_list,
        )
    )
    db_session.bulk_save_objects(addresses_to_create, return_defaults=True)
    db_session.commit()

    # Build list of addresses to create
    employer_addresses_assoc_to_create = []

    for emp in employers_to_create:
        employer_addresses_assoc_to_create.append(
            dor_persistence_util.employer_id_address_id_to_model(
                fein_to_new_employer_id[emp.employer_fein],
                fein_to_new_address_id[emp.employer_fein],
            )
        )

    db_session.bulk_save_objects(employer_addresses_assoc_to_create)
    db_session.commit()

    account_key_to_employer_id_map = {}
    for e in employers_to_create:
        account_key_to_employer_id_map[e.account_key] = fein_to_new_employer_id[e.employer_fein]

    count = 0
    for employer_info in employers_to_update:
        count += 1
        if count % 1000 == 0:
            logger.info("Updating employer info, current %i", count)

        account_key = employer_info["account_key"]
        existing_employer = dor_persistence_util.get_employer_by_fein(
            db_session, employer_info["fein"]
        )

        updated_date = employer_info["updated_date"]
        if updated_date > existing_employer.dor_updated_date:
            dor_persistence_util.update_employer(
                db_session, existing_employer, employer_info, import_log_entry_id
            )

            report.updated_employer_ids.append(str(existing_employer.employer_id))
        else:
            report.unmodified_employer_ids.append(str(existing_employer.employer_id))

        account_key_to_employer_id_map[account_key] = existing_employer.employer_id

    report.unmodified_employer_ids = list(
        map(lambda employer: str(search(employer["fein"]).employer_id), emplyers_to_not_update)
    )
    report.created_employers_count = len(employers_to_create)
    report.updated_employers_count = len(report.updated_employer_ids)
    report.unmodified_employers_count = len(emplyers_to_not_update)

    logger.info(
        "Finished importing employers",
        extra={
            "created_employers_count": report.created_employers_count,
            "updated_employers_count": report.updated_employers_count,
            "unmodified_employers_count": report.unmodified_employers_count,
        },
    )

    return account_key_to_employer_id_map


def import_employees_and_wage_data(
    db_session,
    account_key_to_employer_id_map,
    employers_quarter_info,
    employees_info,
    report,
    import_log_entry_id,
):
    """Import employees and wage information"""
    logger.info(
        "Importing wage information - employer: %i, employee: %i",
        len(employers_quarter_info),
        len(employees_info),
    )

    # create a reference map of amended flag for employee and wage data
    employee_amended_flag_map = {}
    wage_data_amended_flag_map = {}

    count = 0

    for employer_quarter_info in employers_quarter_info:
        count += 1
        if count % 1000 == 0:
            logger.info("Importing employer qaurter info, current %i", count)

        account_key = employer_quarter_info["account_key"]
        filing_period_str = employer_quarter_info["filing_period"].strftime("%Y%m%d")
        composite_key = "{}-{}".format(account_key, filing_period_str)
        amended_flag = employer_quarter_info["amended_flag"]

        employee_amended_flag_map[account_key] = amended_flag
        wage_data_amended_flag_map[composite_key] = amended_flag

    # import employees
    ssn_to_new_employee_id = {}
    employee_ids_created_in_current_run = set()

    count = 0

    # find all employees by ssn to see if create or update
    ssns = map(lambda employee_info: employee_info["employee_ssn"], employees_info)
    existing_employees = dor_persistence_util.get_employees_by_ssn(db_session, ssns)

    ssn_to_employee = {}
    for employee in existing_employees:
        ssn_to_employee[employee.tax_identifier.tax_identifier] = employee

    employees_list = list(
        filter(lambda employee: employee["employee_ssn"] not in ssn_to_employee, employees_info)
    )
    ssn_to_new_tax_id = {}
    for emp in employees_list:
        ssn_to_new_employee_id[emp["employee_ssn"]] = uuid.uuid4()
        ssn_to_new_tax_id[emp["employee_ssn"]] = uuid.uuid4()
        employee_ids_created_in_current_run.add(ssn_to_new_employee_id[emp["employee_ssn"]])

    tax_ids_to_create = []
    for ssn in ssn_to_new_employee_id:
        tax_ids_to_create.append(dor_persistence_util.tax_id_from_dict(ssn_to_new_tax_id[ssn], ssn))

    db_session.bulk_save_objects(tax_ids_to_create)
    db_session.commit()

    employee_models = list(
        map(
            lambda employee_info: dor_persistence_util.dict_to_employee(
                employee_info,
                import_log_entry_id,
                ssn_to_new_employee_id[employee_info["employee_ssn"]],
                ssn_to_new_tax_id[employee_info["employee_ssn"]],
            ),
            employees_list,
        )
    )

    employee_id_to_employee_record = {}
    for emp in employee_models:
        employee_id_to_employee_record[emp.employee_id] = emp

    employees_to_create = employee_id_to_employee_record.values()

    db_session.bulk_save_objects(employees_to_create)
    db_session.commit()

    employees_to_update = list(
        filter(lambda employee: employee["employee_ssn"] in ssn_to_employee, employees_info)
    )

    report.created_employees_count = report.created_employees_count + len(
        list(set(employees_to_create))
    )
    for employee_info in employees_to_update:

        count += 1

        ssn = employee_info["employee_ssn"]
        account_key = employee_info["account_key"]
        existing_employee = ssn_to_employee[ssn]

        if existing_employee is None:
            created_employee = dor_persistence_util.create_employee(
                db_session, employee_info, import_log_entry_id
            )

            ssn_to_new_employee_id[ssn] = created_employee.employee_id
            employee_ids_created_in_current_run.add(created_employee.employee_id)
            report.created_employees_count = report.created_employees_count + 1
        else:
            # There may be multiple employee and wage data rows for the same employee for each quarte or because of multiple employers.
            # Skip if the employee was created in the current run.
            if existing_employee.employee_id in employee_ids_created_in_current_run:
                continue

            if employee_amended_flag_map[account_key] is True:
                dor_persistence_util.update_employee(
                    db_session, existing_employee, employee_info, import_log_entry_id
                )

                report.updated_employee_ids.append(str(existing_employee.employee_id))
            else:
                report.unmodified_employee_ids.append(str(existing_employee.employee_id))

            ssn_to_new_employee_id[ssn] = existing_employee.employee_id

    report.updated_employees_count = len(report.updated_employee_ids)
    report.unmodified_employees_count = len(report.unmodified_employee_ids)

    logger.info(
        "Finished importing employee information",
        extra={
            "created_employees_count": report.created_employees_count,
            "updated_employees_count": report.updated_employees_count,
            "unmodified_employee_ids": report.unmodified_employees_count,
        },
    )

    logger.info("Importing employee wage information")

    wages_contributions_to_create = []
    for employee_info in employees_list:
        wages_contributions_to_create.append(
            dor_persistence_util.dict_to_wages_and_contributions(
                employee_info,
                ssn_to_new_employee_id[employee_info["employee_ssn"]],
                account_key_to_employer_id_map[employee_info["account_key"]],
                import_log_entry_id,
            )
        )

    report.created_wages_and_contributions_count = len(wages_contributions_to_create)

    db_session.bulk_save_objects(wages_contributions_to_create)
    db_session.commit()

    # import wage information
    count = 0
    for employee_info in employees_to_update:

        count += 1
        if count % 1000 == 0:
            logger.info("Importing employee qaurter wage info, current %i", count)

        account_key = employee_info["account_key"]
        filing_period = employee_info["filing_period"]
        ssn = employee_info["employee_ssn"]

        employee_id = ssn_to_new_employee_id[ssn]
        employer_id = account_key_to_employer_id_map[account_key]

        existing_wage = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
            db_session, employee_id, employer_id, filing_period
        )

        if existing_wage is None:
            dor_persistence_util.create_wages_and_contributions(
                db_session, employee_info, employee_id, employer_id, import_log_entry_id
            )

            report.created_wages_and_contributions_count = (
                report.created_wages_and_contributions_count + 1
            )
        else:
            ameneded_flag_key = "{}-{}".format(account_key, filing_period.strftime("%Y%m%d"))
            if wage_data_amended_flag_map[ameneded_flag_key] is True:
                dor_persistence_util.update_wages_and_contributions(
                    db_session, existing_wage, employee_info, import_log_entry_id
                )
                report.updated_wages_and_contributions_ids.append(
                    str(existing_wage.wage_and_contribution_id)
                )
            else:
                report.unmodified_wages_and_contributions_ids.append(
                    str(existing_wage.wage_and_contribution_id)
                )

    report.updated_wages_and_contributions_count = len(report.updated_wages_and_contributions_ids)
    report.unmodified_wages_and_contributions_count = len(
        report.unmodified_wages_and_contributions_ids
    )

    logger.info(
        "Finished importing employee wage information",
        extra={
            "created_wages_and_contributions_count": report.created_wages_and_contributions_count,
            "updated_wages_and_contributions_count": report.updated_wages_and_contributions_count,
            "unmodified_wages_and_contributions_count": report.unmodified_wages_and_contributions_count,
        },
    )

    return ssn_to_new_employee_id


# TODO turn return dataclasses list instead of object list
def parse_employer_file(employer_file_path, decrypter):
    """Parse employer file"""
    logger.info("Start parsing employer file", extra={"employer_file_path": employer_file_path})
    employers = []

    file_bytes = file_util.read_file(employer_file_path, "rb")
    decrypted_str = decrypter.decrypt(file_bytes)
    decrypted_lines = decrypted_str.split("\n")

    employer_file_format = FileFormat(EMPLOYER_FILE_FORMAT)
    for row in decrypted_lines:
        if not row:  # skip empty end of file lines
            continue

        employer = employer_file_format.parse_line(row)
        employers.append(employer)

    logger.info("Finished parsing employer file", extra={"employer_file_path": employer_file_path})
    return employers


def parse_employee_file(employee_file_path, decrypter):
    """Parse employee file"""
    logger.info("Start parsing employee file", extra={"employee_file_path": employee_file_path})

    employers_quarter_info = []
    employees_info = []

    file_bytes = file_util.read_file(employee_file_path, "rb")
    decrypted_str = decrypter.decrypt(file_bytes)
    decrypted_lines = decrypted_str.split("\n")

    employer_quarter_info_file_format = FileFormat(EMPLOYER_QUARTER_INFO_FORMAT)
    employee_wage_file_format = FileFormat(EMPLOYEE_FORMAT)

    for row in decrypted_lines:
        if not row:  # skip empty end of file lines
            continue

        if row.startswith("A"):
            employer_quarter_info = employer_quarter_info_file_format.parse_line(row)
            employers_quarter_info.append(employer_quarter_info)
        else:
            employee_info = employee_wage_file_format.parse_line(row)
            employees_info.append(employee_info)

    logger.info("Finished parsing employee file", extra={"employee_file_path": employee_file_path})
    return employers_quarter_info, employees_info


def read_file(bucket, key):
    """Read the data from an s3 object."""
    response = s3.get_object(Bucket=bucket.name, Key=key)
    # read all the data at once for now since we need to decrypt.
    return response["Body"].read()


def move_file_to_processed(bucket, file_to_copy):
    """Move file from recieved to processed folder"""
    # TODO make this a move instead of copy in real implementation
    bucket_name = bucket.name
    copy_source = "/" + bucket_name + "/" + file_to_copy

    file_name = get_file_name(file_to_copy)
    copy_destination = (
        PROCESSED_FOLDER + file_name + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
    )

    s3.copy_object(
        Bucket=bucket_name, CopySource=copy_source, Key=copy_destination,
    )


def write_report_to_s3(bucket, report):
    """Write report of import to s3"""
    report_str = json.dumps(asdict(report), indent=2)
    file_name = get_file_name(report.employee_file)
    destination_key = (
        PROCESSED_FOLDER
        + file_name
        + "_"
        + datetime.now().strftime("%Y%m%d%H%M%S")
        + "_report.json"
    )
    s3.put_object(Body=report_str, Bucket=bucket.name, Key=destination_key)


def get_files_to_process(path: Optional[str]) -> List[ImportBatch]:
    files_by_date = get_files_for_import_grouped_by_date(path)
    file_date_keys = sorted(files_by_date.keys())

    import_batches: List[ImportBatch] = []

    if not file_date_keys:
        return []

    for file_date_key in file_date_keys:
        files_for_import = files_by_date[file_date_key]

        # logger.info("importing files", extra={"files_for_import": files_for_import})

        employer_file_filter = [
            f for f in files_for_import if get_file_name(f).startswith(EMPLOYER_FILE_PREFIX)
        ]
        if not employer_file_filter:
            logger.info("Employer file not found for date", extra={"date": file_date_key})
            continue

        employer_file = employer_file_filter[0]

        employee_file_filter = [
            f for f in files_for_import if get_file_name(f).startswith(EMPLOYEE_FILE_PREFIX)
        ]
        if len(employee_file_filter) == 0:
            logger.info("Employee file not found for date", extra={"date": file_date_key})
            continue

        employee_file = employee_file_filter[0]

        import_batches.append(
            ImportBatch(
                upload_date=file_date_key, employer_file=employer_file, employee_file=employee_file
            )
        )

    return import_batches


def get_files_for_import_grouped_by_date(path):
    """Get the paths (s3 keys) of files in the recieved folder of the bucket"""

    files_by_date: Dict[str, List[str]] = {}
    files_for_import = file_util.list_files(path)
    files_for_import.sort()
    for file_key in files_for_import:
        date_start_index = file_key.rfind("_")
        if date_start_index >= 0:
            date_start_index = date_start_index + 1
            date_end_index = date_start_index + 8  # only date part is relevant
            file_date = file_key[date_start_index:date_end_index]
            if files_by_date.get(file_date, None) is None:
                files_by_date[file_date] = []
            files_by_date[file_date].append("{}/{}".format(str(path), file_key))
    return files_by_date


def get_file_name(s3_file_key):
    """Get file name without extension from an object key"""
    file_name_index = s3_file_key.rfind("/") + 1
    file_name_extention_index = s3_file_key.rfind(".txt")
    file_name = s3_file_key[file_name_index:file_name_extention_index]
    return file_name
