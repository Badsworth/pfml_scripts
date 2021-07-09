#!/usr/bin/python3
#
# ECS task to import DOR data from S3 to PostgreSQL (RDS).
#

import os
import resource
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import boto3
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.util.batch.log
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
import massgov.pfml.util.newrelic.events
from massgov.pfml import db
from massgov.pfml.db.models.employees import (
    EmployeeLog,
    EmployerQuarterlyContribution,
    ImportLog,
    WagesAndContributions,
)
from massgov.pfml.dor.importer.dor_file_formats import (
    EMPLOYEE_FILE_ROW_LENGTH,
    EMPLOYEE_FORMAT,
    EMPLOYER_FILE_FORMAT,
    EMPLOYER_FILE_ROW_LENGTH,
    EMPLOYER_QUARTER_INFO_FORMAT,
)
from massgov.pfml.dor.importer.paths import ImportBatch, get_files_to_process
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.config import get_secret_from_env
from massgov.pfml.util.encryption import Crypt, GpgCrypt, Utf8Crypt

logger = logging.get_logger("massgov.pfml.dor.importer.import_dor")

s3 = boto3.client("s3")
s3Bucket = boto3.resource("s3")
aws_ssm = boto3.client("ssm", region_name="us-east-1")


# TODO get these from environment variables
RECEIVED_FOLDER = "dor/received/"
PROCESSED_FOLDER = "dor/processed/"

EMPLOYEE_LINE_LIMIT = 25000


class ImportException(Exception):
    __slots__ = ["message", "error_type"]

    def __init__(self, message: str, error_type: str):
        self.message = message
        self.error_type = error_type


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
    unmodified_employees_count: int = 0
    logged_employees_for_new_employer: int = 0
    created_wages_and_contributions_count: int = 0
    updated_wages_and_contributions_count: int = 0
    unmodified_wages_and_contributions_count: int = 0
    created_employer_quarters_count: int = 0
    updated_employer_quarters_count: int = 0
    skipped_employer_quarterly_contribution: int = 0
    unmodified_employer_quarters_count: int = 0
    sample_employers_line_lengths: Dict[Any, Any] = field(default_factory=dict)
    invalid_employer_lines_count: int = 0
    parsed_employers_exception_line_nums: List[Any] = field(default_factory=list)
    invalid_employer_addresses_by_account_key: Dict[Any, Any] = field(default_factory=dict)
    invalid_employee_lines_count: int = 0
    skipped_wages_count: int = 0
    parsed_employer_quarter_exception_count: int = 0
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


