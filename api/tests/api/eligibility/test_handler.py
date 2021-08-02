#
# Tests for /v1/financial-eligibility API.
#

from datetime import date

import pytest

from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.types import Fein, TaxId

# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_endpoint_with_employee_wages_data(
    client, test_db_session, initialize_factories_session, fineos_user_token
):
    tax_id = TaxIdentifierFactory.create(tax_identifier=TaxId("088574541"))
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=Fein("716779225"))

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 6, 30),
        employee_qtr_wages=10000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 3, 1),
        employee_qtr_wages=11000,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2019, 12, 1),
        employee_qtr_wages=10100,
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2017, 12, 1),
        employee_qtr_wages=10010,
    )  # outside the base period

    body = {
        "application_submitted_date": "2020-12-30",
        "employer_fein": "71-6779225",
        "employment_status": "Employed",
        "leave_start_date": "2020-12-30",
        "tax_identifier": "088-57-4541",
    }
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
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
    client, test_db_session, initialize_factories_session, fineos_user_token
):
    body = {
        "application_submitted_date": "2020-12-30",
        "employer_fein": "71-6779225",
        "employment_status": "Unknown",
        "leave_start_date": "2020-12-30",
        "tax_identifier": "088-57-4541",
    }
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
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
    client, test_db_session, initialize_factories_session, fineos_user_token
):
    WagesAndContributionsFactory.create()

    body = {
        "application_submitted_date": "2020-06-30",
        "employer_fein": "00-0000000",
        "employment_status": "Employed",
        "leave_start_date": "2020-06-30",
        "tax_identifier": "000-00-0000",
    }
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.status_code == 404
    assert response.get_json().get("data") == {}


def test_endpoint_unauthenticated_user(client, test_db_session, initialize_factories_session):
    WagesAndContributionsFactory.create()

    body = {
        "application_submitted_date": "2020-06-30",
        "employer_fein": "00-0000000",
        "employment_status": "Employed",
        "leave_start_date": "2020-06-30",
        "tax_identifier": "000-00-0000",
    }
    response = client.post("/v1/financial-eligibility", json=body)

    assert response.status_code == 401
    assert response.get_json().get("message") == "No authorization token provided"


def test_endpoint_unauthorized_user(
    client, test_db_session, initialize_factories_session, auth_token
):
    WagesAndContributionsFactory.create()

    body = {
        "application_submitted_date": "2020-06-30",
        "employer_fein": "00-0000000",
        "employment_status": "Employed",
        "leave_start_date": "2020-06-30",
        "tax_identifier": "000-00-0000",
    }
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": "Bearer {}".format(auth_token)},
        json=body,
    )

    assert response.status_code == 403


def test_self_employed_two_quarters(
    client, test_db_session, initialize_factories_session, fineos_user_token
):
    tax_id = TaxIdentifierFactory.create(tax_identifier=TaxId("088574541"))
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=Fein("716779225"))

    wages_and_contribution1 = WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 6, 30),
        employee_qtr_wages=25000,
    )
    wages_and_contribution2 = WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 3, 1),
        employee_qtr_wages=25000,
    )

    body = {
        "application_submitted_date": "2020-12-30",
        "employer_fein": "71-6779225",
        "employment_status": "Self-Employed",
        "leave_start_date": "2020-12-30",
        "tax_identifier": "088-57-4541",
    }
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )
    assert response.status_code == 200
    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("description") == "Financially eligible"
    assert response.get_json().get("data").get("total_wages") == float(
        round(
            wages_and_contribution1.employee_qtr_wages + wages_and_contribution2.employee_qtr_wages,
            2,
        )
    )


def test_self_employed_one_quarter(
    client, test_db_session, initialize_factories_session, fineos_user_token
):
    tax_id = TaxIdentifierFactory.create(tax_identifier=TaxId("088574541"))
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein=Fein("716779225"))
    employer2 = EmployerFactory.create(employer_fein=Fein("553897622"))

    wages_and_contribution1 = WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        filing_period=date(2020, 6, 30),
        employee_qtr_wages=25000,
    )
    wages_and_contribution2 = WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        filing_period=date(2020, 6, 30),
        employee_qtr_wages=25000,
    )

    body = {
        "application_submitted_date": "2020-12-30",
        "employer_fein": "71-6779225",
        "employment_status": "Self-Employed",
        "leave_start_date": "2020-12-30",
        "tax_identifier": "088-57-4541",
    }
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )
    assert response.status_code == 200
    assert response.get_json().get("data").get("financially_eligible") is False
    assert (
        response.get_json().get("data").get("description")
        == "Opt-in quarterly contributions not met"
    )
    assert response.get_json().get("data").get("total_wages") == float(
        round(
            wages_and_contribution1.employee_qtr_wages + wages_and_contribution2.employee_qtr_wages,
            2,
        )
    )


@pytest.fixture
def tax_id():
    return TaxIdentifierFactory.create(tax_identifier=TaxId("088574541"))


@pytest.fixture
def employee(tax_id):
    return EmployeeFactory.create(tax_identifier=tax_id)


