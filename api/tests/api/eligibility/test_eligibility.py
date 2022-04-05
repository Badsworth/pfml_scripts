#
# Tests for massgov.pfml.api.eligibility.
#
from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import uuid4

import pytest
from freezegun import freeze_time

from massgov.pfml import db
from massgov.pfml.api.eligibility import eligibility, wage
from massgov.pfml.api.eligibility.benefit_year import (
    find_employer_benefit_year_IAWW_contribution,
    get_benefit_year_by_employee_id,
)
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.api.eligibility.eligibility_date import eligibility_date
from massgov.pfml.api.eligibility.mock.scenario_data_generator import (
    generate_eligibility_scenario_data_in_db,
    run_eligibility_for_scenario,
)
from massgov.pfml.api.eligibility.mock.scenarios import (
    EligibilityScenarioDescriptor,
    EligibilityScenarioName,
    get_eligibility_scenario_by_name,
)
from massgov.pfml.api.eligibility.wage import get_wage_calculator
from massgov.pfml.api.models.applications.common import EligibilityEmploymentStatus
from massgov.pfml.db.models.absences import AbsenceStatus
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
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
    WagesAndContributionsFactory,
)
from massgov.pfml.util.datetime.quarter import Quarter


def test_compute_financial_eligibility_no_data(test_db_session, initialize_factories_session):
    scenario = get_eligibility_scenario_by_name(EligibilityScenarioName.NO_EXISTING_DATA)
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

    assert result == eligibility.EligibilityResponse(
        financially_eligible=False,
        description="Claimant wages under minimum",
        total_wages=Decimal("0"),
        state_average_weekly_wage=Decimal("1487.78"),
        unemployment_minimum=Decimal("5400"),
        employer_average_weekly_wage=Decimal("0"),
    )


