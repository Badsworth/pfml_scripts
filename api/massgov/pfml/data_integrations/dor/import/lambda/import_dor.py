#!/usr/bin/python3
#
# Lambda function to import DOR data from S3 to PostgreSQL (RDS).
#

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List

import boto3
import pydash

FORMAT = "%(levelname)s %(asctime)s [%(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")
s3Bucket = boto3.resource("s3")

RECEIVED_FOLDER = "external-integrations/dor/daily_import/received/"
PROCESSED_FOLDER = "external-integrations/dor/daily_import/processed/"

EMPLOYER_FILE_PREFIX = "DORDFMLEmp_"
EMPLOYEE_FILE_PREFIX = "DORDFML_"


@dataclass
class ImportReport:
    start: datetime
    employer_file: str
    employee_file: str
    employers_count: int = 0
    employers_quarter_info_count: int = 0
    status: str = None
    end: datetime = None


@dataclass
class ImportRunReport:
    start: datetime
    imports: List[ImportReport] = field(default_factory=list)
    end: datetime = None


@dataclass
class FieldFormat:
    property_name: str
    length: int
    trim: bool = False


# File formats
# See details in https://lwd.atlassian.net/wiki/spaces/API/pages/229539929/DOR+Import#Import-Process
EMPLOYER_FILE_FORMAT = (
    FieldFormat("account_key", 11),
    FieldFormat("employer_name", 255, True),
    FieldFormat("fein", 9),
    FieldFormat("employer_address_street", 50, True),
    FieldFormat("employer_address_city", 25, True),
    FieldFormat("employer_address_state", 2),
    FieldFormat("employer_address_zip", 9),
    FieldFormat("employer_dba", 255, True),
    FieldFormat("family_exemption", 1),
    FieldFormat("medical_exemption", 1),
    FieldFormat("exemption_commence_date", 8),
    FieldFormat("exemption_cease_date", 8),
    FieldFormat("updated_date", 14),
)

EMPLOYER_QUARTER_INFO_FORMAT = (
    FieldFormat("record_type", 1),
    FieldFormat("account_key", 11),
    FieldFormat("filing_period", 8),
    FieldFormat("employer_name", 255, True),
    FieldFormat("employer_fein", 9),
    FieldFormat("amended_flag", 1),
    FieldFormat("received_date", 8),
    FieldFormat("updated_date", 14),
)

EMPLOYEE_FORMAT = (
    FieldFormat("record_type", 1),
    FieldFormat("account_key", 11),
    FieldFormat("filing_period", 8),
    FieldFormat("employee_first_name", 255, True),
    FieldFormat("employee_last_name", 255, True),
    FieldFormat("employee_ssn", 9),
    FieldFormat("independent_contractor", 1),
    FieldFormat("opt_in", 1),
    FieldFormat("employer_ytd_wages", 20, True),
    FieldFormat("employer_qtr_wages", 20, True),
    FieldFormat("employee_medical", 20, True),
    FieldFormat("employee_medical", 20, True),
    FieldFormat("employee_family", 20, True),
    FieldFormat("employer_family", 20, True),
)


def handler(event, context):
    """Lambda handler function."""

    bucket = get_bucket(event)

    files_by_date = get_files_for_import_grouped_by_date(bucket)
    file_date_keys = sorted(files_by_date.keys())

    if len(file_date_keys) == 0:
        # TODO need to capture some report for this
        logger.info("no files to import")
        return {"status": "OK", "msg": "no files to import"}

    report = ImportRunReport(start=datetime.now().isoformat())

    for file_date_key in file_date_keys:
        files_for_import = files_by_date[file_date_key]

        logger.info(files_for_import)

        employer_file = pydash.find(
            files_for_import, lambda f: get_file_name(f).startswith(EMPLOYER_FILE_PREFIX)
        )
        employee_file = pydash.find(
            files_for_import, lambda f: get_file_name(f).startswith(EMPLOYEE_FILE_PREFIX)
        )

        logger.info(
            "date: %s, employer: %s, employee: %s", file_date_key, employer_file, employee_file
        )

        import_report = process_daily_import(bucket, employer_file, employee_file)
        report.imports.append(import_report)

    report.end = datetime.now().isoformat()
    return {"status": "OK", "import_type": "daily", "report": asdict(report)}


def get_bucket(event):
    """Extract an S3 bucket from an event."""
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    bucket = s3Bucket.Bucket(bucket_name)
    return bucket


def get_files_for_import_grouped_by_date(bucket):
    """Get the paths (s3 keys) of files in the recieved folder of the bucket"""
    files_for_import = []
    for s3_object in bucket.objects.filter(Prefix=RECEIVED_FOLDER):
        if s3_object.key != RECEIVED_FOLDER:  # skip the folder
            files_for_import.append(s3_object.key)

    files_by_date = {}
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


def process_daily_import(bucket, employer_file, employee_file):
    """Process s3 file by key"""
    logger.info("processing employer file: %s, employee file: %s", employer_file, employee_file)
    report = ImportReport(
        start=datetime.now().isoformat(), employer_file=employer_file, employee_file=employee_file
    )

    try:
        employers = parse_employer_file(bucket, employer_file)
        employers_quarter_info, employees_info = parse_employee_file(bucket, employee_file)

        employers_count = len(employers)
        employers_quarter_info_count = len(employers_quarter_info)
        employees_info_count = len(employees_info)

        # TODO
        import_to_db(employers, employers_quarter_info, employees_info, report)

        # finalize report
        report.employers_count = employers_count
        report.employers_quarter_info_count = employers_quarter_info_count
        report.employees_info_count = employees_info_count
        report.status = "success"
        report.end = datetime.now().isoformat()

        # move file to processed folder
        # move_file_to_processed(bucket, file_for_import) # commented out during frequent tests

    except Exception:
        logger.exception("exception in file process")
        report.status = "error"
        report.end = datetime.now().isoformat()

    # write report
    # write_report(bucket, report)
    return report


def import_to_db(employers, employers_quarter_info, employees_info, report):
    """Process through parsed objects and persist into database"""
    # TODO
    return None


def parse_employer_file(bucket, employer_file):
    employers = []

    lines = read_file(bucket, employer_file)
    for lineb in lines:
        row = lineb.decode("utf-8")
        employer = parse_row_to_object_by_format(row, EMPLOYER_FILE_FORMAT)
        employers.append(employer)

    return employers


def parse_employee_file(bucket, employee_file):
    employers_quarter_info = []
    employees_info = []

    lines = read_file(bucket, employee_file)
    for lineb in lines:
        row = lineb.decode("utf-8")
        if row.startswith("A"):
            employer_quarter_info = parse_row_to_object_by_format(row, EMPLOYER_QUARTER_INFO_FORMAT)
            employers_quarter_info.append(employer_quarter_info)
        else:
            employee_info = parse_row_to_object_by_format(row, EMPLOYEE_FORMAT)
            employees_info.append(employee_info)

    return employers_quarter_info, employees_info


def parse_row_to_object_by_format(row, row_format):
    object = {}
    start_index = 0
    for column_format in row_format:
        property_name = column_format.property_name
        trim = column_format.trim
        end_index = start_index + column_format.length

        column_value = row[start_index:end_index]
        if trim is True:
            column_value = column_value.strip()
        object[property_name] = column_value

        start_index = end_index + 1  # account for space between columns

    return object


def read_file(bucket, key):
    """Read the data from an s3 object."""
    response = s3.get_object(Bucket=bucket.name, Key=key)
    return response["Body"].iter_lines()


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


def write_report(bucket, report):
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
