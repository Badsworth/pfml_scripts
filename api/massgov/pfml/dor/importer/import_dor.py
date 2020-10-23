#!/usr/bin/python3
#
# Lambda function to import DOR data from S3 to PostgreSQL (RDS).
#

import os
import re
import resource
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.logging.audit
from massgov.pfml import db
from massgov.pfml.db.models.employees import GeoState, ImportLog
from massgov.pfml.dor.importer.dor_file_formats import (
    EMPLOYEE_FILE_ROW_LENGTH,
    EMPLOYEE_FORMAT,
    EMPLOYER_FILE_FORMAT,
    EMPLOYER_FILE_ROW_LENGTH,
)
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

EMPLOYER_LINE_LIMIT = 250000
EMPLOYEE_LINE_LIMIT = 200000


class ImportException(Exception):
    __slots__ = ["message", "error_type"]

    def __init__(self, message: str, error_type: str):
        self.message = message
        self.error_type = error_type


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
    parsed_employees_info_count: int = 0
    created_employers_count: int = 0
    updated_employers_count: int = 0
    unmodified_employers_count: int = 0
    created_employees_count: int = 0
    updated_employees_count: int = 0
    created_wages_and_contributions_count: int = 0
    updated_wages_and_contributions_count: int = 0
    sample_employers_line_lengths: Dict[Any, Any] = field(default_factory=dict)
    invalid_employer_lines_count: int = 0
    parsed_employers_exception_line_nums: List[Any] = field(default_factory=list)
    invalid_address_state_and_account_keys: Dict[Any, Any] = field(default_factory=dict)
    invalid_employee_lines_count: int = 0
    skipped_wages_count: int = 0
    parsed_employees_exception_count: int = 0
    message: str = ""
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

    report = ImportRunReport(start=datetime.now().isoformat())

    try:
        folder_path = os.environ["FOLDER_PATH"]
        decrypt_files = os.getenv("DECRYPT") == "true"

        logger.info(
            "Starting import run",
            extra={"folder_path": folder_path, "decrypt_files": decrypt_files},
        )

        import_batches = get_files_to_process(folder_path)

        if not import_batches:
            logger.info("no files found to import")
            report.message = "no files found to import"
        else:
            import_reports = process_import_batches(import_batches, decrypt_files)
            report.imports = import_reports
            report.message = "files imported"

        report.end = datetime.now().isoformat()
        logger.info("Finished import run", extra={"report": asdict(report)})
    except ImportException as ie:
        report.end = datetime.now().isoformat()
        message = str(ie)
        report.message = message
        logger.error(message, extra={"report": asdict(report)})
    except Exception as e:
        report.end = datetime.now().isoformat()
        message = f"Unexpected error during import run: {type(e)}"
        report.message = message
        logger.error(message, extra={"report": asdict(report)})


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
    try:
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
    except ImportException as ie:
        raise ie
    except Exception as e:
        raise ImportException("Unexpected error importing batches", type(e).__name__)

    return import_reports


class EmployeeWriter(object):
    def __init__(
        self,
        line_buffer_length,
        db_session,
        account_key_to_employer_id_map,
        report,
        report_log_entry,
    ):
        self.line_count = 0
        self.line_buffer_length = line_buffer_length
        self.remainder = ""
        self.remainder_encoded = b""
        self.lines = []
        self.parsed_employees_info_count = 0
        self.db_session = db_session
        self.account_key_to_employer_id_map = account_key_to_employer_id_map
        self.report = report
        self.report_log_entry = report_log_entry
        self.employee_ssns_created_in_current_import_run = {}

    def clear_buffer(self):
        employees_info = []

        for row in self.lines:
            if row.startswith("B"):
                employee_info = EMPLOYEE_FORMAT.parse_line(row)
                employees_info.append(employee_info)
                self.parsed_employees_info_count = self.parsed_employees_info_count + 1

        if len(employees_info) > 0:
            import_employees_and_wage_data(
                self.db_session,
                self.account_key_to_employer_id_map,
                employees_info,
                self.employee_ssns_created_in_current_import_run,
                self.report,
                self.report_log_entry.import_log_id,
            )

        self.lines = []

    def __call__(self, data):
        if data:
            try:
                to_decode = self.remainder_encoded + data
                lines = str(to_decode.decode("utf-8")).split("\n")
                self.remainder_encoded = b""

                i = 0
                while i < len(lines):
                    if i != (len(lines) - 1):
                        self.lines.append(self.remainder + lines[i])
                        self.line_count = self.line_count + 1
                        self.remainder = ""
                    if i == (len(lines) - 1):
                        self.remainder = lines[i]

                    i += 1

            except UnicodeDecodeError:
                self.remainder_encoded = data

            if len(self.lines) > self.line_buffer_length:
                self.clear_buffer()

        else:
            logger.info("Done parsing", extra={"lines_parsed": self.line_count})
            self.clear_buffer()

        return False


