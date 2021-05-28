import decimal

import pytest

import massgov.pfml.fineos.import_fineos_updates as fineos_updates
from massgov.pfml.db.models.employees import (
    Employee,
    EmployeeLog,
    EmployeeOccupation,
    Gender,
    MaritalStatus,
    TaxIdentifier,
    Title,
)
from massgov.pfml.db.models.factories import EmployeeFactory, EmployerFactory, TaxIdentifierFactory
from massgov.pfml.util import datetime

# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def emp_updates_path(tmp_path):
    file_name = "2020-12-10-23-10-11-EmployeeDataLoad_feed.csv"
    content_line_one = '"EMPLOYEEIDENTIFIER","EMPLOYEETITLE","EMPLOYEEDATEOFBIRTH","EMPLOYEEGENDER","EMPLOYEEMARITALSTATUS","TELEPHONEINTCODE","TELEPHONEAREACODE","TELEPHONENUMBER","CELLINTCODE","CELLAREACODE","CELLNUMBER","EMPLOYEEEMAIL","EMPLOYEEID","EMPLOYEECLASSIFICATION","EMPLOYEEJOBTITLE","EMPLOYEEDATEOFHIRE","EMPLOYEEENDDATE","EMPLOYMENTSTATUS","EMPLOYEEORGUNITNAME","EMPLOYEEHOURSWORKEDPERWEEK","EMPLOYEEDAYSWORKEDPERWEEK","MANAGERIDENTIFIER","QUALIFIERDESCRIPTION","EMPLOYEEWORKSITEID","ORG_CUSTOMERNO","ORG_NAME","EMPLOYEENATIONALID","EMPLOYEEFIRSTNAME","EMPLOYEELASTNAME","CUSTOMERNO"'
    content_line_two = '"4376896b-596c-4c86-a653-1915cf997a84","Mr","1970-10-06 00:00:00","Male","Single","","","","","","","nona@comm.com","","Unknown","DEFAULT","2000-01-01 00:00:00","","Active","Testing Department","37.5","0","","","","10","Test Company","123456789","John","Doe","444"'
    content_line_three = '"cb2f2d72-ac68-4402-a82f-6e32edd086b3","Unknown","1994-09-14 00:00:00","Unknown","Unknown","","","","","","","rob+pfml-cypress-gh3@lastcallmedia.com","","Unknown","DEFAULT","2020-01-01 00:00:00","","Active","","42","4.55","","","","10","Test Company","987654321","Jerry","Smith","555"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)

    # Additional file to test file filter
    file_name_two = "EmployeeExtract.csv"
    test_file_two = test_folder / file_name_two
    test_file_two.write_text("Just another file\nto Filter out.")

    return test_folder


@pytest.fixture
def emp_updates_path_no_org_no(tmp_path):
    file_name = "2020-12-10-23-10-11-EmployeeDataLoad_feed.csv"
    content_line_one = '"EMPLOYEEIDENTIFIER","EMPLOYEETITLE","EMPLOYEEDATEOFBIRTH","EMPLOYEEGENDER","EMPLOYEEMARITALSTATUS","TELEPHONEINTCODE","TELEPHONEAREACODE","TELEPHONENUMBER","CELLINTCODE","CELLAREACODE","CELLNUMBER","EMPLOYEEEMAIL","EMPLOYEEID","EMPLOYEECLASSIFICATION","EMPLOYEEJOBTITLE","EMPLOYEEDATEOFHIRE","EMPLOYEEENDDATE","EMPLOYMENTSTATUS","EMPLOYEEORGUNITNAME","EMPLOYEEHOURSWORKEDPERWEEK","EMPLOYEEDAYSWORKEDPERWEEK","MANAGERIDENTIFIER","QUALIFIERDESCRIPTION","EMPLOYEEWORKSITEID","ORG_CUSTOMERNO","ORG_NAME","EMPLOYEENATIONALID","EMPLOYEEFIRSTNAME","EMPLOYEELASTNAME","CUSTOMERNO"'
    content_line_two = '"4376896b-596c-4c86-a653-1915cf997a84","Mr","1970-10-06 00:00:00","Male","Single","","","","","","","nona@comm.com","","Unknown","DEFAULT","2000-01-01 00:00:00","","Active","Testing Department","37.5","0","","","","","Test Company","123456789","John","Doe","444"'
    content_line_three = '"cb2f2d72-ac68-4402-a82f-6e32edd086b3","Unknown","1994-09-14 00:00:00","Unknown","Unknown","","","","","","","rob+pfml-cypress-gh3@lastcallmedia.com","","Unknown","DEFAULT","2020-01-01 00:00:00","","Active","","42","4.55","","","","10","Test Company","987654321","Jerry","Smith","555"'
    content = f"{content_line_one}\n{content_line_two}\n{content_line_three}"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)

    # Additional file to test file filter
    file_name_two = "EmployeeExtract.csv"
    test_file_two = test_folder / file_name_two
    test_file_two.write_text("Just another file\nto Filter out.")

    return test_folder


