import os
from dataclasses import dataclass
from datetime import date, datetime

import boto3
import pytest

import massgov.pfml.evaluate_new_eligibility.report as new_eligiblity
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)


@pytest.fixture
def cli_args(tmpdir, mock_s3_bucket):
    s3_bucket_uri = "s3://" + mock_s3_bucket

    @dataclass
    class CliArgs:
        start_date = datetime.today()
        end_date = datetime.today()
        s3_bucket: str = s3_bucket_uri

    return CliArgs()


def test_full_generate_evaluate_new_eligibility(
    test_db_session, initialize_factories_session, monkeypatch, cli_args, mock_s3_bucket
):
    s3_bucket_uri = f"s3://{mock_s3_bucket}/"
    monkeypatch.setenv("S3_EXPORT_BUCKET", s3_bucket_uri)
    employer = EmployerFactory.create(employer_fein="999999999")

    claim = ClaimFactory.create(
        employer_id=employer.employer_id, absence_period_start_date="2022-01-15"
    )
    WagesAndContributionsFactory.create(
        employee=claim.employee,
        employer=employer,
        filing_period=date(2021, 11, 1),
        employee_qtr_wages=5500,
    )

    def mock_new_relic(start_date, end_date):
        return [
            {
                "leave_start_date": "2022-01-15",
                "employment_status": "Employed",
                "application_submitted_date": "2021-11-30",
                "request_id": "123",
                "@ptr": "123",
                "employee_id": str(claim.employee_id),
                "employer_id": str(employer.employer_id),
                "employer_average_weekly_wage": "1000",
                "created": "1630407922.167176",
                "description": "Financially eligible",
                "financially_eligible": "True",
                "@timestamp": "2021-08-03 11:05:22.167",
            }
        ]

    monkeypatch.setattr(new_eligiblity, "pull_data_from_cloudwatch", mock_new_relic)
    monkeypatch.setattr(new_eligiblity, "parse_args", lambda x: None)

    # generate the files
    new_eligiblity.main(cli_args, test_db_session)
    s3 = boto3.client("s3")
    dest_dir = f"financial_eligibility/{os.getenv('ENVIRONMENT')}/"
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert len(object_list) == 1

    output_csv_path = object_list[0]["Key"]
    output_csv = s3.get_object(Bucket=mock_s3_bucket, Key=output_csv_path)
    output_csv_str = output_csv["Body"].read().decode("utf-8")

    assert (
        output_csv_str
        == f"claimaint_id,application_submitted_date,leave_start_date,previous_decision,previous_description,new_decision,new_description,total_wages\n{claim.employee_id},2021-11-30,2022-01-15,True,Financially eligible,False,Claimant wages under minimum,5500\n"
    )
