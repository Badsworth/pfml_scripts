import csv
import json
import logging  # noqa: B1
import os
from collections import Counter

import pytest
import sqlalchemy
from freezegun import freeze_time

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import ImportLog, ReferenceFile, ReferenceFileType, State
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import (
    REPORTS,
    REPORTS_BY_NAME,
    ReportName,
)


@pytest.fixture
def outbound_report_path(monkeypatch, mock_s3_bucket):
    dfml_report_outbound_path = f"s3://{mock_s3_bucket}/outbound"
    monkeypatch.setenv("DFML_REPORT_OUTBOUND_PATH", dfml_report_outbound_path)
    return dfml_report_outbound_path


@pytest.fixture
def report_archive_path(monkeypatch, mock_s3_bucket):
    pfml_error_reports_archive_path = f"s3://{mock_s3_bucket}/error-reports/archive"
    monkeypatch.setenv("PFML_ERROR_REPORTS_ARCHIVE_PATH", pfml_error_reports_archive_path)
    return pfml_error_reports_archive_path


def init_step(db_session, db_other_session, report_names):
    report_names = [report.report_name for report in REPORTS]
    step = ReportStep(db_session, db_other_session, report_names=report_names)
    return step


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_report_generation(
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    outbound_report_path,
    report_archive_path,
):
    def create_employee_with_pre_note_state(first_name, last_name, pre_note_state):
        employee = EmployeeFactory.create(first_name=first_name, last_name=last_name)

        state_log_util.create_finished_state_log(
            employee, pre_note_state, state_log_util.build_outcome("test"), test_db_session,
        )

        return employee

    # setup some data
    employee_1 = create_employee_with_pre_note_state(
        "Jane", "Smith", State.DELEGATED_EFT_SEND_PRENOTE
    )
    create_employee_with_pre_note_state("John", "Smith", State.DELEGATED_EFT_PRENOTE_SENT)
    employee_3 = create_employee_with_pre_note_state(
        "Susan", "Smith", State.DELEGATED_EFT_SEND_PRENOTE
    )

    test_db_session.commit()

    step = ReportStep(test_db_session, test_db_other_session, [])
    step.generate_report(
        outbound_report_path,
        report_archive_path,
        "test-error-report",
        "select employee.employee_id, employee.first_name from employee inner join state_log on state_log.employee_id = employee.employee_id where state_log.end_state_id = 110 order by employee.first_name",
    )

    date_folder = "2021-01-15"
    timestamp_prefix = "2021-01-15-12-00-00"
    archive_folder_path = os.path.join(report_archive_path, "sent", date_folder)

    base_file_name = "test-error-report.csv"
    file_name = f"{timestamp_prefix}-{base_file_name}"

    # confirm report was generated
    assert_files(outbound_report_path, [base_file_name])
    assert_files(archive_folder_path, [file_name])

    # confirm we have a reference file for archive
    file_path = os.path.join(archive_folder_path, file_name)
    assert_report_reference_files([file_path], test_db_session)

    # confirm content of report
    reader = csv.DictReader(file_util.open_stream(file_path), delimiter=",")
    rows = [record for record in reader]

    assert len(rows) == 2

    assert rows[0]["employee_id"] == str(employee_1.employee_id)
    assert rows[0]["first_name"] == "Jane"

    assert rows[1]["employee_id"] == str(employee_3.employee_id)
    assert rows[1]["first_name"] == "Susan"


def test_report_generation_query_exception(
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    outbound_report_path,
    report_archive_path,
):
    step = ReportStep(test_db_session, test_db_other_session, [])
    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        step.generate_report(
            outbound_report_path,
            report_archive_path,
            "test-error-report",
            "select * from nonexistent_table",
        )


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_all_reports(
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    outbound_report_path,
    report_archive_path,
):
    """Validate that all reports run without any exceptions"""
    report_names = [report.value for report in ReportName]
    # Make sure every named report has report details defined.
    for report_name in report_names:
        assert REPORTS_BY_NAME.get(report_name) is not None

    step = init_step(test_db_session, test_db_other_session, report_names)
    step.run()

    # validate expected report counts
    log_report = json.loads(step.log_entry.import_log.report)
    assert log_report["report_generated_count"] == len(REPORTS)
    assert log_report.get("report_error_count") == 0

    # validate generated files
    date_folder = "2021-01-15"
    timestamp_prefix = "2021-01-15-12-00-00"

    archive_folder_path = os.path.join(report_archive_path, "sent", date_folder)

    expected_archive_files = [f"{timestamp_prefix}-{report.report_name}.csv" for report in REPORTS]
    expected_outbound_files = [f"{report.report_name}.csv" for report in REPORTS]

    assert_files(archive_folder_path, expected_archive_files)
    assert_files(outbound_report_path, expected_outbound_files)

    file_paths = [
        os.path.join(archive_folder_path, file_name) for file_name in expected_archive_files
    ]
    assert_report_reference_files(file_paths, test_db_session)


@freeze_time("2021-01-15 12:00:00", tz_offset=5)  # payments_util.get_now returns EST time
def test_invalid_and_missing_report_in_step_execution(
    test_db_session,
    test_db_other_session,
    initialize_factories_session,
    outbound_report_path,
    report_archive_path,
    caplog,
):
    caplog.set_level(logging.INFO)  # noqa: B1

    report_names = [report.report_name for report in REPORTS]
    step = init_step(test_db_session, test_db_other_session, report_names)

    invalid_report_name = ReportName.ADDRESS_ERROR_REPORT
    REPORTS_BY_NAME[invalid_report_name].sql_command = "select * from nonexistent_table"

    missing_report_name = ReportName.DAILY_CASH_REPORT
    REPORTS_BY_NAME[missing_report_name] = None

    with pytest.raises(
        Exception,
        match=f"Expected reports do not match generated reports - expected: {len(REPORTS)}, generated: {len(REPORTS)-2}",
    ):
        step.run()

    # validate expected report counts
    import_log = test_db_other_session.query(ImportLog).one_or_none()
    log_report = json.loads(import_log.report)
    assert log_report["report_generated_count"] == len(REPORTS) - 2
    assert log_report["report_error_count"] == 2

    # validate error messages
    log_with_counts = Counter(record.message for record in caplog.records)

    invalid_report_message = f"Error generating report: {invalid_report_name}"
    assert log_with_counts[invalid_report_message] == 1

    missing_report_message = f"Could not find configuration for report: {missing_report_name}"
    assert log_with_counts[missing_report_message] == 1


def assert_files(folder_path, expected_files):
    files_in_folder = file_util.list_files(folder_path)
    for expected_file in expected_files:
        assert expected_file in files_in_folder


def assert_report_reference_files(file_paths, db_session):
    assert len(
        db_session.query(ReferenceFile)
        .filter(
            ReferenceFile.file_location.in_(file_paths),
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DELEGATED_PAYMENT_REPORT_FILE.reference_file_type_id,
        )
        .all()
    ) == len(file_paths)
