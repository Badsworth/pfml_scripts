#
# Tests for massgov.pfml.api.eligibility.wage.
#
import datetime
import decimal
import uuid
from unittest.mock import MagicMock, call

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


def test_get_employer_average_weekly_wage_one_zero(test_db_session, initialize_factories_session):
    employer = factories.EmployerFactory(employer_id=EMPL1)
    employee = factories.EmployeeFactory()
    add_wage_row(employer, employee, datetime.date(2022, 9, 30), 0)
    add_wage_row(employer, employee, datetime.date(2022, 6, 30), 0)
    wage_calculator = wage.get_wage_calculator(
        employee.employee_id, datetime.date(2022, 9, 16), test_db_session
    )
    wage_calculator.set_each_employers_average_weekly_wage()
    wage_calculator.compute_employer_average_weekly_wage(EMPL1)
    assert wage_calculator.get_employer_average_weekly_wage(EMPL1) == 0


def test_get_employer_average_weekly_wage_one_row(test_db_session, initialize_factories_session):
    employer = factories.EmployerFactory(employer_id=EMPL1)
    employee = factories.EmployeeFactory()
    add_wage_row(employer, employee, datetime.date(2022, 9, 30), 13000)
    wage_calculator = wage.get_wage_calculator(
        employee.employee_id, datetime.date(2022, 9, 16), test_db_session
    )
    wage_calculator.set_each_employers_average_weekly_wage()
    assert wage_calculator.get_employer_average_weekly_wage(EMPL1) == 1000


@pytest.mark.parametrize("default_value", [None, decimal.Decimal("0")])
@pytest.mark.parametrize("should_round", [False, True])
def test_get_employer_average_weekly_wage_multiple_rows(
    test_db_session, initialize_factories_session, default_value, should_round
):
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
        employee.employee_id, datetime.date(2022, 12, 30), test_db_session
    )
    wage_calculator.set_each_employers_average_weekly_wage()
    assert (
        wage_calculator.get_employer_average_weekly_wage(EMPL1, default_value, should_round)
        == (13000 + 13520) / 26
    )
    assert (
        wage_calculator.get_employer_average_weekly_wage(EMPL2, default_value, should_round)
        == (7800 + 7540) / 26
    )


def test_get_employer_average_weekly_wage_should_round_if_provided(
    test_db_session, initialize_factories_session
):
    employer1 = factories.EmployerFactory(employer_id=EMPL1)
    employee = factories.EmployeeFactory()
    add_wage_row(employer1, employee, datetime.date(2022, 9, 30), 13000.2)  # Base p
    add_wage_row(employer1, employee, datetime.date(2022, 6, 30), 12870.02)  # Base p
    add_wage_row(employer1, employee, datetime.date(2022, 3, 31), 12688.01)  # Base p
    add_wage_row(employer1, employee, datetime.date(2021, 12, 31), 13520.1)  # Base p
    add_wage_row(employer1, employee, datetime.date(2021, 9, 30), 14040.1)

    factories.WagesAndContributionsFactory.create_batch(size=200)

    wage_calculator = wage.get_wage_calculator(
        employee.employee_id, datetime.date(2022, 12, 30), test_db_session
    )
    wage_calculator.set_each_employers_average_weekly_wage()
    should_round = True
    default = None
    assert wage_calculator.get_employer_average_weekly_wage(EMPL1, default, should_round) == round(
        decimal.Decimal((13000.2 + 13520.1) / 26), 2
    )


@pytest.mark.parametrize("default_value", [decimal.Decimal("0"), decimal.Decimal("123.232")])
@pytest.mark.parametrize("should_round", [False, True])
def test_get_employer_average_weekly_wage_should_return_default_value_if_employer_not_found(
    test_db_session, initialize_factories_session, default_value, should_round
):
    employee = factories.EmployeeFactory()
    wage_calculator = wage.get_wage_calculator(
        employee.employee_id, datetime.date(2022, 12, 30), test_db_session
    )
    wage_calculator.set_each_employers_average_weekly_wage()

    expected_value = default_value
    if should_round:
        expected_value = round(default_value, 2)

    assert (
        wage_calculator.get_employer_average_weekly_wage(EMPL1, default_value, should_round)
        == expected_value
    )


