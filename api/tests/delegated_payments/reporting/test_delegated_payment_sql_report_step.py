from typing import Any
from unittest import mock

import pytest

from massgov.pfml import db
from massgov.pfml.db.models.employees import ImportLog, ImportLogReportQueue
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_report_step import ReportStep
from massgov.pfml.delegated_payments.reporting.delegated_payment_sql_reports import REPORT_NAMES
from massgov.pfml.delegated_payments.step import Step


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


def create_import_log_with_report_queue_item(db_session: db.Session, **import_log_kwargs: Any):
    import_log = ImportLog(**import_log_kwargs)
    import_log.report_queue_item = ImportLogReportQueue()
    db_session.add(import_log)
    return import_log


class ExampleStepA(Step):
    pass


class ExampleStepB(Step):
    pass


class ExampleStepC(Step):
    pass


class ExampleStepD(Step):
    pass


def test_clear_sources_from_report_queue__should_not_clear_when_sources_empty(
    outbound_report_path,
    report_archive_path,
    test_db_session: db.Session,
    test_db_other_session: db.Session,
):
    source = ExampleStepA.__name__
    import_logs = [
        create_import_log_with_report_queue_item(test_db_other_session, source=source)
        for _ in range(5)
    ]

    report_step = ReportStep(test_db_session, test_db_other_session, report_names=REPORT_NAMES)
    report_step.run()

    # All queue items should be present
    assert (
        test_db_other_session.query(ImportLogReportQueue)
        .join(ImportLog)
        .filter(ImportLog.source == source)
        .count()
    ) == len(import_logs)


def test_clear_sources_from_report_queue__should_not_clear_when_error_in_run_step(
    outbound_report_path,
    report_archive_path,
    test_db_session: db.Session,
    test_db_other_session: db.Session,
):
    source = ExampleStepA.__name__
    import_logs = [
        create_import_log_with_report_queue_item(test_db_other_session, source=source)
        for _ in range(5)
    ]

    # Sources to clear list matches the source above
    report_step = ReportStep(
        test_db_session,
        test_db_other_session,
        report_names=REPORT_NAMES,
        sources_to_clear_from_report_queue=[ExampleStepA],
    )

    # Force an exception
    report_step.generate_report = mock.Mock(side_effect=Exception)

    with pytest.raises(Exception):
        report_step.run()

    # All queue items should be present
    assert (
        test_db_other_session.query(ImportLogReportQueue)
        .join(ImportLog)
        .filter(ImportLog.source == source)
        .count()
    ) == len(import_logs)


def test_clear_sources_from_report_queue__clear_specified_items_when_run_step_successful(
    outbound_report_path,
    report_archive_path,
    test_db_session: db.Session,
    test_db_other_session: db.Session,
):
    # This test demonstrates that the queue items removed
    # specifically relate to the sources to clear from report queue list

    # Sources that should be removed after processing report
    source_steps_to_clear = [ExampleStepA, ExampleStepB]

    # Source that should remain after processing report
    extra_source_steps = [ExampleStepC, ExampleStepD]

    # Create import log data for each of the source steps
    for source_step in source_steps_to_clear + extra_source_steps:
        for _ in range(5):
            create_import_log_with_report_queue_item(
                test_db_other_session, source=source_step.__name__
            )

    extra_report_queue_items = (
        test_db_other_session.query(ImportLogReportQueue)
        .join(ImportLog)
        .filter(ImportLog.source.in_([source_step.__name__ for source_step in extra_source_steps]))
    ).all()
    assert len(extra_report_queue_items) == 10

    # Provide the report step with sources to clear ExampleStepA and ExampleStepB
    report_step = ReportStep(
        test_db_session,
        test_db_other_session,
        report_names=REPORT_NAMES,
        sources_to_clear_from_report_queue=source_steps_to_clear,
    )

    report_step.run()

    # Ensure that the remaining items are only from the extra sources
    report_queue_items_remaining = (
        test_db_other_session.query(ImportLogReportQueue).join(ImportLog).all()
    )
    assert len(report_queue_items_remaining) == len(extra_report_queue_items)
    assert report_queue_items_remaining == extra_report_queue_items
