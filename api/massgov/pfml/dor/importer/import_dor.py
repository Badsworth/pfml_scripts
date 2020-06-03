#!/usr/bin/python3
#
# Lambda function to import DOR data from S3 to PostgreSQL (RDS).
#

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Callable, Dict, List, Optional, Union
from uuid import UUID

import boto3

import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging as logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import ImportLog
from massgov.pfml.dor.importer.lib.decrypter import GpgDecrypter, Utf8Decrypter
from massgov.pfml.util.aws_ssm import get_secret

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


@dataclass
class FieldFormat:
    property_name: str
    length: int
    conversion_function: Optional[Callable] = None


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y%m%d")


def parse_datetime(datetime_str):
    return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")


def parse_boolean(boolean_str):
    # expected format is "1" or "0"
    return boolean_str == "T"


def parse_dollar_amount(dollar_amount_str):
    return Decimal(dollar_amount_str)


# File formats
# See details in https://lwd.atlassian.net/wiki/spaces/API/pages/229539929/DOR+Import#Import-Process
EMPLOYER_FILE_FORMAT = (
    FieldFormat("account_key", 11),
    FieldFormat("employer_name", 255),
    FieldFormat("fein", 9),
    FieldFormat("employer_address_street", 255),
    FieldFormat("employer_address_city", 30),
    FieldFormat("employer_address_state", 2),
    FieldFormat("employer_address_zip", 9),
    FieldFormat("employer_dba", 255),
    FieldFormat("family_exemption", 1, parse_boolean),
    FieldFormat("medical_exemption", 1, parse_boolean),
    FieldFormat("exemption_commence_date", 8, parse_date),
    FieldFormat("exemption_cease_date", 8, parse_date),
    FieldFormat("updated_date", 14, parse_datetime),
)

EMPLOYER_QUARTER_INFO_FORMAT = (
    FieldFormat("record_type", 1),
    FieldFormat("account_key", 11),
    FieldFormat("filing_period", 8, parse_date),
    FieldFormat("employer_name", 255),
    FieldFormat("employer_fein", 9),
    FieldFormat("amended_flag", 1, parse_boolean),
    FieldFormat("received_date", 8, parse_date),
    FieldFormat("updated_date", 14, parse_datetime),
)

EMPLOYEE_FORMAT = (
    FieldFormat("record_type", 1),
    FieldFormat("account_key", 11),
    FieldFormat("filing_period", 8, parse_date),
    FieldFormat("employee_first_name", 255),
    FieldFormat("employee_last_name", 255),
    FieldFormat("employee_ssn", 9),
    FieldFormat("independent_contractor", 1, parse_boolean),
    FieldFormat("opt_in", 1, parse_boolean),
    FieldFormat("employee_ytd_wages", 20, parse_dollar_amount),
    FieldFormat("employee_qtr_wages", 20, parse_dollar_amount),
    FieldFormat("employee_medical", 20, parse_dollar_amount),
    FieldFormat("employer_medical", 20, parse_dollar_amount),
    FieldFormat("employee_family", 20, parse_dollar_amount),
    FieldFormat("employer_family", 20, parse_dollar_amount),
)


def handler(event, context):
    """Lambda handler function."""
    logging.init(__name__)

    decrypter: Union[Utf8Decrypter, GpgDecrypter]

    FOLDER_PATH = os.environ.get("FOLDER_PATH")

    if os.getenv("DECRYPT") != "true":
        logger.info("Skipping GPG decrypter setup")
        decrypter = Utf8Decrypter()
    else:
        logger.info("Setting up GPG")
        gpg_decryption_key = get_secret(aws_ssm, os.environ["GPG_DECRYPTION_KEY_SSM_PATH"])
        gpg_decryption_passphrase = get_secret(
            aws_ssm, os.environ["GPG_DECRYPTION_KEY_PASSPHRASE_SSM_PATH"]
        )

        decrypter = GpgDecrypter(gpg_decryption_key, gpg_decryption_passphrase)

    logger.info("Start import run")

    logger.info("Starting import run")

    files_by_date = get_files_for_import_grouped_by_date(FOLDER_PATH)
    file_date_keys = sorted(files_by_date.keys())

    if len(file_date_keys) == 0:
        # TODO need to capture some report for this
        logger.info("no files to import")
        return {"status": "OK", "msg": "no files to import"}

    report = ImportRunReport(start=datetime.now().isoformat())

    for file_date_key in file_date_keys:
        files_for_import = files_by_date[file_date_key]

        logger.info("importing files", extra={"files_for_import": files_for_import})

        employer_file_filter = [
            f for f in files_for_import if get_file_name(f).startswith(EMPLOYER_FILE_PREFIX)
        ]
        employer_file = None if len(employer_file_filter) == 0 else employer_file_filter[0]

        employee_file_filter = [
            f for f in files_for_import if get_file_name(f).startswith(EMPLOYEE_FILE_PREFIX)
        ]
        employee_file = None if len(employer_file_filter) == 0 else employee_file_filter[0]

        logger.info(
            "got file names",
            extra={
                "date": file_date_key,
                "employer_file": employer_file,
                "employee_file": employee_file,
            },
        )

        import_report = process_daily_import(FOLDER_PATH, employer_file, employee_file, decrypter)
        report.imports.append(import_report)

    report.end = datetime.now().isoformat()
    logger.info("Finished import run")
    decrypter.remove_keys()
    return {"status": "OK", "import_type": "daily", "report": asdict(report)}


