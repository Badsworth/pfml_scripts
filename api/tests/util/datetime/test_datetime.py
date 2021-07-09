#
# Tests for massgov.pfml.util.datetime.
#

import datetime

import massgov.pfml.util.datetime


def test_to_datetime_date():
    assert massgov.pfml.util.datetime.to_datetime(datetime.date(2020, 3, 24)) == datetime.datetime(
        2020, 3, 24, 0, 0, 0, tzinfo=datetime.timezone.utc
    )


def test_to_datetime_datetime():
    assert massgov.pfml.util.datetime.to_datetime(
        datetime.datetime(2020, 3, 24, 12, 15, 30)
    ) == datetime.datetime(2020, 3, 24, 0, 0, 0, tzinfo=datetime.timezone.utc)


def test_to_datetime_datetime_with_utc():
    assert massgov.pfml.util.datetime.to_datetime(
        datetime.datetime(2020, 3, 24, 12, 15, 30, tzinfo=datetime.timezone.utc)
    ) == datetime.datetime(2020, 3, 24, 0, 0, 0, tzinfo=datetime.timezone.utc)


def test_to_datetime_datetime_with_other_timezone():
    assert massgov.pfml.util.datetime.to_datetime(
        datetime.datetime(
            2020, 3, 24, 12, 15, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=13))
        )
    ) == datetime.datetime(2020, 3, 24, 0, 0, 0, tzinfo=datetime.timezone.utc)
