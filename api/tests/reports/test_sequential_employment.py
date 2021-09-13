import os
from datetime import date, timedelta
from typing import List

import boto3
import pytest

from massgov.pfml.db.models.employees import Employee, Employer
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.report.sequential_employment import (
    base_query,
    create_report,
    get_scenario_groups,
    multiple_employers,
    non_zero_wages_between_quarters,
)
from massgov.pfml.util.datetime.quarter import Quarter

WAGES_1_QUARTER_AGO = [1000, 0, 0, 0]
WAGES_2_QUARTERS_AGO = [0, 1000, 0, 0]
WAGES_3_QUARTERS_AGO = [0, 0, 1000, 0]
WAGES_3_QUARTERS_AGO = [0, 0, 0, 1000]

LAST_2_QUARTERS_WAGES = [1000, 1000, 0, 0]
LAST_4_QUARTERS_WAGES = [1000, 1000, 1000, 1000]
WAGES_3_AND_4_QUARTERS_AGO = [0, 0, 1000, 1000]

pytestmark = pytest.mark.integration


def generate_prev_4_quarters_wages(employee: Employee, employer: Employer, wages_list: List[int]):
    """
    Generate wage data going back 4 quarters before the current quarter.
    """
    previous_quarter = Quarter.from_date(date.today()).previous_quarter()
    previous_4_quarters = [qtr for qtr in previous_quarter.series_backwards(4)]
    for idx, qtr in enumerate(previous_4_quarters):
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=employer,
            filing_period=qtr.as_date(),
            employee_qtr_wages=wages_list[idx],
        )


def test_base_query(initialize_factories_session, test_db_session):
    employer1, employer2, employer3 = [EmployerFactory.create() for _ in range(3)]

    employee, employee2, employee3, employee4, employee5 = [
        EmployeeFactory.create() for _ in range(5)
    ]

    # Employee 1 - has wage data for only 2 prior quarters with 2 employers - Expect returned
    generate_prev_4_quarters_wages(employee, employer1, LAST_2_QUARTERS_WAGES)
    generate_prev_4_quarters_wages(employee, employer2, LAST_2_QUARTERS_WAGES)

    # Employee 2 - has wage data for last 4 quarters with one employer, last 2 quarters with another - Not returned by query
    generate_prev_4_quarters_wages(employee2, employer3, LAST_2_QUARTERS_WAGES)
    generate_prev_4_quarters_wages(employee2, employer2, LAST_4_QUARTERS_WAGES)

    # Employee 3 - has wage data from 1 employer for only prior 2 quarters - other employer has reported zero dollar wages - Not returned
    generate_prev_4_quarters_wages(employee3, employer1, LAST_2_QUARTERS_WAGES)
    generate_prev_4_quarters_wages(employee3, employer2, [0, 0, 0, 0])

    # Employee 4 - has wage data from multiple employers 3 and 4 quarters ago - Not returned
    generate_prev_4_quarters_wages(employee4, employer3, WAGES_3_AND_4_QUARTERS_AGO)
    generate_prev_4_quarters_wages(employee4, employer2, WAGES_3_AND_4_QUARTERS_AGO)

    # Employee 5 - has wage data one employer for last 2 quarters and another from the current quarter and 2 years ago
    generate_prev_4_quarters_wages(employee5, employer3, LAST_2_QUARTERS_WAGES)
    WagesAndContributionsFactory.create(
        employee=employee5,
        employer=employer3,
        filing_period=date.today() - timedelta(days=365),
        employee_qtr_wages=1000,
    )
    WagesAndContributionsFactory.create(
        employee=employee5, employer=employer3, filing_period=date.today(), employee_qtr_wages=1000,
    )

    res = base_query(test_db_session).all()

    assert len(res) == 1
    assert res[0].employee_id == employee.employee_id


def test_multiple_employers(initialize_factories_session, test_db_session):
    employee, employee2, employee3 = [EmployeeFactory.create() for _ in range(3)]

    employer1, employer2, employer3 = [EmployerFactory.create() for _ in range(3)]

    previous_quarter = Quarter.from_date(date.today()).previous_quarter()
    two_quarters_ago = previous_quarter.previous_quarter().start_date()
    previous_quarter = previous_quarter.as_date()

    WagesAndContributionsFactory.create(
        employee=employee, employer=employer1, filing_period=previous_quarter
    )

    WagesAndContributionsFactory.create(
        employee=employee, employer=employer2, filing_period=two_quarters_ago
    )

    WagesAndContributionsFactory.create(
        employee=employee2, employer=employer2, filing_period=previous_quarter
    )

    # Filing period today - current quarter. Ignored
    WagesAndContributionsFactory.create(employee=employee, employer=employer3)

    five_quarters_ago = Quarter.from_date(date.today()).subtract_quarters(3).as_date()
    # Filing period older than previous two quarters. Ignored
    WagesAndContributionsFactory.create(
        employee=employee, employer=employer3, filing_period=five_quarters_ago
    )

    # Not returned - one of two employers has filed with only zero dollar wages, which do not count.
    WagesAndContributionsFactory.create(
        employee=employee3, employer=employer1, filing_period=previous_quarter
    )

    WagesAndContributionsFactory.create(
        employee=employee3, employer=employer2, filing_period=previous_quarter, employee_qtr_wages=0
    )

    res = test_db_session.query(multiple_employers(test_db_session)).all()

    assert len(res) == 1
    assert res[0].employee_id == employee.employee_id
    assert res[0].employer_count == 2


