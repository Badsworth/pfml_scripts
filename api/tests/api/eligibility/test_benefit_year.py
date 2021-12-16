from datetime import date, timedelta
from typing import List, Optional

import pytest
from freezegun.api import freeze_time
from werkzeug.exceptions import NotFound

from massgov.pfml import db
from massgov.pfml.api.eligibility.benefit_year import (
    AbsenceStatusesWithBenefitYear,
    CreateBenefitYearContribution,
    _get_earliest_claim_in_benefit_year,
    create_benefit_year_by_ssn,
    get_benefit_year_by_ssn,
    set_base_period_for_benefit_year,
)
from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates
from massgov.pfml.db.models.employees import (
    AbsencePeriod,
    AbsenceStatus,
    BenefitYear,
    BenefitYearContribution,
    Claim,
    ClaimType,
    Employee,
    Employer,
    TaxIdentifier,
)
from massgov.pfml.db.models.factories import (
    AbsencePeriodFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)


@pytest.fixture
def include_dummy_claims(initialize_factories_session):
    employers: List[Employer] = []
    employees: List[Employee] = []
    claims: List[Claim] = []

    for _er in range(5):
        employer: Employer = EmployerFactory.create()
        employers.append(employer)
        for _ee in range(10):
            employee: Employee = EmployeeFactory.create()
            employees.append(employee)
            for c in range(6):
                start_date = date(2019, 1, 1) + timedelta(weeks=(52 / 2) * c)
                end_date = start_date + timedelta(weeks=(52 / 2) * c)
                claims.append(
                    ClaimFactory.create(
                        employee=employee,
                        employer=employer,
                        claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
                        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                        absence_period_start_date=start_date,
                        absence_period_end_date=end_date,
                    )
                )


@pytest.fixture
def include_employee(initialize_factories_session):
    employee: Employee = EmployeeFactory.create()
    return employee


@pytest.fixture
def include_employers(initialize_factories_session):
    employer1: Employer = EmployerFactory.create()
    employer2: Employer = EmployerFactory.create()
    return [employer1, employer2]


@pytest.fixture
def include_employee_claims(include_employee: Employee, include_employers: List[Employer]):
    claims: List[Claim] = []

    # Absence dates for claims
    # 2018-12-31 (Mon) 2019-04-01 (Mon)
    # 2019-04-02 (Tue) 2019-10-01 (Tue)
    # 2019-07-03 (Wed) 2020-04-01 (Wed)
    # 2019-10-03 (Thu) 2020-10-01 (Thu)
    # 2020-01-03 (Fri) 2021-04-02 (Fri)
    # 2020-04-04 (Sat) 2021-10-02 (Sat)
    # 2020-07-05 (Sun) 2022-04-03 (Sun)
    # 2020-10-05 (Mon) 2022-10-03 (Mon)
    # 2021-01-05 (Tue) 2023-04-04 (Tue)
    # 2021-04-07 (Wed) 2023-10-04 (Wed)
    # 2021-07-08 (Thu) 2024-04-04 (Thu)
    # 2021-10-08 (Fri) 2024-10-04 (Fri)
    # 2022-01-08 (Sat) 2025-04-05 (Sat)
    # 2022-04-10 (Sun) 2025-10-05 (Sun)

    for employer in include_employers:
        for c in range(14):
            start_date = date(2018, 12, 31) + timedelta(weeks=(52 / 4) * c, days=c)
            end_date = start_date + timedelta(weeks=(52 / 4) * (c + 1))
            claim: Claim = ClaimFactory.create(
                employee=include_employee,
                employer=employer,
                claim_type_id=ClaimType.FAMILY_LEAVE.claim_type_id,
                fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
                absence_period_start_date=start_date,
                absence_period_end_date=end_date,
            )

            absence_period: AbsencePeriod = AbsencePeriodFactory.create(
                claim=claim, fineos_average_weekly_wage=c + 1
            )
            claim.absence_periods = [absence_period]
            claims.append(claim)

    return claims


