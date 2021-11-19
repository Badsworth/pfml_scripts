import os

import pytest

from massgov.pfml.db.models.employees import Employee, Gender
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.dua.gender_backfill import backfill_employee_gender
from massgov.pfml.util.batch.log import LogEntry
from massgov.pfml.util.csv import CSVSourceWrapper


def get_mock_data():
    return CSVSourceWrapper(
        os.path.join(os.path.dirname(__file__), "test_files", "test_gender_backfill_data.csv")
    )


@pytest.fixture
def add_test_employees(initialize_factories_session):
    return [
        EmployeeFactory.create(fineos_customer_number="1234567"),
        EmployeeFactory.create(fineos_customer_number="7654321"),
        EmployeeFactory.create(fineos_customer_number="1111111"),
        EmployeeFactory.create(fineos_customer_number="2222222", gender_id=Gender.WOMAN.gender_id),
        EmployeeFactory.create(fineos_customer_number="3333333"),
        EmployeeFactory.create(fineos_customer_number="4444444"),
        EmployeeFactory.create(fineos_customer_number="5555555"),
        EmployeeFactory.create(fineos_customer_number="6666666"),
        EmployeeFactory.create(fineos_customer_number="7777777"),
    ]


def test_update_employee_demographics(test_db_session, add_test_employees):
    with LogEntry(test_db_session, "test log entry") as log_entry:
        for row in get_mock_data():
            backfill_employee_gender(test_db_session, log_entry, row)

        metrics = log_entry.metrics

        # 10 rows in the file (not counting headers)
        assert metrics["employees_total_count"] == 11

        # 2 claimants in the CSV show up on multiple rows + 1 already has a gender value in our DB
        assert metrics["dua_no_gender_count"] == 1

        # 1 claimant in the CSV has the wrong value
        assert metrics["dua_invalid_gender_count"] == 1

        # one of the records to update shows an invalid "X" for gender in the CSV
        assert metrics["employees_updated_count"] == 6

        # skipped 2 duplicate rows and one that already has a gender value so won't be found
        assert metrics["employees_not_found_or_skipped_count"] == 3

        emp444 = (
            test_db_session.query(Employee)
            .filter(Employee.fineos_customer_number == "4444444")
            .one_or_none()
        )
        assert emp444
        # the SECOND row that has this user says "male" which should be ignored
        assert emp444.gender_id == Gender.WOMAN.gender_id

        emp666 = (
            test_db_session.query(Employee)
            .filter(Employee.fineos_customer_number == "6666666")
            .one_or_none()
        )
        assert emp666
        # "6666666" in the CSV had an invalid "X" gender which should be ignored
        assert emp666.gender_id is None
