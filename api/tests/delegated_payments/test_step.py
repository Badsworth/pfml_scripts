import enum

import pytest
from freezegun.api import freeze_time

from massgov.pfml import db
from massgov.pfml.db.models.employees import ImportLogReportQueue
from massgov.pfml.delegated_payments.step import Step


class ExampleStep(Step):
    class Metrics(str, enum.Enum):
        METRIC_A = "metric_a"
        METRIC_B = "metric_b"

    metric_to_increment = None

    def run_step(self):
        if self.metric_to_increment:
            self.increment(self.metric_to_increment)


class ExampleErrorStep(Step):
    def run_step(self):
        raise Exception()


@pytest.mark.parametrize(
    "business_days,date_ran,found_log",
    [
        (1, "2021-12-28", True),  # Tue
        (2, "2021-12-27", True),  # Mon
        (2, "2021-12-24", True),  # Mon
        (3, "2021-12-23", True),  # Thu
        (4, "2021-12-22", True),  # Wed
        (4, "2021-12-21", False),  # Tue
        (4, "2021-12-20", False),  # Mon
    ],
)
def test_check_if_processed_within_x_days(
    local_initialize_factories_session,
    local_test_db_session,
    local_test_db_other_session,
    business_days,
    date_ran,
    found_log,
):
    metric_to_increment = "metric_a"

    with freeze_time(date_ran):
        step = ExampleStep(local_test_db_session, local_test_db_other_session)
        step.metric_to_increment = "metric_a"
        step.run()

    # Now is always the 28th
    with freeze_time("2021-12-28"):
        was_processed_within_x_days = ExampleStep.check_if_processed_within_x_days(
            local_test_db_session, metric_to_increment, business_days
        )
        assert found_log == was_processed_within_x_days


def test_add_to_report_queue__run_failed(
    initialize_factories_session,
    test_db_session: db.Session,
    test_db_other_session: db.Session,
):
    # Should not add import log report queue item when run_step fails

    example_step = ExampleErrorStep(
        test_db_session, test_db_other_session, should_add_to_report_queue=True
    )

    with pytest.raises(Exception):
        example_step.run()

    assert test_db_other_session.query(ImportLogReportQueue).count() == 0


def test_add_to_report_queue__flag_not_set(
    initialize_factories_session,
    test_db_session: db.Session,
    test_db_other_session: db.Session,
):
    example_step = ExampleStep(test_db_session, test_db_other_session)

    example_step.run()

    assert test_db_other_session.query(ImportLogReportQueue).count() == 0


def test_add_to_report_queue__flag_set(
    initialize_factories_session,
    test_db_session: db.Session,
    test_db_other_session: db.Session,
):

    example_step = ExampleStep(
        test_db_session, test_db_other_session, should_add_to_report_queue=True
    )

    example_step.run()

    report_queue_items = test_db_other_session.query(ImportLogReportQueue).all()

    assert len(report_queue_items) == 1
    assert report_queue_items[0].import_log_id == example_step.get_import_log_id()
