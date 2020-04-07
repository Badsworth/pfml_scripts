#!/usr/bin/python3
#
# Lambda function to import DOR data from S3 to PostgreSQL (RDS).
#

import json
import logging
from datetime import datetime

import boto3

FORMAT = "%(levelname)s %(asctime)s [%(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")
s3Bucket = boto3.resource("s3")

RECEIVED_FOLDER = "external-integrations/dor/daily_import/received/"
PROCESSED_FOLDER = "external-integrations/dor/daily_import/processed/"


def handler(event, context):
    """Lambda handler function."""

    bucket = get_bucket(event)

    files_for_import = get_files_for_import(bucket)

    if len(files_for_import) == 0:
        logger.info("no files to import")
        return {"status": "OK", "msg": "no files to import"}

    report = {"start": datetime.now().isoformat(), "imports": []}

    for file_for_import in files_for_import:
        file_report = process_file(bucket, file_for_import)
        report["imports"].append(file_report)

    return {"status": "OK", "import_type": "daily", "report": report}


def get_bucket(event):
    """Extract an S3 bucket from an event."""
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    bucket = s3Bucket.Bucket(bucket_name)
    return bucket


def get_files_for_import(bucket):
    """Get the paths (s3 keys) of files in the recieved folder of the bucket"""
    files_for_import = []
    for s3_object in bucket.objects.filter(Prefix=RECEIVED_FOLDER):
        if s3_object.key != RECEIVED_FOLDER:
            files_for_import.append(s3_object.key)

    files_for_import.sort()
    return files_for_import


def process_file(bucket, file_for_import):
    """Process s3 file by key"""
    logger.info("processing file: %s", file_for_import)
    report = {"filename": file_for_import, "start": datetime.now().isoformat()}

    lines = read_file(bucket, file_for_import)

    try:
        employer_rows_count = 0
        employee_rows_count = 0

        # process file and populate report
        for lineb in lines:
            line = lineb.decode("utf-8")
            if line.startswith("A"):
                employer_rows_count += 1
            else:
                employee_rows_count += 1

        # finalize report
        end = datetime.now()
        report["employer_rows_count"] = employer_rows_count
        report["employee_rows_count"] = employee_rows_count
        report["status"] = "success"
        report["end"] = end.isoformat()

        # move file to processed folder
        move_file_to_processed(bucket, file_for_import)

    except Exception:
        logger.exception("exception in file process")
        report["status"] = "error"
        report["end"] = datetime.now().isoformat()

    # write report
    write_report(bucket, report)
    return report


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
    report_str = json.dumps(report, indent=2)
    file_name = get_file_name(report["filename"])
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
