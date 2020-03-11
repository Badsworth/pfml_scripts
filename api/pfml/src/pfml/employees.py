import connexion
import flask
import pfml.generate_fake_data as fake

employees_dict = fake.employees

# this endpoint has been created for test purposes only. As fake employee data is automatically
# generated when the server starts, this endpoint is a mechanism to grab ids for the objects 
# that have been mocked, and those ids can be used at the PATCH to /employees/{employee_id} and
# the GET to /wages which requires an employee_id param
def employees_get_all_fake():
    return employees_dict

def employees_get(first_name, last_name):
    header = connexion.request.headers

    # not sure how we'll handle encryption yet, but this will have to be encrypted
    ssn_or_itin = header.get('ssn_or_itin')

    # get employee from the dictionary whose ssn/itin is the same as the one in the header
    try:
        employee = employees_dict[ssn_or_itin]
    except KeyError:
        not_found_error = flask.Response(status=404)
        return not_found_error

    same_first_name = employee['first_name'] == first_name
    same_last_name = employee['last_name'] == last_name

    # if the ssn/itin, first name and last name match, return employee
    if employee and same_first_name and same_last_name:
        return employee 
    # if ssn/itin exists but names don't match, return an error
    return not_found_error


# this endpoint will allow an employees personal information to be updated
def employees_patch(employee_id):
    body = connexion.request.json

    # there are properties that a user should not be allowed to modify, for the purpose of
    # this mock, only the following properties are mutable
    mutable_properties = ['first_name', 'middle_name', 'last_name', 'date_of_birth']

    employee = {}

    # the following logic would not be necessary in real life, but because we are using dictionaries
    # to simulate a db and the key to the employees dictionary is ssn/itin --as the arg here is employee id and not ssn--
    # we'll need to iterate through the dictionary and find the record where the employee id matches
    for key, value in employees_dict.items():
        if value.get('employee_id') == employee_id:
            employee = value

    if employee:
        for attr in body:
            if attr in mutable_properties and attr is not 'employee_id':
                employee[attr] = body.get(attr)

    return employee