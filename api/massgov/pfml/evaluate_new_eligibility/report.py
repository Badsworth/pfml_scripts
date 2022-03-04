import argparse
import csv
import itertools
import os
from datetime import date, datetime, timedelta
from time import sleep
from typing import Any, Dict, List

import boto3
from sqlalchemy import tuple_

import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.api.eligibility.eligibility import compute_financial_eligibility
from massgov.pfml.db.models.employees import Claim, EmployeeOccupation, Employer
from massgov.pfml.util.bg import background_task

logger = massgov.pfml.util.logging.get_logger(__name__)
ENVIRONMENT = os.getenv("ENVIRONMENT")


def valid_date_type(arg_date_str):
    """custom argparse *date* type for user dates values given from the command line"""
    try:
        return datetime.strptime(arg_date_str, "%Y-%m-%d")
    except ValueError:
        msg = "Given Date ({0}) not valid! Expected format, YYYY-MM-DD!".format(arg_date_str)
        raise argparse.ArgumentTypeError(msg)


def run_cloud_watch_query(start_date, end_date, client, query):
    log_group = f"service/pfml-api-{ENVIRONMENT}"

    start_query_response = client.start_query(
        logGroupName=log_group, startTime=start_date, endTime=end_date, queryString=query
    )
    query_id = start_query_response["queryId"]
    response: Dict[Any, Any] = {}
    while response.get("status") == "Running" or not response:
        sleep(1)
        response = client.get_query_results(queryId=query_id)
        if response["status"] == "Complete":
            logger.info(
                "pulled one day of logs",
                extra={"end_day": str(datetime.fromtimestamp(end_date).date()), "query": query},
            )
            return [
                {line["field"]: line["value"] for line in log_lines}
                for log_lines in response["results"]
            ]


def one_day_date_windows(start_date: datetime, end_date: datetime) -> List[tuple[int, int]]:
    date_windows = []
    date = start_date
    delta = timedelta(days=1)
    while date <= end_date:
        date_windows.append((int(date.timestamp()), int((date + timedelta(1)).timestamp())))
        date += delta

    return date_windows


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate impact of financial eligiblity changes")
    parser.add_argument(
        "--start_date",
        type=valid_date_type,
        default=(datetime.now() - timedelta(days=5)),
        help="The start date; format YYYY-MM-DD",
    )
    parser.add_argument(
        "--end_date",
        type=valid_date_type,
        default=datetime.now(),
        help="The end date; format YYYY-MM-DD",
    )
    parser.add_argument(
        "--s3_bucket",
        default=os.getenv("S3_EXPORT_BUCKET"),
        help=("An S3 bucket to export query data to; default is set in env"),
    )
    args = parser.parse_args()
    return args


def pull_data_from_cloudwatch(logs_start_date: datetime, logs_end_date: datetime) -> List[Dict]:
    client = boto3.client("logs", region_name="us-east-1")
    # this could be done in parralel
    date_ranges = one_day_date_windows(logs_start_date, logs_end_date)
    claim_data_query = "fields employee_id, employer_id, employer_average_weekly_wage, created, description, financially_eligible, @timestamp, request_id | filter message = 'Calculated financial eligibility' | limit 10000"

    claim_data_results = list(
        itertools.chain(
            *[
                run_cloud_watch_query(date_range[0], date_range[1], client, claim_data_query)
                for date_range in date_ranges
            ]
        )
    )

    start_date_query = "fields leave_start_date,employment_status, application_submitted_date,  request_id | filter message = 'Received financial eligibility request' | filter ispresent(leave_start_date) | limit 10000"

    all_leave_start_dates = list(
        itertools.chain(
            *[
                run_cloud_watch_query(date_range[0], date_range[1], client, start_date_query)
                for date_range in date_ranges
            ]
        )
    )

    # this is basically a groupby
    claim_data_request_dict = {
        claim_data["request_id"]: claim_data for claim_data in claim_data_results
    }
    for start_date in all_leave_start_dates:
        if start_date["request_id"] in claim_data_request_dict.keys():
            claim_data_request_dict[start_date["request_id"]]["leave_start_date"] = start_date[
                "leave_start_date"
            ]
            claim_data_request_dict[start_date["request_id"]]["employment_status"] = start_date[
                "employment_status"
            ]
            claim_data_request_dict[start_date["request_id"]][
                "application_submitted_date"
            ] = start_date["application_submitted_date"]
        else:
            logger.warning(
                "could not join request id",
                extra={"request_id": start_date["request_id"]},
                exc_info=True,
            )

    return list(claim_data_request_dict.values())


