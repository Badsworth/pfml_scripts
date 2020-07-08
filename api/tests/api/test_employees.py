import pytest

from massgov.pfml.db.models.factories import EmployeeFactory


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


def test_employees_get_invalid(client):
    response = client.get("/v1/employees/{}".format("9e243bae-3b1e-43a4-aafe-aca3c6517cf0"))
    assert response.status_code == 404


def test_employees_search_valid(client, employee, consented_user_token):
    first_name = employee.first_name
    last_name = employee.last_name
    tax_identifier = employee.tax_identifier

    body = {
        "first_name": first_name,
        "last_name": last_name,
        "tax_identifier": "{}-{}-{}".format(
            tax_identifier[:3], tax_identifier[3:5], tax_identifier[5:]
        ),
    }
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    assert response.status_code == 200


def test_employees_search_missing_param(client, employee):
    body = {"last_name": "Doe", "tax_identifier": "000-00-0000"}
    response = client.post("/v1/employees/search", json=body)
    assert response.status_code == 400


def test_employees_search_nonexisting_employee(client, consented_user_token):
    body = {"first_name": "Damian", "last_name": "Wayne", "tax_identifier": "123-45-6789"}
    response = client.post(
        "/v1/employees/search",
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    assert response.status_code == 404


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
    assert updated_employee["first_name"] == "James"
    assert updated_employee["last_name"] == "Brown"
    assert updated_employee["employee_id"] == str(employee.employee_id)
    assert updated_employee["middle_name"] == employee.middle_name


def test_employees_patch_empty(client, employee, consented_user_token):
    body = {"first_name": "", "last_name": ""}
    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id),
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )
    updated_employee = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    ).get_json()

    # This test should return a 400 because blank requests shouldn't be accepted.
    assert response.status_code == 400
    assert updated_employee["first_name"] == employee.first_name


def test_employees_patch_404(client, consented_user_token):
    # This tests attempts to PATCH an employee that doesn't exist
    body = {"first_name": "Barbara", "last_name": "Gordon"}
    response = client.patch(
        "/v1/employees/{}".format("9e243bae-3b1e-43a4-aafe-aca3c6517cf0"),
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    assert response.status_code == 404


def test_employee_auth_get(disable_employee_endpoint, client, employee, consented_user_token):
    # This tests a user that doesn't meet authorization rules. Should return 403

    response = client.get(
        "/v1/employees/{}".format(employee.employee_id),
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    assert response.status_code == 403


def test_employee_auth_patch(disable_employee_endpoint, client, employee, consented_user_token):
    # Attempts to patch when user doesn't meet authorization rules.

    body = {"first_name": "James", "last_name": "Brown"}

    response = client.patch(
        "/v1/employees/{}".format(employee.employee_id),
        json=body,
        headers={"Authorization": "Bearer {}".format(consented_user_token)},
    )

    assert response.status_code == 403
