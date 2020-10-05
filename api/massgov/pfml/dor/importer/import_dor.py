#!/usr/bin/python3
#
# Lambda function to import DOR data from S3 to PostgreSQL (RDS).
#

import os
import pathlib
import re
import resource
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import boto3
from sqlalchemy.orm.session import Session

import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit
from massgov.pfml import db
from massgov.pfml.dor.importer.dor_file_formats import EMPLOYEE_FORMAT, EMPLOYER_FILE_FORMAT
from massgov.pfml.util.config import get_secret_from_env
from massgov.pfml.util.encryption import Crypt, GpgCrypt, Utf8Crypt

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
    employer_file: pathlib.PurePath
    employee_file: pathlib.PurePath


@dataclass
class ImportReport:
    start: str = datetime.now().isoformat()
    employer_file: str = ""
    employee_file: str = ""
    parsed_employers_count: int = 0
    parsed_employees_info_count: int = 0
    created_employers_count: int = 0
    updated_employers_count: int = 0
    unmodified_employers_count: int = 0
    created_employees_count: int = 0
    updated_employees_count: int = 0
    created_wages_and_contributions_count: int = 0
    updated_wages_and_contributions_count: int = 0
    status: Optional[str] = None
    end: Optional[str] = None


@dataclass
class ImportRunReport:
    start: str
    imports: List[ImportReport] = field(default_factory=list)
    end: Optional[str] = None
    message: str = ""


def handler(event=None, context=None):
    """Lambda handler function."""
    massgov.pfml.util.logging.audit.init_security_logging()
    logging.init(__name__)

    logger.addFilter(filter_add_memory_usage)

    folder_path = pathlib.PurePath(os.environ["FOLDER_PATH"])
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


def filter_add_memory_usage(record):
    """Logging filter that adds memory usage as an extra attribute."""
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    record.maxrss = "%iM" % (rusage.ru_maxrss / 1024)
    return True


def process_import_batches(
    import_batches: List[ImportBatch],
    decrypt_files: bool,
    optional_db_session: Optional[Session] = None,
) -> List[ImportReport]:
    import_reports: List[ImportReport] = []

    decrypter = decrypter_factory(decrypt_files)

    # Initialize the database
    db_session_raw = optional_db_session
    if not db_session_raw:
        db_session_raw = db.init()

    with db.session_scope(db_session_raw) as db_session:

        # process each batch
        for import_batch in import_batches:
            logger.info(
                "Processing import batch",
                extra={
                    "date": import_batch.upload_date,
                    "employer_file": import_batch.employer_file,
                    "employee_file": import_batch.employee_file,
                },
            )

            import_report = process_daily_import(
                db_session,
                str(import_batch.employer_file),
                str(import_batch.employee_file),
                decrypter,
            )
            import_reports.append(import_report)

        return import_reports


def decrypter_factory(decrypt_files):
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
    return decrypter


def process_daily_import(
    db_session: Session, employer_file_path: str, employee_file_path: str, decrypter: Crypt,
) -> ImportReport:

    logger.info("Starting to process files")
    report = ImportReport(
        start=datetime.now().isoformat(),
        status="in progress",
        employer_file=employer_file_path,
        employee_file=employee_file_path,
    )

    report_log_entry = dor_persistence_util.create_import_log_entry(db_session, report)
    try:
        employers = parse_employer_file(employer_file_path, decrypter)
        employees_info = parse_employee_file(employee_file_path, decrypter)

        parsed_employers_count = len(employers)
        parsed_employees_info_count = len(employees_info)

        logger.info(
            "Finished parsing files",
            extra={
                "employer_file": employer_file_path,
                "employee_file": employee_file_path,
                "parsed_employers_count": parsed_employers_count,
                "parsed_employees_info_count": parsed_employees_info_count,
            },
        )

        import_to_db(
            db_session, employers, employees_info, report, report_log_entry.import_log_id,
        )

        # finalize report
        report.parsed_employers_count = parsed_employers_count
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

    return report


