#
# Tests for massgov.pfml.api.eligibility.
#

from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from massgov.pfml.api.eligibility import eligibility
from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.types import Fein, TaxId


@pytest.mark.integration
def test_compute_financial_eligibility_no_data(test_db_session):
    result = eligibility.compute_financial_eligibility(
        test_db_session,
        UUID(int=1),
        UUID(int=2),
        "100000055",
        date(2021, 1, 1),
        date(2021, 1, 1),
        "Employed",
    )

    assert result == eligibility.EligibilityResponse(
        financially_eligible=False,
        description="Claimant wages under minimum",
        total_wages=Decimal("0"),
        state_average_weekly_wage=Decimal("1487.78"),
        unemployment_minimum=Decimal("5400"),
        employer_average_weekly_wage=Decimal("0"),
    )


# Testing Scenarios found here:
# https://docs.google.com/spreadsheets/d/1RAJaUNo2pMlVHhEniwEpg_5pBISs-dEKAw7FXF-E5kQ/edit?ts=60f19864#gid=1138956639
@pytest.mark.parametrize(
    "last_6_quarters_wages, is_eligible, expected_description, expected_total_wages, expected_weekly_avg",
    [
        ([0, 0, 2000, 3000, 5000, 5000], True, "Financially eligible", "10000", "307.69"),
        ([0, 10000, 0, 10000, 10000, 10000], True, "Financially eligible", "30000", "769.23"),
        ([0, 6000, 6000, 6000, 6000, 0], True, "Financially eligible", "24000", "461.54"),
        ([1000, 8000, 0, 0, 0, 0], False, "Claimant wages failed 30x rule", "9000", "615.38"),
        ([1000, 8000, 1000, 0, 0, 0], True, "Financially eligible", "10000", "346.15"),
        ([10000, 8000, 0, 0, 0, 0], False, "Claimant wages failed 30x rule", "18000", "769.23"),
    ],
)
def test_compute_financial_eligibility_multiple_scenarios(
    test_db_session,
    initialize_factories_session,
    last_6_quarters_wages,
    is_eligible,
    expected_description,
    expected_total_wages,
    expected_weekly_avg,
):
    """
    In these scenarios thre is no data for 'current' quarter.
    """

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier=TaxId("088574541"))
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=Fein(str(employer_fein)))
    application_submitted_date = date(2021, 1, 1)
    leave_start_date = date(2021, 1, 1)
    employee_id = UUID(str(employee.employee_id))
    employer_id = UUID(str(employer.employer_id))
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 10, 1),
        employee_qtr_wages=last_6_quarters_wages[0],
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 7, 1),
        employee_qtr_wages=last_6_quarters_wages[1],
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 4, 1),
        employee_qtr_wages=last_6_quarters_wages[2],
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 1, 1),
        employee_qtr_wages=last_6_quarters_wages[3],
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2019, 10, 1),
        employee_qtr_wages=last_6_quarters_wages[4],
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2019, 7, 1),
        employee_qtr_wages=last_6_quarters_wages[5],
    )

    result = eligibility.compute_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    assert result == eligibility.EligibilityResponse(
        financially_eligible=is_eligible,
        description=expected_description,
        total_wages=Decimal(expected_total_wages),
        state_average_weekly_wage=Decimal("1487.78"),
        unemployment_minimum=Decimal("5400.00"),
        employer_average_weekly_wage=Decimal(expected_weekly_avg),
    )


def test_scenario_A_case_B(test_db_session, initialize_factories_session):
    """
    In this scenario there is recorded wage data of 0 dollars for the current quarter
    """

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier=TaxId("088574541"))
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=Fein(str(employer_fein)))
    application_submitted_date = date(2020, 10, 1)
    leave_start_date = date(2020, 10, 1)
    employee_id = UUID(str(employee.employee_id))
    employer_id = UUID(str(employer.employer_id))
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 10, 1), employee_qtr_wages=0,
    )
    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 7, 1), employee_qtr_wages=0,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 4, 1),
        employee_qtr_wages=6000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 1, 1),
        employee_qtr_wages=6000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2019, 10, 1),
        employee_qtr_wages=8000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2019, 7, 1),
        employee_qtr_wages=8000,
    )

    result = eligibility.compute_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    assert result == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=Decimal("28000"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("615.38"),
    )
