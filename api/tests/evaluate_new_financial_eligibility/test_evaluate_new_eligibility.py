import os
from dataclasses import dataclass
from datetime import date

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
        historical_len: int = 0
        s3_bucket: str = s3_bucket_uri

    return CliArgs()


@pytest.mark.integration
def test_full_generate_evaluate_new_eligibility(
    test_db_session, initialize_factories_session, monkeypatch, cli_args, mock_s3_bucket
):
    s3_bucket_uri = f"s3://{mock_s3_bucket}/"
    monkeypatch.setenv("S3_EXPORT_BUCKET", s3_bucket_uri)
    employer = EmployerFactory.create(employer_fein="999999999")
    employer2 = EmployerFactory.create(employer_fein="553897622")

    claim = ClaimFactory.create(
        employer_id=employer.employer_id, absence_period_start_date="2021-08-05"
    )
    WagesAndContributionsFactory.create(
        employee=claim.employee,
        employer=employer,
        filing_period=date(2020, 5, 1),
        employee_qtr_wages=1,
    )
    WagesAndContributionsFactory.create(
        employee=claim.employee,
        employer=employer2,
        filing_period=date(2020, 5, 1),
        employee_qtr_wages=0,
    )

    def mock_new_relic(len):
        return [
            {
                "leave_start_date": date.fromisoformat("2021-08-05"),
                "employment_status": "Employed",
                "application_submitted_date": "2021-08-31",
                "request_id": "123",
                "@ptr": "123",
                "employee_id": str(claim.employee_id),
                "employer_id": str(employer.employer_id),
                "employer_average_weekly_wage": "100",
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
    assert len(object_list) == 2

    output_csv_is_first = object_list[0]["Key"].endswith("/output.csv")
    output_csv_path = object_list[0]["Key"] if output_csv_is_first else object_list[1]
    diff_csv_path = object_list[1]["Key"] if output_csv_is_first else object_list[0]

    output_csv = s3.get_object(Bucket=mock_s3_bucket, Key=output_csv_path["Key"])
    diff_csv = s3.get_object(Bucket=mock_s3_bucket, Key=diff_csv_path["Key"])
    output_csv_str = output_csv["Body"].read().decode("utf-8")
    diff_csv_str = diff_csv["Body"].read().decode("utf-8")

    assert (
        output_csv_str
        == f"claimaint_id,time,previous_decision,new_decision,old_aww,new_aww\n{claim.employee_id},2021-08-31,True,False,100,0.08\n"
    )
    assert (
        diff_csv_str
        == f"employee_id,employer_id,leave_start_date,reason\n{claim.employee_id},{employer2.employer_id},,zero_wage\n{claim.employee_id},{employer.employer_id},2021-08-05,multiple_employers\n"
    )


@pytest.mark.integration
def test_full_generate_evaluate_new_eligibility_missing_data(
    test_db_session, initialize_factories_session, monkeypatch, cli_args, mock_s3_bucket
):
    s3_bucket_uri = f"s3://{mock_s3_bucket}/"
    monkeypatch.setenv("S3_EXPORT_BUCKET", s3_bucket_uri)

    employer = EmployerFactory.create(employer_fein="813648030")
    claim = ClaimFactory.create(
        employer_id=employer.employer_id, absence_period_start_date="2021-08-05"
    )
    WagesAndContributionsFactory.create(
        employee=claim.employee,
        employer=employer,
        filing_period=date(2020, 5, 1),
        employee_qtr_wages=0,
    )

    def mock_new_relic(len):
        return [
            {
                "leave_start_date": date.fromisoformat("2021-08-05"),
                "application_submitted_date": "2021-08-31",
                "request_id": "123",
                "@ptr": "123",
                "employee_id": str(claim.employee_id),
                "employer_id": str(employer.employer_id),
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
    assert len(object_list) == 2

    output_csv_is_first = object_list[0]["Key"].endswith("/output.csv")
    output_csv_path = object_list[0]["Key"] if output_csv_is_first else object_list[1]
    diff_csv_path = object_list[1]["Key"] if output_csv_is_first else object_list[0]

    output_csv = s3.get_object(Bucket=mock_s3_bucket, Key=output_csv_path["Key"])
    diff_csv = s3.get_object(Bucket=mock_s3_bucket, Key=diff_csv_path["Key"])
    output_csv_str = output_csv["Body"].read().decode("utf-8")
    diff_csv_str = diff_csv["Body"].read().decode("utf-8")

    assert (
        output_csv_str
        == f"claimaint_id,time,previous_decision,new_decision,old_aww,new_aww\n{claim.employee_id},2021-08-31,True,False,,0\n"
    )
    assert (
        diff_csv_str
        == f"employee_id,employer_id,leave_start_date,reason\n{claim.employee_id},{employer.employer_id},,zero_wage\n"
    )
