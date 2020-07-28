from massgov.pfml.api.services import fineos_actions
from massgov.pfml.fineos.exception import FINEOSClientBadResponse, FINEOSNotFound


def test_register_employee_pass(test_db_session):
    employer_fein = 179892886
    employee_ssn = 784569632
    employee_external_id = fineos_actions.register_employee(
        employee_ssn, employer_fein, test_db_session
    )

    assert employee_external_id is not None


def test_using_existing_id(test_db_session):
    employer_fein = 179892886
    employee_ssn = 784569632
    employee_external_id_1 = fineos_actions.register_employee(
        employee_ssn, employer_fein, test_db_session
    )

    employee_external_id_2 = fineos_actions.register_employee(
        employee_ssn, employer_fein, test_db_session
    )

    assert employee_external_id_1 == employee_external_id_2


def test_create_different_id_for_other_employer(test_db_session):
    employer_fein = 179892886
    employee_ssn = 784569632
    employee_external_id_1 = fineos_actions.register_employee(
        employee_ssn, employer_fein, test_db_session
    )

    employer_fein = 179892897
    employee_external_id_2 = fineos_actions.register_employee(
        employee_ssn, employer_fein, test_db_session
    )

    assert employee_external_id_1 != employee_external_id_2


def test_register_employee_bad_fein(test_db_session):
    employer_fein = 999999999
    employee_ssn = 784569632

    try:
        fineos_actions.register_employee(employee_ssn, employer_fein, test_db_session)
    except FINEOSNotFound:
        assert True


def test_register_employee_bad_ssn(test_db_session):
    employer_fein = 179892886
    employee_ssn = 999999999

    try:
        fineos_actions.register_employee(employee_ssn, employer_fein, test_db_session)
    except FINEOSClientBadResponse:
        assert True
