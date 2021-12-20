#
# Tests for massgov.pfml.api.eligibility.
#

from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

import pytest

from massgov.pfml import db
from massgov.pfml.api.eligibility import eligibility
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.api.eligibility.wage import get_wage_calculator
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    AbsenceStatus,
    BenefitYear,
    BenefitYearContribution,
    Claim,
    ClaimType,
    Employer,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)


def test_compute_financial_eligibility_no_data(test_db_session):
    result = eligibility.compute_financial_eligibility(
        test_db_session,
        UUID(int=1),
        UUID(int=2),
        "100000055",
        date(2021, 1, 5),
        date(2021, 1, 5),
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


def test_state_metrics_based_on_benefit_year_start_date(test_db_session):
    result = eligibility.compute_financial_eligibility(
        test_db_session,
        UUID(int=1),
        UUID(int=2),
        "100000055",
        date(2021, 1, 2),
        date(2021, 1, 2),
        "Employed",
    )

    # 01/02/2021 is a Saturday, so we should be using the prior Sunday
    # (12/27/2020) to look up the SAWW and the UI minimum.
    # For reference, if we were incorrectly using the leave start date to
    # look these up, we would get a SAWW of 1487.78 and a UI minimum of
    # 5400 instead.
    assert result == eligibility.EligibilityResponse(
        financially_eligible=False,
        description="Claimant wages under minimum",
        total_wages=Decimal("0"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
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
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2021, 1, 5)
    leave_start_date = date(2021, 1, 5)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
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
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 10, 5)
    leave_start_date = date(2020, 10, 5)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
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


def test_retrieve_financial_eligibility_no_data(test_db_session, initialize_factories_session):
    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    result = eligibility.retrieve_financial_eligibility(
        test_db_session,
        uuid4(),
        uuid4(),
        "100000055",
        date(2021, 1, 5),
        date(2021, 1, 5),
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

    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == 0


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
def test_retrieve_financial_eligibility_multiple_scenarios(
    test_db_session: db.Session,
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
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2021, 1, 5)
    leave_start_date = date(2021, 1, 5)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
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
    wage_calculator = get_wage_calculator(employee_id, leave_start_date, test_db_session)
    (
        expected_base_period_start_date,
        expected_base_period_end_date,
    ) = wage_calculator.get_base_period_quarters_as_dates()

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    result = eligibility.retrieve_financial_eligibility(
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

    benefit_years_after = test_db_session.query(BenefitYear).all()

    if not is_eligible:
        assert len(benefit_years_after) == 0
    else:
        assert len(benefit_years_after) == 1
        assert benefit_years_after[0].employee_id == employee_id
        assert benefit_years_after[0].total_wages == Decimal(expected_total_wages)
        assert benefit_years_after[0].base_period_start_date == expected_base_period_start_date
        assert benefit_years_after[0].base_period_end_date == expected_base_period_end_date
        expected_date_range = get_benefit_year_dates(leave_start_date)
        assert benefit_years_after[0].start_date == expected_date_range.start_date
        assert benefit_years_after[0].end_date == expected_date_range.end_date

        assert len(benefit_years_after[0].contributions) == 1
        assert benefit_years_after[0].contributions[0].employer_id == employer_id
        assert (
            benefit_years_after[0].contributions[0].average_weekly_wage
            == result.employer_average_weekly_wage
        )


def test_retrieve_financial_eligibility_scenario_A_case_B(
    test_db_session, initialize_factories_session
):
    """
    In this scenario there is recorded wage data of 0 dollars for the current quarter
    """

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
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

    expected_total_wages = Decimal("28000")

    wage_calculator = get_wage_calculator(employee_id, leave_start_date, test_db_session)
    (
        expected_base_period_start_date,
        expected_base_period_end_date,
    ) = wage_calculator.get_base_period_quarters_as_dates()

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    result = eligibility.retrieve_financial_eligibility(
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

    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == 1
    assert benefit_years_after[0].employee_id == employee_id
    assert benefit_years_after[0].total_wages == Decimal(expected_total_wages)
    assert benefit_years_after[0].base_period_start_date == expected_base_period_start_date
    assert benefit_years_after[0].base_period_end_date == expected_base_period_end_date

    expected_date_range = get_benefit_year_dates(leave_start_date)
    assert benefit_years_after[0].start_date == expected_date_range.start_date
    assert benefit_years_after[0].end_date == expected_date_range.end_date

    assert len(benefit_years_after[0].contributions) == 1
    assert benefit_years_after[0].contributions[0].employer_id == employer_id
    assert (
        benefit_years_after[0].contributions[0].average_weekly_wage
        == result.employer_average_weekly_wage
    )


def test_existing_BY_provides_different_IAWW_than_would_be_calculated_by_FE_1(
    test_db_session: db.Session, initialize_factories_session
):

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 10, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 7, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 4, 1),
        employee_qtr_wages=25_000,
    )

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    assert result_1 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=Decimal("75000"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("1923.08"),
    )

    # Alter the BY data with differing total_wages and employer_average_weekly_wage
    benefit_year_created = test_db_session.query(BenefitYear).one()
    benefit_year_created.total_wages = Decimal("90000")
    benefit_year_created.contributions[0].average_weekly_wage = Decimal("1000")

    # Confirm the values are the stored not computed values
    result_2 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    assert result_2 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=benefit_year_created.total_wages,
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=benefit_year_created.contributions[0].average_weekly_wage,
    )


def test_existing_BY_provides_different_IAWW_than_would_be_calculated_by_FE_2(
    test_db_session: db.Session, initialize_factories_session
):

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 11, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 7, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 4, 1),
        employee_qtr_wages=25_000,
    )

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.compute_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    assert result_1 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=Decimal("75000"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("1923.08"),
    )

    # Create a BY with differing total_wages and employer_average_weekly_wage
    benefit_year_dates = get_benefit_year_dates(leave_start_date)
    benefit_year_created = BenefitYear()
    benefit_year_created.start_date = benefit_year_dates.start_date
    benefit_year_created.end_date = benefit_year_dates.end_date
    benefit_year_created.employee_id = employee_id
    benefit_year_created.total_wages = Decimal("90000")
    benefit_year_contribution = BenefitYearContribution()
    benefit_year_contribution.employee_id = employee_id
    benefit_year_contribution.employer_id = employer_id
    benefit_year_contribution.average_weekly_wage = Decimal("1000")
    benefit_year_created.contributions.append(benefit_year_contribution)
    test_db_session.add(benefit_year_created)

    # Confirm the values are the stored not computed values
    result_2 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    assert result_2 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=benefit_year_created.total_wages,
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=benefit_year_created.contributions[0].average_weekly_wage,
    )