def import_to_db(db_session, employers, employees_info, report, import_log_entry_id):
    """Process through parsed objects and persist into database"""
    logger.info("Starting import")

    account_key_to_employer_id_map = import_employers(
        db_session, employers, report, import_log_entry_id
    )
    import_employees_and_wage_data(
        db_session, account_key_to_employer_id_map, employees_info, report, import_log_entry_id,
    )

    logger.info("Finished import")


def batch_apply(items, batch_fn_name, batch_fn, batch_size=100000):
    size = len(items)
    start_index = 0
    while start_index < size:
        logger.info("batch: %s, batch start: %i", batch_fn_name, start_index)

        end_index = start_index + batch_size
        batch = items[start_index:end_index]

        batch_fn(batch)

        start_index = end_index


def bulk_save(db_session, models_list, model_name, commit=False, batch_size=10000):
    def bulk_save_helper(models_batch):
        db_session.bulk_save_objects(models_batch)
        if commit:
            db_session.commit()

    batch_apply(models_list, f"Saving {model_name}", bulk_save_helper, batch_size=batch_size)


def import_employers(db_session, employers, report, import_log_entry_id):
    """Import employers into db"""
    logger.info("Importing employers")

    # 1 - Get all employers in DB
    existing_employer_reference_models = dor_persistence_util.get_all_employers_fein(db_session)
    fein_to_existing_employer_reference_models = {
        employer.employer_fein: employer for employer in existing_employer_reference_models
    }

    logger.info("Found employers in db: %i", len(existing_employer_reference_models))

    # 2 - Create employers
    not_found_employer_info_list = list(
        filter(
            lambda employer: employer["fein"] not in fein_to_existing_employer_reference_models,
            employers,
        )
    )

    fein_to_new_employer_id = {}
    fein_to_new_address_id = {}
    for emp in not_found_employer_info_list:
        fein_to_new_employer_id[emp["fein"]] = uuid.uuid4()
        fein_to_new_address_id[emp["fein"]] = uuid.uuid4()

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

    logger.info("Done - Creating new employers: %i", len(employer_models_to_create))

    report.created_employers_count = len(employer_models_to_create)

    # 3 - Create employer addresses
    addresses_models_to_create = list(
        map(
            lambda employer_info: dor_persistence_util.dict_to_address(
                employer_info, fein_to_new_address_id[employer_info["fein"]]
            ),
            not_found_employer_info_list,
        )
    )

    logger.info("Creating new employer addresses: %i", len(addresses_models_to_create))

    bulk_save(db_session, addresses_models_to_create, "Employer Addresses")

    logger.info("Done - Creating new employer addresses: %i", len(addresses_models_to_create))

    # 4 - Create Address to Employer mapping records

    employer_address_relationship_models_to_create = []

    for emp in employer_models_to_create:
        employer_address_relationship_models_to_create.append(
            dor_persistence_util.employer_id_address_id_to_model(
                fein_to_new_employer_id[emp.employer_fein],
                fein_to_new_address_id[emp.employer_fein],
            )
        )

    logger.info(
        "Creating new employer address mapping: %i",
        len(employer_address_relationship_models_to_create),
    )

    bulk_save(
        db_session,
        employer_address_relationship_models_to_create,
        "Employer Address Mapping",
        commit=True,
    )

    logger.info(
        "Done - Creating new employer address mapping: %i",
        len(employer_address_relationship_models_to_create),
    )

    # 5 - Create map of new employer account keys
    account_key_to_employer_id_map = {}
    for e in employer_models_to_create:
        account_key_to_employer_id_map[e.account_key] = fein_to_new_employer_id[e.employer_fein]

    # 6 - Update existing employers
    found_employer_info_list = list(
        filter(
            lambda employer: employer["fein"] in fein_to_existing_employer_reference_models,
            employers,
        )
    )

    found_employer_info_to_update_list = list(
        filter(
            lambda employer: employer["updated_date"]
            > fein_to_existing_employer_reference_models[employer["fein"]].dor_updated_date,
            found_employer_info_list,
        )
    )

    logger.info("Updating employers: %i", len(found_employer_info_to_update_list))

    count = 0
    for employer_info in found_employer_info_to_update_list:
        count += 1
        if count % 1000 == 0:
            logger.info("Updating employer info, current %i", count)

        existing_employer_model = dor_persistence_util.get_employer_by_fein(
            db_session, employer_info["fein"]
        )
        dor_persistence_util.update_employer(
            db_session, existing_employer_model, employer_info, import_log_entry_id
        )

        account_key = employer_info["account_key"]
        account_key_to_employer_id_map[account_key] = existing_employer_model.employer_id

    report.updated_employers_count = len(found_employer_info_to_update_list)
    logger.info("Done - Updating employers: %i", len(found_employer_info_to_update_list))

    # 7 - Track and report not updated employers
    found_employer_info_to_not_update_list = list(
        filter(
            lambda employer: employer["updated_date"]
            <= fein_to_existing_employer_reference_models[employer["fein"]].dor_updated_date,
            found_employer_info_list,
        )
    )

    for employer_info in found_employer_info_to_not_update_list:
        existing_employer_reference_model = fein_to_existing_employer_reference_models[
            employer_info["fein"]
        ]
        account_key = employer_info["account_key"]
        account_key_to_employer_id_map[account_key] = existing_employer_reference_model.employer_id

    report.unmodified_employers_count = len(found_employer_info_to_not_update_list)
    logger.info("Employers not updated: %i", len(found_employer_info_to_not_update_list))

    # 8 - Done
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
    employee_and_wage_info_list,
    report,
    import_log_entry_id,
):
    """Import employees and wage information"""
    logger.info(
        "Start import of wage information - rows: %i", len(employee_and_wage_info_list),
    )

    # 1 - Create existing employee reference maps
    logger.info("Create existing employee reference maps")

    incoming_ssns = map(
        lambda employee_info: employee_info["employee_ssn"], employee_and_wage_info_list
    )
    existing_employee_models = dor_persistence_util.get_employees_by_ssn(db_session, incoming_ssns)

    ssn_to_existing_employee_model = {}
    for employee in existing_employee_models:
        ssn_to_existing_employee_model[employee.tax_identifier.tax_identifier] = employee

    logger.info(
        "Done - Create existing employee reference maps. Existing employees matched: %i",
        len(existing_employee_models),
    )

    # 2 - Stage employee and wage info for creation
    logger.info("Staging employee and wage info for creation")

    not_found_employee_and_wage_info_list = list(
        filter(
            lambda employee: employee["employee_ssn"] not in ssn_to_existing_employee_model,
            employee_and_wage_info_list,
        )
    )

    ssn_to_new_tax_id = {}
    ssn_to_new_employee_id = {}

    for emp in not_found_employee_and_wage_info_list:
        ssn_to_new_employee_id[emp["employee_ssn"]] = uuid.uuid4()
        ssn_to_new_tax_id[emp["employee_ssn"]] = uuid.uuid4()

    logger.info(
        "Done - Staging employee and wage info for creation. Employees staged for creation: %i",
        len(not_found_employee_and_wage_info_list),
    )

    # 3 - Create tax ids for new employees
    tax_id_models_to_create = []
    for ssn in ssn_to_new_employee_id:
        tax_id_models_to_create.append(
            dor_persistence_util.tax_id_from_dict(ssn_to_new_tax_id[ssn], ssn)
        )

    logger.info("Creating new tax ids: %i", len(tax_id_models_to_create))

    bulk_save(db_session, tax_id_models_to_create, "Tax Ids")

    logger.info("Done - Creating new tax ids: %i", len(tax_id_models_to_create))

    # 4 - Create new employees
    employee_ssns_staged_for_creation = set()
    employee_models_to_create = []
    for employee_info in not_found_employee_and_wage_info_list:
        ssn = employee_info["employee_ssn"]

        # since there are multiple rows with the same employee information ignore all but the first one
        if ssn in employee_ssns_staged_for_creation:
            continue

        employee_models_to_create.append(
            dor_persistence_util.dict_to_employee(
                employee_info,
                import_log_entry_id,
                ssn_to_new_employee_id[ssn],
                ssn_to_new_tax_id[ssn],
            )
        )
        employee_ssns_staged_for_creation.add(ssn)

    logger.info("Creating new employees: %i", len(employee_models_to_create))

    bulk_save(db_session, employee_models_to_create, "Employees", commit=True)

    logger.info("Done - Creating new employees: %i", len(employee_models_to_create))

    report.created_employees_count = len(employee_models_to_create)

    logger.info("Creating new wage information: %i", len(not_found_employee_and_wage_info_list))

    def wage_create(employee_wage_info_list):
        wages_contributions_models_to_create = []
        for employee_info in employee_wage_info_list:
            wages_contributions_models_to_create.append(
                dor_persistence_util.dict_to_wages_and_contributions(
                    employee_info,
                    ssn_to_new_employee_id[employee_info["employee_ssn"]],
                    account_key_to_employer_id_map[employee_info["account_key"]],
                    import_log_entry_id,
                )
            )

        bulk_save(db_session, wages_contributions_models_to_create, "Employee Wages", commit=True)

    batch_apply(not_found_employee_and_wage_info_list, "wage_create", wage_create)

    logger.info(
        "Done - Creating new wage information: %i", len(not_found_employee_and_wage_info_list)
    )

    report.created_wages_and_contributions_count = len(not_found_employee_and_wage_info_list)

    # 6 - Update all existing employees
    found_employee_and_wage_info_list = list(
        filter(
            lambda employee: employee["employee_ssn"] in ssn_to_existing_employee_model,
            employee_and_wage_info_list,
        )
    )

    logger.info(
        "Updating existing employees from total records: %i", len(found_employee_and_wage_info_list)
    )

    ssn_to_employee_id = ssn_to_new_employee_id  # collect all ssn to employee ids for next step
    ssn_updated_in_current_run = set()
    for employee_info in found_employee_and_wage_info_list:
        ssn = employee_info["employee_ssn"]

        # since there are multiple rows with the same employee information ignore all but the first one
        if ssn in ssn_updated_in_current_run:
            continue

        existing_employee_model = ssn_to_existing_employee_model[ssn]
        dor_persistence_util.update_employee(
            db_session, existing_employee_model, employee_info, import_log_entry_id
        )

        ssn_updated_in_current_run.add(ssn)
        ssn_to_employee_id[ssn] = existing_employee_model.employee_id

    logger.info("Done - Updating existing employees: %i", len(ssn_updated_in_current_run))

    report.updated_employees_count = len(ssn_updated_in_current_run)

    # 7 - Create or update wage information for existing employees
    logger.info(
        "Creating or updating wage information for existing employees. Total records: %i",
        len(found_employee_and_wage_info_list),
    )

    count = 0
    created_count = 0

    for employee_info in found_employee_and_wage_info_list:

        count += 1
        if count % 1000 == 0:
            logger.info("Updating existing employee wage info, current %i", count)

        account_key = employee_info["account_key"]
        filing_period = employee_info["filing_period"]
        ssn = employee_info["employee_ssn"]

        employee_id = ssn_to_employee_id[ssn]
        employer_id = account_key_to_employer_id_map[account_key]

        existing_wage = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
            db_session, employee_id, employer_id, filing_period
        )

        if existing_wage is None:
            dor_persistence_util.create_wages_and_contributions(
                db_session, employee_info, employee_id, employer_id, import_log_entry_id
            )

            created_count += 1
        else:
            dor_persistence_util.update_wages_and_contributions(
                db_session, existing_wage, employee_info, import_log_entry_id
            )
            report.updated_wages_and_contributions_count += 1

        report.created_wages_and_contributions_count += created_count

    logger.info(
        "Done - Creating or updating wage information for existing employees. Total: %i, Creates: %i, Updates: %i",
        len(found_employee_and_wage_info_list),
        created_count,
        report.updated_wages_and_contributions_count,
    )

    # 8 - Done
    logger.info(
        "Finished importing employee and wage information",
        extra={
            "created_employees_count": report.created_employees_count,
            "updated_employees_count": report.updated_employees_count,
            "created_wages_and_contributions_count": report.created_wages_and_contributions_count,
            "updated_wages_and_contributions_count": report.updated_wages_and_contributions_count,
        },
    )

    return ssn_to_new_employee_id


