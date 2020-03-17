import massgov.pfml.api.generate_fake_data as fake


def test_employees_get(client, test_employee):
    response = client.get(
        "/v1/employees/government-id?first_name={}&last_name={}".format(
            test_employee["first_name"], test_employee["last_name"]
        ),
        headers={"ssn_or_itin": test_employee["ssn_or_itin"]},
    )
    assert response.status_code == 200


def test_employees_get_missing_header(client, test_employee):
    response = client.get(
        "/v1/employees/government-id?first_name={}&last_name={}".format(
            test_employee["first_name"], test_employee["last_name"]
        )
    )
    assert response.status_code == 400


def test_employees_get_invalid_parameters(client, test_employee):
    response = client.get(
        "/v1/employees/government-id?first_name={}&last_name={}&nope=noooope ".format(
            test_employee["first_name"], test_employee["last_name"]
        ),
        headers={"ssn_or_itin": test_employee["ssn_or_itin"]},
    )
    assert response.status_code == 400


def test_employees_patch(client, test_employee):
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch("/v1/employees/{}".format(test_employee["employee_id"]), json=body)
    assert response.status_code == 200

    updated_employee = fake.employees.get(test_employee["ssn_or_itin"])
    assert updated_employee.get("first_name") == "James"
    assert updated_employee.get("last_name") == "Brown"
