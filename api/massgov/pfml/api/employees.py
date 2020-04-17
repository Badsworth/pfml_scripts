import connexion
from werkzeug.exceptions import NotFound

import massgov.pfml.api.generate_fake_data as fake

employees_dict = fake.employees


def employees_get_all_fake():
    # this endpoint has been created for test purposes only. As fake employee data is automatically
    # generated when the server starts, this endpoint is a mechanism to grab ids for the objects
    # that have been mocked, and those ids can be used at the PATCH to /employees/{employee_id} and
    # the GET to /wages which requires an employee_id param

    return employees_dict


def employees_get(employee_id):
    for employee in employees_dict.values():
        if employee.get("employee_id") == employee_id:
            return employee

    raise NotFound()


def employees_patch(employee_id):
    """ this endpoint will allow an employee's personal information to be updated """
    body = connexion.request.json

    # there are properties that a user should not be allowed to modify, for the purpose of
    # this mock, only the following properties are mutable
    mutable_properties = ["first_name", "middle_name", "last_name", "date_of_birth"]

    # the following logic would not be necessary in real life, but because we are using dictionaries
    # to simulate a db and the key to the employees dictionary is ssn/itin --as the arg here is employee id and not ssn--
    # we'll need to iterate through the dictionary and find the record where the employee id matches
    for employee in employees_dict.values():
        if employee.get("employee_id") == employee_id:

            for attr in body:
                if attr in mutable_properties and attr != "employee_id":
                    employee[attr] = body.get(attr)
            return employee

    raise NotFound()


def employees_search():
    body = connexion.request.json
    first_name = body.get("first_name")
    last_name = body.get("last_name")
    ssn_or_itin = body.get("ssn_or_itin")

    # get employee from the dictionary whose ssn/itin is the same as the one in the header
    try:
        employee = employees_dict[ssn_or_itin]
    except KeyError:
        raise NotFound()

    same_first_name = employee["first_name"] == first_name
    same_last_name = employee["last_name"] == last_name

    # if the ssn/itin, first name and last name match, return employee
    if employee and same_first_name and same_last_name:
        return employee

    # if ssn/itin exists but names don't match, return an error
    raise NotFound()