@pytest.fixture
def include_employee_benefit_years(
    test_db_session: db.Session, include_employee: Employee, include_employee_claims: List[Claim]
):
    benefit_years: List[BenefitYear] = []
    claims = (
        test_db_session.query(Claim)
        .join(Employee, Claim.employee_id == Employee.employee_id)
        .join(TaxIdentifier, Employee.tax_identifier_id == TaxIdentifier.tax_identifier_id)
        .filter(
            TaxIdentifier.tax_identifier == include_employee.tax_identifier.tax_identifier,
            Claim.fineos_absence_status_id.in_(AbsenceStatusesWithBenefitYear),
        )
        .order_by(Claim.absence_period_start_date)
        .all()
    )
    # Benefit years dates
    # 2018-12-30 (Sun) 2019-12-28 (Sat)
    # 2019-12-29 (Sun) 2020-12-26 (Sat)
    # 2021-01-03 (Sun) 2022-01-01 (Sat)
    # 2022-01-02 (Sun) 2022-12-31 (Sat)

    for claim in claims:
        if not claim.absence_period_start_date:
            continue
        if len(benefit_years) == 0 or (
            claim.absence_period_start_date >= benefit_years[-1].end_date
        ):
            benefit_year_dates = get_benefit_year_dates(claim.absence_period_start_date)
            by = BenefitYear()
            by.start_date = benefit_year_dates.start_date
            by.end_date = benefit_year_dates.end_date
            by.employee_id = include_employee.employee_id
            by.total_wages = 0
            test_db_session.add(by)
            benefit_years.append(by)

    return benefit_years


# (leave_start_date, expected_benefit_year_start, expected_benefit_year_end)
leave_start_date_expectations: List[tuple[date, date, date]] = [
    # (1) -- 2018-12-30 (Sun) 2019-12-28 (Sat)
    (date(2018, 12, 30), date(2018, 12, 30), date(2019, 12, 28)),
    (date(2018, 12, 31), date(2018, 12, 30), date(2019, 12, 28)),
    (date(2019, 2, 5), date(2018, 12, 30), date(2019, 12, 28)),
    (date(2019, 6, 17), date(2018, 12, 30), date(2019, 12, 28)),
    (date(2019, 9, 7), date(2018, 12, 30), date(2019, 12, 28)),
    (date(2019, 12, 28), date(2018, 12, 30), date(2019, 12, 28)),
    # (2) -- 2019-12-29 (Sun) 2020-12-26 (Sat)
    (date(2019, 12, 29), date(2019, 12, 29), date(2020, 12, 26)),
    (date(2019, 12, 30), date(2019, 12, 29), date(2020, 12, 26)),
    (date(2020, 2, 5), date(2019, 12, 29), date(2020, 12, 26)),
    (date(2020, 6, 17), date(2019, 12, 29), date(2020, 12, 26)),
    (date(2020, 9, 7), date(2019, 12, 29), date(2020, 12, 26)),
    (date(2020, 12, 26), date(2019, 12, 29), date(2020, 12, 26)),
    # (3) -- 2021-01-03 (Sun) 2022-01-01 (Sat)
    (date(2021, 1, 3), date(2021, 1, 3), date(2022, 1, 1)),
    (date(2021, 1, 4), date(2021, 1, 3), date(2022, 1, 1)),
    (date(2021, 2, 5), date(2021, 1, 3), date(2022, 1, 1)),
    (date(2021, 6, 17), date(2021, 1, 3), date(2022, 1, 1)),
    (date(2021, 9, 7), date(2021, 1, 3), date(2022, 1, 1)),
    (date(2022, 1, 1), date(2021, 1, 3), date(2022, 1, 1)),
    # (4) -- 2022-01-02 (Sun) 2022-12-31 (Sat)
    (date(2022, 1, 2), date(2022, 1, 2), date(2022, 12, 31)),
    (date(2022, 1, 3), date(2022, 1, 2), date(2022, 12, 31)),
    (date(2022, 2, 5), date(2022, 1, 2), date(2022, 12, 31)),
    (date(2022, 6, 17), date(2022, 1, 2), date(2022, 12, 31)),
    (date(2022, 9, 7), date(2022, 1, 2), date(2022, 12, 31)),
    (date(2022, 12, 31), date(2022, 1, 2), date(2022, 12, 31)),
]


