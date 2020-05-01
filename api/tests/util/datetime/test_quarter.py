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


def test_quarter_invalid_quarter():
    with pytest.raises(ValueError):
        Quarter(2020, 7)


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
