#!/usr/bin/env python3
import argparse
import csv
import os
from datetime import timedelta
from itertools import groupby
from typing import Dict, List

import boto3
import smart_open
from csvsorter import csvsort

from massgov.pfml.util.csv import CSVSourceWrapper

OUTPUT_CSV_FIELDS = ["Employer Name", "EIN", "Contact Name", "Contact Email"]
RESULT_CSV_FIELDS = ["email", "url"]
CSV_BUCKET_NAME = "massgov-pfml-tpa-csv-storage"


def main():
    """
    Main program:
    Given a valid input CSV, writes individual CSVs to given output directory for any
    entries that have duplicate email addresses.  Then uploads those CSVs to the S3 bucket
    and creates signed URLs for each one.  Writes a final CSV called 'results.csv' to the
    output directory in the format of "email,url" for each created individual CSV that was
    uploaded.
    """
    args = parse_args()

    check_for_empty_output_dir(args.output_dir)
    csvsort(args.input, ["email"])
    emails_with_files = process_file(args.input, args.output_dir)
    emails_and_urls = upload_to_s3(
        emails_with_files,
        args.output_dir,
        args.url_expiration_days,
        args.aws_access_key_id,
        args.aws_secret_access_key,
        args.aws_session_token,
    )
    write_result_csv(emails_and_urls, args.output_dir)


def check_for_empty_output_dir(output_dir: str) -> None:
    """Throws an exception if the output directory is not empty"""
    if len(os.listdir(output_dir)) != 0:
        raise Exception("Output directory must be empty!")


def create_csv(filename: str, row_queue: List, output_dir: str) -> None:
    """Creates a CSV with the required fields"""
    output_csv_filename = f"{output_dir}/{filename}.csv"
    with smart_open.open(output_csv_filename, "w") as output_file:
        csv_output = csv.DictWriter(
            output_file, fieldnames=OUTPUT_CSV_FIELDS, restval="", extrasaction="ignore"
        )
        csv_output.writeheader()
        for row in row_queue:
            csv_output.writerow(
                {
                    "Employer Name": row["employer"],
                    "EIN": row["fein"],
                    "Contact Name": "",
                    "Contact Email": "",
                }
            )


def de_dupe(row_queue: List[Dict]) -> List[Dict]:
    """
    Given a list of commonly structured dictionaries, removes duplicates based on the
    employer and fein keys.
    """
    keys = ["employer", "fein"]
    deduped_list = [
        list(data)[0]
        for key, data in groupby(row_queue, key=lambda x: tuple(x[i].lower() for i in keys))
    ]
    return deduped_list


def upload_to_s3(
    emails_with_files: List[str],
    output_dir: str,
    expiration_days: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    aws_session_token: str,
) -> List[Dict]:
    """Uploads a CSV file to S3, gets a signed S3 URL to the file and returns a list of email and URL pairs"""
    emails_and_urls: List[Dict] = []
    folder_name = output_dir
    expiration_seconds = timedelta(days=int(expiration_days)).total_seconds()
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
    )
    for email in emails_with_files:
        filename = f"{email}.csv"
        full_file_path = os.path.join(output_dir, filename)
        file_key = f"{folder_name}/{filename}"
        s3_client.upload_file(full_file_path, CSV_BUCKET_NAME, file_key)
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": CSV_BUCKET_NAME, "Key": file_key},
            ExpiresIn=expiration_seconds,
        )
        emails_and_urls.append({"email": email, "url": url})

    return emails_and_urls


def process_file(input_csv_filename: str, output_dir: str) -> List[str]:
    """
    Creates a new CSV file for any entries that have duplicate email addresses and places
    those files in the directory specified via the output-dir command line argument.
    """
    emails_with_files: List[str] = []
    row_queue: List[Dict] = []
    csv_input = CSVSourceWrapper(input_csv_filename)
    for row in csv_input:
        if len(row_queue) == 0:
            row_queue.append(row)
        elif row["email"] == row_queue[-1]["email"]:
            row_queue.append(row)
        else:
            row_queue = de_dupe(row_queue)
            if len(row_queue) > 1:
                create_csv(row_queue[0]["email"], row_queue, output_dir)
                emails_with_files.append(row_queue[0]["email"])
            row_queue = [row]

    row_queue = de_dupe(row_queue)
    if len(row_queue) > 1:
        create_csv(row_queue[0]["email"], row_queue, output_dir)
        emails_with_files.append(row_queue[0]["email"])

    return emails_with_files


def write_result_csv(emails_and_urls: list, output_dir: str) -> None:
    """
    Writes a CSV that has the email and signed URL on each row
    """
    output_csv_filename = f"{output_dir}/results.csv"
    with smart_open.open(output_csv_filename, "w") as output_file:
        csv_output = csv.DictWriter(
            output_file, fieldnames=RESULT_CSV_FIELDS, restval="", extrasaction="ignore"
        )
        csv_output.writeheader()
        for row in emails_and_urls:
            csv_output.writerow(row)


def parse_args():
    """Parses arguments sent via the command line"""
    parser = argparse.ArgumentParser(
        description="Create individual CSVs to be mailed based on TPA/BMA CSV file contents"
    )
    parser.add_argument(
        "--input",
        help="CSV filename containing at least the columns [email, contact, employer, fein]",
    )
    parser.add_argument("--aws-access-key-id", help="AWS access key ID")
    parser.add_argument("--aws-secret-access-key", help="AWS secret access key")
    parser.add_argument("--aws-session-token", help="AWS session token")
    parser.add_argument("--output-dir", help="Directory to store the output CSVs")
    parser.add_argument(
        "--url-expiration-days",
        help="(Optional) Expiration, in days, for the signed S3 URLs to expire",
    )
    args = parser.parse_args()
    if (
        not args.input
        and args.output_dir
        and args.aws_access_key_id
        and args.aws_secret_access_key
        and args.aws_session_token
    ):
        parser.print_help()
        exit(1)
    return args


if __name__ == "__main__":
    main()
