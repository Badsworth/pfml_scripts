import json
import flask
import pfml
import pfml.employees
from pfml import generate_fake_data as fake

app = pfml.create_app()

def test_valid_patch():
    employee = fake.create_employee()
    ssn_itin = employee.get('ssn_or_itin')
    employee_id = employee.get('employee_id')

    # put employee into fake data dictionary
    fake.employees[ssn_itin] = employee

    client = app.app.test_client()
    body = {"first_name": "James", "last_name": "Brown"}
    response = client.patch("/v1/employees/{}".format(employee_id), json=body)
    assert response.status_code == 200

    updated_employee = fake.employees.get(ssn_itin)
    assert updated_employee.get('first_name') == "James"
    assert updated_employee.get('last_name') == "Brown"