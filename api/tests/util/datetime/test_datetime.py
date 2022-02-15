#
# Tests for massgov.pfml.util.datetime.
#

from datetime import date, datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

import massgov.pfml.util.datetime as datetime_util


def test_to_datetime_date():
    assert datetime_util.to_datetime(date(2020, 3, 24)) == datetime(
        2020, 3, 24, 0, 0, 0, tzinfo=timezone.utc
    )


def test_to_datetime_datetime():
    assert datetime_util.to_datetime(datetime(2020, 3, 24, 12, 15, 30)) == datetime(
        2020, 3, 24, 0, 0, 0, tzinfo=timezone.utc
    )


def test_to_datetime_datetime_with_utc():
    assert datetime_util.to_datetime(
        datetime(2020, 3, 24, 12, 15, 30, tzinfo=timezone.utc)
    ) == datetime(2020, 3, 24, 0, 0, 0, tzinfo=timezone.utc)


def test_to_datetime_datetime_with_other_timezone():
    assert datetime_util.to_datetime(
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
    assert datetime_util.get_period_in_weeks(start, end) == weeks


def test_getnow_est_edt():
    with freeze_time("2021-01-01 19:00:00"):
        assert "2021-01-01 14:00:00-05:00" == str(datetime_util.get_now_us_eastern())
    with freeze_time("2021-08-01 19:00:00"):
        assert "2021-08-01 15:00:00-04:00" == str(datetime_util.get_now_us_eastern())


def test_datetime_str_to_date():
    assert datetime_util.datetime_str_to_date("2019-12-30") == date(2019, 12, 30)
    assert datetime_util.datetime_str_to_date("") is None
    assert datetime_util.datetime_str_to_date(None) is None
