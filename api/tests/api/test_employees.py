from datetime import date

import pytest

import tests.api
from massgov.pfml.api.models.applications.common import MaskedAddress
from massgov.pfml.db.models.employees import EmployeeAddress
from massgov.pfml.db.models.factories import (
    AddressFactory,
    ApplicationFactory,
    ClaimFactory,
    EmployeeFactory,
    EmployerFactory,
    TaxIdentifierFactory,
)


@pytest.fixture
def employee():
    employee = EmployeeFactory.create()
    return employee


@pytest.fixture
def employee_different_fineos_name():
    employee = EmployeeFactory.create(
        first_name="Foo",
        last_name="Bar",
        middle_name="Baz",
        fineos_employee_first_name="Foo2",
        fineos_employee_last_name="Bar2",
        fineos_employee_middle_name="Baz2",
    )
    return employee


def test_employees_get_snow_user_allowed(client, employee, snow_user_headers):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id), headers=snow_user_headers,
    )

    assert response.status_code == 200


def test_employees_get_snow_user_requires_agent_id(client, employee, snow_user_token):
    # requires header {"Mass-PFML-Agent-ID": "123"}
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(snow_user_token)},
    )

    assert response.status_code == 401


def test_employess_get_invalid_employee(client, employee, snow_user_headers):
    response = client.get(
        "/v1/employees/{}".format("9e243bae-3b1e-43a4-aafe-aca3c6517cf0"),
        headers=snow_user_headers,
    )
    tests.api.validate_error_response(response, 404)


def test_employees_get_nonsnow_forbidden(client, employee, consented_user_token):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token),},
    )

    assert response.status_code == 403


def test_employees_get_nonsnow_with_agent_header_also_forbidden(
    client, employee, consented_user_token
):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={
            "Authorization": "Bearer {}".format(consented_user_token),
            "Mass-PFML-Agent-ID": "123",
        },
    )

    assert response.status_code == 403


def test_employees_get_fineos_user_forbidden(client, employee, fineos_user_token):
    # Fineos role cannot access this endpoint
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={
            "Authorization": "Bearer {}".format(fineos_user_token),
            # Agent ID header only required for SNOW users but including here to verify it doesn't cause unexpected
            # behavior
            "Mass-PFML-Agent-ID": "123",
        },
    )

    assert response.status_code == 403


def test_employees_patch_snow_user_forbidden(client, employee, snow_user_headers):
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id), json=body, headers=snow_user_headers,
    )
    assert response.status_code == 403


def test_employees_search_nonsnow_forbidden(client, employee, consented_user_token):
    body = {
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "tax_identifier_last4": employee.tax_identifier.tax_identifier_last4,
    }
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={
            "Authorization": "Bearer {}".format(consented_user_token),
            "Mass-PFML-Agent-ID": "123",
        },
    )
    assert response.status_code == 403


def test_employees_search_snow_allowed(client, employee, snow_user_headers):
    body = {
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "tax_identifier_last4": employee.tax_identifier.tax_identifier_last4,
    }
    response = client.post("/v1/employees/search", json=body, headers=snow_user_headers,)

    assert response.status_code == 200


def test_employees_search_valid_with_middle_name(client, employee, snow_user_headers):
    # create identical employee except for middle name
    # and tax_identifier (which is now enforced as unique)
    new_tax_id = TaxIdentifierFactory.create()
    EmployeeFactory.create(
        first_name=employee.first_name, last_name=employee.last_name, tax_identifier=new_tax_id,
    )

    body = {
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "middle_name": employee.middle_name,
        "tax_identifier_last4": employee.tax_identifier.tax_identifier_last4,
    }

    response = client.post("/v1/employees/search", json=body, headers=snow_user_headers,)

    assert response.status_code == 200

    response_data = response.get_json().get("data")

    assert response_data.get("middle_name") == employee.middle_name


def test_employees_search_missing_param(client, consented_user_token):
    body = {"last_name": "Doe", "foo": "bar"}
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    tests.api.validate_error_response(response, 400)


def test_employees_search_nonexisting_employee(client, consented_user_token):
    body = {"first_name": "Damian", "last_name": "Wayne", "tax_identifier_last4": "6789"}
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    tests.api.validate_error_response(response, 404)


def test_get_employee_basic_response(client, employee_different_fineos_name, snow_user_headers):
    response = client.get(
        f"/v1/employees/{employee_different_fineos_name.employee_id}", headers=snow_user_headers,
    )

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")

    assert employee_data["first_name"] == "Foo2"
    assert employee_data["middle_name"] == "Baz2"
    assert employee_data["last_name"] == "Bar2"


def test_employee_for_pfml_crm_response(client, employee, snow_user_headers, user, test_db_session):
    tax_identifier = TaxIdentifierFactory.create(tax_identifier="587777091")
    employee = EmployeeFactory.create(
        tax_identifier_id=tax_identifier.tax_identifier_id,
        first_name="Foo",
        last_name="Bar",
        middle_name="Baz",
        date_of_birth=date(2020, 1, 1),
        fineos_employee_first_name="Foo2",
        fineos_employee_last_name="Bar2",
        fineos_employee_middle_name="Baz2",
    )

    address = AddressFactory.create()
    employee.employee_addresses = [
        EmployeeAddress(employee_id=employee.employee_id, address_id=address.address_id,)
    ]

    test_db_session.commit()

    ApplicationFactory.create(user=user)
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers,)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["tax_identifier"] is not None
    assert employee_data["date_of_birth"] == "****-01-01"
    assert employee_data["addresses"][0] == MaskedAddress.from_orm(address)


