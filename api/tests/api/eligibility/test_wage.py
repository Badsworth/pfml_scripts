#
# Tests for massgov.pfml.api.eligibility.wage.
#

import datetime
import decimal
import uuid

import pytest

from massgov.pfml.api.eligibility import wage
from massgov.pfml.db.models import factories
from massgov.pfml.db.models.employees import WagesAndContributions
from massgov.pfml.util.datetime import quarter

EMPL1 = uuid.UUID(int=1)
EMPL2 = uuid.UUID(int=2)
EMPL3 = uuid.UUID(int=3)


def add_wage_row(employer, employee, filing_period, qtr_wage):
    return WagesAndContributions(
        account_key="000111",
        employer=employer,
        employee=employee,
        filing_period=filing_period,
        employee_qtr_wages=qtr_wage,
        employee_ytd_wages=qtr_wage,
        employee_med_contribution=0,
        employer_med_contribution=0,
        employee_fam_contribution=0,
        employer_fam_contribution=0,
        is_independent_contractor=False,
        is_opted_in=False,
    )


@pytest.mark.integration
def test_get_average_weekly_wage_one_row(test_db_session, initialize_factories_session):
    employer = factories.EmployerFactory(employer_id=EMPL1)
    employee = factories.EmployeeFactory()
    add_wage_row(employer, employee, datetime.date(2022, 9, 30), 13000)
    factories.WagesAndContributionsFactory.create_batch(size=100)

    wage_calculator = wage.get_wage_calculator(
        employee.employee_id, datetime.date(2022, 9, 16), test_db_session
    )
    aww = wage_calculator.compute_average_weekly_wage()

    assert aww == 1000


@pytest.mark.integration
def test_get_average_weekly_wage_multiple_rows(test_db_session, initialize_factories_session):
    employer1 = factories.EmployerFactory(employer_id=EMPL1)
    employer2 = factories.EmployerFactory(employer_id=EMPL2)
    employee = factories.EmployeeFactory()
    add_wage_row(employer1, employee, datetime.date(2022, 9, 30), 13000)  # Base p
    add_wage_row(employer1, employee, datetime.date(2022, 6, 30), 12870)  # Base p
    add_wage_row(employer1, employee, datetime.date(2022, 3, 31), 12688)  # Base p
    add_wage_row(employer1, employee, datetime.date(2021, 12, 31), 13520)  # Base p
    add_wage_row(employer1, employee, datetime.date(2021, 9, 30), 14040)
    add_wage_row(employer2, employee, datetime.date(2022, 9, 30), 7800)  # Base p
    add_wage_row(employer2, employee, datetime.date(2022, 6, 30), 7540)  # Base p
    add_wage_row(employer2, employee, datetime.date(2022, 3, 31), 7280)  # Base p
    add_wage_row(employer2, employee, datetime.date(2021, 12, 31), 7020)  # Base p
    add_wage_row(employer2, employee, datetime.date(2021, 9, 30), 6760)
    add_wage_row(employer2, employee, datetime.date(2021, 6, 30), 6500)
    factories.WagesAndContributionsFactory.create_batch(size=200)

    wage_calculator = wage.get_wage_calculator(
        employee.employee_id, datetime.date(2022, 9, 16), test_db_session
    )
    aww = wage_calculator.compute_average_weekly_wage()

    assert aww == (13000 + 13520) / 26 + (7800 + 7540) / 26


@pytest.mark.integration
def test_query_employee_wages(test_db_session, initialize_factories_session):
    employer1 = factories.EmployerFactory(employer_id=EMPL1)
    employer2 = factories.EmployerFactory(employer_id=EMPL2)
    employee1 = factories.EmployeeFactory()
    employee2 = factories.EmployeeFactory()
    # Insert 80 rows (2 employers * 2 employees * 20 dates)
    for employer in (employer1, employer2):
        for employee in (employee1, employee2):
            for q in quarter.Quarter(2020, 1).series(20):
                add_wage_row(employer, employee, q.as_date(), 13000)

    rows = wage.query_employee_wages(
        test_db_session, quarter.Quarter(2022, 2), employee1.employee_id
    )

    # Expect 12 rows (2 employers * 1 employee * 6 dates)
    assert len(rows) == 12
    for row in rows:
        assert row.employee_id == employee1.employee_id
        assert row.employer_id in (EMPL1, EMPL2)


def test_average_weekly_wage_calculator_one_employer_current_quarter():
    calculator = wage.WageCalculator()
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
    calculator = wage.WageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(20000))  # Base p

    average_weekly_wage = calculator.compute_average_weekly_wage()
    assert average_weekly_wage == decimal.Decimal(
        "1539.00"
    )  # 20000 / 13, rounded up to next dollar


def test_average_weekly_wage_calculator_one_employer_next_quarter():
    calculator = wage.WageCalculator()
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
    calculator = wage.WageCalculator()
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
    calculator = wage.WageCalculator()
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
    calculator = wage.WageCalculator()
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


def test_total_wage_calculator_one_employeer():
    calculator = wage.WageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(11700))  # Base p

    total_wage = calculator.compute_total_wage()
    assert total_wage == (13000 + 12870 + 11700)


def test_total_wage_calculator_multiple_employeers():
    calculator = wage.WageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(11700))  # Base p

    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 3), decimal.Decimal(7800))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 2), decimal.Decimal(7540))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 1), decimal.Decimal(7280))  # Base p

    calculator.set_quarter_wage(
        EMPL3, quarter.Quarter(2020, 1), decimal.Decimal(20540)
    )  # Outside of Base Period. Will not be included

    total_wage = calculator.compute_total_wage()
    assert total_wage == (13000 + 12870 + 11700 + 7800 + 7540 + 7280)


def test_total_quarterly_wage_calculator_one_employer():
    calculator = wage.WageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 3), decimal.Decimal(1000))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 2), decimal.Decimal(1000))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 1), decimal.Decimal(1000))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2020, 4), decimal.Decimal(1000))

    total_quarterly_wages = calculator.compute_total_quarterly_wages()
    assert len(total_quarterly_wages) == 4
    assert total_quarterly_wages[quarter.Quarter(2022, 3)] == 1000
    assert total_quarterly_wages[quarter.Quarter(2022, 2)] == 1000
    assert total_quarterly_wages[quarter.Quarter(2022, 1)] == 1000
    assert total_quarterly_wages[quarter.Quarter(2021, 4)] == 1000


def test_total_quarterly_wage_calculator_multiple_employers():
    calculator = wage.WageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(1000))  # Base p

    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 3), decimal.Decimal(2000))  # Base p

    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2022, 3), decimal.Decimal(3000))  # Base p
    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 4), decimal.Decimal(4000))  # Base p

    total_quarterly_wages = calculator.compute_total_quarterly_wages()
    assert len(total_quarterly_wages) == 4
    assert total_quarterly_wages[quarter.Quarter(2022, 3)] == 6000  # three employers wages added
    assert total_quarterly_wages[quarter.Quarter(2022, 2)] == 1000
    assert total_quarterly_wages[quarter.Quarter(2022, 1)] == 1000
    assert total_quarterly_wages[quarter.Quarter(2021, 4)] == 5000  # two employers wages added
