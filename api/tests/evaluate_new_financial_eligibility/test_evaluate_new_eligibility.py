import os
from dataclasses import dataclass
from datetime import date

import pytest

import massgov.pfml.evaluate_new_eligibility.report as new_eligiblity
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)


@pytest.fixture
def cli_args(tmpdir):
    @dataclass
    class CliArgs:
        historical_len: int = 0
        s3_output_reason_for_difference: None = None
        s3_output_different_result: None = None
        s3_bucket: None = None
        save_path = tmpdir

    return CliArgs()


@pytest.mark.integration
def test_full_generate_evaluate_new_eligibility(
    test_db_session, initialize_factories_session, monkeypatch, cli_args,
):
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
    monkeypatch.setattr(new_eligiblity, "upload_csvs", lambda x, y, z: None)

    # generate the files
    new_eligiblity.main(cli_args, test_db_session)

    for filename in ["reason_for_difference.csv", "diff_eligibility_results.csv"]:
        assert filename in os.listdir(cli_args.save_path)

    with open(cli_args.save_path / "reason_for_difference.csv") as reason_diff_file:
        file_lines = reason_diff_file.read()
        assert (
            file_lines
            == f"{claim.employee_id},{employer2.employer_id},,zero_wage\n{claim.employee_id},{employer.employer_id},2021-08-05,multiple_employers\n"
        )
    with open(cli_args.save_path / "diff_eligibility_results.csv") as diff_eligibility_file:
        file_lines = diff_eligibility_file.read()
        assert (
            file_lines
            == f"claimaint_id,time,previous_decision,new_decision,old_aww,new_aww\n{claim.employee_id},2021-08-31,True,False,100,0.08\n"
        )


@pytest.mark.integration
def test_full_generate_evaluate_new_eligibility_missing_data(
    test_db_session, initialize_factories_session, monkeypatch, cli_args,
):
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
    monkeypatch.setattr(new_eligiblity, "upload_csvs", lambda x, y, z: None)

    # generate the files
    new_eligiblity.main(cli_args, test_db_session)

    for filename in ["reason_for_difference.csv", "diff_eligibility_results.csv"]:
        assert filename in os.listdir(cli_args.save_path)

    with open(cli_args.save_path / "reason_for_difference.csv") as reason_diff_file:
        file_lines = reason_diff_file.read()
        assert file_lines == f"{claim.employee_id},{employer.employer_id},,zero_wage\n"
    with open(cli_args.save_path / "diff_eligibility_results.csv") as diff_eligibility_file:
        file_lines = diff_eligibility_file.read()
        assert (
            file_lines
            == f"claimaint_id,time,previous_decision,new_decision,old_aww,new_aww\n{claim.employee_id},2021-08-31,True,False,,0\n"
        )
