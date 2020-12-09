import argparse
import csv
import os
from collections import defaultdict
from typing import List, Optional

import boto3
import botocore
from smart_open import open as smart_open

import massgov.pfml.util.logging
from massgov.pfml import db, fineos
from massgov.pfml.util.users import create_or_update_user_record

#
# Import CSV file of Leave Admins into Cognito, Paid Leave DB, FINEOS
#
# This is intended to be run as an ECS task with the filenames (or s3 locations) passed as arguments.
# Ex: ./bin/run-ecs-task/run-task.sh <env> process-import-csv <firstname>.<lastname> process-import-csv \
#     "https://my-bucket.s3.us-west-2.amazonaws.com/folder/filename.csv"
#


logger = massgov.pfml.util.logging.get_logger(__name__)


def parse_args():
    """Parse command line arguments and flags."""
    parser = argparse.ArgumentParser(
        description="Import CSV file(s) containing emails+fein as leave admins",
    )
    parser.add_argument("files", nargs="+", help="Files to import")
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
    with smart_open(file) as open_fh:
        csv_file = csv.DictReader(open_fh)
        for row in csv_file:
            email = row.get("email", "UNKNOWN") or "UNKNOWN"
            data[email].append(row)
    return data


def clean_fein(fein: str) -> str:
    return fein.replace("-", "").zfill(9)


def mask_fein(fein: str) -> str:
    # Log only last 4 of FEIN
    return f"**-***{fein[5:]}"


def process_by_email(
    email: str,
    input_data: List[dict],
    db_session: db.Session,
    cognito_pool_id: str,
    filename: Optional[str] = "",
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
    fineos_client: Optional[fineos.AbstractFINEOSClient] = None,
) -> int:
    processed = 0
    for employer_to_register in input_data:
        if employer_to_register.get("fein"):
            fein = clean_fein(employer_to_register["fein"])
            registered = create_or_update_user_record(
                db_session=db_session,
                fein=fein,
                email=email,
                cognito_pool_id=cognito_pool_id,
                verification_code=employer_to_register.get("verification_code"),
                cognito_client=cognito_client,
                fineos_client=fineos_client,
            )
            if registered:
                processed += 1
            else:
                logger.error(
                    "Unable to complete registration for %s for employer %s in filename %s",
                    email,
                    mask_fein(fein),
                    filename,
                )
    return processed


def process_files(
    files: List[str],
    cognito_pool_id: str,
    db_session: Optional[db.Session] = None,
    cognito_client: Optional["botocore.client.CognitoIdentityProvider"] = None,
) -> None:
    if not db_session:
        db_session = massgov.pfml.db.init()
    if not cognito_client:
        cognito_client = boto3.client("cognito-idp", region_name="us-east-1")
    fineos_client = massgov.pfml.fineos.create_client()

    try:
        for input_file in files:
            data = pivot_csv_file(input_file)
            records_to_import = sum(len(x) for x in data.values())
            processed = 0
            last_updated = 0
            logger.info("found %s emails to import in %s", len(data.keys()), input_file)
            for email, employers in data.items():
                # Insert parallelization here :tada:
                processed += process_by_email(
                    email=email,
                    input_data=employers,
                    db_session=db_session,
                    cognito_pool_id=cognito_pool_id,
                    filename=input_file,
                    cognito_client=cognito_client,
                    fineos_client=fineos_client,
                )
                last_updated = log_progress(
                    processed, records_to_import, last_updated, update_every=100
                )
            logger.info(
                "processed file: %s; imported %s emails, %s records",
                input_file,
                len(data.keys()),
                records_to_import,
            )

    except Exception as ex:
        logger.error("error during import: %s %s", ex.__class__, str(ex))

    logger.info("done processing files ")


def process():
    massgov.pfml.util.logging.init("process_csv")
    cognito_pool_id = os.environ.get("COGNITO_IDENTITY_POOL_ID", None)
    if not cognito_pool_id:
        logger.error("Required: COGNITO_IDENTITY_POOL_ID value")
        exit(1)

    args = parse_args()
    process_files(files=args.files, cognito_pool_id=cognito_pool_id)