@pytest.fixture
def emp_updates_path_incorrect_org_no(tmp_path):
    file_name = "2020-12-10-23-10-11-EmployeeDataLoad_feed.csv"
    content_line_one = '"EMPLOYEEIDENTIFIER","EMPLOYEETITLE","EMPLOYEEDATEOFBIRTH","EMPLOYEEGENDER","EMPLOYEEMARITALSTATUS","TELEPHONEINTCODE","TELEPHONEAREACODE","TELEPHONENUMBER","CELLINTCODE","CELLAREACODE","CELLNUMBER","EMPLOYEEEMAIL","EMPLOYEEID","EMPLOYEECLASSIFICATION","EMPLOYEEJOBTITLE","EMPLOYEEDATEOFHIRE","EMPLOYEEENDDATE","EMPLOYMENTSTATUS","EMPLOYEEORGUNITNAME","EMPLOYEEHOURSWORKEDPERWEEK","EMPLOYEEDAYSWORKEDPERWEEK","MANAGERIDENTIFIER","QUALIFIERDESCRIPTION","EMPLOYEEWORKSITEID","ORG_CUSTOMERNO","ORG_NAME","EMPLOYEENATIONALID","EMPLOYEEFIRSTNAME","EMPLOYEELASTNAME","CUSTOMERNO"'
    content_line_two = '"4376896b-596c-4c86-a653-1915cf997a84","Mr","1970-10-06 00:00:00","Male","Single","","","","","","","nona@comm.com","","Unknown","DEFAULT","2000-01-01 00:00:00","","Active","Testing Department","37.5","0","","","","11","Test Company","123456789","John","Doe","444"'
    content = f"{content_line_one}\n{content_line_two}"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)

    return test_folder


@pytest.fixture
def emp_updates_path_no_ssn_present(tmp_path):
    file_name = "2020-12-10-23-10-11-EmployeeDataLoad_feed.csv"
    content_line_one = '"EMPLOYEEIDENTIFIER","EMPLOYEETITLE","EMPLOYEEDATEOFBIRTH","EMPLOYEEGENDER","EMPLOYEEMARITALSTATUS","TELEPHONEINTCODE","TELEPHONEAREACODE","TELEPHONENUMBER","CELLINTCODE","CELLAREACODE","CELLNUMBER","EMPLOYEEEMAIL","EMPLOYEEID","EMPLOYEECLASSIFICATION","EMPLOYEEJOBTITLE","EMPLOYEEDATEOFHIRE","EMPLOYEEENDDATE","EMPLOYMENTSTATUS","EMPLOYEEORGUNITNAME","EMPLOYEEHOURSWORKEDPERWEEK","EMPLOYEEDAYSWORKEDPERWEEK","MANAGERIDENTIFIER","QUALIFIERDESCRIPTION","EMPLOYEEWORKSITEID","ORG_CUSTOMERNO","ORG_NAME","EMPLOYEENATIONALID","EMPLOYEEFIRSTNAME","EMPLOYEELASTNAME","CUSTOMERNO"'
    content_line_two = '"cb2f2d72-ac68-4402-a82f-6e32edd086b3","Unknown","1994-09-14 00:00:00","Unknown","Unknown","","","","","","","rob+pfml-cypress-gh3@lastcallmedia.com","","Unknown","DEFAULT","2020-01-01 00:00:00","","Active","","42","4.55","","","","10","Test Company","","Jerry","Smith","555"'
    content = f"{content_line_one}\n{content_line_two}"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)

    return test_folder


