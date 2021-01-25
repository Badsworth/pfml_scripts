import pytest

from massgov.pfml.db.models.employees import Employee, EmployeeLog, Employer, EmployerLog
from massgov.pfml.db.models.factories import EmployeeFactory, EmployerFactory


@pytest.fixture
def employee(initialize_factories_session):
    employee = EmployeeFactory.create()
    return employee


@pytest.fixture
def employees(initialize_factories_session):
    return [EmployeeFactory.create(), EmployeeFactory.create(), EmployeeFactory.create()]


def test_insert_employee_row(
    test_db_session, initialize_factories_session, create_triggers, employee
):
    employee_id = employee.employee_id
    test_db_session.add(employee)
    test_db_session.commit()

    audited_employee = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.employee_id == employee_id).one()
    )
    assert audited_employee is not None
    assert employee_id == audited_employee.employee_id
    assert audited_employee.action == "INSERT"


def test_update_employee_row(
    test_db_session, initialize_factories_session, create_triggers, employee
):
    employee_id = employee.employee_id
    test_db_session.add(employee)
    test_db_session.commit()
    test_db_session.refresh(employee)

    employee.first_name = "Carlos"
    employee.last_name = "Gomez"
    test_db_session.add(employee)
    test_db_session.commit()

    audited_employees = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.employee_id == employee_id).all()
    )
    assert len(audited_employees) == 2
    audited_employee = (
        test_db_session.query(EmployeeLog)
        .filter(EmployeeLog.employee_id == employee_id, EmployeeLog.action == "UPDATE")
        .one()
    )
    assert audited_employee is not None
    assert employee_id == audited_employee.employee_id

    audited_employee = (
        test_db_session.query(EmployeeLog)
        .filter(EmployeeLog.employee_id == employee_id, EmployeeLog.action == "INSERT")
        .one()
    )
    assert audited_employee is not None


def test_delete_employee_row(
    test_db_session, initialize_factories_session, create_triggers, employee
):
    employee_id = employee.employee_id
    test_db_session.add(employee)
    test_db_session.commit()

    test_db_session.delete(employee)
    test_db_session.commit()

    audited_employees = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.employee_id == employee_id).all()
    )
    assert len(audited_employees) == 2
    audited_employee = (
        test_db_session.query(EmployeeLog)
        .filter(EmployeeLog.employee_id == employee_id, EmployeeLog.action == "DELETE")
        .one()
    )
    assert audited_employee is not None
    assert employee_id == audited_employee.employee_id

    audited_employee = (
        test_db_session.query(EmployeeLog)
        .filter(EmployeeLog.employee_id == employee_id, EmployeeLog.action == "INSERT")
        .one()
    )
    assert audited_employee is not None


def test_employee_bulk_insert(
    test_db_session, initialize_factories_session, create_triggers, employees
):
    test_db_session.add_all(employees)
    test_db_session.commit()

    inserted_employees = test_db_session.query(Employee).all()
    assert len(inserted_employees) == 3

    audited_employees = test_db_session.query(EmployeeLog).all()
    assert len(audited_employees) == 3

    audited_employee = (
        test_db_session.query(EmployeeLog)
        .filter(EmployeeLog.employee_id == employees[0].employee_id)
        .one()
    )
    assert audited_employee is not None


def test_employee_bulk_save(
    test_db_session, initialize_factories_session, create_triggers, employees
):
    test_db_session.bulk_save_objects(employees)
    test_db_session.commit()

    inserted_employees = test_db_session.query(Employee).all()
    assert len(inserted_employees) == 3

    audited_employees = test_db_session.query(EmployeeLog).all()
    assert len(audited_employees) == 3

    audited_employee = (
        test_db_session.query(EmployeeLog)
        .filter(EmployeeLog.employee_id == employees[0].employee_id)
        .one()
    )
    assert audited_employee is not None