class Capturer(object):
    def __init__(self, line_offset, line_limit):
        self.line_offset = line_offset
        self.line_limit = line_limit
        self.line_count = 0

        self.remainder = ""
        self.remainder_encoded = b""
        self.lines = []

        logger.info("Capturer initialized")

    def append_line(self, line):
        if self.line_count < self.line_offset:
            self.line_count = self.line_count + 1
            return

        if len(self.lines) > self.line_limit:
            return

        self.lines.append(line)
        self.line_count = self.line_count + 1

    def __call__(self, data):
        if data:
            try:
                to_decode = self.remainder_encoded + data
                lines = str(to_decode.decode("utf-8")).split("\n")
                self.remainder_encoded = b""

                i = 0
                while i < len(lines):
                    if i != (len(lines) - 1):
                        self.append_line(self.remainder + lines[i])
                        self.remainder = ""
                    if i == (len(lines) - 1):
                        self.remainder = lines[i]

                    i += 1
            # We may have hit a UTF-8 boundary at the wrong byte. If so, save line for next data call
            except UnicodeDecodeError:
                self.remainder_encoded = data

        else:
            logger.info("Done parsing", extra={"lines_parsed": self.line_count})

        return False


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


# TODO take this out once psql is on TERSE logging setting https://lwd.atlassian.net/browse/API-697
def get_discreet_db_exception_message(db_exception: SQLAlchemyError) -> str:
    exception_type = type(db_exception).__name__
    # see https://github.com/zzzeek/sqlalchemy/blob/master/lib/sqlalchemy/exc.py
    message = db_exception._message()  # type: ignore[attr-defined]
    discreet_message = message
    detail_index = message.find("DETAIL")
    if detail_index != -1:
        discreet_message = message[0:detail_index]

    return f"DB Exception: {discreet_message}, exception type: {exception_type}"


def handle_import_exception(
    exception: Exception, db_session: Session, report_log_entry: ImportLog, report: ImportReport
) -> None:
    """Gracefully close out import run"""
    try:
        if isinstance(exception, SQLAlchemyError):
            db_session.rollback()
            message = get_discreet_db_exception_message(exception)
            logger.error(message)
        else:
            message = f"Unexpected error while processing import: {str(exception)}"
            logger.exception("exception occurred during import")

        report.status = "error"
        report.message = message
        report.end = datetime.now().isoformat()
        dor_persistence_util.update_import_log_entry(db_session, report_log_entry, report)
        import_exception = ImportException(message, type(exception).__name__)
    except Exception as e:
        message = f"Unexpected error while closing out import run due to original exception: {type(exception)}"
        import_exception = ImportException(message, type(e).__name__)
    finally:
        raise import_exception


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

    try:
        report.sample_employers_line_lengths = {}
        report.parsed_employers_exception_line_nums = []
        report.invalid_address_state_and_account_keys = {}

        report_log_entry = dor_persistence_util.create_import_log_entry(db_session, report)

        db_session.refresh(report_log_entry)

        employers = parse_employer_file(employer_file_path, decrypter, report)

        parsed_employers_count = len(employers)
        parsed_employees_info_count = 0

        account_key_to_employer_id_map = import_employers(
            db_session, employers, report, report_log_entry.import_log_id
        )

        decrypt_files = os.getenv("DECRYPT") == "true"

        if decrypt_files:
            writer = EmployeeWriter(
                line_buffer_length=EMPLOYEE_LINE_LIMIT,
                db_session=db_session,
                account_key_to_employer_id_map=account_key_to_employer_id_map,
                report=report,
                report_log_entry=report_log_entry,
            )
            decrypter.set_on_data(writer)
            get_decrypted_file_stream(employee_file_path, decrypter)
            parsed_employees_info_count = writer.parsed_employees_info_count

        else:
            # TODO: parameterize
            batch_size = EMPLOYEE_LINE_LIMIT
            processed_count = 0

            employee_count = get_employee_file_lines(employee_file_path, decrypter)

            logger.info("Employee file count", extra={"count": employee_count})

            while processed_count < employee_count:
                logger.info("Processed count", extra={"count": processed_count})
                employees_info = parse_employee_file(
                    employee_file_path, decrypter, report, processed_count, batch_size
                )

                parsed_employees_info_count += len(employees_info)
                logger.info("Employees to process this batch", extra={"count": len(employees_info)})
                if len(employees_info) > 0:
                    import_employees_and_wage_data(
                        db_session,
                        account_key_to_employer_id_map,
                        employees_info,
                        {},
                        report,
                        report_log_entry.import_log_id,
                    )

                processed_count = processed_count + batch_size

        # finalize report
        report.parsed_employers_count = parsed_employers_count
        report.parsed_employees_info_count = parsed_employees_info_count
        report.status = "success"
        report.end = datetime.now().isoformat()
        dor_persistence_util.update_import_log_entry(db_session, report_log_entry, report)

        logger.info("Invalid states: %s", repr(report.invalid_address_state_and_account_keys))
        logger.info("Sample Employer line lengths: %s", repr(report.sample_employers_line_lengths))

        # move file to processed folder
        # move_file_to_processed(bucket, file_for_import) # TODO turn this on with invoke flag

    except Exception as e:
        handle_import_exception(e, db_session, report_log_entry, report)

    return report


