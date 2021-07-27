#
# Tests for massgov.pfml.api.eligibility.base_period.
#

from massgov.pfml.api.eligibility import base_period
from massgov.pfml.util.datetime import quarter


def test_compute_base_period_empty():
    assert base_period.compute_base_period(quarter.Quarter(2044, 4), {}) == (
        quarter.Quarter(2044, 2),
        quarter.Quarter(2044, 1),
        quarter.Quarter(2043, 4),
        quarter.Quarter(2043, 3),
    )


def test_compute_base_period_one_current():
    assert base_period.compute_base_period(
        quarter.Quarter(2044, 4), {quarter.Quarter(2044, 4)}
    ) == (
        quarter.Quarter(2044, 4),
        quarter.Quarter(2044, 3),
        quarter.Quarter(2044, 2),
        quarter.Quarter(2044, 1),
    )


def test_compute_base_period_one_previous():
    assert base_period.compute_base_period(
        quarter.Quarter(2044, 4), {quarter.Quarter(2044, 3)}
    ) == (
        quarter.Quarter(2044, 3),
        quarter.Quarter(2044, 2),
        quarter.Quarter(2044, 1),
        quarter.Quarter(2043, 4),
    )


def test_compute_base_period_many_previous():
    assert base_period.compute_base_period(
        quarter.Quarter(2044, 4),
        {
            quarter.Quarter(2044, 3),
            quarter.Quarter(2044, 1),
            quarter.Quarter(2043, 4),
            quarter.Quarter(2043, 1),
            quarter.Quarter(2042, 4),
            quarter.Quarter(2040, 4),
            quarter.Quarter(2040, 2),
            quarter.Quarter(2040, 1),
            quarter.Quarter(2030, 3),
            quarter.Quarter(2030, 2),
            quarter.Quarter(2030, 1),
        },
    ) == (
        quarter.Quarter(2044, 3),
        quarter.Quarter(2044, 2),
        quarter.Quarter(2044, 1),
        quarter.Quarter(2043, 4),
    )
