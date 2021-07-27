#
# Eligibility - wage calculations.
#

import datetime
import decimal
import math
import uuid
from typing import Any, Dict, List

import massgov.pfml.db
import massgov.pfml.util.logging
from massgov.pfml.db.models import employees
from massgov.pfml.util.datetime import quarter

from . import base_period

logger = massgov.pfml.util.logging.get_logger(__name__)


def query_employee_wages(
    db_session: massgov.pfml.db.Session, effective_quarter: quarter.Quarter, employee_id: uuid.UUID
) -> List[Any]:
    """Read DOR wage data from database, going back up to 6 quarters inclusive.

    6 quarters is the maximum possible needed to compute eligibility.
    """
    earliest_quarter = effective_quarter.subtract_quarters(5)

    rows = (
        db_session.query(employees.WagesAndContributions)
        .filter(
            employees.WagesAndContributions.employee_id == employee_id,
            employees.WagesAndContributions.filing_period.between(
                earliest_quarter.start_date(), effective_quarter.as_date()
            ),
        )
        .order_by(
            employees.WagesAndContributions.employer_id,
            employees.WagesAndContributions.filing_period,
        )
        .all()
    )

    return rows


class WageCalculator:
    """Calculate various wages for an employee.

    To calculate the average weekly wage:

      For each employer:

       1. Determine the “Base Period”.  This is 4 consecutive quarters ending with the last reported
          quarter with wage data (could include the quarter of the effective date), but not ending
          prior to 2 quarters before the effective date.

       2. Determine within the base period the number of quarters where wages have been reported (N)

        If N >= 3, then:

            Take the 2 quarters with the highest earnings, and sum them all
            Divide the total by 26

        If N <= 2, then:

            Take the highest quarter of total wages
            Divide by 13

       3. If there are more than one employer, sum the total across employers.

    To calculate the quarterly wage:

      For each employer:

        1. Determine the “Base Period”.  This is 4 consecutive quarters ending with the last reported
          quarter with wage data (could include the quarter of the effective date), but not ending
          prior to 2 quarters before the effective date.

        2. For each quarter, if the quarter has no wages from other employers, initialize the quarterly
           wage to that value, otherwise increment the quarterly wage.
    """

    employer_quarter_wage: Dict[uuid.UUID, Dict[quarter.Quarter, decimal.Decimal]]
    effective_quarter: quarter.Quarter
    employer_average_weekly_wage: Dict[uuid.UUID, decimal.Decimal]

    def __init__(self):
        self.employer_quarter_wage = {}
        self.effective_quarter = quarter.Quarter(2020, 1)
        self.employer_average_weekly_wage = {}

    def set_quarter_wage(
        self, employer_id: uuid.UUID, period: quarter.Quarter, wage: decimal.Decimal
    ) -> None:
        """Set the reported wage for the given employer and quarter."""
        if employer_id not in self.employer_quarter_wage:
            self.employer_quarter_wage[employer_id] = {}
        self.employer_quarter_wage[employer_id][period] = wage

    def set_effective_quarter(self, effective_quarter: quarter.Quarter) -> None:
        """Set the effective quarter for the computation."""
        self.effective_quarter = effective_quarter

    def get_employer_average_weekly_wage(self, employer_id):
        """Get average weekly wage for a specific employer, or raise KeyError if not found."""
        return self.employer_average_weekly_wage[employer_id]

    def compute_average_weekly_wage(self) -> decimal.Decimal:
        """Compute the average weekly wage, summed across all employers."""
        logger.info(
            "employers %i, total data rows %i",
            len(self.employer_quarter_wage),
            sum(len(value) for value in self.employer_quarter_wage.values()),
        )
        for employer_id in self.employer_quarter_wage:
            self.compute_employer_average_weekly_wage(employer_id)

        # M.G.L. c. 151A, §1(w) reads, "If such weekly wage includes a fractional part of a dollar it shall be raised
        # to the next highest dollar."
        # https://malegislature.gov/Laws/GeneralLaws/PartI/TitleXXI/Chapter151A/Section1
        next_highest_dollar = math.ceil(sum(self.employer_average_weekly_wage.values()))
        return decimal.Decimal(f"{next_highest_dollar}.00")

    def compute_employer_average_weekly_wage(self, employer_id: uuid.UUID) -> decimal.Decimal:
        """Compute average weekly wage for one employer."""
        quarter_wages = self.employer_quarter_wage[employer_id]

        base_period_quarters = base_period.compute_base_period(
            self.effective_quarter, quarter_wages
        )

        wages = []
        for reported_quarter, wage in quarter_wages.items():
            if reported_quarter in base_period_quarters:
                wages.append(wage)

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

        base_period_quarters = base_period.compute_base_period(
            self.effective_quarter, quarter_wages
        )

        total_wage = decimal.Decimal("0")
        for reported_quarter, wage in quarter_wages.items():
            if reported_quarter in base_period_quarters:
                total_wage += wage

        return total_wage

    def compute_total_quarterly_wages(self) -> Dict[quarter.Quarter, decimal.Decimal]:
        total_quarterly_wages: Dict[quarter.Quarter, decimal.Decimal] = {}

        for quarter_wages in self.employer_quarter_wage.values():
            base_period_quarters = base_period.compute_base_period(
                self.effective_quarter, quarter_wages
            )

            for reported_quarter, wage in quarter_wages.items():
                if reported_quarter in base_period_quarters and wage > 0:
                    total_quarterly_wages[reported_quarter] = (
                        total_quarterly_wages.get(reported_quarter, 0) + wage
                    )

        return total_quarterly_wages


def get_wage_calculator(
    employee_id: uuid.UUID, effective_date: datetime.date, db_session: massgov.pfml.db.Session
) -> WageCalculator:
    """Read DOR wage data from database and setup a calculator for the given employee."""
    effective_quarter = quarter.Quarter.from_date(effective_date)
    calculator = WageCalculator()
    calculator.set_effective_quarter(effective_quarter)

    rows = query_employee_wages(db_session, effective_quarter, employee_id)

    for row in rows:
        calculator.set_quarter_wage(
            row.employer_id, quarter.Quarter.from_date(row.filing_period), row.employee_qtr_wages
        )

    return calculator