# TODO turn return dataclasses list instead of object list
def parse_employer_file(employer_file_path, decrypter):
    """Parse employer file"""
    logger.info("Start parsing employer file", extra={"employer_file_path": employer_file_path})
    employers = []

    file_stream = file_util.open_stream(employer_file_path, "rb")
    decrypted_str = decrypter.decrypt_stream(file_stream)

    decrypted_lines = decrypted_str.split("\n")

    for row in decrypted_lines:
        if not row:  # skip empty end of file lines
            continue

        employer = EMPLOYER_FILE_FORMAT.parse_line(row)
        employers.append(employer)

    logger.info("Finished parsing employer file", extra={"employer_file_path": employer_file_path})
    return employers


def parse_employee_file(employee_file_path, decrypter):
    """Parse employee file"""
    logger.info("Start parsing employee file", extra={"employee_file_path": employee_file_path})

    employees_info = []

    file_stream = file_util.open_stream(employee_file_path, "rb")
    decrypted_str = decrypter.decrypt_stream(file_stream)
    decrypted_lines = decrypted_str.split("\n")

    for row in decrypted_lines:
        if not row:  # skip empty end of file lines
            continue

        if row.startswith("B"):
            employee_info = EMPLOYEE_FORMAT.parse_line(row)
            employees_info.append(employee_info)

    logger.info("Finished parsing employee file", extra={"employee_file_path": employee_file_path})
    return employees_info


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


