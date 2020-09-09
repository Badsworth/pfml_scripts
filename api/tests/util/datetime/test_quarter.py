#
# Tests for massgov.pfml.util.datetime.quarter.
#

import datetime

import pytest

from massgov.pfml.util.datetime.quarter import Quarter


def test_quarter():
    q = Quarter(2020, 2)

    assert repr(q) == "Quarter(2020, 2)"
    assert str(q) == "20200630"
    assert q.as_date() == datetime.date(2020, 6, 30)
    assert q.start_date() == datetime.date(2020, 4, 1)
    assert q.next_quarter() == Quarter(2020, 3)
    assert q.previous_quarter() == Quarter(2020, 1)
    assert q.subtract_quarters(0) == Quarter(2020, 2)
    assert q.subtract_quarters(1) == Quarter(2020, 1)
    assert q.subtract_quarters(2) == Quarter(2019, 4)
    assert q.subtract_quarters(6) == Quarter(2018, 4)


def test_quarter_invalid_quarter():
    with pytest.raises(ValueError):
        Quarter(2020, 7)


def test_quarter_from_date():
    assert Quarter.from_date(datetime.date(2020, 1, 1)) == Quarter(2020, 1)
    assert Quarter.from_date(datetime.date(2020, 3, 31)) == Quarter(2020, 1)
    assert Quarter.from_date(datetime.date(2020, 4, 1)) == Quarter(2020, 2)
    assert Quarter.from_date(datetime.date(2020, 6, 30)) == Quarter(2020, 2)
    assert Quarter.from_date(datetime.date(2020, 7, 1)) == Quarter(2020, 3)
    assert Quarter.from_date(datetime.date(2020, 9, 30)) == Quarter(2020, 3)
    assert Quarter.from_date(datetime.date(2020, 10, 1)) == Quarter(2020, 4)
    assert Quarter.from_date(datetime.date(2020, 12, 31)) == Quarter(2020, 4)


def test_quarter_series():
    q = Quarter(2020, 2)

    assert tuple(q.series(10)) == (
        Quarter(2020, 2),
        Quarter(2020, 3),
        Quarter(2020, 4),
        Quarter(2021, 1),
        Quarter(2021, 2),
        Quarter(2021, 3),
        Quarter(2021, 4),
        Quarter(2022, 1),
        Quarter(2022, 2),
        Quarter(2022, 3),
    )


def test_quarter_series_backwards():
    q = Quarter(2020, 2)

    assert tuple(q.series_backwards(10)) == (
        Quarter(2020, 2),
        Quarter(2020, 1),
        Quarter(2019, 4),
        Quarter(2019, 3),
        Quarter(2019, 2),
        Quarter(2019, 1),
        Quarter(2018, 4),
        Quarter(2018, 3),
        Quarter(2018, 2),
        Quarter(2018, 1),
    )
