from datetime import date

from massgov.pfml.db.models.factories import (
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
    WagesAndContributionsFactory,
)


def test_endpoint_with_employee_wages_data(client, test_db_session, initialize_factories_session):
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee = EmployeeFactory.create(tax_identifier=tax_id)
    employer = EmployerFactory.create(employer_fein="716779225")

    wages_and_contribution1 = WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 6, 30)
    )
    wages_and_contribution2 = WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2020, 3, 1)
    )
    wages_and_contribution3 = WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2019, 12, 1)
    )
    WagesAndContributionsFactory.create(
        employee=employee, employer=employer, filing_period=date(2017, 12, 1)
    )  # outside the base period

    body = {
        "application_submitted_date": "2020-12-30",
        "employer_fein": "71-6779225",
        "employment_status": "Employed",
        "leave_start_date": "2020-12-30",
        "tax_identifier": "088-57-4541",
    }
    response = client.post("/v1/financial-eligibility", json=body)
    assert response.status_code == 200
    assert response.get_json().get("data").get("total_wages") == float(
        round(
            wages_and_contribution1.employee_qtr_wages
            + wages_and_contribution2.employee_qtr_wages
            + wages_and_contribution3.employee_qtr_wages,
            2,
        )
    )


def test_endpoint_no_employee_wage_data(client, test_db_session, initialize_factories_session):
    WagesAndContributionsFactory.create()

    body = {
        "application_submitted_date": "2020-06-30",
        "employer_fein": "00-0000000",
        "employment_status": "Employed",
        "leave_start_date": "2020-06-30",
        "tax_identifier": "000-00-0000",
    }
    response = client.post("/v1/financial-eligibility", json=body)
    assert response.status_code == 404
    assert response.get_json().get("data") == {}