def get_files_to_process(path: pathlib.PurePath) -> List[ImportBatch]:
    files_by_date = get_files_for_import_grouped_by_date(path)
    file_date_keys = sorted(files_by_date.keys())

    import_batches: List[ImportBatch] = []

    for file_date_key in file_date_keys:
        files = files_by_date[file_date_key]

        if EMPLOYER_FILE_PREFIX not in files or EMPLOYEE_FILE_PREFIX not in files:
            logger.warning("incomplete files for %s: %s", file_date_key, files)
            continue

        import_batches.append(
            ImportBatch(
                upload_date=file_date_key,
                employer_file=files[EMPLOYER_FILE_PREFIX],
                employee_file=files[EMPLOYEE_FILE_PREFIX],
            )
        )

    return import_batches


def get_files_for_import_grouped_by_date(
    path: pathlib.PurePath,
) -> Dict[str, Dict[str, pathlib.PurePath]]:
    """Get the paths (s3 keys) of files in the received folder of the bucket"""

    files_by_date: Dict[str, Dict[str, pathlib.PurePath]] = {}
    files_for_import = file_util.list_files(str(path))
    files_for_import.sort()
    for file_key in files_for_import:
        match = re.match(r"(DORDFML.*_)(\d+)", file_key)
        if not match:
            logger.warning("file %s does not match expected format - skipping", file_key)
            continue

        prefix = match[1]
        file_date = match[2]

        if prefix not in (EMPLOYER_FILE_PREFIX, EMPLOYEE_FILE_PREFIX):
            logger.warning("file %s does not have a known prefix - skipping", file_key)
            continue

        if file_date not in files_by_date:
            files_by_date[file_date] = {}
        files_by_date[file_date][prefix] = path / file_key

    return files_by_date


def get_file_name(s3_file_key):
    """Get file name without extension from an object key"""
    file_name_index = s3_file_key.rfind("/") + 1
    file_name_extention_index = s3_file_key.rfind(".txt")
    file_name = s3_file_key[file_name_index:file_name_extention_index]
    return file_name


if __name__ == "__main__":
    handler()