@pytest.mark.parametrize("default_value", [None, decimal.Decimal("0")])
@pytest.mark.parametrize("should_round", [False, True])
def test_get_employer_average_weekly_wage_missing_employer(
    test_db_session, initialize_factories_session, default_value, should_round
):
    employer1 = factories.EmployerFactory(employer_id=EMPL1)
    employee = factories.EmployeeFactory()
    add_wage_row(employer1, employee, datetime.date(2022, 9, 30), 13000)  # Base p
    add_wage_row(employer1, employee, datetime.date(2022, 6, 30), 12870)  # Base p
    add_wage_row(employer1, employee, datetime.date(2022, 3, 31), 12688)  # Base p
    add_wage_row(employer1, employee, datetime.date(2021, 12, 31), 13520)  # Base p
    add_wage_row(employer1, employee, datetime.date(2021, 9, 30), 14040)

    factories.WagesAndContributionsFactory.create_batch(size=200)

    wage_calculator = wage.get_wage_calculator(
        employee.employee_id, datetime.date(2022, 12, 30), test_db_session
    )
    wage_calculator.set_each_employers_average_weekly_wage()
    assert (
        wage_calculator.get_employer_average_weekly_wage(EMPL1, default_value, should_round)
        == (13000 + 13520) / 26
    )


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

    assert len(rows) == 12
    for row in rows:
        assert row.employee_id == employee1.employee_id
        assert row.employer_id in (EMPL1, EMPL2)


def test_query_employee_wages_ignores_zero_dollar_contributions(
    test_db_session, initialize_factories_session
):
    employer = factories.EmployerFactory(employer_id=EMPL1)
    employee = factories.EmployeeFactory()
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2020, 10, 1),
        employee_qtr_wages=1000,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2020, 7, 1),
        employee_qtr_wages=0,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2020, 4, 1),
        employee_qtr_wages=1000,
    )

    rows = wage.query_employee_wages(
        test_db_session, quarter.Quarter(2021, 1), employee.employee_id
    )

    # Expect 2 rows - Zero dollar reported wages ignored
    assert len(rows) == 2
    for row in rows:
        assert row.employee_qtr_wages == 1000


def test_get_employer_average_weekly_wage_calculator_one_employer_current_quarter():
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

    calculator.set_each_employers_average_weekly_wage()
    assert calculator.get_employer_average_weekly_wage(EMPL1) == (13000 + 13520) / 26


def test_get_employer_average_weekly_wage_calculator_one_employer_current_quarter_only():
    calculator = wage.WageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(20000))  # Base p
    calculator.set_each_employers_average_weekly_wage()
    assert float(calculator.get_employer_average_weekly_wage(EMPL1)) == 20000 / 13


def test_get_employer_average_weekly_wage_calculator_one_employer_next_quarter():
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

    calculator.set_each_employers_average_weekly_wage()
    assert calculator.get_employer_average_weekly_wage(EMPL1) == (13000 + 13520) / 26


def test_get_employer_average_weekly_wage_calculator_one_employer_3_quarters_later():
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

    calculator.set_each_employers_average_weekly_wage()
    assert calculator.get_employer_average_weekly_wage(EMPL1) == (13000 + 12870) / 26


def test_get_employer_average_weekly_wage_calculator_one_employer_previous_quarter():
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

    calculator.set_each_employers_average_weekly_wage()
    assert calculator.get_employer_average_weekly_wage(EMPL1) == (13520 + 14040) / 26


def test_get_employer_average_weekly_wage_calculator_three_employers_current_quarter():
    calculator = wage.WageCalculator()
    calculator.set_effective_quarter(quarter.Quarter(2022, 3))

    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(12688))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(13520))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 3), decimal.Decimal(14040))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 2), decimal.Decimal(12688))

    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 3), decimal.Decimal(7800))
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 2), decimal.Decimal(7540))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 1), decimal.Decimal(7280))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2021, 4), decimal.Decimal(7020))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2021, 3), decimal.Decimal(6760))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2021, 2), decimal.Decimal(6500))

    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 3), decimal.Decimal(20800))  # Base p
    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 2), decimal.Decimal(20540))
    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 1), decimal.Decimal(20540))

    calculator.set_each_employers_average_weekly_wage()
    assert calculator.get_employer_average_weekly_wage(EMPL1) == (14040 + 13520) / 26
    assert calculator.get_employer_average_weekly_wage(EMPL2) == (7540 + 7280) / 26
    assert calculator.get_employer_average_weekly_wage(EMPL3) == (20800) / 13


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
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(13000))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(12870))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(11700))  # Base p

    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 3), decimal.Decimal(7800))
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 2), decimal.Decimal(7540))  # Base p
    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 1), decimal.Decimal(7280))  # Base p

    calculator.set_quarter_wage(
        EMPL3, quarter.Quarter(2020, 1), decimal.Decimal(20540)
    )  # Outside of Base Period. Will not be included

    total_wage = calculator.compute_total_wage()
    assert total_wage == (12870 + 11700 + 7540 + 7280)


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
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 3), decimal.Decimal(1000))
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 2), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2022, 1), decimal.Decimal(1000))  # Base p
    calculator.set_quarter_wage(EMPL1, quarter.Quarter(2021, 4), decimal.Decimal(1000))  # Base p

    calculator.set_quarter_wage(EMPL2, quarter.Quarter(2022, 3), decimal.Decimal(2000))

    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2022, 3), decimal.Decimal(3000))
    calculator.set_quarter_wage(EMPL3, quarter.Quarter(2021, 4), decimal.Decimal(4000))  # Base p

    total_quarterly_wages = calculator.compute_total_quarterly_wages()
    assert total_quarterly_wages[quarter.Quarter(2022, 2)] == 1000
    assert total_quarterly_wages[quarter.Quarter(2022, 1)] == 1000
    assert total_quarterly_wages[quarter.Quarter(2021, 4)] == 5000  # two employers wages added


