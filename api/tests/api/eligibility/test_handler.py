#
# Tests for /v1/financial-eligibility API.
#
from collections import namedtuple
from datetime import date
from enum import Enum

import pytest

from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)

# every test in here requires real resources
pytestmark = pytest.mark.integration


class QuarterDates(Enum):
    CQ = date(2020, 12, 30)
    Q_1 = date(2020, 9, 30)
    Q_2 = date(2020, 6, 30)
    Q_3 = date(2020, 3, 30)
    Q_4 = date(2019, 12, 30)
    Q_5 = date(2019, 9, 30)
    Q_6 = date(2019, 6, 30)


employee_claim_row = namedtuple("employee_claim_row", ["date", "wage_list"])


@pytest.fixture
def tax_id():
    return TaxIdentifierFactory.create(tax_identifier="088574541")


@pytest.fixture
def employee(tax_id):
    return EmployeeFactory.create(tax_identifier=tax_id)


@pytest.fixture
def employer():
    return EmployerFactory.create(employer_fein="716779225")


@pytest.fixture
def body():
    return {
        "application_submitted_date": "2020-10-15",
        "employer_fein": "71-6779225",
        "employment_status": "Employed",
        "leave_start_date": "2020-10-15",
        "tax_identifier": "088-57-4541",
    }


def generate_claimant_data(employee, employers_list, financial_data):
    wage_factories = []
    for claim_row in financial_data:
        for employer_index, employer_wage in enumerate(claim_row.wage_list):
            if employer_wage is not None:
                wage_factories.append(
                    WagesAndContributionsFactory.create(
                        employee=employee,
                        employer=employers_list[employer_index],
                        employee_qtr_wages=employer_wage,
                        filing_period=claim_row.date.value
                        if isinstance(claim_row.date, QuarterDates)
                        else claim_row.date,
                    )
                )
    return wage_factories


def test_endpoint_with_employee_wages_data(
    client,
    test_db_session,
    initialize_factories_session,
    fineos_user_token,
    body,
    employer,
    employee,
):
    financial_data = [
        employee_claim_row(QuarterDates.Q_2, [10_000]),
        employee_claim_row(QuarterDates.Q_3, [11_000]),
        employee_claim_row(QuarterDates.Q_4, [10_100]),
        employee_claim_row(date(2017, 12, 1), [10_010]),
    ]
    generate_claimant_data(employee, [employer], financial_data)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "application_submitted_date": "2020-12-30", "leave_start_date": "2020-12-30"},
    )

    assert response.json == {
        "data": {
            "description": "Financially eligible",
            "employer_average_weekly_wage": 811.54,  # = (11000 + 10100) / 26
            "financially_eligible": True,
            "state_average_weekly_wage": 1431,
            "total_wages": 31100.0,
            "unemployment_minimum": 5100,
        },
        "message": "Calculated financial eligibility",
        "meta": {"method": "POST", "resource": "/v1/financial-eligibility"},
        "status_code": 200,
    }


def test_endpoint_with_unknown_employment_status(
    client, test_db_session, initialize_factories_session, fineos_user_token, body
):
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={
            **body,
            "application_submitted_date": "2020-12-30",
            "leave_start_date": "2020-12-30",
            "employment_status": "Unknown",
        },
    )

    assert response.json == {
        "data": {
            "description": "Not Known: invalid employment status",
            "employer_average_weekly_wage": None,
            "financially_eligible": False,
            "state_average_weekly_wage": None,
            "total_wages": None,
            "unemployment_minimum": None,
        },
        "message": "success",
        "meta": {"method": "POST", "resource": "/v1/financial-eligibility"},
        "status_code": 200,
    }


def test_endpoint_no_employee_wage_data(
    client, test_db_session, initialize_factories_session, fineos_user_token, body
):
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "00-0000000", "employer_fein": "00-0000000",},
    )

    assert response.status_code == 404
    assert response.get_json().get("data") == {}


def test_endpoint_unauthenticated_user(client, test_db_session, initialize_factories_session, body):
    response = client.post(
        "/v1/financial-eligibility",
        json={**body, "employer_fein": "00-0000000", "tax_identifier": "000-00-0000"},
    )

    assert response.status_code == 401
    assert response.get_json().get("message") == "No authorization token provided"


def test_endpoint_unauthorized_user(
    client, test_db_session, initialize_factories_session, auth_token, body
):
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": "Bearer {}".format(auth_token)},
        json={**body, "employer_fein": "00-0000000", "tax_identifier": "000-00-0000"},
    )

    assert response.status_code == 403


