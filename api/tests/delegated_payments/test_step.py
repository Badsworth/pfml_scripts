import enum

import pytest
from freezegun.api import freeze_time

from massgov.pfml.delegated_payments.step import Step


class ExampleStep(Step):
    class Metrics(str, enum.Enum):
        METRIC_A = "metric_a"
        METRIC_B = "metric_b"

    metric_to_increment = None

    def run_step(self):
        if self.metric_to_increment:
            self.increment(self.metric_to_increment)


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