@pytest.fixture
def emp_updates_path_name_fields_have_no_value(tmp_path):
    file_name = "2020-12-10-23-10-11-EmployeeDataLoad_feed.csv"
    content_line_one = '"EMPLOYEEIDENTIFIER","EMPLOYEETITLE","EMPLOYEEDATEOFBIRTH","EMPLOYEEGENDER","EMPLOYEEMARITALSTATUS","TELEPHONEINTCODE","TELEPHONEAREACODE","TELEPHONENUMBER","CELLINTCODE","CELLAREACODE","CELLNUMBER","EMPLOYEEEMAIL","EMPLOYEEID","EMPLOYEECLASSIFICATION","EMPLOYEEJOBTITLE","EMPLOYEEDATEOFHIRE","EMPLOYEEENDDATE","EMPLOYMENTSTATUS","EMPLOYEEORGUNITNAME","EMPLOYEEHOURSWORKEDPERWEEK","EMPLOYEEDAYSWORKEDPERWEEK","MANAGERIDENTIFIER","QUALIFIERDESCRIPTION","EMPLOYEEWORKSITEID","ORG_CUSTOMERNO","ORG_NAME","EMPLOYEENATIONALID","EMPLOYEEFIRSTNAME","EMPLOYEELASTNAME","CUSTOMERNO"'
    content_line_two = '"cb2f2d72-ac68-4402-a82f-6e32edd086b3","Unknown","1994-09-14 00:00:00","Unknown","Unknown","","","","","","","rob+pfml-cypress-gh3@lastcallmedia.com","","Unknown","DEFAULT","2020-01-01 00:00:00","","Active","","42","4.55","","","","10","Test Company","987654321","","","555"'
    content = f"{content_line_one}\n{content_line_two}"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)

    return test_folder


@pytest.fixture
def emp_updates_path_name_fields_not_present(tmp_path):
    file_name = "2020-12-10-23-10-11-EmployeeDataLoad_feed.csv"
    content_line_one = '"EMPLOYEEIDENTIFIER","EMPLOYEETITLE","EMPLOYEEDATEOFBIRTH","EMPLOYEEGENDER","EMPLOYEEMARITALSTATUS","TELEPHONEINTCODE","TELEPHONEAREACODE","TELEPHONENUMBER","CELLINTCODE","CELLAREACODE","CELLNUMBER","EMPLOYEEEMAIL","EMPLOYEEID","EMPLOYEECLASSIFICATION","EMPLOYEEJOBTITLE","EMPLOYEEDATEOFHIRE","EMPLOYEEENDDATE","EMPLOYMENTSTATUS","EMPLOYEEORGUNITNAME","EMPLOYEEHOURSWORKEDPERWEEK","EMPLOYEEDAYSWORKEDPERWEEK","MANAGERIDENTIFIER","QUALIFIERDESCRIPTION","EMPLOYEEWORKSITEID","ORG_CUSTOMERNO","ORG_NAME","EMPLOYEENATIONALID","CUSTOMERNO"'
    content_line_two = '"cb2f2d72-ac68-4402-a82f-6e32edd086b3","Unknown","1994-09-14 00:00:00","Unknown","Unknown","","","","","","","rob+pfml-cypress-gh3@lastcallmedia.com","","Unknown","DEFAULT","2020-01-01 00:00:00","","Active","","42","4.55","","","","10","Test Company","987654321","555"'
    content = f"{content_line_one}\n{content_line_two}"

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / file_name
    test_file.write_text(content)

    return test_folder