def test_BY_from_previous_leave_absence_provides_different_IAWW_than_would_be_calculated_by_FE_1(
    test_db_session: db.Session, initialize_factories_session
):

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 11, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 7, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 4, 1),
        employee_qtr_wages=25_000,
    )

    # Previous claim 6 months in the past and went for 6 weeks
    fineos_average_weekly_wage = Decimal("123.34")
    claim_start_date = leave_start_date - timedelta(weeks=52 / 2)
    claim_end_date = claim_start_date + timedelta(weeks=6)
    claim: Claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=claim_start_date,
        absence_period_end_date=claim_end_date,
    )
    absence_period: AbsencePeriod = AbsencePeriodFactory.create(
        claim=claim, fineos_average_weekly_wage=fineos_average_weekly_wage
    )
    claim.absence_periods = [absence_period]
    # This claim is in the same BY
    claim_start_date_2 = claim_end_date + timedelta(weeks=2)
    claim_end_date_2 = claim_start_date_2 + timedelta(weeks=6)
    claim_2: Claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=claim_start_date_2,
        absence_period_end_date=claim_end_date_2,
    )
    absence_period_2: AbsencePeriod = AbsencePeriodFactory.create(
        claim=claim_2, fineos_average_weekly_wage=Decimal("100")
    )
    claim_2.absence_periods = [absence_period_2]

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.compute_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    assert result_1 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=Decimal("75000"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("1923.08"),
    )

    # Confirm the values are stored from previous claim data and not computed values
    result_2 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    benefit_year_created = test_db_session.query(BenefitYear).one()
    assert benefit_year_created.total_wages is None
    assert benefit_year_created.contributions[0].average_weekly_wage == fineos_average_weekly_wage

    assert result_2 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=benefit_year_created.total_wages,
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=fineos_average_weekly_wage,
    )


def test_BY_from_previous_leave_absence_provides_different_IAWW_than_would_be_calculated_by_FE_2(
    test_db_session: db.Session, initialize_factories_session
):

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 11, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 7, 1),
        employee_qtr_wages=25_000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 4, 1),
        employee_qtr_wages=25_000,
    )

    # Previous claim 6 months in the past and went for 6 weeks
    fineos_average_weekly_wage = Decimal("123.34")
    claim_start_date = leave_start_date - timedelta(weeks=52 / 2)
    claim_end_date = claim_start_date + timedelta(weeks=6)
    claim: Claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=claim_start_date,
        absence_period_end_date=claim_end_date,
    )
    absence_period: AbsencePeriod = AbsencePeriodFactory.create(
        claim=claim, fineos_average_weekly_wage=fineos_average_weekly_wage
    )
    claim.absence_periods = [absence_period]
    # This claim is in the previous BY
    claim_start_date_2 = claim_start_date - timedelta(weeks=52)
    claim_end_date_2 = claim_start_date_2 + timedelta(weeks=6)
    claim_2: Claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=claim_start_date_2,
        absence_period_end_date=claim_end_date_2,
    )
    absence_period_2: AbsencePeriod = AbsencePeriodFactory.create(
        claim=claim_2, fineos_average_weekly_wage=Decimal("100")
    )
    claim_2.absence_periods = [absence_period_2]

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.compute_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    assert result_1 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=Decimal("75000"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("1923.08"),
    )

    # Confirm the values are stored from previous claim data and not computed values
    result_2 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    benefit_years_created = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_created) == 2
    assert benefit_years_created[1].total_wages is None
    assert (
        benefit_years_created[1].contributions[0].average_weekly_wage == fineos_average_weekly_wage
    )

    assert result_2 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=benefit_years_created[1].total_wages,
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=fineos_average_weekly_wage,
    )