@pytest.mark.parametrize(
    "leave_start_date,expected_benefit_year_start,expected_benefit_year_end",
    leave_start_date_expectations,
)
def test_get_benefit_year__should_return_valid_benefit_year_and_create_benefit_years__with_no_persisted_benefit_years(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_claims: List[Claim],
    include_employee: Employee,
    include_employers: Employer,
    leave_start_date: date,
    expected_benefit_year_start: date,
    expected_benefit_year_end: date,
):

    benefit_year_contributions_before = (
        test_db_session.query(BenefitYearContribution)
        .join(BenefitYear, BenefitYearContribution.benefit_year_id == BenefitYear.benefit_year_id)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_year_contributions_before) == 0

    benefit_years_before = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_before) == 0

    # Calculate Benefit Year
    benefit_year = get_benefit_year_by_ssn(
        test_db_session, include_employee.tax_identifier.tax_identifier, leave_start_date
    )

    assert benefit_year

    benefit_years_after = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_after) == 4

    benefit_year_contributions_after = (
        test_db_session.query(BenefitYearContribution)
        .join(BenefitYear, BenefitYearContribution.benefit_year_id == BenefitYear.benefit_year_id)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_year_contributions_after) == 4

    # Determine which claim and absence period was used to create BY
    expected_claim_used_in_by: Optional[Claim] = None
    for claim in include_employee_claims:
        if expected_claim_used_in_by:
            break
        if (
            claim.absence_period_start_date >= benefit_year.start_date
            and claim.absence_period_start_date <= benefit_year.end_date
        ):
            expected_claim_used_in_by = claim

    assert expected_claim_used_in_by

    expected_absence_period_used_in_by = next(
        a if a else None for a in expected_claim_used_in_by.absence_periods
    )
    assert expected_absence_period_used_in_by

    # Determine which claim and absence period was used to create BY
    assert benefit_year.start_date == expected_benefit_year_start
    assert benefit_year.end_date == expected_benefit_year_end
    assert len(benefit_year.contributions) == 1
    assert (
        benefit_year.contributions[0].average_weekly_wage
        == expected_absence_period_used_in_by.fineos_average_weekly_wage
    )


@pytest.mark.parametrize(
    "leave_start_date,expected_benefit_year_start,expected_benefit_year_end",
    leave_start_date_expectations,
)
def test_get_benefit_year__should_return_valid_benefit_year__from_persisted_benefit_year(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_benefit_years: List[Claim],
    include_employee: Employee,
    leave_start_date: date,
    expected_benefit_year_start: date,
    expected_benefit_year_end: date,
):

    benefit_years_before = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_before) == 4

    benefit_year = get_benefit_year_by_ssn(
        test_db_session, include_employee.tax_identifier.tax_identifier, leave_start_date
    )

    assert benefit_year

    benefit_years_after = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_after) == 4

    assert benefit_year.start_date == expected_benefit_year_start
    assert benefit_year.end_date == expected_benefit_year_end


@pytest.mark.parametrize(
    "leave_start_date,expected_benefit_year_start,expected_benefit_year_end",
    leave_start_date_expectations,
)
def test_get_benefit_year__should_return_valid_benefit_year__with_previous_claims_and_persisted_benefit_years(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_claims: List[Claim],
    include_employee_benefit_years: List[Claim],
    include_employee: Employee,
    leave_start_date: date,
    expected_benefit_year_start: date,
    expected_benefit_year_end: date,
):

    benefit_years_before = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_before) == 4

    benefit_year = get_benefit_year_by_ssn(
        test_db_session, include_employee.tax_identifier.tax_identifier, leave_start_date
    )

    assert benefit_year
    benefit_years_after = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_after) == 4

    assert benefit_year.start_date == expected_benefit_year_start
    assert benefit_year.end_date == expected_benefit_year_end


@pytest.mark.parametrize(
    "leave_start_date", [date(2017, 12, 29), date(2023, 12, 31)],
)
def test_get_benefit_year__should_return_none_when_absence_date_outside_of_data__with_previous_claims_and_persisted_benefit_years(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_claims: List[Claim],
    include_employee_benefit_years: List[Claim],
    include_employee: Employee,
    leave_start_date: date,
):
    benefit_years_before = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_before) == 4

    benefit_year = get_benefit_year_by_ssn(
        test_db_session, include_employee.tax_identifier.tax_identifier, leave_start_date
    )

    assert benefit_year is None

    benefit_years_after = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_after) == 4


def test_get_benefit_year__should_raise_exception_when_employee_not_found__with_previous_claims_and_persisted_benefit_years(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_claims: List[Claim],
    include_employee_benefit_years: List[Claim],
):

    leave_start_date = date(2011, 1, 1)
    tax_identifier = "12345"

    benefit_years_before = test_db_session.query(BenefitYear).all()

    with pytest.raises(NotFound):
        get_benefit_year_by_ssn(test_db_session, tax_identifier, leave_start_date)

    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == len(benefit_years_before)