def get_bucket(event):
    """Extract an S3 bucket from an event."""
    # get bucket name from environment variable
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    bucket = s3Bucket.Bucket(bucket_name)
    return bucket


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
            files_by_date[file_date].append(file_key)
    return files_by_date


def process_daily_import(path, employer_file, employee_file, decrypter):
    """Process s3 file by key"""
    logger.info("Starting to process files")
    report = ImportReport(
        start=datetime.now().isoformat(), employer_file=employer_file, employee_file=employee_file
    )

    config = db.get_config(aws_ssm)
    db_session_raw = db.init(config)

    with db.session_scope(db_session_raw) as db_session:
        try:
            employers = parse_employer_file(path, employer_file, decrypter)
            employers_quarter_info, employees_info = parse_employee_file(
                path, employee_file, decrypter
            )

            parsed_employers_count = len(employers)
            parsed_employers_quarter_info_count = len(employers_quarter_info)
            parsed_employees_info_count = len(employees_info)

            logger.info(
                "Finished parsing files",
                extra={
                    "employer_file": employer_file,
                    "employee_file": employee_file,
                    "parsed_employers_count": parsed_employers_count,
                    "parsed_employers_quarter_info_count": parsed_employers_quarter_info_count,
                    "parsed_employees_info_count": parsed_employees_info_count,
                },
            )

            import_to_db(db_session, employers, employers_quarter_info, employees_info, report)

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

        # write report
        write_report_to_db(db_session, report)
        # TODO determine if this is still necessary now that we have db logs
        # write_report_to_s3(bucket, report)

    return report


def import_to_db(db_session, employers, employers_quarter_info, employees_info, report):
    """Process through parsed objects and persist into database"""
    logger.info("Starting import")

    account_key_to_employer_id_map = import_employers(db_session, employers, report)
    import_employees_and_wage_data(
        db_session, account_key_to_employer_id_map, employers_quarter_info, employees_info, report,
    )

    logger.info("Finished import")