def test_benefit_year_is_not_created_when_claimant_is_ineligible(
    test_db_session: db.Session, initialize_factories_session
):

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 11, 1), employee_qtr_wages=1,
    )
    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 7, 1), employee_qtr_wages=4,
    )

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    # No benefit year should be created
    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == 0

    assert result == eligibility.EligibilityResponse(
        financially_eligible=False,
        description="Claimant wages under minimum",
        total_wages=Decimal("5"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("0.31"),
    )


def test_existing_BY_keeps_someone_eligible_who_would_be_calculated_to_be_ineligible_otherwise(
    test_db_session: db.Session, initialize_factories_session
):

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 11, 1), employee_qtr_wages=1,
    )
    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 7, 1), employee_qtr_wages=4,
    )

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    # No benefit year should be created
    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == 0

    assert result_1 == eligibility.EligibilityResponse(
        financially_eligible=False,
        description="Claimant wages under minimum",
        total_wages=Decimal("5"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("0.31"),
    )

    # Create a BY with differing total_wages and employer_average_weekly_wage
    benefit_year_dates = get_benefit_year_dates(leave_start_date)
    benefit_year_created = BenefitYear()
    benefit_year_created.start_date = benefit_year_dates.start_date
    benefit_year_created.end_date = benefit_year_dates.end_date
    benefit_year_created.employee_id = employee_id
    benefit_year_created.total_wages = Decimal("90000")
    benefit_year_contribution = BenefitYearContribution()
    benefit_year_contribution.employee_id = employee_id
    benefit_year_contribution.employer_id = employer_id
    benefit_year_contribution.average_weekly_wage = Decimal("1000")
    benefit_year_created.contributions.append(benefit_year_contribution)
    test_db_session.add(benefit_year_created)

    # Confirm the values are the stored not computed values
    result_2 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    assert result_2 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=benefit_year_created.total_wages,
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=benefit_year_created.contributions[0].average_weekly_wage,
    )


def test_BY_from_previous_leave_absence_keeps_someone_eligible_who_would_be_calculated_to_be_ineligible_otherwise(
    test_db_session: db.Session, initialize_factories_session
):

    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employer_id = employer.employer_id
    employment_status = "Employed"

    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 11, 1), employee_qtr_wages=1,
    )
    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 7, 1), employee_qtr_wages=4,
    )

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    # No benefit year should be created
    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == 0

    assert result_1 == eligibility.EligibilityResponse(
        financially_eligible=False,
        description="Claimant wages under minimum",
        total_wages=Decimal("5"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("0.31"),
    )

    # Create a BY with differing total_wages and employer_average_weekly_wage
    # Previous claim 6 months in the past and went for 6 weeks
    fineos_average_weekly_wage = Decimal("123.34")
    claim_start_date = leave_start_date - timedelta(weeks=52 / 2)
    claim_end_date = claim_start_date + timedelta(weeks=6)
    claim: Claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=claim_start_date,
        absence_period_end_date=claim_end_date,
    )
    absence_period: AbsencePeriod = AbsencePeriodFactory.create(
        claim=claim, fineos_average_weekly_wage=fineos_average_weekly_wage
    )
    claim.absence_periods = [absence_period]
    # This claim is in the same BY
    claim_start_date_2 = claim_end_date + timedelta(weeks=2)
    claim_end_date_2 = claim_start_date_2 + timedelta(weeks=6)
    claim_2: Claim = ClaimFactory.create(
        employee=employee,
        employer=employer,
        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=claim_start_date_2,
        absence_period_end_date=claim_end_date_2,
    )
    absence_period_2: AbsencePeriod = AbsencePeriodFactory.create(
        claim=claim_2, fineos_average_weekly_wage=Decimal("100")
    )
    claim_2.absence_periods = [absence_period_2]

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Confirm the values are the stored not computed values
    result_2 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )

    benefit_year_created = test_db_session.query(BenefitYear).one()
    assert benefit_year_created.total_wages is None
    assert benefit_year_created.contributions[0].average_weekly_wage == fineos_average_weekly_wage

    assert result_2 == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=benefit_year_created.total_wages,
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=fineos_average_weekly_wage,
    )