# Valid benefit years
# (1) -- 2018-12-30 (Sun) 2019-12-28 (Sat)
# (2) -- 2019-12-29 (Sun) 2020-12-26 (Sat)
# (3) -- 2021-01-03 (Sun) 2022-01-01 (Sat)
# (4) -- 2022-01-02 (Sun) 2022-12-31 (Sat)
@pytest.mark.parametrize(
    "leave_start_date", [date(2017, 12, 29), date(2023, 12, 31)],
)
def test_create_benefit_year_by_ssn__should_create_and_return_valid_benefit_year__with_previous_claims_and_persisted_benefit_years(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_claims: List[Claim],
    include_employee_benefit_years: List[Claim],
    include_employers: List[Employer],
    include_employee: Employee,
    leave_start_date: date,
):

    benefit_years_before = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_before) == 4

    benefit_year_dates = get_benefit_year_dates(leave_start_date)
    expected_benefit_year_start = benefit_year_dates.start_date
    expected_benefit_year_end = benefit_year_dates.end_date

    total_wages = 1234
    employer_contributions = list(
        map(
            lambda x: CreateBenefitYearContribution(
                employer_id=x.employer_id, average_weekly_wage=1234
            ),
            include_employers,
        )
    )

    benefit_year = create_benefit_year_by_ssn(
        test_db_session,
        include_employee.tax_identifier.tax_identifier,
        leave_start_date,
        total_wages,
        employer_contributions,
    )

    assert benefit_year
    benefit_years_after = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )
    assert len(benefit_years_after) == 5

    assert benefit_year.start_date == expected_benefit_year_start
    assert benefit_year.end_date == expected_benefit_year_end

    assert benefit_year.total_wages == total_wages

    assert len(benefit_year.contributions) == len(employer_contributions)

    assert benefit_year.contributions[0].employer_id == employer_contributions[0].employer_id
    assert (
        benefit_year.contributions[0].average_weekly_wage
        == employer_contributions[0].average_weekly_wage
    )

    assert benefit_year.contributions[1].employer_id == employer_contributions[1].employer_id
    assert (
        benefit_year.contributions[1].average_weekly_wage
        == employer_contributions[1].average_weekly_wage
    )


def test_create_benefit_year_by_ssn__should_raise_exception_when_employee_not_found__with_previous_claims_and_persisted_benefit_years(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_claims: List[Claim],
    include_employee_benefit_years: List[Claim],
    include_employers: List[Employer],
):
    leave_start_date = date(2021, 1, 1)
    total_wages = None
    employer_contributions = []

    benefit_years_before = test_db_session.query(BenefitYear).all()

    with pytest.raises(NotFound, match="Cannot find employee with provided tax identifer."):
        create_benefit_year_by_ssn(
            test_db_session, "123123", leave_start_date, total_wages, employer_contributions,
        )

    benefit_years_after = test_db_session.query(BenefitYear).all()
    assert len(benefit_years_after) == len(benefit_years_before)


@pytest.mark.parametrize(
    "leave_start_date",
    [
        # (1) -- 2018-12-30 (Sun) 2019-12-28 (Sat)
        date(2018, 12, 30),
        date(2019, 6, 17),
        date(2019, 12, 28),
        # (2) -- 2019-12-29 (Sun) 2020-12-26 (Sat)
        date(2019, 12, 29),
        date(2020, 6, 17),
        date(2020, 12, 26),
        # (3) -- 2021-01-03 (Sun) 2022-01-01 (Sat)
        date(2021, 1, 3),
        date(2021, 6, 17),
        date(2022, 1, 1),
        # (4) -- 2022-01-02 (Sun) 2022-12-31 (Sat)
        date(2022, 1, 2),
        date(2022, 6, 17),
        date(2022, 12, 31),
    ],
)
def test_create_benefit_year_by_ssn__should_raise_value_error_when_attempting_to_overwrite_benefit_year__with_previous_claims_and_persisted_benefit_years(
    test_db_session: db.Session,
    include_dummy_claims,
    include_employee_claims: List[Claim],
    include_employee_benefit_years: List[Claim],
    include_employers: List[Employer],
    include_employee: Employee,
    leave_start_date: date,
):
    total_wages = None
    employer_contributions = []

    benefit_years_before = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )

    with pytest.raises(ValueError):
        create_benefit_year_by_ssn(
            test_db_session,
            include_employee.tax_identifier.tax_identifier,
            leave_start_date,
            total_wages,
            employer_contributions,
        )

    benefit_years_after = (
        test_db_session.query(BenefitYear)
        .filter(BenefitYear.employee_id == include_employee.employee_id)
        .all()
    )

    assert len(benefit_years_after) == len(benefit_years_before)


