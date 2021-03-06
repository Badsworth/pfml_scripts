#
# Eligibility - wage calculations.
#
import datetime
import decimal
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

from sqlalchemy.orm.query import Query

import massgov.pfml.db
import massgov.pfml.util.logging
from massgov.pfml.db.models import employees
from massgov.pfml.util.datetime import quarter

from . import base_period

logger = massgov.pfml.util.logging.get_logger(__name__)


def _employee_wages_query(
    db_session: massgov.pfml.db.Session, effective_quarter: quarter.Quarter, employee_id: uuid.UUID
) -> "Query[employees.WagesAndContributions]":
    earliest_quarter = effective_quarter.subtract_quarters(5)
    query = (
        db_session.query(employees.WagesAndContributions)
        .filter(
            employees.WagesAndContributions.employee_id == employee_id,
            employees.WagesAndContributions.filing_period.between(
                earliest_quarter.start_date(), effective_quarter.as_date()
            ),
            employees.WagesAndContributions.employee_qtr_wages != 0,
        )
        .order_by(
            employees.WagesAndContributions.employer_id,
            employees.WagesAndContributions.filing_period,
        )
    )
    return query


def query_employee_wages(
    db_session: massgov.pfml.db.Session, effective_quarter: quarter.Quarter, employee_id: uuid.UUID
) -> List[Any]:
    """Read DOR wage data from database, going back up to 6 quarters inclusive.

    6 quarters is the maximum possible needed to compute eligibility.
    """
    qry = _employee_wages_query(db_session, effective_quarter, employee_id)
    return qry.all()


class WageCalculator:
    """Calculate various wages for an employee.

    To determine the base period:

        1. This is 4 consecutive quarters ending with the last reported
           quarter with wage data (if only one employer; this could include the quarter of the effective date), but not ending
           prior to 2 quarters before the effective date.

    To calculate the average weekly wage:

       1. Determine within the base period the number of quarters where wages have been reported (N)

       2. Consolidate wages across employers (take the sum across each employer in each base period)

        If N >= 3, then:

            Sum the  2 quarters with the highest earnings from consolidated table
            Divide the total by 26

        If N <= 2, then:

            Take the highest quarter of total wages from consolidated table
            Divide by 13

    To calculate the quarterly wage:

      For each employer:

        1. For each quarter in the base period, if the quarter has no wages from other employers, initialize the quarterly
           wage to that value, otherwise increment the quarterly wage.
    """

    employer_quarter_wage: DefaultDict[uuid.UUID, Dict[quarter.Quarter, decimal.Decimal]]
    effective_quarter: quarter.Quarter
    employer_average_weekly_wage: Dict[uuid.UUID, decimal.Decimal]
    base_period_quarters: Tuple[quarter.Quarter, ...]
    consolidated_aww: decimal.Decimal
    consolidated_wages: Dict[quarter.Quarter, decimal.Decimal]

    def __init__(self):
        self.employer_quarter_wage = defaultdict(dict)
        self.effective_quarter = quarter.Quarter(2020, 1)
        self.employer_average_weekly_wage = {}
        self.consolidated_wages = {}
        self.base_period_quarters = tuple()
        self.consolidated_aww = decimal.Decimal("0")

    def set_quarter_wage(
        self, employer_id: uuid.UUID, period: quarter.Quarter, wage: decimal.Decimal
    ) -> None:
        """Set the reported wage for the given employer and quarter."""
        if employer_id not in self.employer_quarter_wage:
            self.employer_quarter_wage[employer_id] = {}
        self.employer_quarter_wage[employer_id][period] = wage
        if period not in self.consolidated_wages:
            self.consolidated_wages[period] = decimal.Decimal("0")
        self.consolidated_wages[period] += wage

    def set_effective_quarter(self, effective_quarter: quarter.Quarter) -> None:
        """Set the effective quarter for the computation."""
        self.effective_quarter = effective_quarter

    def set_base_period(self) -> None:
        """Set the base period"""
        possible_quarters = list(self.consolidated_wages.keys())
        multiple_employers_bool = len(self.employer_quarter_wage.keys()) > 1
        self.base_period_quarters = base_period.compute_base_period(
            self.effective_quarter, possible_quarters, multiple_employers_bool
        )

    def get_employer_average_weekly_wage(
        self,
        employer_id: uuid.UUID,
        default: Optional[decimal.Decimal] = None,
        should_round: Optional[bool] = None,
    ) -> decimal.Decimal:
        """Get average weekly wage for a specific employer.
        If not found and no default is supplied, raise KeyError.
        Round to two decimal places if should_round supplied.
        """
        employer_average_weekly_wage = default
        if employer_id in self.employer_average_weekly_wage:
            employer_average_weekly_wage = self.employer_average_weekly_wage[employer_id]

        if employer_average_weekly_wage is None:
            raise KeyError

        if should_round:
            employer_average_weekly_wage = round(employer_average_weekly_wage, 2)

        return employer_average_weekly_wage

    def set_each_employers_average_weekly_wage(self):
        """Compute the average weekly wage, summed across all employers."""
        logger.info(
            "employers %i, total data rows %i",
            len(self.employer_quarter_wage),
            sum(len(value) for value in self.employer_quarter_wage.values()),
        )
        if not self.base_period_quarters:
            self.set_base_period()
        for employer_id in self.employer_quarter_wage:
            self.compute_employer_average_weekly_wage(employer_id)

    def compute_consolidated_aww(self) -> decimal.Decimal:
        """Compute average weekly on consolidated wages for eligibility determination."""
        try:
            consolidated_wage_totals = [
                value
                for date, value in self.consolidated_wages.items()
                if date in self.base_period_quarters
            ]
            consolidated_aww = decimal.Decimal(
                max(consolidated_wage_totals) / 13
                if len(consolidated_wage_totals) <= 2
                else sum(sorted(consolidated_wage_totals)[-2:]) / 26
            )
        except ValueError:  # no wages
            consolidated_aww = decimal.Decimal("0")
        # # M.G.L. c. 151A, ??1(w) reads, "If such weekly wage includes a fractional part of a dollar it shall be raised
        # # to the next highest dollar."
        # # https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXXI/Chapter151A/Section1
        next_highest_dollar = decimal.Decimal(f"{math.ceil(consolidated_aww)}.00")
        self.consolidated_aww = next_highest_dollar
        return next_highest_dollar

    def compute_employer_average_weekly_wage(self, employer_id: uuid.UUID) -> decimal.Decimal:
        """Compute average weekly wage for an invidiaual employer."""
        if not self.base_period_quarters:
            self.set_base_period()

        quarter_wages = self.employer_quarter_wage[employer_id]
        wages = []
        for reported_quarter, wage in quarter_wages.items():
            if reported_quarter in self.base_period_quarters and wage != decimal.Decimal("0"):
                wages.append(wage)

        average_weekly_wage = decimal.Decimal("0")
        if wages:
            if len(wages) <= 2:
                max_wage = max(wages)
                average_weekly_wage = max_wage / 13
            else:
                max_wage_0, max_wage_1 = sorted(wages)[-2:]
                average_weekly_wage = (max_wage_0 + max_wage_1) / 26
        self.employer_average_weekly_wage[employer_id] = average_weekly_wage
        return average_weekly_wage

    def compute_total_wage(self) -> decimal.Decimal:
        """Compute the total wage, summed across all employers."""
        if not self.base_period_quarters:
            self.set_base_period()
        logger.info(
            "employers %i, total data rows %i",
            len(self.employer_quarter_wage),
            sum(len(value) for value in self.employer_quarter_wage.values()),
        )

        total_wage = decimal.Decimal("0")
        for employer_id in self.employer_quarter_wage:
            total_wage += self.compute_employer_total_wage(employer_id)

        return total_wage

    def compute_employer_total_wage(self, employer_id: uuid.UUID) -> decimal.Decimal:
        """Compute total weekly wage for one employer."""
        quarter_wages = self.employer_quarter_wage[employer_id]
        total_wage = decimal.Decimal("0")
        for reported_quarter, wage in quarter_wages.items():
            if reported_quarter in self.base_period_quarters:
                total_wage += wage

        return total_wage

    def compute_total_quarterly_wages(self) -> Dict[quarter.Quarter, decimal.Decimal]:
        total_quarterly_wages: Dict[quarter.Quarter, decimal.Decimal] = {}
        if not self.base_period_quarters:
            self.set_base_period()

        for quarter_wages in self.employer_quarter_wage.values():
            for reported_quarter, wage in quarter_wages.items():
                if reported_quarter in self.base_period_quarters and wage > 0:
                    total_quarterly_wages[reported_quarter] = (
                        total_quarterly_wages.get(reported_quarter, 0) + wage
                    )

        return total_quarterly_wages

    def get_base_period_quarters_as_dates(self) -> Tuple[datetime.date, datetime.date]:
        # raises IndexError
        base_period_qtrs = self.base_period_quarters
        base_period_start, base_period_end = base_period_qtrs[-1], base_period_qtrs[0]

        base_period_start_date = base_period_start.start_date()
        base_period_end_date = base_period_end.as_date()

        return (base_period_start_date, base_period_end_date)

    def compute_employee_dor_wage_data(self):
        total_wages = self.compute_total_wage()
        consolidated_weekly_wage = self.compute_consolidated_aww()
        self.set_each_employers_average_weekly_wage()
        quarterly_wages = self.compute_total_quarterly_wages()
        return ComputeDORWageData(total_wages, consolidated_weekly_wage, quarterly_wages)