def test_non_zero_wages_between_quarters_query(initialize_factories_session, test_db_session):
    employee, employee2 = [EmployeeFactory.create() for _ in range(2)]

    employer1 = EmployerFactory.create()

    generate_prev_4_quarters_wages(employee, employer1, WAGES_2_QUARTERS_AGO)
    generate_prev_4_quarters_wages(employee2, employer1, WAGES_3_AND_4_QUARTERS_AGO)

    res = test_db_session.query(non_zero_wages_between_quarters(test_db_session, 2, 1)).all()

    assert len(res) == 1
    assert res[0].employee_id == employee.employee_id

    # --- Ensure the function can handle a single quarter ---

    res = test_db_session.query(non_zero_wages_between_quarters(test_db_session, 1, 1)).all()
    # Neither employee has wages from the previous quarter
    assert len(res) == 0

    res = test_db_session.query(non_zero_wages_between_quarters(test_db_session, 2, 2)).all()

    # Only the first employee has wages from the second most recent quarter
    assert len(res) == 1
    assert res[0].employee_id == employee.employee_id


def _setup_scenarios(employees, employers):
    employer1, employer2 = employers

    # SCENARIO 1 group - has wage data for only 1 of 2 previous quarters with 2 employers
    # Employee 1
    generate_prev_4_quarters_wages(employees[0], employer1, WAGES_1_QUARTER_AGO)
    generate_prev_4_quarters_wages(employees[0], employer2, WAGES_1_QUARTER_AGO)

    # Employee 2
    generate_prev_4_quarters_wages(employees[1], employer1, WAGES_2_QUARTERS_AGO)
    generate_prev_4_quarters_wages(employees[1], employer2, WAGES_2_QUARTERS_AGO)

    # SCENARIO 2 group - wage data for both of the 2 previous quarters with 2 employers
    # Employee 3
    generate_prev_4_quarters_wages(employees[2], employer1, LAST_2_QUARTERS_WAGES)
    generate_prev_4_quarters_wages(employees[2], employer2, LAST_2_QUARTERS_WAGES)

    # Employee 4
    generate_prev_4_quarters_wages(employees[3], employer1, WAGES_1_QUARTER_AGO)
    generate_prev_4_quarters_wages(employees[3], employer2, WAGES_2_QUARTERS_AGO)

    # Employee 5
    generate_prev_4_quarters_wages(employees[4], employer1, LAST_2_QUARTERS_WAGES)
    generate_prev_4_quarters_wages(employees[4], employer2, WAGES_2_QUARTERS_AGO)

    # NOT RETURNED GROUP - does not match base criteria
    # Employee 6 - has wages 3 quarters ago - excluded
    generate_prev_4_quarters_wages(employees[5], employer1, WAGES_2_QUARTERS_AGO)
    generate_prev_4_quarters_wages(employees[5], employer2, WAGES_3_QUARTERS_AGO)

    # Employee 7 - has wages for last 4 quarters - excluded
    generate_prev_4_quarters_wages(employees[6], employer1, LAST_4_QUARTERS_WAGES)
    generate_prev_4_quarters_wages(employees[6], employer2, WAGES_1_QUARTER_AGO)

    # Employee 8 - has multiple employers but not in the last 4 quarters
    generate_prev_4_quarters_wages(employees[6], employer1, LAST_4_QUARTERS_WAGES)
    generate_prev_4_quarters_wages(employees[6], employer2, WAGES_1_QUARTER_AGO)


def test_get_scenario_groups(initialize_factories_session, test_db_session):
    employers = [EmployerFactory.create() for _ in range(2)]

    # Track employees by their index in this array
    employees = [EmployeeFactory.create() for _ in range(7)]

    _setup_scenarios(employees, employers)

    expected_scenario1_matches = {e.employee_id for e in employees[:2]}
    expected_scenario2_matches = {e.employee_id for e in employees[2:5]}
    expected_not_returned = {e.employee_id for e in employees[5:]}

    assert len(expected_scenario1_matches) + len(expected_scenario2_matches) + len(
        expected_not_returned
    ) == len(employees)

    scenario1_group, scenario2_group = get_scenario_groups(test_db_session)

    assert scenario1_group == expected_scenario1_matches
    assert scenario2_group == expected_scenario2_matches
    assert scenario1_group.isdisjoint(scenario2_group)
    # Test that expected_not_returned is equal to the list of employees minus the contents of both scenarios
    assert expected_not_returned == {e.employee_id for e in employees} - (
        scenario1_group ^ scenario2_group
    )


@pytest.fixture
def expected_csv():
    """
    The fixture file needs to be encoded with \r\n for newline characters.
    Saving the file in vscode will ruin this encoding and cause the test to fail.
    """
    return open(
        os.path.join(os.path.dirname(__file__), "test_files", "sequential_employment.csv"), "rb",
    ).read()


def test_create_report(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session, expected_csv
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "reports/sequential_employment/"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("ENVIRONMENT", "test")

    employers = [EmployerFactory.create() for _ in range(2)]

    # Track employees by their index in this array
    employees = [EmployeeFactory.create() for _ in range(8)]

    _setup_scenarios(employees, employers)

    # Create 4 claims unrelated to any of our employees
    [ClaimFactory.create() for _ in range(4)]

    # Create 3 claims attached to our employees
    [ClaimFactory.create(employee=e) for e in employees[:4]]

    create_report(test_db_session)

    s3 = boto3.client("s3")
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]

    assert object_list
    assert len(object_list) == 1

    dest_filepath_prefix = os.path.join(dest_dir, "test/")
    assert object_list[0]["Key"].startswith(dest_filepath_prefix)

    uploaded_csv = s3.get_object(Bucket=mock_s3_bucket, Key=object_list[0]["Key"])["Body"].read()

    assert uploaded_csv == expected_csv