def import_to_db(db_session, employers, employees_info, report, import_log_entry_id):
    """Process through parsed objects and persist into database"""
    logger.info("Starting import")

    account_key_to_employer_id_map = import_employers(
        db_session, employers, report, import_log_entry_id
    )
    import_employees_and_wage_data(
        db_session, account_key_to_employer_id_map, employees_info, {}, report, import_log_entry_id,
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

    # 1 - Stage employers for creation and update

    # Get all employers in DB
    existing_employer_reference_models = dor_persistence_util.get_all_employers_fein(db_session)
    fein_to_existing_employer_reference_models = {
        employer.employer_fein: employer for employer in existing_employer_reference_models
    }

    logger.info("Found employers in db: %i", len(existing_employer_reference_models))

    not_found_employer_info_list = []
    found_employer_info_list = []

    unique_employer_state_codes = set()
    staged_not_found_employer_ssns = set()
    for employer_info in employers:
        unique_employer_state_codes.add(employer_info["employer_address_state"])
        fein = employer_info["fein"]
        if fein in staged_not_found_employer_ssns:
            # this means there is more than one line for the same employer
            # add it to the found list for later possible update processing
            logger.warning(
                "found multiple lines for same employer: %s", employer_info["account_key"]
            )
            found_employer_info_list.append(employer_info)
            continue

        if fein not in fein_to_existing_employer_reference_models:
            not_found_employer_info_list.append(employer_info)
            staged_not_found_employer_ssns.add(fein)
        else:
            found_employer_info_list.append(employer_info)

    logger.info("employer states to insert: %s", repr(unique_employer_state_codes))

    # 2 - Create employers
    fein_to_new_employer_id = {}
    fein_to_new_address_id = {}
    for emp in not_found_employer_info_list:
        fein_to_new_employer_id[emp["fein"]] = uuid.uuid4()
        fein_to_new_address_id[emp["fein"]] = uuid.uuid4()

    employers_with_valid_addresses = []
    for employer in not_found_employer_info_list:
        try:
            GeoState.get_id(employer["employer_address_state"])
            employers_with_valid_addresses.append(employer)
        except Exception:
            logger.warning(
                "Invalid employer state: {}, {}, {}".format(
                    employer_info["employer_address_city"],
                    employer_info["employer_address_state"],
                    employer_info["employer_address_zip"],
                )
            )
            report.invalid_address_state_and_account_keys[employer_info["account_key"]] = employer[
                "employer_address_state"
            ]

    logger.warning(
        "Invalid employer states: %s", repr(report.invalid_address_state_and_account_keys)
    )

    employer_models_to_create = list(
        map(
            lambda employer_info: dor_persistence_util.dict_to_employer(
                employer_info, import_log_entry_id, fein_to_new_employer_id[employer_info["fein"]]
            ),
            employers_with_valid_addresses,
        )
    )

    logger.warning("Creating new employers: %i", len(employer_models_to_create))

    bulk_save(db_session, employer_models_to_create, "Employers")

    logger.info("Done - Creating new employers: %i", len(employer_models_to_create))

    report.created_employers_count += len(employer_models_to_create)

    # 3 - Create employer addresses
    addresses_models_to_create = list(
        map(
            lambda employer_info: dor_persistence_util.dict_to_address(
                employer_info, fein_to_new_address_id[employer_info["fein"]]
            ),
            employers_with_valid_addresses,
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
    found_employer_info_to_update_list = []
    found_employer_info_to_not_update_list = []

    for employer_info in found_employer_info_list:
        fein = employer_info["fein"]

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

        if (
            employer_info["updated_date"]
            > fein_to_existing_employer_reference_models[fein].dor_updated_date
        ):
            found_employer_info_to_update_list.append(employer_info)
        else:
            found_employer_info_to_not_update_list.append(employer_info)

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

    report.updated_employers_count += len(found_employer_info_to_update_list)
    logger.info("Done - Updating employers: %i", len(found_employer_info_to_update_list))

    # 7 - Track and report not updated employers
    for employer_info in found_employer_info_to_not_update_list:
        existing_employer_reference_model = fein_to_existing_employer_reference_models[
            employer_info["fein"]
        ]
        account_key = employer_info["account_key"]
        account_key_to_employer_id_map[account_key] = existing_employer_reference_model.employer_id

    report.unmodified_employers_count += len(found_employer_info_to_not_update_list)
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


def import_employees(
    db_session,
    employee_info_list,
    account_key_to_employer_id_map,
    employee_ssns_to_id_created_in_current_import_run,
    report,
    import_log_entry_id,
):
    """Create or update employees data in the db"""
    logger.info(
        "Start import of wage information - rows: %i", len(employee_info_list),
    )

    # 1 - Create existing employee reference maps
    logger.info("Create existing employee reference maps")

    incoming_ssns = map(lambda employee_info: employee_info["employee_ssn"], employee_info_list)

    ssns_to_check_in_db = list(
        filter(
            lambda ssn: ssn not in employee_ssns_to_id_created_in_current_import_run, incoming_ssns
        )
    )

    existing_employee_models = dor_persistence_util.get_employees_by_ssn(
        db_session, ssns_to_check_in_db
    )

    ssn_to_existing_employee_model = {}
    for employee in existing_employee_models:
        ssn_to_existing_employee_model[employee.tax_identifier.tax_identifier] = employee

    logger.info(
        "Done - Create existing employee reference maps. Existing employees matched: %i",
        len(existing_employee_models),
    )

    # 2 - Stage employee info for creation
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

    for emp in not_found_employee_info_list:
        ssn_to_new_employee_id[emp["employee_ssn"]] = uuid.uuid4()
        ssn_to_new_tax_id[emp["employee_ssn"]] = uuid.uuid4()

    logger.info(
        "Done - Staging employee and wage info for creation. Employees staged for creation: %i",
        len(not_found_employee_info_list),
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
    employee_models_to_create = []
    employee_ssns_staged_for_creation_in_current_loop = set()
    for employee_info in not_found_employee_info_list:
        ssn = employee_info["employee_ssn"]

        # since there are multiple rows with the same employee information ignore all but the first one
        if ssn in employee_ssns_staged_for_creation_in_current_loop:
            continue

        new_employee_id = ssn_to_new_employee_id[ssn]
        employee_models_to_create.append(
            dor_persistence_util.dict_to_employee(
                employee_info, import_log_entry_id, new_employee_id, ssn_to_new_tax_id[ssn],
            )
        )

        employee_ssns_staged_for_creation_in_current_loop.add(ssn)
        employee_ssns_to_id_created_in_current_import_run[ssn] = new_employee_id

    logger.info("Creating new employees: %i", len(employee_models_to_create))

    bulk_save(db_session, employee_models_to_create, "Employees", commit=True)

    report.created_employees_count += len(employee_models_to_create)

    logger.info("Done - Creating new employees: %i", len(employee_models_to_create))

    # 6 - Update all existing employees
    found_employee_and_wage_info_list = list(
        filter(
            lambda employee: employee["employee_ssn"] in ssn_to_existing_employee_model,
            employee_info_list,
        )
    )
    logger.info(
        "Updating existing employees from total records: %i", len(found_employee_and_wage_info_list)
    )

    employee_ssns_updated_in_current_loop = set()
    for employee_info in found_employee_and_wage_info_list:
        ssn = employee_info["employee_ssn"]

        # since there are multiple rows with the same employee information ignore all but the first one
        if ssn in employee_ssns_updated_in_current_loop:
            continue

        existing_employee_model = ssn_to_existing_employee_model[ssn]
        dor_persistence_util.update_employee(
            db_session, existing_employee_model, employee_info, import_log_entry_id
        )

        employee_ssns_updated_in_current_loop.add(ssn)

        report.updated_employees_count += 1

    logger.info(
        "Done - Updating existing employees: %i", len(employee_ssns_updated_in_current_loop)
    )


def import_wage_data(
    db_session,
    wage_info_list,
    account_key_to_employer_id_map,
    employee_ssns_to_id_created_in_current_import_run,
    report,
    import_log_entry_id,
):
    # Create wage data
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

        wages_contributions_models_to_create.append(
            dor_persistence_util.dict_to_wages_and_contributions(
                employee_info,
                employee_ssns_to_id_created_in_current_import_run[employee_info["employee_ssn"]],
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

    # Update wage data
    wage_info_list_to_create_or_update = list(
        filter(
            lambda wage_info: wage_info["employee_ssn"]
            not in employee_ssns_to_id_created_in_current_import_run,
            wage_info_list,
        )
    )

    count = 0

    wages_contributions_models_existing_employees_to_create = []

    for wage_info in wage_info_list_to_create_or_update:

        count += 1
        if count % 1000 == 0:
            logger.info("Creating or updating existing wage info, current %i", count)

        account_key = wage_info["account_key"]
        filing_period = wage_info["filing_period"]
        ssn = wage_info["employee_ssn"]

        employer_id = account_key_to_employer_id_map[account_key]
        existing_employee = dor_persistence_util.get_employees_by_ssn(db_session, [ssn])[0]

        existing_wage = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
            db_session, existing_employee.employee_id, employer_id, filing_period
        )

        if existing_wage is None:

            wage_model = dor_persistence_util.dict_to_wages_and_contributions(
                wage_info, existing_employee.employee_id, employer_id, import_log_entry_id
            )
            wages_contributions_models_existing_employees_to_create.append(wage_model)

        else:
            dor_persistence_util.update_wages_and_contributions(
                db_session, existing_wage, wage_info, import_log_entry_id
            )
            report.updated_wages_and_contributions_count += 1

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


def import_employees_and_wage_data(
    db_session,
    account_key_to_employer_id_map,
    employee_and_wage_info_list,
    employee_ssns_created_in_current_import_run,
    report,
    import_log_entry_id,
):
    import_employees(
        db_session,
        employee_and_wage_info_list,
        account_key_to_employer_id_map,
        employee_ssns_created_in_current_import_run,
        report,
        import_log_entry_id,
    )

    import_wage_data(
        db_session,
        employee_and_wage_info_list,
        account_key_to_employer_id_map,
        employee_ssns_created_in_current_import_run,
        report,
        import_log_entry_id,
    )


def get_decrypted_file_stream(file_path, decrypter):
    file_stream = file_util.open_stream(file_path, "rb")
    logger.info("Finished getting file stream")

    decrypt_files = os.getenv("DECRYPT") == "true"
    if decrypt_files:
        decrypter.decrypt_stream(file_stream)

        logger.info("Finished decrypted file", extra={"file path": file_path})
    else:
        return file_stream


# TODO turn return dataclasses list instead of object list
def parse_employer_file(employer_file_path, decrypter, report):
    """Parse employer file"""
    logger.info("Start parsing employer file", extra={"employer_file_path": employer_file_path})
    employers = []

    decrypt_files = os.getenv("DECRYPT") == "true"

    invalid_employer_key_line_nums = []
    line_count = 0

    if decrypt_files:
        employer_capturer = Capturer(line_offset=0, line_limit=EMPLOYER_LINE_LIMIT)
        decrypter.set_on_data(employer_capturer)
        get_decrypted_file_stream(employer_file_path, decrypter)

        for row in employer_capturer.lines:
            if not row:  # skip empty end of file lines
                continue

            line_count = line_count + 1

            try:
                employer = EMPLOYER_FILE_FORMAT.parse_line(row)

                line_length = len(row.strip("\n\r"))
                line_length_value = report.sample_employers_line_lengths.get(line_length, [])
                if len(line_length_value) < 3:
                    line_length_value.append(employer["account_key"])
                    report.sample_employers_line_lengths[line_length] = line_length_value

                if line_length != EMPLOYER_FILE_ROW_LENGTH:
                    logger.warning(
                        "Incorrect employer line length - Line {0}, account key: {1}, line length: {2}".format(
                            line_count, employer["account_key"], line_length
                        )
                    )
                    report.invalid_employer_lines_count += 1

                employers.append(employer)
            except Exception as e:
                logger.exception(e)
                report.parsed_employers_exception_line_nums.append(line_count)
    else:
        for row in get_decrypted_file_stream(employer_file_path, decrypter):
            if not row:  # skip empty end of file lines
                continue

            line_count = line_count + 1

            if len(str(row.decode("utf-8")).strip("\n")) != EMPLOYER_FILE_ROW_LENGTH:
                employer = EMPLOYER_FILE_FORMAT.parse_line(row)
                invalid_employer_key_line_nums.append(
                    "Line {0}, account key: {1}".format(line_count, employer["account_key"])
                )
                continue

            employer = EMPLOYER_FILE_FORMAT.parse_line(str(row.decode("utf-8")))
            employers.append(employer)

    logger.info(
        "Finished parsing employer file",
        extra={
            "employer_file_path": employer_file_path,
            "invalid_parsed_employers": repr(invalid_employer_key_line_nums),
        },
    )
    return employers


def get_employee_file_lines(employee_file_path, decrypter):
    line_count = 0

    with get_decrypted_file_stream(employee_file_path, decrypter) as file_stream:
        has_next = True
        while has_next:
            line = file_stream.readline()
            if not line:
                has_next = False

            line_count = line_count + 1

        return line_count


def parse_employee_file(employee_file_path, decrypter, report, offset=0, limit=EMPLOYEE_LINE_LIMIT):
    """Parse employee file"""
    logger.info("Start parsing employee file", extra={"employee_file_path": employee_file_path})

    employees_info = []
    line_count = 0

    decrypt_files = os.getenv("DECRYPT") == "true"
    if decrypt_files:
        employee_capturer = Capturer(line_offset=offset, line_limit=limit)
        decrypter.set_on_data(employee_capturer)

        get_decrypted_file_stream(employee_file_path, decrypter)

        for row in employee_capturer.lines:
            if not row:  # skip empty end of file lines
                continue

            line_count = line_count + 1

            if row.startswith("B"):
                line_length = len(row.strip("\n\r"))
                if line_length != EMPLOYEE_FILE_ROW_LENGTH:
                    logger.warning(
                        "Incorrect employee line length - Line {0}, line length: {1}".format(
                            line_count, line_length
                        )
                    )
                    report.invalid_employee_lines_count += 1

                try:
                    employee_info = EMPLOYEE_FORMAT.parse_line(row)
                    employees_info.append(employee_info)

                except Exception:
                    logger.warning("Parse error with employee on line %i", line_count)
                    report.parsed_employees_exception_count += 1

    else:
        for row in get_decrypted_file_stream(employee_file_path, decrypter):
            if not row:  # skip empty end of file lines
                continue

            # TODO: tests pass in binary strings vs. smart open sending in str lines
            if not isinstance(row, str):
                row = str(row.decode("utf-8"))

            if row.startswith("B"):
                employee_info = EMPLOYEE_FORMAT.parse_line(row)
                employees_info.append(employee_info)

        logger.info(
            "Finished parsing employee file", extra={"employee_file_path": employee_file_path},
        )

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


def get_files_to_process(path: str) -> List[ImportBatch]:
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


def get_files_for_import_grouped_by_date(path: str,) -> Dict[str, Dict[str, str]]:
    """Get the paths (s3 keys) of files in the received folder of the bucket"""

    files_by_date: Dict[str, Dict[str, str]] = {}
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
        files_by_date[file_date][prefix] = f"{path}/{file_key}"

    return files_by_date


def get_file_name(s3_file_key):
    """Get file name without extension from an object key"""
    file_name_index = s3_file_key.rfind("/") + 1
    file_name_extention_index = s3_file_key.rfind(".txt")
    file_name = s3_file_key[file_name_index:file_name_extention_index]
    return file_name


if __name__ == "__main__":
    handler()
