import json
import uuid
from datetime import date, datetime

import pytest
from sqlalchemy.orm.exc import NoResultFound

import massgov.pfml.dor.importer.lib.dor_persistence_util as util
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.dor.importer.import_dor import ImportReport

# every test in here requires real resources
pytestmark = pytest.mark.integration

sample_employee_file = "DORDFML_20200519120622"
sample_employer_file = "DORDFMLEMP_20200519120622"

# === test helper functions empty returns and exception raises ===


def test_get_wages_and_contributions_by_employee_ids(test_db_session, initialize_factories_session):
    empty_wages = util.get_wages_and_contributions_by_employee_ids(test_db_session, [])
    assert len(empty_wages) == 0

    employer = EmployerFactory.create()
    employee1 = EmployeeFactory.create()
    employee2 = EmployeeFactory.create()
    WagesAndContributionsFactory.create(
        employee=employee1, employer=employer, filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee1, employer=employer, filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee2, employer=employer, filing_period=date(2020, 9, 30),
    )
    wages = util.get_wages_and_contributions_by_employee_ids(
        test_db_session, [employee1.employee_id, employee2.employee_id]
    )
    assert len(wages) == 3


def test_get_wages_and_contributions_by_employee_id_and_filling_period(test_db_session):
    wage_row = util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, uuid.uuid4(), uuid.uuid4(), date.today()
    )

    assert wage_row is None


def test_get_employer_by_fein(test_db_session):
    employer_row = util.get_employer_by_fein(test_db_session, "00-000000000")

    assert employer_row is None


def test_get_employer_address(test_db_session):
    with pytest.raises(NoResultFound):
        util.get_employer_address(test_db_session, uuid.uuid4())


def test_get_address(test_db_session):
    with pytest.raises(NoResultFound):
        util.get_address(test_db_session, uuid.uuid4())


def test_create_import_log_entry(test_db_session):
    report = ImportReport(
        start=datetime.now().isoformat(),
        employee_file=sample_employee_file,
        employer_file=sample_employer_file,
    )

    report_log_entry = util.create_import_log_entry(test_db_session, report)
    assert report_log_entry.import_log_id is not None


def test_update_import_log_entry(test_db_session):
    report = ImportReport(
        start=datetime.now().isoformat(),
        employee_file=sample_employee_file,
        employer_file=sample_employer_file,
    )

    report_log_entry = util.create_import_log_entry(test_db_session, report)

    report.parsed_employers_info_count = 2
    report.parsed_employees_info_count = 3
    report.end = datetime.now().isoformat()

    updated_report_log_entry = util.update_import_log_entry(
        test_db_session, report_log_entry, report
    )
    persisted_report = json.loads(updated_report_log_entry.report)
    assert updated_report_log_entry.import_log_id == report_log_entry.import_log_id
    assert updated_report_log_entry.start == report_log_entry.start
    assert updated_report_log_entry.end == report_log_entry.end
    assert persisted_report["parsed_employers_count"] == report.parsed_employers_count
    assert persisted_report["parsed_employees_info_count"] == report.parsed_employees_info_count