def generate_report(cli_args, db_session, output_csv):
    start_date: datetime = cli_args.start_date
    end_date: datetime = cli_args.end_date
    merged_results = pull_data_from_cloudwatch(start_date, end_date)

    # leave start date here is used to basically allow for multiple employee employer pairs
    log_eligibility_dict = {
        (log["employee_id"], log["employer_id"], log["leave_start_date"]): log
        for log in merged_results
        if {"employee_id", "employer_id", "leave_start_date"}.issubset(log.keys())
    }

    all_claims = (
        db_session.query(
            Claim.created_at,
            Claim.absence_period_start_date,
            Employer.employer_fein,
            Claim.employee_id,
            Claim.employer_id,
            EmployeeOccupation.employment_status,
        )
        .select_from(Claim)
        .join(Employer, isouter=True)
        .join(
            EmployeeOccupation,
            (EmployeeOccupation.employee_id == Claim.employee_id)
            & (EmployeeOccupation.employer_id == Claim.employer_id),
            isouter=True,
        )
        .filter(
            tuple_(Claim.employee_id, Claim.employer_id, Claim.absence_period_start_date).in_(
                list(log_eligibility_dict.keys())
            )
        )
        .all()
    )
    logger.info(f"claims len: {len(all_claims)}")
    for claim in all_claims:
        old_claim_result = log_eligibility_dict.get(
            (str(claim.employee_id), str(claim.employer_id), str(claim.absence_period_start_date))
        )

        if not old_claim_result:
            logger.warning(
                "could not find claim in dict",
                extra={
                    "employee_id": claim.employee_id,
                    "employer_id": claim.employer_id,
                    "absence_period_start_date": claim.absence_period_start_date,
                },
            )
            continue

        leave_start_date = date.fromisoformat(str(old_claim_result.get("leave_start_date")))
        employment_status = old_claim_result.get("employment_status") or claim.employment_status
        prior_eligibility = old_claim_result.get("financially_eligible") == "True"
        prior_description = old_claim_result.get("description")
        claimaint_id = str(claim.employee_id)
        application_submitted_date = date.fromisoformat(
            str(old_claim_result.get("application_submitted_date"))
        )

        try:
            eligibility = compute_financial_eligibility(
                db_session=db_session,
                employee_id=claim.employee_id,
                employer_id=claim.employer_id,
                application_submitted_date=application_submitted_date,
                leave_start_date=leave_start_date,
                employment_status=employment_status,
            )
            new_eligibility = eligibility.financially_eligible
            new_description = eligibility.description
            if new_eligibility != prior_eligibility:
                result = [
                    claimaint_id,
                    application_submitted_date,
                    leave_start_date,
                    prior_eligibility,
                    prior_description,
                    new_eligibility,
                    new_description,
                    eligibility.total_wages,
                ]
                output_csv.writerow(result)
        except Exception as ex:
            logger.warning(
                "unable to process claim ",
                exc_info=ex,
                extra={"employee_id": claim.employee_id, "employer_id": claim.employer_id},
            )


def main(cli_args, db_session):
    s3_bucket = cli_args.s3_bucket
    s3_bucket = s3_bucket if s3_bucket.startswith("s3://") else f"s3://{s3_bucket}"
    base_path = (
        f"{s3_bucket}/financial_eligibility/{ENVIRONMENT}/{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    with file_util.open_stream(f"{base_path}/output.csv", "w") as output_csv_path:
        output_csv = csv.writer(output_csv_path, lineterminator="\n")
        output_csv.writerow(
            [
                "claimaint_id",
                "application_submitted_date",
                "leave_start_date",
                "previous_decision",
                "previous_description",
                "new_decision",
                "new_description",
                "total_wages",
            ]
        )
        generate_report(cli_args, db_session, output_csv)


@background_task("evaluate_new_eligibility")
def evaluate_new_eligibility():
    cli_args = parse_args()
    with db.session_scope(db.init()) as db_session:
        main(cli_args, db_session)
