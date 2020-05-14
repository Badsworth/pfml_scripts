import massgov.pfml.api.generate_fake_data as fake


def test_employees_get_valid(client, test_employee):
    employee_id = test_employee["employee_id"]
    response = client.get("/v1/employees/{}".format(employee_id))
    assert response.status_code == 200


def test_employees_get_invalid(client, test_employee):
    response = client.get("/v1/employees/{}".format("nope"))
    assert response.status_code == 404


def test_employees_search_valid(client, test_employee):
    first_name = test_employee["first_name"]
    last_name = test_employee["last_name"]
    ssn_or_itin = test_employee["ssn_or_itin"]
    body = {"first_name": first_name, "last_name": last_name, "ssn_or_itin": ssn_or_itin}

    response = client.post("/v1/employees/search", json=body)
    assert response.status_code == 200


def test_employees_search_invalid(client, test_employee):
    body = {"last_name": "Doe", "ssn_or_itin": "000-00-0000"}
    response = client.post("/v1/employees/search", json=body)
    assert response.status_code == 400


def test_employees_patch(client, test_employee):
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch("/v1/employees/{}".format(test_employee["employee_id"]), json=body)
    assert response.status_code == 200

    updated_employee = fake.employees.get(test_employee["ssn_or_itin"])
    assert updated_employee
    assert updated_employee.get("first_name") == "James"
    assert updated_employee.get("last_name") == "Brown"
