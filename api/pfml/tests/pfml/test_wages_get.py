#
# Tests for pfml.wages.wages_get
#

import json
import flask
import pfml
import pfml.employees
import pfml.generate_fake_data as fake

app = pfml.create_app()

def test_valid_get():
    # create test employee
    employee = fake.create_employee()
    employee_id = employee.get('employee_id')
    ssn_or_itin = employee.get('ssn_or_itin')

    # create test wages
    wages = fake.create_wages(employee_id, '0000-0000-0000-0000')

    # janky, but can't recall how to mock the dictionary so placing employee 
    # and wages in employees and wages dictionarybecause the dictionary of employees is a psuedo db
    fake.employees[ssn_or_itin] = employee
    fake.wages[employee_id] = [wages]
    
    client = app.app.test_client()
    response = client.get("/v1/wages?employee_id={}".format(employee_id))
    assert response.status_code == 200

def test_invalid_get():
    client = app.app.test_client()
    response = client.get("/v1/wages?employee_id=0000000")
    assert response.status_code == 404