def import_employers(db_session, employers, report):
    # look through all employers
    """Import employers into db"""
    logger.info("Importing employers")

    account_key_to_employer_id_map = {}

    for employer_info in employers:
        account_key = employer_info["account_key"]
        existing_employer = dor_persistence_util.get_employer_by_fein(
            db_session, employer_info["fein"]
        )

        if existing_employer is None:
            created_employer = dor_persistence_util.create_employer(db_session, employer_info)

            account_key_to_employer_id_map[account_key] = created_employer.employer_id
            report.created_employers_count = report.created_employers_count + 1
        else:
            updated_date = employer_info["updated_date"]
            if updated_date > existing_employer.dor_updated_date:
                dor_persistence_util.update_employer(db_session, existing_employer, employer_info)

                report.updated_employer_ids.append(str(existing_employer.employer_id))
            else:
                report.unmodified_employer_ids.append(str(existing_employer.employer_id))

            account_key_to_employer_id_map[account_key] = existing_employer.employer_id

    report.updated_employers_count = len(report.updated_employer_ids)
    report.unmodified_employers_count = len(report.unmodified_employer_ids)

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
    db_session, account_key_to_employer_id_map, employers_quarter_info, employees_info, report
):
    """Import employees and wage information"""
    logger.info("Importing employee information")

    # create a reference map of amended flag for employee and wage data
    employee_amended_flag_map = {}
    wage_data_amended_flag_map = {}

    for employer_quarter_info in employers_quarter_info:
        account_key = employer_quarter_info["account_key"]
        filing_period_str = employer_quarter_info["filing_period"].strftime("%Y%m%d")
        composite_key = "{}-{}".format(account_key, filing_period_str)
        amended_flag = employer_quarter_info["amended_flag"]

        employee_amended_flag_map[account_key] = amended_flag
        wage_data_amended_flag_map[composite_key] = amended_flag

    # import employees
    employee_id_by_ssn = {}

    for employee_info in employees_info:
        ssn = employee_info["employee_ssn"]
        account_key = employee_info["account_key"]
        existing_employee = dor_persistence_util.get_employee_by_ssn(db_session, ssn)

        if existing_employee is None:
            created_employee = dor_persistence_util.create_employee(db_session, employee_info)

            employee_id_by_ssn[ssn] = created_employee.employee_id
            report.created_employees_count = report.created_employees_count + 1
        else:
            if employee_amended_flag_map[account_key] is True:
                dor_persistence_util.update_employee(db_session, existing_employee, employee_info)

                report.updated_employee_ids.append(str(existing_employee.employee_id))
            else:
                report.unmodified_employee_ids.append(str(existing_employee.employee_id))

            employee_id_by_ssn[ssn] = existing_employee.employee_id

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

    # imoport wage information
    for employee_info in employees_info:
        account_key = employee_info["account_key"]
        filing_period = employee_info["filing_period"]
        ssn = employee_info["employee_ssn"]

        employee_id = employee_id_by_ssn[ssn]
        employer_id = account_key_to_employer_id_map[account_key]

        existing_wage = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
            db_session, employee_id, filing_period
        )

        if existing_wage is None:
            dor_persistence_util.create_wages_and_contributions(
                db_session, employee_info, employee_id, employer_id
            )

            report.created_wages_and_contributions_count = (
                report.created_wages_and_contributions_count + 1
            )
        else:
            ameneded_flag_key = "{}-{}".format(account_key, filing_period.strftime("%Y%m%d"))
            if wage_data_amended_flag_map[ameneded_flag_key] is True:
                dor_persistence_util.update_wages_and_contributions(
                    db_session, existing_wage, employee_info
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

    return employee_id_by_ssn


# TODO turn return dataclasses list instead of object list
def parse_employer_file(path, employer_file, decrypter):
    """Parse employer file"""
    logger.info("Start parsing employer file", extra={"employer_file": employer_file})
    employers = []

    full_path = "{}/{}".format(str(path), employer_file)
    file_bytes = file_util.read_file(full_path, "rb")
    decrypted_str = decrypter.decrypt(file_bytes)
    decrypted_lines = decrypted_str.split("\n")

    for row in decrypted_lines:
        if not row:  # skip empty end of file lines
            continue

        employer = parse_row_to_object_by_format(row, EMPLOYER_FILE_FORMAT)
        employers.append(employer)

    logger.info("Finished parsing employer file", extra={"employer_file": employer_file})
    return employers


def parse_employee_file(path, employee_file, decrypter):
    """Parse employee file"""
    logger.info("Start parsing employee file", extra={"employee_file": employee_file})

    employers_quarter_info = []
    employees_info = []

    full_path = "{}/{}".format(str(path), employee_file)
    file_bytes = file_util.read_file(full_path, "rb")
    decrypted_str = decrypter.decrypt(file_bytes)
    decrypted_lines = decrypted_str.split("\n")

    for row in decrypted_lines:
        if not row:  # skip empty end of file lines
            continue

        if row.startswith("A"):
            employer_quarter_info = parse_row_to_object_by_format(row, EMPLOYER_QUARTER_INFO_FORMAT)
            employers_quarter_info.append(employer_quarter_info)
        else:
            employee_info = parse_row_to_object_by_format(row, EMPLOYEE_FORMAT)
            employees_info.append(employee_info)

    logger.info("Finished parsing employee file", extra={"employee_file": employee_file})
    return employers_quarter_info, employees_info


def parse_row_to_object_by_format(row, row_format):
    object = {}
    start_index = 0
    for column_format in row_format:
        property_name = column_format.property_name
        end_index = start_index + column_format.length

        column_value = row[start_index:end_index].strip()
        conversion_function = column_format.conversion_function
        if conversion_function is None:
            object[property_name] = column_value
        else:
            object[property_name] = conversion_function(column_value)

        start_index = end_index

    return object


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


def write_report_to_db(db_session, report):
    """Write report of import to database"""
    logger.info("Saving import report in log")
    import_log = ImportLog(
        source="DOR",
        import_type="Initial",  # Update this from invoke payload
        status=report.status,
        report=json.dumps(asdict(report), indent=2),
        start=report.start,
        end=report.end,
    )
    db_session.add(import_log)
    logger.info("Finished saving import report in log")


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


def get_file_name(s3_file_key):
    """Get file name without extension from an object key"""
    file_name_index = s3_file_key.rfind("/") + 1
    file_name_extention_index = s3_file_key.rfind(".txt")
    file_name = s3_file_key[file_name_index:file_name_extention_index]
    return file_name