def test_self_employed_two_quarters(
    client,
    test_db_session,
    initialize_factories_session,
    fineos_user_token,
    body,
    employer,
    employee,
):
    financial_data = [
        employee_claim_row(QuarterDates.Q_2, [25_000]),
        employee_claim_row(QuarterDates.Q_3, [25_000]),
    ]
    wage_factories = generate_claimant_data(employee, [employer], financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={
            **body,
            "employment_status": "Self-Employed",
            "leave_start_date": "2020-12-30",
            "application_submitted_date": "2020-12-30",
        },
    )
    assert response.status_code == 200
    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("description") == "Financially eligible"
    assert response.get_json().get("data").get("total_wages") == float(
        round(wage_factories[0].employee_qtr_wages + wage_factories[1].employee_qtr_wages, 2,)
    )


def test_self_employed_one_quarter(
    client,
    test_db_session,
    initialize_factories_session,
    fineos_user_token,
    employer,
    employee,
    body,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employers = [employer, employer2]
    financial_data = [
        employee_claim_row(QuarterDates.Q_2, [25_000, 25_000]),
    ]
    wage_factories = generate_claimant_data(employee, employers, financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={
            **body,
            "employment_status": "Self-Employed",
            "leave_start_date": "2020-12-30",
            "application_submitted_date": "2020-12-30",
        },
    )
    assert response.status_code == 200
    assert response.get_json().get("data").get("financially_eligible") is False
    assert (
        response.get_json().get("data").get("description")
        == "Opt-in quarterly contributions not met"
    )
    assert response.get_json().get("data").get("total_wages") == float(
        round(wage_factories[0].employee_qtr_wages + wage_factories[1].employee_qtr_wages, 2,)
    )


# scenarios from https://docs.google.com/spreadsheets/d/1RAJaUNo2pMlVHhEniwEpg_5pBISs-dEKAw7FXF-E5kQ/edit#gid=1747298371


def test_claimaint_scenario_one(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employers = [employer, employer2]
    financial_data = [
        employee_claim_row(QuarterDates.CQ, (2_000, None)),
        employee_claim_row(QuarterDates.Q_1, (0, 5_000)),
        employee_claim_row(QuarterDates.Q_2, (1_000, 2_000)),
        employee_claim_row(QuarterDates.Q_5, (20_000, 0)),
    ]
    generate_claimant_data(employee, employers, financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is False
    assert response.get_json().get("data").get("total_wages") == float(8_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(76.92)


def test_claimaint_scenario_two(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employers = [employer, employer2]
    financial_data = [
        employee_claim_row(QuarterDates.CQ, (0, 10_000)),
        employee_claim_row(QuarterDates.Q_1, (0, 10_000)),
        employee_claim_row(QuarterDates.Q_2, (0, 5_000)),
        employee_claim_row(QuarterDates.Q_3, (0, 5_000)),
        employee_claim_row(QuarterDates.Q_4, (20_000, 5_000)),
        employee_claim_row(QuarterDates.Q_5, (20_000, 0)),
    ]
    generate_claimant_data(employee, employers, financial_data)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(45_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(1538.46)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897622"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(45_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(576.92)


def test_claimaint_scenario_three(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employer3 = EmployerFactory.create(employer_fein="553897623")
    employers = [employer, employer2, employer3]
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (10_000, 0, 2_000)),
        employee_claim_row(QuarterDates.Q_2, (0, 6_000, 2_000)),
        employee_claim_row(QuarterDates.Q_3, (12_000, 0, 2_000)),
        employee_claim_row(QuarterDates.Q_4, (0, 6_000, 2_000)),
        employee_claim_row(QuarterDates.Q_5, (10_000, 0, 2_000)),
    ]
    generate_claimant_data(employee, employers, financial_data)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(42_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(923.08)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897622"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(42_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(461.54)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897623"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(42_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(153.85)


def test_claimaint_scenario_four(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employers = [employer, employer2]
    financial_data = [
        employee_claim_row(QuarterDates.Q_2, (0, 5_000)),
        employee_claim_row(QuarterDates.Q_3, (20_000, 5_000)),
        employee_claim_row(QuarterDates.Q_4, (20_000, 0)),
        employee_claim_row(QuarterDates.Q_5, (20_000, 0)),
    ]
    generate_claimant_data(employee, employers, financial_data)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(70_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(1538.46)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897622"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(70_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(384.62)


def test_claimaint_scenario_five(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employers = [employer, employer2]
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (0, 1_000)),
        employee_claim_row(QuarterDates.Q_2, (1_000, 3_000)),
        employee_claim_row(QuarterDates.Q_3, (4_000, 0)),
    ]
    generate_claimant_data(employee, employers, financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(9_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(307.69)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897622"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(9_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(230.77)


def test_claimaint_scenario_a(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employers = [employer, employer2]
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (0, 10_000)),
        employee_claim_row(QuarterDates.Q_2, (0, 5_000)),
        employee_claim_row(QuarterDates.Q_4, (8_000, 0)),
        employee_claim_row(QuarterDates.Q_5, (4_000, 0)),
    ]
    generate_claimant_data(employee, employers, financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(23_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(615.38)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897622"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(23_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(769.23)


def test_claimaint_scenario_b(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employer3 = EmployerFactory.create(employer_fein="553897623")
    employers = [employer, employer2, employer3]
    financial_data = [
        employee_claim_row(QuarterDates.CQ, (0, 3_000, 0)),
        employee_claim_row(QuarterDates.Q_1, (0, 3_000, 2_000)),
        employee_claim_row(QuarterDates.Q_2, (0, 2_000, 2_000)),
        employee_claim_row(QuarterDates.Q_3, (7_000, 3_000, 2_000)),
        employee_claim_row(QuarterDates.Q_4, (7_000, 1_000, 2_000)),
        employee_claim_row(QuarterDates.Q_5, (7_000, 0, 2_000)),
        employee_claim_row(QuarterDates.Q_6, (7_000, 0, 0)),
    ]
    generate_claimant_data(employee, employers, financial_data)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(31_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(538.46)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897622"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(31_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(230.77)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897623"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(31_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(153.85)


def test_claimaint_scenario_c(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    financial_data = [
        employee_claim_row(QuarterDates.Q_2, (3_000,)),
        employee_claim_row(QuarterDates.Q_3, (3_000,)),
        employee_claim_row(QuarterDates.Q_6, (6_000,)),
    ]
    generate_claimant_data(employee, [employer], financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(6_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(230.77)


def test_claimaint_scenario_d(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (4_500,)),
        employee_claim_row(QuarterDates.Q_3, (5_000,)),
        employee_claim_row(QuarterDates.Q_4, (6_250,)),
        employee_claim_row(QuarterDates.Q_5, (3_000,)),
        employee_claim_row(QuarterDates.Q_6, (6_000,)),
    ]
    generate_claimant_data(employee, [employer], financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(15_750)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(432.69)


def test_claimaint_scenario_e(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    employer2 = EmployerFactory.create(employer_fein="553897622")
    employers = [employer, employer2]
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (20_000, 0)),
        employee_claim_row(QuarterDates.Q_3, (0, 15_000)),
        employee_claim_row(QuarterDates.Q_4, (0, 15_000)),
        employee_claim_row(QuarterDates.Q_5, (0, 15_000)),
        employee_claim_row(QuarterDates.Q_6, (0, 21_343)),
    ]
    generate_claimant_data(employee, employers, financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(50_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(1_538.46)

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json={**body, "employer_fein": "55-3897622"},
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(50_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(1_153.85)


def test_claimaint_scenario_f(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (1_000,)),
        employee_claim_row(QuarterDates.Q_2, (4_000,)),
    ]
    generate_claimant_data(employee, [employer], financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is False
    assert response.get_json().get("data").get("total_wages") == float(5_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(307.69)


def test_claimaint_scenario_g(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (2_000,)),
        employee_claim_row(QuarterDates.Q_2, (2_000,)),
    ]
    generate_claimant_data(employee, [employer], financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is False
    assert response.get_json().get("data").get("total_wages") == float(4_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(153.85)


def test_claimaint_scenario_h(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    financial_data = [
        employee_claim_row(QuarterDates.Q_1, (10_000,)),
        employee_claim_row(QuarterDates.Q_2, (2_000,)),
    ]
    generate_claimant_data(employee, [employer], financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is False
    assert response.get_json().get("data").get("total_wages") == float(12_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(769.23)


def test_claimaint_scenario_i(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    financial_data = [
        employee_claim_row(QuarterDates.CQ, (3_000,)),
        employee_claim_row(QuarterDates.Q_1, (3_000,)),
    ]
    generate_claimant_data(employee, [employer], financial_data)
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(6_000)
    assert response.get_json().get("data").get("employer_average_weekly_wage") == float(230.77)
