import pytest

from massgov.pfml.db.models.factories import EmployeeFactory

params = [("Stacy", "Davis", "123456789"), ("x", "Doe", "123456789"), ("Jane", "x", "123456789")]


@pytest.fixture
def employee():
    employee = EmployeeFactory.create()
    return employee


@pytest.fixture(params=params)
def bad_test_params(request):
    return request.param


@pytest.mark.skip(reason="Testing employees will be in another PR")
def test_employees_get_valid(client, employee):
    response = client.get("/v1/employees/{}".format(employee.employee_id))
    assert response.status_code == 200


@pytest.mark.skip(reason="Testing employees will be in another PR")
def test_employees_get_invalid(client):
    response = client.get("/v1/employees/{}".format("9e243bae-3b1e-43a4-aafe-aca3c6517cf0"))
    assert response.status_code == 404


@pytest.mark.skip(reason="Testing employees will be in another PR")
def test_employees_search_valid(client, employee):
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
    response = client.post("/v1/employees/search", json=body)
    assert response.status_code == 200


@pytest.mark.skip(reason="Testing employees will be in another PR")
def test_employees_search_missing_param(client, employee):
    body = {"last_name": "Doe", "tax_identifier": "000-00-0000"}
    response = client.post("/v1/employees/search", json=body)
    assert response.status_code == 400


@pytest.mark.skip(reason="Testing employees will be in another PR")
def test_employee_search_nonexisting_employee(client, employee):
    body = {"first_name": "Damian", "last_name": "Wayne", "tax_identifier": "123-45-6789"}
    response = client.post("/v1/employees/search", json=body)
    assert response.status_code == 404


@pytest.mark.skip(reason="Testing employees will be in another PR")
def test_employees_patch(client, employee):
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch("/v1/employees/{}".format(employee.employee_id), json=body)
    assert response.status_code == 200

    updated_employee = client.get("/v1/employees/{}".format(employee.employee_id)).get_json()
    assert updated_employee["first_name"] == "James"
    assert updated_employee["last_name"] == "Brown"
    assert updated_employee["employee_id"] == employee.employee_id


@pytest.mark.skip(reason="Testing employees will be in another PR")
def test_employee_patch_empty(client, employee):
    body = {"first_name": "", "last_name": ""}
    response = client.patch("/v1/employees/{}".format(employee.employee_id), json=body)
    # updated_employee = client.get("/v1/employees/{}".format(employee.employee_id)).get_json()

    # This test should return a 200 even though the body is empty
    assert response.status_code == 200
