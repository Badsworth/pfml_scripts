#
# Tests for massgov.pfml.util.datetime.
#

from datetime import date, datetime, timedelta, timezone

import pytest

import massgov.pfml.util.datetime


def test_to_datetime_date():
    assert massgov.pfml.util.datetime.to_datetime(date(2020, 3, 24)) == datetime(
        2020, 3, 24, 0, 0, 0, tzinfo=timezone.utc
    )


def test_to_datetime_datetime():
    assert massgov.pfml.util.datetime.to_datetime(datetime(2020, 3, 24, 12, 15, 30)) == datetime(
        2020, 3, 24, 0, 0, 0, tzinfo=timezone.utc
    )


def test_to_datetime_datetime_with_utc():
    assert massgov.pfml.util.datetime.to_datetime(
        datetime(2020, 3, 24, 12, 15, 30, tzinfo=timezone.utc)
    ) == datetime(2020, 3, 24, 0, 0, 0, tzinfo=timezone.utc)


def test_to_datetime_datetime_with_other_timezone():
    assert massgov.pfml.util.datetime.to_datetime(
        datetime(2020, 3, 24, 12, 15, 30, tzinfo=timezone(timedelta(hours=13)))
    ) == datetime(2020, 3, 24, 0, 0, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "start, end, weeks",
    (
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 1, 11, 0, 0), 1),
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 4, 11, 0, 0), 1),
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 7, 11, 0, 0), 1),
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 8, 11, 0, 0), 2),
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 14, 11, 0, 0), 2),
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 15, 11, 0, 0), 3),
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 7, 10, 0, 0), 1),
        (datetime(2021, 1, 1, 11, 0, 0), datetime(2021, 1, 7, 12, 0, 0), 1),
        (datetime(2021, 1, 28, 11, 0, 0), datetime(2021, 2, 3, 11, 0, 0), 1),
        (datetime(2021, 1, 28, 11, 0, 0), datetime(2021, 2, 4, 11, 0, 0), 2),
        (date(2021, 1, 1), date(2021, 1, 7), 1),
        (date(2021, 1, 1), date(2021, 1, 8), 2),
        (date(2021, 1, 1), date(2021, 1, 14), 2),
        (date(2021, 1, 1), date(2021, 1, 15), 3),
        (datetime(2021, 1, 1, 11, 0, 0), date(2021, 1, 8), 2),
        (date(2021, 1, 1), datetime(2021, 1, 8, 11, 0, 0), 2),
    ),
)
def test_get_period_in_weeks(start, end, weeks):
    assert massgov.pfml.util.datetime.get_period_in_weeks(start, end) == weeks