def test_fineos_updates_happy_path(
    test_db_session, initialize_factories_session, emp_updates_path, create_triggers
):
    employee_one = EmployeeFactory(
        employee_id="4376896b-596c-4c86-a653-1915cf997a84", gender_id=Gender.WOMAN.gender_id
    )
    employee_two = EmployeeFactory(employee_id="cb2f2d72-ac68-4402-a82f-6e32edd086b3")
    employer = EmployerFactory(
        employer_id="4376896b-596c-4c86-a653-1915cf997a85",
        fineos_employer_id=10,
        employer_name="Test Company",
    )

    employee_log_rows_before = test_db_session.query(EmployeeLog).all()

    report = fineos_updates.process_fineos_updates(test_db_session, emp_updates_path)

    updated_employee_one = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_one.employee_id)
        .one()
    )

    updated_employee_two = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_two.employee_id)
        .one()
    )

    employee_occupation_one = (
        test_db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == updated_employee_one.employee_id,
            EmployeeOccupation.employer_id == employer.employer_id,
        )
        .one()
    )

    employee_occupation_two = (
        test_db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == updated_employee_two.employee_id,
            EmployeeOccupation.employer_id == employer.employer_id,
        )
        .one()
    )

    assert updated_employee_one is not None
    assert updated_employee_one.title_id == 2
    assert updated_employee_one.date_of_birth == datetime.date(1970, 10, 6)
    assert updated_employee_one.marital_status_id == MaritalStatus.SINGLE.marital_status_id
    assert updated_employee_one.gender_id == Gender.MAN.gender_id
    assert updated_employee_one.title_id == Title.MR.title_id

    assert updated_employee_two is not None
    assert updated_employee_two.title_id == 1
    assert updated_employee_two.date_of_birth == datetime.date(1994, 9, 14)
    assert updated_employee_two.marital_status_id is None
    assert updated_employee_two.gender_id is Gender.NOT_LISTED.gender_id
    assert updated_employee_two.title_id == Title.UNKNOWN.title_id

    assert employee_occupation_one is not None
    assert employee_occupation_one.date_of_hire == datetime.date(2000, 1, 1)
    assert employee_occupation_one.employment_status == "Active"
    assert employee_occupation_one.hours_worked_per_week == decimal.Decimal("37.5")
    assert employee_occupation_one.days_worked_per_week == decimal.Decimal("0")

    assert employee_occupation_two is not None
    assert employee_occupation_two.date_of_hire == datetime.date(2020, 1, 1)
    assert employee_occupation_two.employment_status == "Active"
    assert employee_occupation_two.hours_worked_per_week == decimal.Decimal("42")
    assert employee_occupation_two.days_worked_per_week == decimal.Decimal("4.55")

    assert report.updated_employees_count == 2
    assert report.errored_employees_count == 0
    assert report.errored_employee_occupation_count == 0
    assert report.total_employees_received_count == 2

    # Confirm EmployeeLog did not pickup an additional entry from the process
    employee_log_rows_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_rows_after) == len(employee_log_rows_before)


def test_fineos_updates_no_employer(
    test_db_session, initialize_factories_session, emp_updates_path
):
    employee_one = EmployeeFactory(employee_id="4376896b-596c-4c86-a653-1915cf997a84")
    employee_two = EmployeeFactory(employee_id="cb2f2d72-ac68-4402-a82f-6e32edd086b3")

    report = fineos_updates.process_fineos_updates(test_db_session, emp_updates_path)

    updated_employee_one = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_one.employee_id)
        .one()
    )

    updated_employee_two = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_two.employee_id)
        .one()
    )

    assert updated_employee_one is not None
    assert updated_employee_one.title_id == 2
    assert updated_employee_one.date_of_birth == datetime.date(1970, 10, 6)

    assert updated_employee_two is not None
    assert updated_employee_two.title_id == 1
    assert updated_employee_two.date_of_birth == datetime.date(1994, 9, 14)

    assert report.updated_employees_count == 0
    assert report.errored_employees_count == 0
    assert report.errored_employee_occupation_count == 2
    assert report.total_employees_received_count == 2


def test_fineos_updates_missing_employee_found_by_ssn(
    test_db_session, initialize_factories_session, emp_updates_path, create_triggers
):
    employee_one = EmployeeFactory(employee_id="4376896b-596c-4c86-a653-1915cf997a84")
    tax_identifier = TaxIdentifierFactory(tax_identifier="987654321")
    EmployeeFactory(
        employee_id="7cd7f452-b7e1-405b-88cf-5657c3bfc04a", tax_identifier=tax_identifier
    )

    employer = EmployerFactory(
        employer_id="4376896b-596c-4c86-a653-1915cf997a85",
        fineos_employer_id=10,
        employer_name="Test Company",
    )

    employee_log_rows_before = test_db_session.query(EmployeeLog).all()

    report = fineos_updates.process_fineos_updates(test_db_session, emp_updates_path)

    updated_employee_one = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee_one.employee_id)
        .one()
    )

    employee_occupation = (
        test_db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == updated_employee_one.employee_id,
            EmployeeOccupation.employer_id == employer.employer_id,
        )
        .one()
    )

    assert updated_employee_one is not None
    assert updated_employee_one.title_id == 2
    assert updated_employee_one.date_of_birth == datetime.date(1970, 10, 6)

    assert employee_occupation is not None
    assert employee_occupation.date_of_hire == datetime.date(2000, 1, 1)
    assert employee_occupation.employment_status == "Active"

    assert report.updated_employees_count == 1
    assert report.emp_id_discrepancies_count == 1
    assert report.errored_employees_count == 1
    assert report.errored_employee_occupation_count == 1
    assert report.total_employees_received_count == 2

    # Confirm EmployeeLog did not pickup an additional entry from the process
    employee_log_rows_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_rows_after) == len(employee_log_rows_before)