def test_employee_with_claims_no_id_proof(
    client, employee, snow_user_headers, user, test_db_session
):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()

    claim = ClaimFactory.create(employer=employer, employee=employee,)

    ApplicationFactory.create(user=user, claim=claim, mass_id="123456789")
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers,)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["mass_id_number"] is None


def test_employee_empty_mass_id(client, employee, snow_user_headers, user, test_db_session):
    employee = EmployeeFactory.create()
    ApplicationFactory.create(user=user)
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers,)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["mass_id_number"] is None


def test_employee_get_mass_id(client, employee, snow_user_headers, user, test_db_session):
    employer = EmployerFactory.create()
    employee = EmployeeFactory.create()

    claim = ClaimFactory.create(
        employer=employer, employee=employee, is_id_proofed=True, created_at=date(2020, 1, 1),
    )

    claim2 = ClaimFactory.create(
        employer=employer,
        employee=employee,
        fineos_absence_status_id=1,
        claim_type_id=1,
        is_id_proofed=True,
        created_at=date(2021, 2, 1),
        fineos_absence_id="NTN-304363-ABS-02",
    )
    ApplicationFactory.create(user=user, claim=claim, mass_id="123456789")
    ApplicationFactory.create(user=user, claim=claim2, mass_id="012345678")
    test_db_session.commit()

    response = client.get(f"/v1/employees/{employee.employee_id}", headers=snow_user_headers,)

    assert response.status_code == 200
    response_body = response.get_json()

    employee_data = response_body.get("data")
    assert employee_data["mass_id_number"] == "012345678"


def test_employees_basic_response_search(client, employee_different_fineos_name, snow_user_headers):
    body = {
        "first_name": employee_different_fineos_name.first_name,
        "last_name": employee_different_fineos_name.last_name,
        "tax_identifier_last4": employee_different_fineos_name.tax_identifier.tax_identifier_last4,
    }
    response = client.post("/v1/employees/search", json=body, headers=snow_user_headers,)

    response_body = response.get_json()
    employee_data = response_body.get("data")

    assert response.status_code == 200
    assert employee_data["first_name"] == "Foo2"
    assert employee_data["middle_name"] == "Baz2"
    assert employee_data["last_name"] == "Bar2"


def test_employees_search_fineos_user_forbidden(client, employee, fineos_user_token):
    # Fineos role cannot access this endpoint
    body = {
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "tax_identifier_last4": employee.tax_identifier.tax_identifier_last4,
    }
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={"Authorization": "Bearer {}".format(fineos_user_token)},
    )
    assert response.status_code == 403


def test_employees_patch_snow_forbidden(client, employee, snow_user_headers):
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id), json=body, headers=snow_user_headers,
    )
    assert response.status_code == 403

    updated_employee = client.get(
        "/v1/employees/{}".format(employee.employee_id), headers=snow_user_headers,
    ).get_json()

    updated_employee_item = updated_employee.get("data")

    # This assertion is sparse because this endpoint is planned to be removed.
    assert updated_employee_item["employee_id"] == str(employee.employee_id)


def test_employees_patch_empty(client, employee, snow_user_headers):
    body = {"first_name": "", "last_name": ""}
    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id), json=body, headers=snow_user_headers,
    )
    tests.api.validate_error_response(response, 400)

    updated_employee = client.get(
        "/v1/employees/{}".format(employee.employee_id), headers=snow_user_headers,
    ).get_json()

    # This test should return a 400 because blank requests shouldn't be accepted.
    assert updated_employee.get("data")["first_name"] == employee.first_name


def test_employees_patch_404(client, consented_user_token):
    # This tests attempts to PATCH an employee that doesn't exist
    body = {"first_name": "Barbara", "last_name": "Gordon"}
    response = client.patch(
        "/v1/employees/{}".format("9e243bae-3b1e-43a4-aafe-aca3c6517cf0"),
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    tests.api.validate_error_response(response, 404)


def test_employee_auth_get(disable_employee_endpoint, client, employee, consented_user_token):
    # This tests a user that doesn't meet authorization rules. Should return 403

    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    tests.api.validate_error_response(response, 403)


def test_employee_auth_patch(disable_employee_endpoint, client, employee, consented_user_token):
    # Attempts to patch when user doesn't meet authorization rules.

    body = {"first_name": "James", "last_name": "Brown"}

    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id),
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    tests.api.validate_error_response(response, 403)


def test_employee_patch_fineos_user_forbidden(client, employee, fineos_user_token):
    # Fineos role cannot access this endpoint
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id),
        json=body,
        headers={"Authorization": "Bearer {}".format(fineos_user_token)},
    )
    tests.api.validate_error_response(response, 403)
