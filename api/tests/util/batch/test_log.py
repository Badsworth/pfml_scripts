#
# Tests for massgov.pfml.util.batch.log.
#

import dataclasses
import datetime
import json

import freezegun
import pytest

import massgov.pfml.util.batch.log
from massgov.pfml import db
from massgov.pfml.db.models.factories import ImportLogFactory


@dataclasses.dataclass
class MockReport:
    something_name: str = ""
    total_count: int = 0


@freezegun.freeze_time("2020-11-20 21:00:01", tz_offset=0)
def test_create_import_log_entry(test_db_session):
    report = MockReport(something_name="abc")

    entry = massgov.pfml.util.batch.log.create_log_entry(
        test_db_session, __name__, "Special", "weekly", report
    )

    assert entry.import_log_id is not None
    assert entry.source == "Special"
    assert entry.import_type == "weekly"
    assert entry.status == "in progress"
    assert (
        entry.report
        == """{
  "something_name": "abc",
  "total_count": 0
}"""
    )
    assert entry.start == datetime.datetime(2020, 11, 20, 21, 0, 1, tzinfo=datetime.timezone.utc)
    assert entry.end is None


@freezegun.freeze_time("2020-11-20 21:00:01", tz_offset=0, auto_tick_seconds=10)
def test_update_import_log_entry(test_db_session):
    report = MockReport(something_name="abc")

    entry = massgov.pfml.util.batch.log.create_log_entry(
        test_db_session, __name__, "Special", "weekly", report
    )

    report.total_count = 123456

    massgov.pfml.util.batch.log.update_log_entry(test_db_session, entry, "success", report)

    assert entry.import_log_id is not None
    assert entry.source == "Special"
    assert entry.import_type == "weekly"
    assert entry.status == "success"
    assert (
        entry.report
        == """{
  "something_name": "abc",
  "total_count": 123456
}"""
    )
    assert entry.start == datetime.datetime(2020, 11, 20, 21, 0, 1, tzinfo=datetime.timezone.utc)

    # import_log.start and import_log.created_at will ask for the current time, so two calls,
    # each increments 10 seconds via the auto_tick_seconds setting, meaning the third call setting
    # import_log.end will be 20 seconds more than the first.
    assert entry.end == datetime.datetime(2020, 11, 20, 21, 0, 21, tzinfo=datetime.timezone.utc)


def test_latest_import_log_for_metric__source_doesnt_exist(
    test_db_session: db.Session, initialize_factories_session
):
    source = "some_source"
    metrics = dict()
    report_str = json.dumps(metrics, indent=2)
    ImportLogFactory.create(source=source, report=report_str)

    found_import_log = massgov.pfml.util.batch.log.latest_import_log_for_metric(
        test_db_session, "other_source", "some_metric"
    )

    assert found_import_log is None


def test_latest_import_log_for_metric__import_metric_doesnt_exist_for_source(
    test_db_session: db.Session, initialize_factories_session
):
    source = "some_source"
    metrics = dict()
    test_metric = "some_metric"
    metrics[test_metric] = 1
    report_str = json.dumps(metrics, indent=2)
    ImportLogFactory.create(source=source, report=report_str)

    found_import_log = massgov.pfml.util.batch.log.latest_import_log_for_metric(
        test_db_session, source, "some_other_metric"
    )

    assert found_import_log is None


def test_latest_import_log_for_metric__import_metric_is_0(
    test_db_session: db.Session, initialize_factories_session
):
    source = "some_source"
    metrics = dict()
    test_metric = "some_metric"
    metrics[test_metric] = 0
    report_str = json.dumps(metrics, indent=2)
    ImportLogFactory.create(source=source, report=report_str)

    found_import_log = massgov.pfml.util.batch.log.latest_import_log_for_metric(
        test_db_session, source, test_metric
    )

    assert found_import_log is None


@pytest.mark.parametrize("test_metric", ["some_metric"])
@pytest.mark.parametrize("metric_count", [1, 10, 100, 1234])
def test_latest_import_log_for_metric(
    test_db_session: db.Session, initialize_factories_session, test_metric: str, metric_count: int
):
    source = "some_source"
    metrics = dict()
    metrics[test_metric] = metric_count
    report_str = json.dumps(metrics, indent=2)
    created_log = ImportLogFactory.create(source=source, report=report_str)

    found_import_log = massgov.pfml.util.batch.log.latest_import_log_for_metric(
        test_db_session, source, test_metric
    )

    assert found_import_log is not None
    assert found_import_log.import_log_id == created_log.import_log_id


def test_latest_import_log_for_metric__multiple(
    test_db_session: db.Session, initialize_factories_session
):
    source = "some_source"
    metrics = dict()
    test_metric = "some_metric"
    metrics[test_metric] = 1
    report_str = json.dumps(metrics, indent=2)

    ImportLogFactory.create(source=source, report=report_str)
    ImportLogFactory.create(source=source, report=report_str)
    created_log_3 = ImportLogFactory.create(source=source, report=report_str)

    found_import_log = massgov.pfml.util.batch.log.latest_import_log_for_metric(
        test_db_session, source, test_metric
    )

    assert found_import_log is not None
    assert found_import_log.import_log_id == created_log_3.import_log_id
