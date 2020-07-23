from massgov.pfml.api.services import fineos_actions


def test_register_employee_pass():
    employer_fein = 179892886
    employee_ssn = 784569632
    employee_external_id = fineos_actions.register_employee(employee_ssn, employer_fein)

    if employee_external_id is None:
        AssertionError
    else:
        assert True


def test_register_employee_bad_fein():
    employer_fein = 999999999
    employee_ssn = 784569632
    employee_external_id = fineos_actions.register_employee(employee_ssn, employer_fein)

    if employee_external_id is None:
        assert True
    else:
        AssertionError


def test_register_employee_bad_ssn():
    employer_fein = 179892886
    employee_ssn = 999999999
    employee_external_id = fineos_actions.register_employee(employee_ssn, employer_fein)

    if employee_external_id is None:
        assert True
    else:
        AssertionError