def test_compute_employee_dor_wage_data_mock_expected_functions_called(
    test_db_session, initialize_factories_session
):
    expected_total_wage = decimal.Decimal("123")
    expected_consolidated_aww = decimal.Decimal("456")
    expected_total_quarterly_wages = {}

    mock_calculator = MagicMock()
    mock_calculator.compute_total_wage = MagicMock(return_value=expected_total_wage)
    mock_calculator.compute_consolidated_aww = MagicMock(return_value=expected_consolidated_aww)
    mock_calculator.set_each_employers_average_weekly_wage = MagicMock()
    mock_calculator.compute_total_quarterly_wages = MagicMock(
        return_value=expected_total_quarterly_wages
    )
    result = wage.WageCalculator.compute_employee_dor_wage_data(mock_calculator)

    assert result == wage.ComputeDORWageData(
        total_wages=expected_total_wage,
        consolidated_weekly_wage=expected_consolidated_aww,
        quarterly_wages=expected_total_quarterly_wages,
    )
    call_list = [
        call.compute_total_wage(),
        call.compute_consolidated_aww(),
        call.set_each_employers_average_weekly_wage(),
        call.compute_total_quarterly_wages(),
    ]
    assert mock_calculator.mock_calls == call_list


def test_compute_employee_dor_wage_data_expected_result(
    test_db_session, initialize_factories_session
):
    effective_date = datetime.date(2022, 9, 16)
    employer = factories.EmployerFactory.create(employer_id=EMPL1)
    employee = factories.EmployeeFactory.create()

    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2022, 9, 30),
        employee_qtr_wages=13000,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2022, 6, 30),
        employee_qtr_wages=12870,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2022, 3, 31),
        employee_qtr_wages=12688,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2021, 12, 31),
        employee_qtr_wages=13520,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2021, 9, 30),
        employee_qtr_wages=14040,
    )

    employee_id = employee.employee_id

    wage_calculator = wage.get_wage_calculator(employee_id, effective_date, test_db_session)
    expected_total_wages = wage_calculator.compute_total_wage()
    expected_consolidated_weekly_wage = wage_calculator.compute_consolidated_aww()
    expected_quarterly_wages = wage_calculator.compute_total_quarterly_wages()

    result = wage_calculator.compute_employee_dor_wage_data()

    assert result == wage.ComputeDORWageData(
        total_wages=expected_total_wages,
        consolidated_weekly_wage=expected_consolidated_weekly_wage,
        quarterly_wages=expected_quarterly_wages,
    )


def test_get_base_period_quarters(test_db_session, initialize_factories_session):
    effective_date = datetime.date(2022, 9, 16)
    employer = factories.EmployerFactory.create(employer_id=EMPL1)
    employee = factories.EmployeeFactory.create()

    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2022, 9, 30),
        employee_qtr_wages=13000,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2022, 6, 30),
        employee_qtr_wages=12870,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2022, 3, 31),
        employee_qtr_wages=12688,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2021, 12, 31),
        employee_qtr_wages=13520,
    )
    factories.WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=datetime.date(2021, 9, 30),
        employee_qtr_wages=14040,
    )

    employee_id = employee.employee_id

    wage_calculator = wage.get_wage_calculator(employee_id, effective_date, test_db_session)
    result = wage_calculator.get_base_period_quarters_as_dates()
    assert result == (datetime.date(2021, 10, 1), datetime.date(2022, 9, 30))


def test_get_base_period_quarters_2():

    start_quarter = quarter.Quarter(2021, 3)
    base_period_qtrs = tuple(start_quarter.series_backwards(4))
    base_period_start, base_period_end = base_period_qtrs[-1], base_period_qtrs[0]
    expected_base_period_quarters = (base_period_start.start_date(), base_period_end.as_date())

    wage_calculator = wage.WageCalculator()
    wage_calculator.base_period_quarters = base_period_qtrs
    result = wage_calculator.get_base_period_quarters_as_dates()

    assert result == expected_base_period_quarters


def test_get_base_period_quarters_should_raise_if_base_period_not_set():

    wage_calculator = wage.WageCalculator()
    with pytest.raises(IndexError):
        wage_calculator.get_base_period_quarters_as_dates()