def _get_wage_calculator(effective_date: datetime.date) -> WageCalculator:
    effective_quarter = quarter.Quarter.from_date(effective_date)
    calculator = WageCalculator()
    calculator.set_effective_quarter(effective_quarter)
    return calculator


def get_wage_calculator(
    employee_id: uuid.UUID, effective_date: datetime.date, db_session: massgov.pfml.db.Session
) -> WageCalculator:
    """Read DOR wage data from database and setup a calculator for the given employee."""
    calculator = _get_wage_calculator(effective_date)

    rows = query_employee_wages(db_session, calculator.effective_quarter, employee_id)
    for row in rows:
        calculator.set_quarter_wage(
            row.employer_id, quarter.Quarter.from_date(row.filing_period), row.employee_qtr_wages
        )
    calculator.set_base_period()

    return calculator


def get_retroactive_base_period(
    db_session: massgov.pfml.db.Session, employee_id: uuid.UUID, effective_date: datetime.date
) -> Tuple[quarter.Quarter, ...]:
    """
    Get the base period for a given effective date using
    wages in the system at the time of the effective date.
    """
    calculator = _get_wage_calculator(effective_date)

    qry = _employee_wages_query(db_session, calculator.effective_quarter, employee_id)
    rows = qry.filter(employees.WagesAndContributions.created_at < effective_date)
    for row in rows:
        calculator.set_quarter_wage(
            row.employer_id, quarter.Quarter.from_date(row.filing_period), row.employee_qtr_wages
        )
    calculator.set_base_period()

    return calculator.base_period_quarters


@dataclass
class ComputeDORWageData:
    total_wages: Decimal
    consolidated_weekly_wage: Decimal
    quarterly_wages: Dict[quarter.Quarter, Decimal]
