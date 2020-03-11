#
# Tests for pfml.employees.employees_get
#

import json
import flask
import pfml
import pfml.employees
import pfml.generate_fake_data as fake

app = pfml.create_app()

# create test employee
employee = fake.create_employee()
ssn_or_itin = employee.get('ssn_or_itin')
first_name = employee.get('first_name')
last_name = employee.get('last_name')

# janky, but can't recall how to mock the dictionary so placing employee in employees dictionary
# because the dictionary of employees is a psuedo db
fake.employees[ssn_or_itin] = employee

def test_valid_get():
    client = app.app.test_client()
    response = client.get("/v1/employees/government-id?first_name={}&last_name={}".format(first_name, last_name), headers={'ssn_or_itin': ssn_or_itin})
    assert response.status_code == 200

def test_missing_header():
    client = app.app.test_client()
    response = client.get("/v1/employees/government-id?first_name={}&last_name={}".format(first_name, last_name))
    assert response.status_code == 400

def test_invalid_parameters():
    client = app.app.test_client()
    response = client.get("/v1/employees/government-id?first_name={}&last_name={}&nope=noooope ".format(first_name, last_name), headers={'ssn_or_itin': ssn_or_itin})
    assert response.status_code == 400