def test_fineos_add_employee(
    test_db_session, initialize_factories_session, emp_updates_path, create_triggers
):
    employee = EmployeeFactory(employee_id="4376896b-596c-4c86-a653-1915cf997a84")
    employer = EmployerFactory(
        employer_id="4376896b-596c-4c86-a653-1915cf997a85",
        fineos_employer_id=10,
        employer_name="Test Company",
    )

    employee_log_rows_before = test_db_session.query(EmployeeLog).all()

    report = fineos_updates.process_fineos_updates(test_db_session, emp_updates_path)

    updated_employee = (
        test_db_session.query(Employee).filter(Employee.employee_id == employee.employee_id).one()
    )

    updated_employee_occupation = (
        test_db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == updated_employee.employee_id,
            EmployeeOccupation.employer_id == employer.employer_id,
        )
        .one()
    )

    assert updated_employee is not None
    assert updated_employee.title_id == 2
    assert updated_employee.date_of_birth == datetime.date(1970, 10, 6)

    assert updated_employee_occupation is not None
    assert updated_employee_occupation.date_of_hire == datetime.date(2000, 1, 1)
    assert updated_employee_occupation.employment_status == "Active"

    created_employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == "cb2f2d72-ac68-4402-a82f-6e32edd086b3")
        .one()
    )

    created_employee_occupation = (
        test_db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == created_employee.employee_id,
            EmployeeOccupation.employer_id == employer.employer_id,
        )
        .one()
    )

    assert created_employee is not None
    assert created_employee.title_id == 1
    assert created_employee.date_of_birth == datetime.date(1994, 9, 14)

    assert created_employee_occupation is not None
    assert created_employee_occupation.date_of_hire == datetime.date(2020, 1, 1)
    assert created_employee_occupation.employment_status == "Active"

    assert report.updated_employees_count == 1
    assert report.created_employees_count == 1
    assert report.errored_employees_count == 0
    assert report.errored_employee_occupation_count == 0
    assert report.total_employees_received_count == 2

    # Confirm EmployeeLog did not pickup an additional entry from the process
    employee_log_rows_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_rows_after) == len(employee_log_rows_before)


def test_fineos_updates_missing_org_customer_no(
    test_db_session, initialize_factories_session, emp_updates_path_no_org_no, create_triggers
):
    employee = EmployeeFactory(employee_id="4376896b-596c-4c86-a653-1915cf997a84")
    employer = EmployerFactory(
        employer_id="4376896b-596c-4c86-a653-1915cf997a85",
        fineos_employer_id=10,
        employer_name="Test Company",
    )

    employee_log_rows_before = test_db_session.query(EmployeeLog).all()

    report = fineos_updates.process_fineos_updates(test_db_session, emp_updates_path_no_org_no)

    updated_employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee.employee_id)
        .one_or_none()
    )

    employee_occupation = (
        test_db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == updated_employee.employee_id,
            EmployeeOccupation.employer_id == employer.employer_id,
        )
        .one_or_none()
    )

    assert updated_employee is not None
    assert employee_occupation is None

    assert report.created_employees_count == 1
    assert report.updated_employees_count == 0
    # Error at employee level because org customer number not present
    assert report.errored_employees_count == 1
    assert report.errored_employee_occupation_count == 0
    assert report.total_employees_received_count == 2

    # Confirm EmployeeLog did not pickup an additional entry from the process
    employee_log_rows_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_rows_after) == len(employee_log_rows_before)