def test_set_base_period_for_benefit_year(test_db_session, initialize_factories_session):
    """
    Test setup reused from eligibility tests.
    In this scenario, there are no wages during the quarter of the effective_date (absence_period_start_date).
    We are relying on behavior implemented in wage.py and the corresponding tests.
    """
    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)
    # Ensure eligibility_date/effective_date is set to 12/1
    with freeze_time("2019-12-1"):
        ClaimFactory.create(
            absence_period_start_date=date(2019, 12, 15), employee=employee, employer=employer
        )

    # Add a claim later in the benefit year
    # This claim will be ignored, since the first claim is earlier in the benefit year.
    with freeze_time("2020-1-1"):
        ClaimFactory.create(
            absence_period_start_date=date(2020, 1, 1), employee=employee, employer=employer
        )

    by_start_date = date(2019, 12, 15)
    by_end_date = date(2020, 12, 12)
    benefit_year = BenefitYear(
        employee_id=employee.employee_id, start_date=by_start_date, end_date=by_end_date
    )
    test_db_session.add(benefit_year)
    test_db_session.commit()

    # Simulate wages being added a reasonable amount of time after they were earned
    with freeze_time("2019-10-1"):
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=employer,
            filing_period=date(2019, 7, 1),
            employee_qtr_wages=1000,
        )
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=employer,
            filing_period=date(2019, 9, 1),
            employee_qtr_wages=1000,
        )

        # Add wages for Q4 2019
        # This causes the base period to end in Q4
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=employer,
            filing_period=date(2019, 12, 1),
            employee_qtr_wages=1000,
        )

    assert benefit_year.base_period_start_date is None
    assert benefit_year.base_period_end_date is None

    updated_benefit_year = set_base_period_for_benefit_year(test_db_session, benefit_year)

    assert updated_benefit_year.base_period_start_date == date(2019, 1, 1)
    assert updated_benefit_year.base_period_end_date == date(2019, 12, 31)


def test_set_base_period_for_benefit_year_ignores_retroactively_added_wages(
    test_db_session, initialize_factories_session
):
    """
    Ignore wages added after the eligibility date
    """
    employer_fein = 716779225
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=employer_fein)

    # Ensure eligibility_date/effective_date is set to 12/1
    with freeze_time("2019-12-1"):
        ClaimFactory.create(
            absence_period_start_date=date(2019, 12, 15), employee=employee, employer=employer
        )

    by_start_date = date(2019, 12, 15)
    by_end_date = date(2020, 12, 12)
    benefit_year = BenefitYear(
        employee_id=employee.employee_id, start_date=by_start_date, end_date=by_end_date
    )
    test_db_session.add(benefit_year)
    test_db_session.commit()

    with freeze_time("2019-10-1"):
        # No wages in Q4 2019 - the quarter eligibility/effective date is in,
        # so the base period ends on the last day of the previous quarter (Q3)
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=employer,
            filing_period=date(2019, 9, 1),
            employee_qtr_wages=1000,
        )
        WagesAndContributionsFactory.create(
            employee=employee,
            employer=employer,
            filing_period=date(2019, 7, 1),
            employee_qtr_wages=1000,
        )

    # Add wages that would move the end of the base_period
    # to Q4 2019. These wages will be ignored due to
    # being added retroactively, and the base period will be set to end in Q3.
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2019, 12, 1),
        employee_qtr_wages=1000,
    )

    assert benefit_year.base_period_start_date is None
    assert benefit_year.base_period_end_date is None

    updated_benefit_year = set_base_period_for_benefit_year(test_db_session, benefit_year)

    assert updated_benefit_year.base_period_start_date == date(2018, 10, 1)
    assert updated_benefit_year.base_period_end_date == date(2019, 9, 30)


def test_get_earliest_claim_in_benefit_year(test_db_session, initialize_factories_session):
    employee = EmployeeFactory.create()
    by_start_date = date(2019, 10, 1)
    by_end_date = date(2020, 10, 1)
    benefit_year = BenefitYear(
        employee_id=employee.employee_id, start_date=by_start_date, end_date=by_end_date
    )

    with freeze_time("2019-12-1"):
        claim1 = ClaimFactory.create(
            absence_period_start_date=date(2019, 12, 15), employee=employee
        )

    with freeze_time("2020-1-1"):
        ClaimFactory.create(absence_period_start_date=date(2020, 1, 1), employee=employee)

    assert _get_earliest_claim_in_benefit_year(test_db_session, benefit_year) == claim1
