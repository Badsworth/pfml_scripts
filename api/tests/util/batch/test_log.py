#
# Tests for massgov.pfml.util.batch.log.
#

import dataclasses
import datetime

import freezegun

import massgov.pfml.util.batch.log


@dataclasses.dataclass
class MockReport:
    something_name: str = ""
    total_count: int = 0


@freezegun.freeze_time("2020-11-20 21:00:01", tz_offset=0)
def test_create_import_log_entry(test_db_session):
    report = MockReport(something_name="abc")

    entry = massgov.pfml.util.batch.log.create_log_entry(
        test_db_session, "Special", "weekly", report
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
        test_db_session, "Special", "weekly", report
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
    assert entry.end == datetime.datetime(2020, 11, 20, 21, 0, 11, tzinfo=datetime.timezone.utc)
