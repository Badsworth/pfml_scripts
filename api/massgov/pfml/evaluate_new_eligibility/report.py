import argparse
import csv
import itertools
import os
from datetime import date, datetime, timedelta
from time import sleep
from typing import Any, Dict

import boto3
from sqlalchemy import tuple_

import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml import db
from massgov.pfml.db.models.employees import Claim, EmployeeOccupation, Employer
from massgov.pfml.evaluate_new_eligibility.eligibility import compute_financial_eligibility
from massgov.pfml.util.bg import background_task

logger = massgov.pfml.util.logging.get_logger(__name__)
ENVIRONMENT = os.getenv("ENVIRONMENT")


def run_cloud_watch_query(start_date, end_date, client, query):
    log_group = f"service/pfml-api-{ENVIRONMENT}"

    start_query_response = client.start_query(
        logGroupName=log_group, startTime=start_date, endTime=end_date, queryString=query,
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


def one_day_date_windows(number):
    today = datetime.today()
    return [
        (
            int((today - timedelta(days=i + 1)).timestamp()),
            int((today - timedelta(days=i)).timestamp()),
        )
        for i in range(number)
    ]


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate impact of financial eligiblity changes",)
    parser.add_argument(
        "--historical_len", type=int, default=5, help="number of days back you want to consider"
    )
    parser.add_argument(
        "--s3_bucket",
        default=os.getenv("S3_EXPORT_BUCKET"),
        help=("An S3 bucket to export query data to; default is set in env"),
    )
    args = parser.parse_args()
    return args


def pull_data_from_cloudwatch(number_of_days):
    client = boto3.client("logs", region_name="us-east-1",)
    # this could be done in parralel
    date_ranges = one_day_date_windows(number_of_days)
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
            claim_data_request_dict[start_date["request_id"]][
                "leave_start_date"
            ] = date.fromisoformat(start_date["leave_start_date"])
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


def generate_report(cli_args, db_session, output_csv, diff_reason_csv):
    merged_results = pull_data_from_cloudwatch(cli_args.historical_len)

    # leave start date here is used to basically allow for multiple employee employer pairs
    log_eligibility_dict = {
        (log["employee_id"], log["employer_id"], log["leave_start_date"]): log
        for log in merged_results
        if {"employee_id", "employer_id", "leave_start_date"}.issubset(log.keys())
    }
    application_submitted_date = date.today()
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
            tuple_(Claim.employee_id, Claim.employer_id, Claim.absence_period_start_date,).in_(
                list(log_eligibility_dict.keys())
            )
        )
        .all()
    )
    logger.info(f"claims len: {len(all_claims)}")
    for claim in all_claims:
        old_claim_result = log_eligibility_dict[
            (str(claim.employee_id), str(claim.employer_id), claim.absence_period_start_date,)
        ]
        leave_start_date = (
            old_claim_result.get("leave_start_date") or claim.absence_period_start_date
        )
        employment_status = old_claim_result.get("employment_status") or claim.employment_status
        prior_eligibility = old_claim_result.get("financially_eligible") == "True"
        claimaint_id = str(claim.employee_id)
        time = old_claim_result.get("application_submitted_date")
        old_aww = old_claim_result.get("employer_average_weekly_wage")
        new_aww, new_decision = None, None

        try:
            eligibility = compute_financial_eligibility(
                db_session=db_session,
                employee_id=claim.employee_id,
                employer_id=claim.employer_id,
                employer_fein=claim.employer_fein,
                application_submitted_date=application_submitted_date,
                leave_start_date=leave_start_date,
                employment_status=employment_status,
                diff_reason_csv=diff_reason_csv,
            )
            current_eligibility = eligibility.financially_eligible
            if current_eligibility != prior_eligibility:
                new_decision = current_eligibility
                new_aww = eligibility.employer_average_weekly_wage
                result = [
                    claimaint_id,
                    time,
                    prior_eligibility,
                    new_decision,
                    old_aww,
                    new_aww,
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
    with file_util.open_stream(
        f"{base_path}/output.csv", "w"
    ) as output_csv_path, file_util.open_stream(
        f"{base_path}/diff_reason.csv", "w"
    ) as diff_reason_csv_path:
        output_csv = csv.writer(output_csv_path, lineterminator="\n")
        diff_reason_csv = csv.writer(diff_reason_csv_path, lineterminator="\n")
        output_csv.writerow(
            ["claimaint_id", "time", "previous_decision", "new_decision", "old_aww", "new_aww",]
        )
        diff_reason_csv.writerow(["employee_id", "employer_id", "leave_start_date", "reason"])
        generate_report(cli_args, db_session, output_csv, diff_reason_csv)


@background_task("evaluate_new_eligibility")
def evaluate_new_eligibility():
    cli_args = parse_args()
    with db.session_scope(db.init()) as db_session:
        main(cli_args, db_session)
