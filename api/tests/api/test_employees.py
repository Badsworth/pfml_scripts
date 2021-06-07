import pytest

import tests.api
from massgov.pfml.db.models.factories import EmployeeFactory, TaxIdentifierFactory

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def employee():
    employee = EmployeeFactory.create()
    return employee


def test_employees_get_valid(client, employee, consented_user_token):
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    assert response.status_code == 200


def test_employees_get_invalid(client, consented_user_token):
    response = client.get(
        "/v1/employees/{}".format("9e243bae-3b1e-43a4-aafe-aca3c6517cf0"),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    tests.api.validate_error_response(response, 404)


def test_employees_get_fineos_user_forbidden(client, employee, fineos_user_token):
    # Fineos role cannot access this endpoint
    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(fineos_user_token)},
    )

    assert response.status_code == 403


def test_employees_search_valid(client, employee, consented_user_token):
    body = {
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "tax_identifier_last4": employee.tax_identifier.tax_identifier_last4,
    }
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    assert response.status_code == 200


def test_employees_search_valid_with_middle_name(client, employee, consented_user_token):
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

    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

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


def test_employees_patch(client, employee, consented_user_token):
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id),
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    assert response.status_code == 200

    updated_employee = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    ).get_json()

    updated_employee_item = updated_employee.get("data")
    assert updated_employee_item["first_name"] == "James"
    assert updated_employee_item["last_name"] == "Brown"
    assert updated_employee_item["employee_id"] == str(employee.employee_id)
    assert updated_employee_item["middle_name"] == employee.middle_name


def test_employees_patch_empty(client, employee, consented_user_token):
    body = {"first_name": "", "last_name": ""}
    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id),
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    tests.api.validate_error_response(response, 400)

    updated_employee = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
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
