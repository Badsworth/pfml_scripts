from datetime import datetime, timedelta

import pytest
from freezegun.api import freeze_time

from massgov.pfml.util.datetime.business_day import BusinessDay


def test_business_days_between_same_day():
    start = datetime(2021, 12, 1)
    end = datetime(2021, 12, 1)

    bd = BusinessDay(start)

    days_between = bd.days_between(end)

    assert days_between == 0


@pytest.mark.parametrize(
    "end_offset,expected_days",
    [
        (0, 0),  # Mon
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
        (6, 5),  # Sun
        (7, 5),
        (8, 6),
        (72, 52),  # later dates
        (-1, 0),  # sunday
        (-2, 0),
        (-3, 1),
        (-4, 2),
        (-5, 3),
        (-6, 4),
        (-7, 5),
        (-8, 5),
        (-9, 5),
        (-10, 6),
        (-72, 50),  # later dates
    ],
)
def test_business_days_between_same_week(end_offset: int, expected_days: int):
    start = datetime(2021, 12, 27)
    end = start + timedelta(days=end_offset)

    bd = BusinessDay(start)

    days_between = bd.days_between(end)
    assert days_between == expected_days


@freeze_time("2021-12-27")
def test_business_days_between_using_utc_a():
    start = datetime.utcnow()
    end = datetime.now() + timedelta(days=1)

    bd = BusinessDay(start)

    days_between = bd.days_between(end)
    assert days_between == 1


@freeze_time("2021-12-27")
def test_business_days_between_using_utc_b():
    start = datetime.now()
    end = datetime.utcnow() + timedelta(days=1)

    bd = BusinessDay(start)

    days_between = bd.days_between(end)
    assert days_between == 1


@freeze_time("2021-12-27")
def test_business_days_between_using_utc_c():
    start = datetime.utcnow()
    end = datetime.utcnow() + timedelta(days=1)

    bd = BusinessDay(start)

    days_between = bd.days_between(end)
    assert days_between == 1
