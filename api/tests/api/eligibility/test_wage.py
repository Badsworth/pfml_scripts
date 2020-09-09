#
# Tests for massgov.pfml.api.eligibility.wage.
#

import decimal
import uuid

from massgov.pfml.api.eligibility import wage
from massgov.pfml.util.datetime import quarter

EMPL1 = uuid.UUID(int=1)
EMPL2 = uuid.UUID(int=2)
EMPL3 = uuid.UUID(int=3)


def test_average_weekly_wage_calculator_one_employer_current_quarter():
    calculator = wage.AverageWeeklyWageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(12688))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(13520))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 3), decimal.Decimal(14040))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 2), decimal.Decimal(12688))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 1), decimal.Decimal(11700))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2020, 4), decimal.Decimal(11700))

    average_weekly_wage = calculator.compute_average_weekly_wage()
    assert average_weekly_wage == (13000 + 13520) / 26


def test_average_weekly_wage_calculator_one_employer_current_quarter_only():
    calculator = wage.AverageWeeklyWageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(20000))  # Base p

    average_weekly_wage = calculator.compute_average_weekly_wage()
    assert average_weekly_wage == 1539  # 20000 / 13, rounded up to next dollar


def test_average_weekly_wage_calculator_one_employer_next_quarter():
    calculator = wage.AverageWeeklyWageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 4))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(12688))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(13520))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 3), decimal.Decimal(14040))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 2), decimal.Decimal(12688))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 1), decimal.Decimal(11700))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2020, 4), decimal.Decimal(11700))

    average_weekly_wage = calculator.compute_average_weekly_wage()
    assert average_weekly_wage == (13000 + 13520) / 26


def test_average_weekly_wage_calculator_one_employer_3_quarters_later():
    calculator = wage.AverageWeeklyWageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2023, 2))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(12688))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(13520))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 3), decimal.Decimal(14040))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 2), decimal.Decimal(12688))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 1), decimal.Decimal(11700))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2020, 4), decimal.Decimal(11700))

    average_weekly_wage = calculator.compute_average_weekly_wage()
    assert average_weekly_wage == (13000 + 12870) / 26


def test_average_weekly_wage_calculator_one_employer_previous_quarter():
    calculator = wage.AverageWeeklyWageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 2))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(12688))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(13520))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 3), decimal.Decimal(14040))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 2), decimal.Decimal(12688))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 1), decimal.Decimal(11700))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2020, 4), decimal.Decimal(11700))

    average_weekly_wage = calculator.compute_average_weekly_wage()
    assert average_weekly_wage == (13520 + 14040) / 26


def test_average_weekly_wage_calculator_three_employers_current_quarter():
    calculator = wage.AverageWeeklyWageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))

    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(12688))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(13520))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 3), decimal.Decimal(14040))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 2), decimal.Decimal(12688))

    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 3), decimal.Decimal(7800))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 2), decimal.Decimal(7540))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 1), decimal.Decimal(7280))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2021, 4), decimal.Decimal(7020))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2021, 3), decimal.Decimal(6760))
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2021, 2), decimal.Decimal(6500))

    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 3), decimal.Decimal(20800))  # Base p
    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 2), decimal.Decimal(20540))  # Base p
    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 1), decimal.Decimal(20540))

    average_weekly_wage = calculator.compute_average_weekly_wage()
    assert average_weekly_wage == (13000 + 13520) / 26 + (7800 + 7540) / 26 + 20800 / 13