def test_state_metrics_based_on_benefit_year_start_date(
    test_db_session, initialize_factories_session
):

    scenario = EligibilityScenarioDescriptor(
        last_x_quarters_wages=[],
        application_submitted_date=date(2021, 1, 2),
        leave_start_date=date(2021, 1, 2),
        employment_status=EligibilityEmploymentStatus.employed,
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

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
        (
            ["0", "0", "2000", "3000", "5000", "5000"],
            True,
            "Financially eligible",
            "10000",
            "307.69",
        ),
        (
            ["0", "10000", "0", "10000", "10000", "10000"],
            True,
            "Financially eligible",
            "30000",
            "769.23",
        ),
        (
            ["0", "6000", "6000", "6000", "6000", "0"],
            True,
            "Financially eligible",
            "24000",
            "461.54",
        ),
        (
            ["1000", "8000", "0", "0", "0", "0"],
            False,
            "Claimant wages failed 30x rule",
            "9000",
            "615.38",
        ),
        (["1000", "8000", "1000", "0", "0", "0"], True, "Financially eligible", "10000", "346.15"),
        (
            ["10000", "8000", "0", "0", "0", "0"],
            False,
            "Claimant wages failed 30x rule",
            "18000",
            "769.23",
        ),
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
    In these scenarios there is no data for 'current' quarter.
    """

    scenario = EligibilityScenarioDescriptor(
        last_x_quarters_wages=last_6_quarters_wages,
        application_submitted_date=date(2021, 1, 5),
        leave_start_date=date(2021, 1, 5),
        current_quarter_has_data=False,
        employment_status=EligibilityEmploymentStatus.employed,
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

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

    scenario = EligibilityScenarioDescriptor(
        last_x_quarters_wages=["0", "0", "6000", "6000", "8000", "8000"],
        application_submitted_date=date(2020, 10, 5),
        leave_start_date=date(2020, 10, 5),
    )

    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

    assert result == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=Decimal("28000"),
        state_average_weekly_wage=Decimal("1431.66"),
        unemployment_minimum=Decimal("5100.00"),
        employer_average_weekly_wage=Decimal("615.38"),
    )


@freeze_time("2021-09-13")
def test_scenario_B_case_G(test_db_session, initialize_factories_session):
    """
    Scenario is listed in the spreadsheet linked above.
    In this scenario the application is submitted 2021 Q3 after the leave has
    started 2021 Q2. The last recorded wages were in 2020 Q3.
    """
    scenario = EligibilityScenarioDescriptor(
        last_x_quarters_wages=["0", "0", "0", "24.78", "3177.13", "4333.07", "6264.50"],
        application_submitted_date=date(2021, 9, 13),
        leave_start_date=date(2021, 6, 4),
        employment_status=EligibilityEmploymentStatus.employed,
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    benefit_year_dates = get_benefit_year_dates(scenario_data.leave_start_date)
    effective_date = eligibility_date(
        benefit_year_dates.start_date, scenario_data.application_submitted_date
    )

    # To determine the effective date: if the leave start date is in the future,
    # choose application submitted date otherwise choose the leave start date.
    assert effective_date == date(2021, 5, 30)  # Q2 2021
    assert effective_date == benefit_year_dates.start_date

    # To get the base period we look at the the employee's quarterly wage history.
    # If the effective quarter has wages, then the base period ends on the effective quarter
    # If the quarter before the effective quarter has wages, then the base period ends on the quarter before the effective quarter
    # Otherwise the base period ends two quarters previous the effective quarter
    wage_calculator = wage.get_wage_calculator(
        scenario_data.employee.employee_id, effective_date, test_db_session
    )
    base_period_quarters = wage_calculator.base_period_quarters

    # Wage calculator determined that the base period
    # starts on Q1 2020
    assert base_period_quarters[-1].year == 2020
    assert base_period_quarters[-1].quarter == 1

    # and ends on Q4 2020
    assert base_period_quarters[0].year == 2020
    assert base_period_quarters[0].quarter == 4

    # Given that Q1 2020 and Q4 2020 are the range over which we are looking
    # for wages, Financial eligibility calculations will use:
    # Q1 $4333.07, Q2 $3177.13, Q3 $24.78, Q4 $0
    result = run_eligibility_for_scenario(scenario_data, test_db_session)

    assert result == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=Decimal("7534.98"),
        state_average_weekly_wage=Decimal("1487.78"),
        unemployment_minimum=Decimal("5400.00"),
        employer_average_weekly_wage=Decimal("288.85"),
    )


def test_retrieve_financial_eligibility_no_data(test_db_session, initialize_factories_session):
    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    scenario = get_eligibility_scenario_by_name(EligibilityScenarioName.NO_EXISTING_DATA)
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

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
        (
            ["0", "0", "2000", "3000", "5000", "5000"],
            True,
            "Financially eligible",
            "10000",
            "307.69",
        ),
        (
            ["0", "10000", "0", "10000", "10000", "10000"],
            True,
            "Financially eligible",
            "30000",
            "769.23",
        ),
        (
            ["0", "6000", "6000", "6000", "6000", "0"],
            True,
            "Financially eligible",
            "24000",
            "461.54",
        ),
        (
            ["1000", "8000", "0", "0", "0", "0"],
            False,
            "Claimant wages failed 30x rule",
            "9000",
            "615.38",
        ),
        (["1000", "8000", "1000", "0", "0", "0"], True, "Financially eligible", "10000", "346.15"),
        (
            ["10000", "8000", "0", "0", "0", "0"],
            False,
            "Claimant wages failed 30x rule",
            "18000",
            "769.23",
        ),
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
    In these scenarios there is no data for 'current' quarter.
    """

    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2021, 1, 5),
        leave_start_date=date(2021, 1, 5),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=last_6_quarters_wages,
        current_quarter_has_data=False,
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    wage_calculator = get_wage_calculator(
        scenario_data.employee.employee_id, scenario_data.leave_start_date, test_db_session
    )
    (
        expected_base_period_start_date,
        expected_base_period_end_date,
    ) = wage_calculator.get_base_period_quarters_as_dates()

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

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
        assert benefit_years_after[0].employee_id == scenario_data.employee.employee_id
        assert benefit_years_after[0].total_wages == Decimal(expected_total_wages)
        assert benefit_years_after[0].base_period_start_date == expected_base_period_start_date
        assert benefit_years_after[0].base_period_end_date == expected_base_period_end_date
        expected_date_range = get_benefit_year_dates(scenario_data.leave_start_date)
        assert benefit_years_after[0].start_date == expected_date_range.start_date
        assert benefit_years_after[0].end_date == expected_date_range.end_date

        assert len(benefit_years_after[0].contributions) == 1
        assert (
            benefit_years_after[0].contributions[0].employer_id
            == scenario_data.employer.employer_id
        )
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
    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["0", "0", "6000", "6000", "8000", "8000"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    expected_total_wages = Decimal("28000")

    wage_calculator = get_wage_calculator(
        scenario_data.employee.employee_id, scenario_data.leave_start_date, test_db_session
    )
    (
        expected_base_period_start_date,
        expected_base_period_end_date,
    ) = wage_calculator.get_base_period_quarters_as_dates()

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    result = eligibility.retrieve_financial_eligibility(
        test_db_session,
        scenario_data.employee.employee_id,
        scenario_data.employer.employer_id,
        scenario_data.leave_start_date,
        scenario_data.application_submitted_date,
        scenario_data.employment_status,
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
    assert benefit_years_after[0].employee_id == scenario_data.employee.employee_id
    assert benefit_years_after[0].total_wages == Decimal(expected_total_wages)
    assert benefit_years_after[0].base_period_start_date == expected_base_period_start_date
    assert benefit_years_after[0].base_period_end_date == expected_base_period_end_date

    expected_date_range = get_benefit_year_dates(scenario_data.leave_start_date)
    assert benefit_years_after[0].start_date == expected_date_range.start_date
    assert benefit_years_after[0].end_date == expected_date_range.end_date

    assert len(benefit_years_after[0].contributions) == 1
    assert benefit_years_after[0].contributions[0].employer_id == scenario_data.employer.employer_id
    assert (
        benefit_years_after[0].contributions[0].average_weekly_wage
        == result.employer_average_weekly_wage
    )


def test_existing_BY_provides_different_IAWW_than_would_be_calculated_by_FE_1(
    test_db_session: db.Session, initialize_factories_session
):

    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["25000", "25000", "25000"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        scenario_data.employee.employee_id,
        scenario_data.employer.employer_id,
        scenario_data.leave_start_date,
        scenario_data.application_submitted_date,
        scenario_data.employment_status,
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
        scenario_data.employee.employee_id,
        scenario_data.employer.employer_id,
        scenario_data.leave_start_date,
        scenario_data.application_submitted_date,
        scenario_data.employment_status,
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
    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["25000", "25000", "25000"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = eligibility.compute_financial_eligibility(
        test_db_session,
        scenario_data.employee.employee_id,
        scenario_data.employer.employer_id,
        scenario_data.leave_start_date,
        scenario_data.application_submitted_date,
        scenario_data.employment_status,
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
    benefit_year_dates = get_benefit_year_dates(scenario_data.leave_start_date)
    benefit_year_created = BenefitYear()
    benefit_year_created.start_date = benefit_year_dates.start_date
    benefit_year_created.end_date = benefit_year_dates.end_date
    benefit_year_created.employee_id = scenario_data.employee.employee_id
    benefit_year_created.total_wages = Decimal("90000")
    benefit_year_contribution = BenefitYearContribution()
    benefit_year_contribution.employee_id = scenario_data.employee.employee_id
    benefit_year_contribution.employer_id = scenario_data.employer.employer_id
    benefit_year_contribution.average_weekly_wage = Decimal("1000")
    benefit_year_created.contributions.append(benefit_year_contribution)
    test_db_session.add(benefit_year_created)

    # Confirm the values are the stored not computed values
    result_2 = eligibility.retrieve_financial_eligibility(
        test_db_session,
        scenario_data.employee.employee_id,
        scenario_data.employer.employer_id,
        scenario_data.leave_start_date,
        scenario_data.application_submitted_date,
        scenario_data.employment_status,
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

    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["25000", "25000", "25000"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    # Previous claim 6 months in the past and went for 6 weeks
    fineos_average_weekly_wage = Decimal("123.34")
    claim_start_date = scenario_data.leave_start_date - timedelta(weeks=52 / 2)
    claim_end_date = claim_start_date + timedelta(weeks=6)
    claim: Claim = ClaimFactory.create(
        employee=scenario_data.employee,
        employer=scenario_data.employer,
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
        employee=scenario_data.employee,
        employer=scenario_data.employer,
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

    result = run_eligibility_for_scenario(scenario_data, test_db_session)
    benefit_year_created = test_db_session.query(BenefitYear).one()
    assert benefit_year_created.total_wages is None
    assert benefit_year_created.contributions[0].average_weekly_wage == fineos_average_weekly_wage

    assert result == eligibility.EligibilityResponse(
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

    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["25000", "25000", "25000"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    # Previous claim 6 months in the past and went for 6 weeks
    fineos_average_weekly_wage = Decimal("123.34")
    claim_start_date = scenario_data.leave_start_date - timedelta(weeks=52 / 2)
    claim_end_date = claim_start_date + timedelta(weeks=6)
    claim: Claim = ClaimFactory.create(
        employee=scenario_data.employee,
        employer=scenario_data.employer,
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
        employee=scenario_data.employee,
        employer=scenario_data.employer,
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

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

    benefit_years_created = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_created) == 2
    assert benefit_years_created[1].total_wages is None
    assert (
        benefit_years_created[1].contributions[0].average_weekly_wage == fineos_average_weekly_wage
    )

    assert result == eligibility.EligibilityResponse(
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

    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["1", "4"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result = run_eligibility_for_scenario(scenario_data, test_db_session)

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

    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["1", "4"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = run_eligibility_for_scenario(scenario_data, test_db_session)

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
    benefit_year_dates = get_benefit_year_dates(scenario_data.leave_start_date)
    benefit_year_created = BenefitYear()
    benefit_year_created.start_date = benefit_year_dates.start_date
    benefit_year_created.end_date = benefit_year_dates.end_date
    benefit_year_created.employee_id = scenario_data.employee.employee_id
    benefit_year_created.total_wages = Decimal("90000")
    benefit_year_contribution = BenefitYearContribution()
    benefit_year_contribution.employee_id = scenario_data.employee.employee_id
    benefit_year_contribution.employer_id = scenario_data.employer.employer_id
    benefit_year_contribution.average_weekly_wage = Decimal("1000")
    benefit_year_created.contributions.append(benefit_year_contribution)
    test_db_session.add(benefit_year_created)

    # Confirm the values are the stored not computed values
    result_2 = run_eligibility_for_scenario(scenario_data, test_db_session)
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

    scenario = EligibilityScenarioDescriptor(
        application_submitted_date=date(2020, 11, 1),
        leave_start_date=date(2020, 11, 1),
        employment_status=EligibilityEmploymentStatus.employed,
        last_x_quarters_wages=["1", "4"],
    )
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)

    benefit_years_before = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_before) == 0

    # Get baseline values for FE check without BY
    result_1 = run_eligibility_for_scenario(scenario_data, test_db_session)

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
    claim_start_date = scenario_data.leave_start_date - timedelta(weeks=52 / 2)
    claim_end_date = claim_start_date + timedelta(weeks=6)
    claim: Claim = ClaimFactory.create(
        employee=scenario_data.employee,
        employer=scenario_data.employer,
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
        employee=scenario_data.employee,
        employer=scenario_data.employer,
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
    result_2 = run_eligibility_for_scenario(scenario_data, test_db_session)

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
    employment_status = EligibilityEmploymentStatus.employed
    employers: List[Employer] = []
    employer_ids_with_wages = set()

    employer_id = employer_id_to_use
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
        [E4, []],  # No wage data
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


@pytest.mark.parametrize(
    "scenario_name, is_eligible, expected_description, expected_total_wages, expected_weekly_avg",
    [
        (
            EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR,
            True,
            "Financially eligible",
            "48000",
            "923.08",
        ),
        (
            EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR_MULTIPLE_EMPLOYERS,
            True,
            "Financially eligible",
            "84000",
            "923.08",
        ),
        (
            EligibilityScenarioName.NO_EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN,
            False,
            "Claimant wages under minimum",
            "4000",
            "76.92",
        ),
        (
            EligibilityScenarioName.EXISTING_BENEFIT_YEAR_WAGES_UNDER_MIN,
            True,
            "Financially eligible",
            "24000",
            "1000",
        ),
        (
            EligibilityScenarioName.EXISTING_BENEFIT_YEAR_KEEP_HIGHER_IAWW,
            True,
            "Financially eligible",
            "30000",
            "1250",
        ),
        (
            EligibilityScenarioName.EXISTING_BENEFIT_YEAR_KEEP_LOWER_IAWW,
            True,
            "Financially eligible",
            "48000",
            "923.08",
        ),
    ],
)
def test_compute_financial_eligibility_benefit_year_scenarios(
    test_db_session,
    initialize_factories_session,
    is_eligible,
    scenario_name,
    expected_description,
    expected_total_wages,
    expected_weekly_avg,
):
    scenario_data = generate_eligibility_scenario_data_in_db(
        get_eligibility_scenario_by_name(scenario_name), test_db_session
    )

    result = run_eligibility_for_scenario(scenario_data, test_db_session)

    assert result == eligibility.EligibilityResponse(
        financially_eligible=is_eligible,
        description=expected_description,
        total_wages=Decimal(expected_total_wages),
        state_average_weekly_wage=Decimal("1487.78"),
        unemployment_minimum=Decimal("5400.00"),
        employer_average_weekly_wage=Decimal(expected_weekly_avg),
    )


def test_benefit_year_eligibility_mulitple_employers(test_db_session, initialize_factories_session):
    # In this scenario the second claim within the benefit year is for a different employer.
    # IAWW should still be based on the wage data when the benefit year was originally created.

    # set up initial scenario

    scenario = EligibilityScenarioDescriptor(
        last_x_quarters_wages=["6000", "6000", "6000", "6000", "6000", "6000"],
        last_x_quarters_wages_other_employer=["4000", "4000", "4000", "4000", "4000", "4000"],
    )

    # create the benefit year based on a finanical eligibility check for Employer A
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)
    first_result = run_eligibility_for_scenario(scenario_data, test_db_session)

    # add additional wage data for Employer B
    employee = scenario_data.employee
    other_employer = scenario_data.other_employer
    for curr_quarter in Quarter.from_date(scenario_data.leave_start_date).series(2):
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=other_employer,
            filing_period=curr_quarter.start_date(),
            employee_qtr_wages="6000",
        )

    # run financial eligibility for a new claim from Employer B
    second_result = eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee.employee_id,
        other_employer.employer_id,
        date(2021, 12, 1),
        date(2021, 12, 1),
        EligibilityEmploymentStatus.employed,
    )

    assert second_result == eligibility.EligibilityResponse(
        financially_eligible=True,
        description="Financially eligible",
        total_wages=first_result.total_wages,
        state_average_weekly_wage=Decimal("1487.78"),
        unemployment_minimum=Decimal("5400.00"),
        employer_average_weekly_wage=Decimal("307.69"),
    )


def test_benefit_year_calculates_employer_iaww(test_db_session, initialize_factories_session):
    # In this scenario the second claim within the benefit year is for a different employer,
    # that we didn't have IAWW for when we created the beneift year.
    # IAWW for the employer should be calculated and stored on the benefit year

    # set up initial scenario

    scenario = EligibilityScenarioDescriptor(
        last_x_quarters_wages=["6000", "6000", "6000", "6000", "6000", "6000"],
    )

    # create the benefit year based on a finanical eligibility check for Employer A
    scenario_data = generate_eligibility_scenario_data_in_db(scenario, test_db_session)
    employee = scenario_data.employee
    other_employer = EmployerFactory.create()

    run_eligibility_for_scenario(scenario_data, test_db_session)
    benefit_year = get_benefit_year_by_employee_id(
        test_db_session, employee.employee_id, scenario_data.leave_start_date
    )
    employer_2_iaww = find_employer_benefit_year_IAWW_contribution(
        benefit_year, other_employer.employer_id
    )

    assert employer_2_iaww is None

    starting_quarter = Quarter.from_date(scenario_data.leave_start_date)

    # add wage data for second employer
    for quarter in Quarter.series_backwards(starting_quarter, 8):
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=other_employer,
            filing_period=quarter.start_date(),
            employee_qtr_wages="4000",
        )

    test_db_session.commit()

    # run financial eligibility for a new claim from Employer B
    eligibility.retrieve_financial_eligibility(
        test_db_session,
        employee.employee_id,
        other_employer.employer_id,
        date(2021, 12, 1),
        date(2021, 12, 1),
        EligibilityEmploymentStatus.employed,
    )

    test_db_session.refresh(benefit_year)

    employer_2_iaww = find_employer_benefit_year_IAWW_contribution(
        benefit_year, other_employer.employer_id
    )

    assert employer_2_iaww is not None