@background_task("dor-import")
def handler(event=None, context=None):
    """ECS task main method."""
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
        sys.exit(1)
    except Exception as e:
        report.end = datetime.now().isoformat()
        message = f"Unexpected error during import run: {type(e)} -- {e}"
        report.message = message
        logger.error(message, extra={"report": asdict(report)})
        sys.exit(1)


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
            db_session_raw = db.init(sync_lookups=True)

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
        self, line_buffer_length, db_session, report, report_log_entry,
    ):
        self.line_count = 0
        self.line_buffer_length = line_buffer_length
        self.remainder = ""
        self.remainder_encoded = b""
        self.lines = []
        self.parsed_employees_info_count = 0
        self.parsed_employer_quarterly_info_count = 0
        self.parsed_employer_quarter_exception_count = 0
        self.db_session = db_session
        self.report = report
        self.report_log_entry = report_log_entry
        self.employee_ssns_created_in_current_import_run = {}
        logger.info("Created EmployeeWriter, buffer length: %i", line_buffer_length)

    def flush_buffer(self):
        logger.info("Flushing buffer, %i lines", len(self.lines))

        employees_info = []
        employers_quarterly_info = []

        count = 0
        for row in self.lines:
            count += 1
            if row.startswith("A"):
                try:
                    employer_quarterly_info = EMPLOYER_QUARTER_INFO_FORMAT.parse_line(row)
                    employers_quarterly_info.append(employer_quarterly_info)

                    self.parsed_employer_quarterly_info_count += 1
                except Exception:
                    logger.exception(
                        "Parse error with employer quarterly line. . Line: %i",
                        (self.line_count - len(self.lines)) + count,
                    )
                    self.report.parsed_employer_quarter_exception_count += 1

            if row.startswith("B"):
                try:
                    employee_info = EMPLOYEE_FORMAT.parse_line(row)

                    line_length = len(row.strip("\n\r"))
                    if line_length != EMPLOYEE_FILE_ROW_LENGTH:
                        logger.warning(
                            "Incorrect employee line length - account key {0}, line length: {1}".format(
                                employee_info["account_key"], line_length
                            )
                        )
                        self.report.invalid_employee_lines_count += 1

                    employees_info.append(employee_info)
                    self.parsed_employees_info_count = self.parsed_employees_info_count + 1
                except Exception:
                    logger.exception(
                        "Parse error with employee line. Line: %i",
                        (self.line_count - len(self.lines)) + count,
                    )
                    self.report.parsed_employees_exception_count += 1

        if len(employers_quarterly_info) > 0:
            import_employer_pfml_contributions(
                self.db_session,
                employers_quarterly_info,
                self.report,
                self.report_log_entry.import_log_id,
            )

        if len(employees_info) > 0:
            import_employees_and_wage_data(
                self.db_session,
                employees_info,
                self.employee_ssns_created_in_current_import_run,
                self.report,
                self.report_log_entry.import_log_id,
            )

        logger.info(
            "** Employer Quarterly Import Progress - created: %i, updated: %i, unmodified: %i, total: %i",
            self.report.created_employer_quarters_count,
            self.report.updated_employer_quarters_count,
            self.report.unmodified_employer_quarters_count,
            self.report.created_employer_quarters_count
            + self.report.updated_employer_quarters_count
            + self.report.unmodified_employer_quarters_count,
        )
        logger.info(
            "** Employee Import Progress - created: %i, updated: %i, unmodified: %i, total: %i, new employer log: %i",
            self.report.created_employees_count,
            self.report.updated_employees_count,
            self.report.unmodified_employees_count,
            self.report.unmodified_employees_count
            + self.report.created_employees_count
            + self.report.updated_employees_count,
            self.report.logged_employees_for_new_employer,
        )

        logger.info(
            "** Wage Import Progress: - created: %i, updated: %i, unmodified: %i, total: %i",
            self.report.created_wages_and_contributions_count,
            self.report.updated_wages_and_contributions_count,
            self.report.unmodified_wages_and_contributions_count,
            self.report.created_wages_and_contributions_count
            + self.report.updated_wages_and_contributions_count
            + self.report.unmodified_wages_and_contributions_count,
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
                self.flush_buffer()

        else:
            logger.info(
                "Done parsing employee and wage rows", extra={"lines_parsed": self.line_count}
            )
            self.flush_buffer()

        return False


class Capturer(object):
    def __init__(self, line_offset):
        self.line_offset = line_offset
        self.line_count = 0

        self.remainder = ""
        self.remainder_encoded = b""
        self.lines = []

        logger.info("Capturer initialized")

    def append_line(self, line):
        if self.line_count < self.line_offset:
            self.line_count = self.line_count + 1
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
            logger.info("Done parsing employer file", extra={"lines_parsed": self.line_count})

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
        massgov.pfml.util.batch.log.update_log_entry(db_session, report_log_entry, "error", report)
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

    report.sample_employers_line_lengths = {}
    report.parsed_employers_exception_line_nums = []
    report.invalid_employer_addresses_by_account_key = {}

    report_log_entry = massgov.pfml.util.batch.log.create_log_entry(
        db_session, "DOR", "Initial", report
    )

    db_session.refresh(report_log_entry)

    try:
        parsed_employers_count = 0

        # If an employer file is given, parse and import
        if employer_file_path:
            employers = parse_employer_file(employer_file_path, decrypter, report)

            parsed_employers_count = len(employers)

            import_employers(db_session, employers, report, report_log_entry.import_log_id)

        parsed_employees_info_count = 0
        if employee_file_path:
            writer = EmployeeWriter(
                line_buffer_length=EMPLOYEE_LINE_LIMIT,
                db_session=db_session,
                report=report,
                report_log_entry=report_log_entry,
            )
            decrypter.set_on_data(writer)
            file_stream = file_util.open_stream(employee_file_path, "rb")
            decrypter.decrypt_stream(file_stream)
            parsed_employees_info_count = writer.parsed_employees_info_count

        # finalize report
        report.parsed_employers_count = parsed_employers_count
        report.parsed_employees_info_count = parsed_employees_info_count
        report.status = "success"
        report.end = datetime.now().isoformat()
        massgov.pfml.util.batch.log.update_log_entry(
            db_session, report_log_entry, "success", report
        )

        logger.info(
            "Invalid employer addresses: %s", repr(report.invalid_employer_addresses_by_account_key)
        )
        logger.info("Sample Employer line lengths: %s", repr(report.sample_employers_line_lengths))

        # move file to processed folder unless explicitly told not to.
        if os.getenv("RETAIN_RECEIVED_FILES") is None and file_util.is_s3_path(employer_file_path):
            move_file_to_processed(employer_file_path, s3)

        if os.getenv("RETAIN_RECEIVED_FILES") is None and file_util.is_s3_path(employee_file_path):
            move_file_to_processed(employee_file_path, s3)

    except Exception as e:
        handle_import_exception(e, db_session, report_log_entry, report)

    return report


def batch_apply(items, batch_fn_name, batch_fn, batch_size=100000):
    size = len(items)
    start_index = 0

    while start_index < size:
        logger.info("batch: %s, count: %i", batch_fn_name, start_index)

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


def is_valid_employer_address(employee_info, report):
    try:
        dor_persistence_util.employer_dict_to_country_and_state_values(employee_info)
    except KeyError:
        invalid_address_msg = "city: {}, state: {}, zip: {}, country: {}".format(
            employee_info["employer_address_city"],
            employee_info["employer_address_state"],
            employee_info["employer_address_zip"],
            employee_info["employer_address_country"],
        )
        logger.warning(f"Invalid employer address - {invalid_address_msg}")
        report.invalid_employer_addresses_by_account_key[
            employee_info["account_key"]
        ] = invalid_address_msg
        return False

    return True


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
    unique_employer_country_codes = set()

    staged_not_found_employer_ssns = set()
    for employer_info in employers:
        unique_employer_state_codes.add(employer_info["employer_address_state"])
        unique_employer_country_codes.add(employer_info["employer_address_country"])

        if not is_valid_employer_address(employer_info, report):
            continue

        fein = employer_info["fein"]
        if fein in staged_not_found_employer_ssns:
            # this means there is more than one line for the same employer
            # add it to the found list for later possible update processing
            logger.warning(
                "Found multiple lines for same employer: %s", employer_info["account_key"]
            )
            found_employer_info_list.append(employer_info)
            continue

        if fein not in fein_to_existing_employer_reference_models:
            not_found_employer_info_list.append(employer_info)
            staged_not_found_employer_ssns.add(fein)
        else:
            found_employer_info_list.append(employer_info)

    logger.info("Employer states to insert: %s", repr(unique_employer_state_codes))
    logger.info("Employer countries to insert: %s", repr(unique_employer_country_codes))
    logger.warning(
        "Invalid employer addresses: %s", repr(report.invalid_employer_addresses_by_account_key)
    )

    # 2 - Create employers
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

    report.created_employers_count += len(employer_models_to_create)

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

    logger.info("Employers to update: %i", len(found_employer_info_to_update_list))

    count = 0
    for employer_info in found_employer_info_to_update_list:
        count += 1
        if count % 10000 == 0:
            logger.info("Updating employer info, current %i", count)

        existing_employer_model = dor_persistence_util.get_employer_by_fein(
            db_session, employer_info["fein"]
        )
        dor_persistence_util.update_employer(
            db_session, existing_employer_model, employer_info, import_log_entry_id
        )

    if len(found_employer_info_to_update_list) > 0:
        logger.info(
            "Batch committing employer updates: %i", len(found_employer_info_to_update_list)
        )
        db_session.commit()

    report.updated_employers_count += len(found_employer_info_to_update_list)
    logger.info("Done - Updating employers: %i", len(found_employer_info_to_update_list))

    # 7 - Track and report not updated employers
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


def import_employees(
    db_session,
    employee_info_list,
    employee_ssns_to_id_created_in_current_import_run,
    ssn_to_existing_employee_model,
    report,
    import_log_entry_id,
):
    """Create or update employees data in the db"""
    logger.info(
        "Start import of employees import - lines: %i", len(employee_info_list),
    )

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

        ssn_to_new_employee_id[emp["employee_ssn"]] = uuid.uuid4()

        # If a tax identifier does not already exists, create a UUID
        # Else use the found one.
        if not found:
            ssn_to_new_tax_id[emp["employee_ssn"]] = uuid.uuid4()
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
        found = False
        for tax_id in previously_created_tax_ids:
            if tax_id.tax_identifier == ssn:
                found = True

        if not found:
            tax_id_models_to_create.append(
                dor_persistence_util.tax_id_from_dict(ssn_to_new_tax_id[ssn], ssn)
            )

    logger.info("Creating new tax ids: %i", len(tax_id_models_to_create))

    bulk_save(db_session, tax_id_models_to_create, "Tax Ids")

    logger.info("Done - Creating new tax ids: %i", len(tax_id_models_to_create))

    # 3 - Create new employees
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

    # 4 - Update all existing employees
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
    found_employee_rows_count = len(found_employee_and_wage_info_list)
    count = 0
    updated_employees_count = 0
    unmodified_employees_count = 0

    for employee_info in found_employee_and_wage_info_list:
        ssn = employee_info["employee_ssn"]
        count += 1

        if count % 10000 == 0:
            logger.info(
                "Updating existing employees - count: %i/%i (%.1f%%), updated: %i, report id: %i",
                count,
                found_employee_rows_count,
                100.0 * count / found_employee_rows_count,
                updated_employees_count,
                import_log_entry_id,
            )

        # since there are multiple rows with the same employee information ignore all but the first one
        if ssn in employee_ssns_updated_in_current_loop:
            continue

        employee_ssns_updated_in_current_loop.add(ssn)

        existing_employee_model = ssn_to_existing_employee_model[ssn]

        is_updated = dor_persistence_util.check_and_update_employee(
            db_session, existing_employee_model, employee_info, import_log_entry_id
        )
        if is_updated:
            updated_employees_count += 1
            report.updated_employees_count += 1
        else:
            unmodified_employees_count += 1
            report.unmodified_employees_count += 1

    if updated_employees_count > 0:
        logger.info("Batch committing employee updates: %i", updated_employees_count)
        db_session.commit()

    logger.info(
        "Done - Updating existing employees: %i, unmodified: %i",
        updated_employees_count,
        unmodified_employees_count,
    )


def get_wage_composite_key(employer_id, employee_id, filing_period):
    return (employer_id, employee_id, filing_period)


def log_employees_with_new_employers(
    db_session,
    employee_wage_info_list,
    account_key_to_employer_id_map,
    ssn_to_existing_employee_model,
    report,
    import_log_entry_id,
):

    logger.info("Check and log employees with new employers")

    # Get existing wages for all existing employees in the current list
    ssn_to_existing_employee_id = {}
    for ssn in ssn_to_existing_employee_model:
        ssn_to_existing_employee_id[ssn] = ssn_to_existing_employee_model[ssn].employee_id

    existing_employee_ids = list(ssn_to_existing_employee_id.values())
    existing_wages = dor_persistence_util.get_wages_and_contributions_by_employee_ids(
        db_session, existing_employee_ids
    )

    # Group existing employer ids by employee id from existing wages
    employee_id_to_employer_id_set: Dict[uuid.UUID, Set[uuid.UUID]] = {}
    for existing_wage in existing_wages:
        employer_id = account_key_to_employer_id_map.get(existing_wage.account_key, None)
        if employer_id is None:
            continue

        employee_id = existing_wage.employee_id

        employer_id_set = employee_id_to_employer_id_set.get(employee_id, None)
        if employer_id_set:
            employer_id_set.add(employer_id)
        else:
            employee_id_to_employer_id_set[employee_id] = {employer_id}

    # Check current list for new employers
    # Filter current list to existing employees only.
    # New employees will have an insert log already, so no need to check here.
    # Note: duplicate entries for the same employer may be created across batches
    employee_wage_info_for_existing_employees = list(
        filter(
            lambda employee_wage_info: employee_wage_info["employee_ssn"]
            in ssn_to_existing_employee_id,
            employee_wage_info_list,
        )
    )

    employee_new_employer_logs_to_create = []
    modified_at = datetime.now()
    already_logged_employee_id_employer_id_tuples = set()

    for employee_wage_info in employee_wage_info_for_existing_employees:
        account_key = employee_wage_info["account_key"]
        employee_id = ssn_to_existing_employee_id[employee_wage_info["employee_ssn"]]
        employer_id = account_key_to_employer_id_map.get(account_key, None)

        if employer_id is None:
            logger.warning(
                "Attempted to check an employee wage row for unknown employer: %s",
                account_key,
                extra={"account_key": account_key},
            )
            continue

        if (employee_id, employer_id) in already_logged_employee_id_employer_id_tuples:
            continue

        employer_id_set = employee_id_to_employer_id_set.get(employee_id, None)
        if employer_id_set is None or employer_id not in employer_id_set:
            employee_log = EmployeeLog(
                employee_log_id=str(uuid.uuid4()),
                employee_id=employee_id,
                employer_id=employer_id,
                action="UPDATE_NEW_EMPLOYER",
                modified_at=modified_at,
                process_id=None,
            )
            employee_new_employer_logs_to_create.append(employee_log)
            already_logged_employee_id_employer_id_tuples.add((employee_id, employer_id))

    employee_logs_count = len(employee_new_employer_logs_to_create)
    if employee_logs_count > 0:
        logger.info("Logging employees as updated for new employer: %i", employee_logs_count)
        bulk_save(
            db_session,
            employee_new_employer_logs_to_create,
            "Employee Logs (New Employer Update)",
            commit=True,
        )

    report.logged_employees_for_new_employer += employee_logs_count
    logger.info("Done - Check and log employees with new employers: %i", employee_logs_count)


def import_wage_data(
    db_session,
    wage_info_list,
    account_key_to_employer_id_map,
    employee_ssns_to_id_created_in_current_import_run,
    ssn_to_existing_employee_model,
    report,
    import_log_entry_id,
):
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

    # 2. Create or update wage rows for existing employees

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
            db_session, existing_employee_ids
        )

    employer_employee_filing_period_to_wage_model: Dict[Any, Any] = {}
    for existing_wage in existing_wages:
        key: str = get_wage_composite_key(
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

        existing_wage_composite_key: str = get_wage_composite_key(
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
        else:
            is_updated = dor_persistence_util.check_and_update_wages_and_contributions(
                db_session, existing_wage, wage_info, import_log_entry_id
            )

            if is_updated:
                updated_count += 1
                report.updated_wages_and_contributions_count += 1
            else:
                unmodified_count += 1
                report.unmodified_wages_and_contributions_count += 1

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

    if updated_count > 0:
        logger.info(
            "Batch committing wage updates: %i, unmodified: %i", updated_count, unmodified_count
        )
        db_session.commit()

    logger.info(
        "Wage data for existing employees - done with check: %i, updated: %i , collected for creation: %i",
        count,
        updated_count,
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


def import_employer_pfml_contributions(
    db_session: massgov.pfml.db.Session,
    employer_quarterly_info_list: List[Dict],
    report: ImportReport,
    import_log_entry_id: int,
) -> None:
    account_key_to_employer_id_map: Dict[str, uuid.UUID] = {}
    account_keys: List[str] = []
    for employee_info in employer_quarterly_info_list:
        account_keys.append(employee_info["account_key"])

    employer_models = dor_persistence_util.get_employers_account_key(db_session, account_keys)
    for employer in employer_models:
        account_key_to_employer_id_map[employer.account_key] = employer.employer_id

    employer_ids_to_check_in_db = []
    for employer_quarterly_info in employer_quarterly_info_list:
        found_employer_id = account_key_to_employer_id_map.get(
            employer_quarterly_info["account_key"], None
        )
        if found_employer_id is not None:
            employer_ids_to_check_in_db.append(found_employer_id)

    existing_employer_models_all_dates = dor_persistence_util.get_employer_quarterly_info_by_employer_id(
        db_session, employer_ids_to_check_in_db
    )

    existing_quarterly_map: Dict[Tuple[uuid.UUID, date], EmployerQuarterlyContribution] = {}
    for existing_employer_model in existing_employer_models_all_dates:
        key = (existing_employer_model.employer_id, existing_employer_model.filing_period)
        existing_quarterly_map[key] = existing_employer_model

    # Determine which are new (employer, quarter) combinations, and which are updates to existing
    # rows in the database.
    not_found_employer_quarterly_contribution_list = []
    found_employer_quarterly_contribution_list = []

    for employer_quarterly_info in employer_quarterly_info_list:
        employer_id = account_key_to_employer_id_map.get(
            employer_quarterly_info["account_key"], None
        )
        if employer_id is None:
            logger.warning(
                "Attempted to create a quarterly row for unknown employer: %s",
                employer_quarterly_info["account_key"],
            )
            report.skipped_employer_quarterly_contribution += 1
            continue

        period = employer_quarterly_info["filing_period"]
        existing_composite_key = (employer_id, period)
        existing_model = existing_quarterly_map.get(existing_composite_key, None)

        if existing_model is not None:
            found_employer_quarterly_contribution_list.append(employer_quarterly_info)
        else:
            not_found_employer_quarterly_contribution_list.append(employer_quarterly_info)

    employer_quarter_models_to_create = list(
        map(
            lambda employer_info: dor_persistence_util.dict_to_employer_quarter_contribution(
                employer_info,
                account_key_to_employer_id_map[employer_info["account_key"]],
                import_log_entry_id,
            ),
            not_found_employer_quarterly_contribution_list,
        )
    )

    logger.info(
        "Creating new employer quarterly contributions records: %i",
        len(employer_quarter_models_to_create),
    )

    bulk_save(db_session, employer_quarter_models_to_create, "Employer Quarterly Contributions")

    logger.info(
        "Done - Creating new employer quarterly contributions: %i",
        len(employer_quarter_models_to_create),
    )

    report.created_employer_quarters_count += len(employer_quarter_models_to_create)

    count = 0
    updated_count = 0
    unmodified_count = 0

    for employer_info in found_employer_quarterly_contribution_list:
        count += 1
        if count % 10000 == 0:
            logger.info("Updating quarterly contribution info, current %i", count)

        account_key = employer_info["account_key"]
        filing_period = employer_info["filing_period"]
        employer_id = account_key_to_employer_id_map[account_key]

        employer_quarterly_contribution = existing_quarterly_map[(employer_id, filing_period)]

        if employer_quarterly_contribution.latest_import_log_id == import_log_entry_id:
            # Since the import log id is equal, we already updated this row during this import.
            logger.warning(
                "duplicate employer quarterly contribution row",
                extra=dict(account_key=account_key, filing_period=filing_period),
            )

        is_updated = dor_persistence_util.check_and_update_employer_quarterly_contribution(
            employer_quarterly_contribution, employer_info, import_log_entry_id,
        )

        if is_updated:
            updated_count += 1
            report.updated_employer_quarters_count += 1
        else:
            unmodified_count += 1
            report.unmodified_employer_quarters_count += 1

    if updated_count > 0:
        logger.info(
            "Batch committing quarterly contribution updates: %i, unmodified: %i",
            updated_count,
            unmodified_count,
        )
        db_session.commit()


def import_employees_and_wage_data(
    db_session,
    employee_and_wage_info_list,
    employee_ssns_created_in_current_import_run,
    report,
    import_log_entry_id,
):
    # 1 - Create account key to existing employer id reference map
    account_key_to_employer_id_map = {}
    account_keys = []
    for employee_info in employee_and_wage_info_list:
        account_keys.append(employee_info["account_key"])

    employer_models = dor_persistence_util.get_employers_account_key(db_session, account_keys)
    for employer in employer_models:
        account_key_to_employer_id_map[employer.account_key] = employer.employer_id

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

    # 4 - Log new employers for existing employees
    log_employees_with_new_employers(
        db_session,
        employee_and_wage_info_list,
        account_key_to_employer_id_map,
        ssn_to_existing_employee_model,
        report,
        import_log_entry_id,
    )

    # 5 - Import wages
    import_wage_data(
        db_session,
        employee_and_wage_info_list,
        account_key_to_employer_id_map,
        employee_ssns_created_in_current_import_run,
        ssn_to_existing_employee_model,
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
        employer_capturer = Capturer(line_offset=0)
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


def move_file_to_processed(file_path, s3_client):
    """Move file from received to processed folder"""
    file_name = file_util.get_file_name(file_path)
    file_key = file_util.get_s3_file_key(file_path)

    bucket_name = file_util.get_s3_bucket(file_path)

    logger.info("Moving file to processed folder. Bucket: %s, file: %s", bucket_name, file_key)

    file_dest_key = PROCESSED_FOLDER + file_name

    s3_client.copy({"Bucket": bucket_name, "Key": file_key}, bucket_name, file_dest_key)
    s3_client.delete_object(Bucket=bucket_name, Key=file_key)


def get_file_name(s3_file_key):
    """Get file name without extension from an object key"""
    file_name_index = s3_file_key.rfind("/") + 1
    file_name_extension_index = s3_file_key.rfind(".txt")
    file_name = s3_file_key[file_name_index:file_name_extension_index]
    return file_name


if __name__ == "__main__":
    handler()