E1 = uuid4()
E2 = uuid4()
E3 = uuid4()
E4 = uuid4()
E5 = uuid4()
E6 = uuid4()
E7 = uuid4()
E8 = uuid4()
E9 = uuid4()
E10 = uuid4()


@pytest.mark.parametrize("employer_id_to_use", [E1, E2, E2, E4, E5, E6, E7, E8])
def test_retrieve_financial_eligibility_multiple_employers(
    test_db_session, initialize_factories_session, employer_id_to_use
):
    employee = EmployeeFactory.create()
    application_submitted_date = date(2020, 11, 1)
    leave_start_date = date(2020, 11, 1)
    employee_id = employee.employee_id
    employment_status = "Employed"
    employers: List[Employer] = []
    employer_ids_with_wages = set()

    employer_id = employer_id_to_use
    employer_fein = None
    quarters = [
        date(2020, 10, 1),
        date(2020, 7, 1),
        date(2020, 4, 1),
        date(2020, 1, 1),
        date(2019, 10, 1),
        date(2019, 7, 1),
    ]
    employer_wage_data = [
        [E1, [6000, 6000, 6000, 6000, 8000, 8000]],
        [E2, [1, 1, 1, 1, 1, 1]],
        [E3, [2, 2, 2, 2, 2, 2]],
        [E4, [],],  # No wage data
        [E5, [3, 3, 3, 3, 3, 3]],
        [E6, []],
        [E7, [0, 0, 0, 0, 0, 0]],  # No non-zero wage data,
        [E8, [0, 0, 0, 0, 0, 1]],
    ]
    for new_employer_id, employer_wages in employer_wage_data:
        new_employer = EmployerFactory.create(employer_id=new_employer_id)
        employers.append(new_employer)
        for q, quarter in enumerate(quarters):
            employer_contains_wages = False
            try:
                WagesAndContributionsFactory.create(
                    employee=employee,
                    employer=new_employer,
                    filing_period=quarter,
                    employee_qtr_wages=employer_wages[q],
                )
                if employer_wages[q] > 0:
                    employer_contains_wages = True
            except IndexError:
                pass
            if employer_contains_wages:
                employer_ids_with_wages.add(new_employer.employer_id)

    effective_date = eligibility.eligibility_date(leave_start_date, application_submitted_date)
    wage_calculator = get_wage_calculator(employee_id, effective_date, test_db_session)
    (
        expected_base_period_start_date,
        expected_base_period_end_date,
    ) = wage_calculator.get_base_period_quarters_as_dates()
    computed_wage_data = wage_calculator.compute_employee_dor_wage_data()
    expected_total_wages = computed_wage_data.total_wages

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    expected_employer_average_weekly_wage = wage_calculator.get_employer_average_weekly_wage(
        employer_id, default=Decimal("0"), should_round=True
    )
    assert expected_employer_average_weekly_wage is not None

    result = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee_id,
        employer_id,
        employer_fein,
        leave_start_date,
        application_submitted_date,
        employment_status,
    )
    expected_result = eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=expected_total_wages,
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=expected_employer_average_weekly_wage,
    )

    assert result.total_wages == expected_result.total_wages
    assert result.state_average_weekly_wage == expected_result.state_average_weekly_wage
    assert result.unemployment_minimum == expected_result.unemployment_minimum
    assert result.employer_average_weekly_wage == expected_result.employer_average_weekly_wage
    assert result.description == expected_result.description
    assert result.financially_eligible == expected_result.financially_eligible

    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == 1
    assert benefit_years_after[0].employee_id == employee_id
    assert benefit_years_after[0].total_wages == expected_total_wages
    assert benefit_years_after[0].base_period_start_date == expected_base_period_start_date
    assert benefit_years_after[0].base_period_end_date == expected_base_period_end_date

    expected_date_range = get_benefit_year_dates(leave_start_date)
    assert benefit_years_after[0].start_date == expected_date_range.start_date
    assert benefit_years_after[0].end_date == expected_date_range.end_date

    # Verify contributions are all created
    assert len(benefit_years_after[0].contributions) == len(employer_ids_with_wages)

    contribution_employer_ids = [
        contribution.employer_id for contribution in benefit_years_after[0].contributions
    ]
    intersection = list(employer_ids_with_wages.intersection(contribution_employer_ids))
    assert len(intersection) == len(employer_ids_with_wages)

    for contribution in benefit_years_after[0].contributions:
        assert contribution.employer_id in employer_ids_with_wages
        expected_employer_average_weekly_wage = wage_calculator.get_employer_average_weekly_wage(
            contribution.employer_id, default=Decimal("0"), should_round=True
        )
        assert contribution.average_weekly_wage == expected_employer_average_weekly_wage
