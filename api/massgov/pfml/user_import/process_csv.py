import argparse
import csv
import io
import os
import time
from collections import defaultdict
from typing import List, Optional, Tuple

import boto3
import botocore
from smart_open import open as smart_open

import massgov.pfml.util.logging
from massgov.pfml import db, fineos
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.strings import mask_fein
from massgov.pfml.util.users import register_or_update_leave_admin

#
# Import CSV file of Leave Admins into Cognito, Paid Leave DB, FINEOS
#
# This is intended to be run as an ECS task with the filenames (or s3 locations) passed as arguments.
# Ex: ./bin/run-ecs-task/run-task.sh <env> process-import-csv <firstname>.<lastname> process-import-csv \
#     "https://my-bucket.s3.us-west-2.amazonaws.com/folder/filename.csv"
#

logger = massgov.pfml.util.logging.get_logger(__name__)
REQUIRED_FIELDS = set(("fein", "email"))


def parse_args():
    """Parse command line arguments and flags."""
    parser = argparse.ArgumentParser(
        description="Import CSV file(s) containing emails+fein as leave admins",
    )
    parser.add_argument("files", nargs="+", help="Files to import")
    parser.add_argument(
        "--force_registration",
        help="To register users in Fineos without verification",
        action="store_true",
    )
    args = parser.parse_args()
    if not args.files:
        parser.print_help()
        exit(1)
    return args


def log_progress(
    processed: int, total: int, last_updated: int, update_every: Optional[int] = None
) -> int:
    if not update_every:
        update_every = 100
    if (processed - last_updated) >= update_every:
        logger.info("processed %s out of %s imports", processed, total)
        last_updated = processed
    return last_updated


def pivot_csv_file(file: str) -> dict:
    data = defaultdict(list)
    with smart_open(file, encoding="utf-8-sig") as open_fh:
        csv_file = csv.DictReader(open_fh)
        headers = csv_file.fieldnames
        if not headers or not REQUIRED_FIELDS.issubset(headers):
            logger.error(f"File has invalid headers; requires at minimum {REQUIRED_FIELDS}")
            raise Exception(f"File has invalid headers; requires at minimum {REQUIRED_FIELDS}")
        for row in csv_file:
            email = row.get("email", "UNKNOWN") or "UNKNOWN"
            data[email].append(row)
    return data


def clean_fein(fein: str) -> str:
    return fein.replace("-", "").zfill(9)


def create_csv_and_send_to_s3(data: List[dict], file_name: str) -> None:
    if not data:
        return

    document_stream = io.StringIO()
    document_writer = csv.DictWriter(document_stream, fieldnames=data[0].keys())
    _ = document_writer.writeheader()
    for row in data:
        _ = document_writer.writerow(row)
    s3 = boto3.resource("s3", region_name="us-east-1")
    bucket_name = os.environ.get("PROCESS_CSV_DATA_BUCKET_NAME", None)
    if not bucket_name:
        logger.warning("S3 bucket name not set. Cannot upload results to S3.")
        return
    logger.info("Uploading results to S3.")
    s3.Bucket(bucket_name).put_object(Key=file_name, Body=document_stream.getvalue())


def split_successes_from_failures(processed: List[dict]) -> Tuple[List[dict], List[dict]]:
    successes = list(filter(lambda x: "error" not in x, processed))
    failures = list(filter(lambda x: "error" in x, processed))
    return successes, failures


def process_by_email(
    email: str,
    input_data: List[dict],
    db_session: db.Session,
    force_registration: bool,
    cognito_pool_id: str,
    filename: Optional[str] = "",
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
    fineos_client: Optional[fineos.AbstractFINEOSClient] = None,
) -> List[dict]:
    processed_records = []
    for employer_to_register in input_data:
        if employer_to_register.get("fein"):
            fein = clean_fein(employer_to_register["fein"])
            registered, reg_msg = register_or_update_leave_admin(
                db_session=db_session,
                fein=fein,
                email=email,
                force_registration=force_registration,
                cognito_pool_id=cognito_pool_id,
                cognito_client=cognito_client,
                fineos_client=fineos_client,
            )
            if not registered:
                employer_to_register["error"] = reg_msg
                logger.error(
                    "Unable to complete registration for %s for employer %s in filename %s: %s",
                    email,
                    mask_fein(fein),
                    filename,
                    reg_msg,
                )
            processed_records.append(employer_to_register)
    return processed_records


def process_files(
    files: List[str],
    force_registration: bool,
    cognito_pool_id: str,
    db_session: Optional[db.Session] = None,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> None:
    if not db_session:
        db_session = massgov.pfml.db.init()
    if not cognito_client:
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
    fineos_client = massgov.pfml.fineos.create_client()

    for input_file in files:
        data = pivot_csv_file(input_file)
        records_to_import = sum(len(x) for x in data.values())
        processed = []
        last_updated = 0
        logger.info("found %s emails to import in %s", len(data.keys()), input_file)
        for email, employers in data.items():
            processed += process_by_email(
                email=email,
                input_data=employers,
                db_session=db_session,
                force_registration=force_registration,
                cognito_pool_id=cognito_pool_id,
                filename=input_file,
                cognito_client=cognito_client,
                fineos_client=fineos_client,
            )
            last_updated = log_progress(
                len(processed), records_to_import, last_updated, update_every=100
            )

        (
            successfully_processed_records,
            unsuccessfully_processed_records,
        ) = split_successes_from_failures(processed)

        # write successes to S3
        success_file_name = f'{time.strftime("%Y%m%d-%H%M%S")}-valid_employers-SUCCEEDED.csv'
        create_csv_and_send_to_s3(successfully_processed_records, success_file_name)

        # write failures to S3
        failed_file_name = f'{time.strftime("%Y%m%d-%H%M%S")}-valid_employers-FAILED.csv'
        create_csv_and_send_to_s3(unsuccessfully_processed_records, failed_file_name)

        logger.info(
            "processed file: %s; imported %s emails, %s records",
            input_file,
            len(data.keys()),
            records_to_import,
        )

    logger.info("done processing files ")


@background_task("bulk-user-import")
def process():
    cognito_pool_id = os.environ.get("COGNITO_IDENTITY_POOL_ID", None)
    if not cognito_pool_id:
        logger.error("Required: COGNITO_IDENTITY_POOL_ID value")
        exit(1)

    args = parse_args()
    process_files(
        files=args.files,
        force_registration=args.force_registration,
        cognito_pool_id=cognito_pool_id,
    )
