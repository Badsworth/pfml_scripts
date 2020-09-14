#
# Tests for massgov.pfml.api.eligibility.benefit.
#

import decimal

import pytest

from massgov.pfml.api.eligibility import benefit


@pytest.mark.parametrize(
    "individual_aww,expected_benefit",
    (
        (0, 0),
        (5, 4),
        (10, 8),
        (20, 16),
        (100, 80),
        (200, 160),
        (300, 240),
        (400, 320),
        (495, 396),
        (500, 400),  # <- 80% up to here (50% of state aww)
        (502, 401),  # <- plus 50% of portion above from here
        (510, 405),
        (600, 450),
        (700, 500),
        (800, 550),
        (900, 600),
        (960, 630),
        (970, 635),
        (978, 639),
        (980, 640),  # <- maximum reached (64% of state aww)
        (990, 640),
        (1000, 640),
        (1100, 640),
        (1200, 640),
        (1300, 640),
        (1400, 640),
        (1500, 640),
        (2000, 640),
        (10000, 640),
        (100000, 640),
    ),
)
def test_calculate_weekly_benefit_amount(individual_aww, expected_benefit):
    state_aww = decimal.Decimal("1000")
    assert benefit.calculate_weekly_benefit_amount(individual_aww, state_aww) == expected_benefit


def test_calculate_weekly_benefit_amount_realistic():
    individual_aww = 1538
    state_aww = decimal.Decimal("1431.66")
    assert benefit.calculate_weekly_benefit_amount(individual_aww, state_aww) == decimal.Decimal(
        "916.2624"
    )


def test_calculate_weekly_benefit_amount_realistic_low():
    individual_aww = 240
    state_aww = decimal.Decimal("1431.66")
    assert benefit.calculate_weekly_benefit_amount(individual_aww, state_aww) == 192


def test_calculate_weekly_benefit_amount_realistic_on_50_percent_boundary():
    individual_aww = decimal.Decimal("715.84")
    state_aww = decimal.Decimal("1431.66")
    assert benefit.calculate_weekly_benefit_amount(individual_aww, state_aww) == decimal.Decimal(
        "572.6690"
    )