@pytest.fixture
def employer():
    return EmployerFactory.create(employer_fein=Fein("716779225"))


@pytest.fixture
def body():
    return {
        "application_submitted_date": "2020-10-15",
        "employer_fein": "71-6779225",
        "employment_status": "Employed",
        "leave_start_date": "2020-10-15",
        "tax_identifier": "088-57-4541",
    }


# test claimants found here https://docs.google.com/spreadsheets/d/1QzojMBMOqJm8r8ChVNoDMy9xzGdcpJUsyRXfLuGEHR4


def test_claimant_A(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    # Claimant is eligible, with wages from 2 employers
    employer2 = EmployerFactory.create(employer_fein=Fein("553897622"))

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=5000,
        filing_period=date(2020, 3, 15),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=6000,
        filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=4000,
        filing_period=date(2020, 9, 1),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=5500,
        filing_period=date(2020, 12, 1),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=5000,
        filing_period=date(2021, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=5000,
        filing_period=date(2021, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=2000,
        filing_period=date(2020, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=2000,
        filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=2000,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=1500,
        filing_period=date(2020, 12, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=1500,
        filing_period=date(2021, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=1500,
        filing_period=date(2021, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=1500,
        filing_period=date(2021, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=1500,
        filing_period=date(2021, 12, 30),
    )

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )
    assert response.get_json().get("data").get("total_wages") == float(28000)
    assert response.get_json().get("data").get("financially_eligible") is True


def test_claimant_B(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    # claimant has 3 employers, and is eligible
    employer2 = EmployerFactory.create(employer_fein=Fein("553897622"))
    employer3 = EmployerFactory.create(employer_fein=Fein("904721143"))

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=7000,
        filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=7000,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=7000,
        filing_period=date(2020, 12, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=7000,
        filing_period=date(2021, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=7000,
        filing_period=date(2021, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=7000,
        filing_period=date(2021, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=3000,
        filing_period=date(2020, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=3300,
        filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=2000,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=3000,
        filing_period=date(2020, 12, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=1000,
        filing_period=date(2021, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=3000,
        filing_period=date(2021, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=3000,
        filing_period=date(2021, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer3,
        employee_qtr_wages=500,
        filing_period=date(2020, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer3,
        employee_qtr_wages=500,
        filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer3,
        employee_qtr_wages=500,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer3,
        employee_qtr_wages=500,
        filing_period=date(2021, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer3,
        employee_qtr_wages=500,
        filing_period=date(2021, 9, 30),
    )

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )
    assert response.get_json().get("data").get("total_wages") == float(33800)
    assert response.get_json().get("data").get("financially_eligible") is True


def test_claimant_C(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    # claimant has 1 employer, and is ineligible
    wages_and_contribution1 = WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=5000,
        filing_period=date(2020, 6, 15),
    )
    wages_and_contribution2 = WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=2000,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=6000,
        filing_period=date(2021, 1, 1),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=6000,
        filing_period=date(2021, 4, 1),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=6000,
        filing_period=date(2021, 9, 30),
    )

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("total_wages") == float(
        round(
            wages_and_contribution1.employee_qtr_wages + wages_and_contribution2.employee_qtr_wages,
            2,
        )
    )

    assert response.get_json().get("data").get("description") == "Claimant wages failed 30x rule"
    assert response.get_json().get("data").get("financially_eligible") is False


def test_claimant_D(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    # wages from 1 employer, eligible
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=4500,
        filing_period=date(2020, 6, 15),
    )

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=5000,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=6250,
        filing_period=date(2020, 12, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=3000,
        filing_period=date(2021, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=6000,
        filing_period=date(2021, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=4600,
        filing_period=date(2021, 9, 30),
    )
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(15750)


def test_claimant_E(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    # wages from 2 employers, eligible
    employer2 = EmployerFactory.create(employer_fein=Fein("553897622"))
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=12000,
        filing_period=date(2020, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=12000,
        filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=10000,
        filing_period=date(2020, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=10000,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=10000,
        filing_period=date(2020, 12, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=10000,
        filing_period=date(2021, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=10000,
        filing_period=date(2021, 6, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=10000,
        filing_period=date(2021, 3, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer2,
        employee_qtr_wages=10000,
        filing_period=date(2021, 9, 30),
    )

    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is True
    assert response.get_json().get("data").get("total_wages") == float(54000)


def test_claimant_F(
    client,
    test_db_session,
    initialize_factories_session,
    tax_id,
    employee,
    employer,
    body,
    fineos_user_token,
):
    # Claimant is ineligible, with wages from 1 employer

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=1000,
        filing_period=date(2020, 6, 15),
    )

    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=4000,
        filing_period=date(2020, 9, 30),
    )
    WagesAndContributionsFactory.create(
        employee=employee,
        employer=employer,
        employee_qtr_wages=4000,
        filing_period=date(2021, 6, 30),
    )
    response = client.post(
        "/v1/financial-eligibility",
        headers={"Authorization": f"Bearer {fineos_user_token}"},
        json=body,
    )

    assert response.get_json().get("data").get("financially_eligible") is False
    assert response.get_json().get("data").get("total_wages") == float(5000)