def test_fineos_updates_incorrect_org_customer_no(
    test_db_session,
    initialize_factories_session,
    emp_updates_path_incorrect_org_no,
    create_triggers,
):
    employee = EmployeeFactory(employee_id="4376896b-596c-4c86-a653-1915cf997a84")
    employer = EmployerFactory(
        employer_id="4376896b-596c-4c86-a653-1915cf997a85",
        fineos_employer_id=10,
        employer_name="Test Company",
    )

    employee_log_rows_before = test_db_session.query(EmployeeLog).all()

    report = fineos_updates.process_fineos_updates(
        test_db_session, emp_updates_path_incorrect_org_no
    )

    updated_employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee.employee_id)
        .one_or_none()
    )

    employee_occupation = (
        test_db_session.query(EmployeeOccupation)
        .filter(
            EmployeeOccupation.employee_id == updated_employee.employee_id,
            EmployeeOccupation.employer_id == employer.employer_id,
        )
        .one_or_none()
    )

    assert updated_employee is not None
    assert employee_occupation is None

    assert report.created_employees_count == 0
    assert report.updated_employees_count == 0
    # Error at employee occupation level because org customer number present but incorrect
    assert report.errored_employees_count == 0
    assert report.errored_employee_occupation_count == 1
    assert report.total_employees_received_count == 1

    # Confirm EmployeeLog did not pickup an additional entry from the process
    employee_log_rows_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_rows_after) == len(employee_log_rows_before)


def test_fineos_updates_no_ssn_present(
    test_db_session, initialize_factories_session, emp_updates_path_no_ssn_present, create_triggers,
):
    report = fineos_updates.process_fineos_updates(test_db_session, emp_updates_path_no_ssn_present)

    assert report.created_employees_count == 0
    assert report.updated_employees_count == 0
    assert report.errored_employees_count == 1
    assert report.no_ssn_present_count == 1
    assert report.errored_employee_occupation_count == 0
    assert report.total_employees_received_count == 1


def test_fineos_updates_name_fields_have_no_value(
    test_db_session,
    initialize_factories_session,
    emp_updates_path_name_fields_have_no_value,
    create_triggers,
):
    EmployerFactory(
        employer_id="4376896b-596c-4c86-a653-1915cf997a85",
        fineos_employer_id=10,
        employer_name="Test Company",
    )

    employee_log_rows_before = test_db_session.query(EmployeeLog).all()

    report = fineos_updates.process_fineos_updates(
        test_db_session, emp_updates_path_name_fields_have_no_value
    )

    # Name values default to empty string so there should be no errors.
    assert report.created_employees_count == 1
    assert report.updated_employees_count == 0
    assert report.errored_employees_count == 0
    assert report.no_ssn_present_count == 0
    assert report.errored_employee_occupation_count == 0
    assert report.total_employees_received_count == 1

    employee = (
        test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "987654321")
        .one_or_none()
    )

    assert employee.first_name == ""
    assert employee.last_name == ""

    # Confirm EmployeeLog did not pickup an additional entry from the process
    employee_log_rows_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_rows_after) == len(employee_log_rows_before)


def test_fineos_updates_name_fields_not_present(
    test_db_session,
    initialize_factories_session,
    emp_updates_path_name_fields_not_present,
    create_triggers,
):
    EmployerFactory(
        employer_id="4376896b-596c-4c86-a653-1915cf997a85",
        fineos_employer_id=10,
        employer_name="Test Company",
    )

    employee_log_rows_before = test_db_session.query(EmployeeLog).all()

    report = fineos_updates.process_fineos_updates(
        test_db_session, emp_updates_path_name_fields_not_present
    )

    # Name values default to empty string so there should be no errors.
    assert report.created_employees_count == 1
    assert report.updated_employees_count == 0
    assert report.errored_employees_count == 0
    assert report.no_ssn_present_count == 0
    assert report.errored_employee_occupation_count == 0
    assert report.total_employees_received_count == 1

    employee = (
        test_db_session.query(Employee)
        .join(TaxIdentifier)
        .filter(TaxIdentifier.tax_identifier == "987654321")
        .one_or_none()
    )

    assert employee.first_name == ""
    assert employee.last_name == ""

    # Confirm EmployeeLog did not pickup an additional entry from the process
    employee_log_rows_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_rows_after) == len(employee_log_rows_before)