def test_employee_bulk_delete(
    test_db_session, initialize_factories_session, create_triggers, employees
):
    test_db_session.add_all(employees)
    test_db_session.commit()
    test_db_session.query(Employee).delete()
    test_db_session.commit()

    audit_deleted_employees = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "DELETE").all()
    )
    assert len(audit_deleted_employees) == 3


@pytest.fixture
def employer(initialize_factories_session):
    employer = EmployerFactory.create()
    return employer


@pytest.fixture
def employers(initialize_factories_session):
    return [EmployerFactory.create(), EmployerFactory.create(), EmployerFactory.create()]


def test_insert_employer_row(
    test_db_session, initialize_factories_session, create_triggers, employer
):
    employer_id = employer.employer_id
    test_db_session.add(employer)
    test_db_session.commit()

    audited_employer = (
        test_db_session.query(EmployerLog).filter(EmployerLog.employer_id == employer_id).one()
    )
    assert audited_employer is not None
    assert employer_id == audited_employer.employer_id
    assert audited_employer.action == "INSERT"


def test_update_employer_row(
    test_db_session, initialize_factories_session, create_triggers, employer
):
    employer_id = employer.employer_id
    test_db_session.add(employer)
    test_db_session.commit()
    test_db_session.refresh(employer)

    employer.employer_name = "One Organization"
    test_db_session.add(employer)
    test_db_session.commit()

    audited_employers = test_db_session.query(EmployerLog).all()
    assert len(audited_employers) == 2
    audited_employer = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer_id, EmployerLog.action == "UPDATE")
        .one()
    )
    assert audited_employer is not None
    assert employer_id == audited_employer.employer_id

    audited_employer = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer_id, EmployerLog.action == "INSERT")
        .one()
    )
    assert audited_employer is not None


def test_delete_employer_row(
    test_db_session, initialize_factories_session, create_triggers, employer
):
    employer_id = employer.employer_id
    test_db_session.add(employer)
    test_db_session.commit()

    test_db_session.delete(employer)
    test_db_session.commit()

    audited_employers = (
        test_db_session.query(EmployerLog).filter(EmployerLog.employer_id == employer_id).all()
    )
    assert len(audited_employers) == 2
    audited_employer = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer_id, EmployerLog.action == "DELETE")
        .one()
    )
    assert audited_employer is not None
    assert employer_id == audited_employer.employer_id

    audited_employer = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employer_id, EmployerLog.action == "INSERT")
        .one()
    )
    assert audited_employer is not None


def test_employer_bulk_insert(
    test_db_session, initialize_factories_session, create_triggers, employers
):
    test_db_session.add_all(employers)
    test_db_session.commit()

    inserted_employers = test_db_session.query(Employer).all()
    assert len(inserted_employers) == 3

    audited_employers = test_db_session.query(EmployerLog).all()
    assert len(audited_employers) == 3

    audited_employer = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employers[0].employer_id)
        .one()
    )
    assert audited_employer is not None


def test_employer_bulk_save(
    test_db_session, initialize_factories_session, create_triggers, employers
):
    test_db_session.bulk_save_objects(employers)
    test_db_session.commit()

    inserted_employers = test_db_session.query(Employer).all()
    assert len(inserted_employers) == 3

    audited_employers = test_db_session.query(EmployerLog).all()
    assert len(audited_employers) == 3

    audited_employer = (
        test_db_session.query(EmployerLog)
        .filter(EmployerLog.employer_id == employers[0].employer_id)
        .one()
    )
    assert audited_employer is not None


def test_employer_bulk_delete(
    test_db_session, initialize_factories_session, create_triggers, employers
):
    test_db_session.add_all(employers)
    test_db_session.commit()
    test_db_session.query(Employer).delete()
    test_db_session.commit()

    audit_deleted_employers = (
        test_db_session.query(EmployerLog).filter(EmployerLog.action == "DELETE").all()
    )
    assert len(audit_deleted_employers) == 3
