import csv
import os
from datetime import date
from pathlib import Path

import boto3
import pytest

import massgov.pfml.fineos
import massgov.pfml.fineos.eligibility_feed as ef
from massgov.pfml.db.models.employees import (
    Employee,
    EmployeeAddress,
    EmployeeLog,
    EmployeeOccupation,
    Employer,
    Gender,
    TaxIdentifier,
    Title,
)
from massgov.pfml.db.models.factories import (
    AddressFactory,
    EmployeeFactory,
    EmployeeLogFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.types import Fein, TaxId

# almost every test in here requires real resources
pytestmark = pytest.mark.integration


class SpecialTestException(Exception):
    """Exception only defined here for ensure mocked exception is bubbled up"""


# every test in here requires real resources
pytestmark = pytest.mark.integration


def test_employee_to_eligibility_feed_record(initialize_factories_session):
    employee = EmployeeFactory.create()
    employer = EmployerFactory.create()
    wages_and_contributions = WagesAndContributionsFactory.create_batch(
        size=5, employee=employee, employer=employer
    )

    most_recent_wages = sorted(
        wages_and_contributions, key=lambda w: w.filing_period, reverse=True
    )[0]

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, most_recent_wages, employer
    )

    # fields that should be set
    assert eligibility_feed_record.employeeIdentifier == str(employee.employee_id)
    assert eligibility_feed_record.employeeFirstName == employee.first_name
    assert eligibility_feed_record.employeeLastName == employee.last_name
    assert eligibility_feed_record.employeeDateOfBirth == ef.DEFAULT_DATE

    assert (
        eligibility_feed_record.employeeNationalID
        == employee.tax_identifier.tax_identifier.to_unformatted_str()
    )
    assert eligibility_feed_record.employeeNationalIDType == ef.NationalIdType.ssn
    assert eligibility_feed_record.employeeEmail == employee.email_address

    # fields that *should not* be set
    assert eligibility_feed_record.employeeEffectiveFromDate is None
    assert eligibility_feed_record.employeeSalary is None
    assert eligibility_feed_record.employeeEarningFrequency is None


def test_employee_to_eligibility_feed_record_with_itin(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer
    employee.tax_identifier = TaxIdentifier(tax_identifier=TaxId("999887777"))
    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeNationalIDType == ef.NationalIdType.itin


def test_employee_to_eligibility_feed_record_with_date_of_birth(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.date_of_birth = date(2020, 7, 6)

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeDateOfBirth == employee.date_of_birth


def test_employee_to_eligibility_feed_record_with_date_of_death(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.date_of_death = date(2020, 7, 6)

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeDateOfDeath == employee.date_of_death


def test_employee_to_eligibility_feed_record_with_address(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer
    address = AddressFactory.create()

    employee.addresses = [
        EmployeeAddress(employee_id=employee.employee_id, address_id=address.address_id)
    ]

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    # at the moment, no address info should be included in export
    assert eligibility_feed_record.addressType is None
    assert eligibility_feed_record.addressAddressLine1 is None
    assert eligibility_feed_record.addressCity is None
    assert eligibility_feed_record.addressState is None
    assert eligibility_feed_record.addressZipCode is None


def test_employee_to_eligibility_feed_record_with_no_tax_identifier(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.tax_identifier = None

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeNationalID is None
    assert eligibility_feed_record.employeeNationalIDType is None


def test_employee_to_eligibility_feed_record_with_gender(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.gender_id = Gender.WOMAN.gender_id

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeGender == Gender.WOMAN.fineos_gender_description

    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.gender_id = Gender.MAN.gender_id

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeGender == Gender.MAN.fineos_gender_description

    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.gender_id = Gender.NONBINARY.gender_id

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeGender == Gender.NONBINARY.fineos_gender_description


def test_employee_to_eligibility_feed_record_with_employee_title(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.title_id = Title.DR.title_id

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeTitle == employee.title.title_description


def test_employee_to_eligibility_feed_record_with_phone_numbers(initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.phone_number = "+12025555555"
    employee.cell_phone_number = "+442083661177"

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.telephoneIntCode == "1"
    assert eligibility_feed_record.telephoneAreaCode == "202"
    assert eligibility_feed_record.telephoneNumber == "5555555"

    assert eligibility_feed_record.cellIntCode == "44"
    assert eligibility_feed_record.cellAreaCode is None
    assert eligibility_feed_record.cellNumber == "2083661177"


def test_employee_to_eligibility_feed_record_with_occupation(
    test_db_session, initialize_factories_session
):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    occupation = EmployeeOccupation(
        employee_id=employee.employee_id,
        employer_id=employer.employer_id,
        job_title="IT Support",
        date_of_hire=date(2019, 1, 1),
        date_job_ended=date(2020, 11, 30),
        employment_status="Resigned",
        org_unit_name="IT",
        hours_worked_per_week=24,
        days_worked_per_week=3,
        manager_id="E9999",
        worksite_id="A1234",
        occupation_qualifier="Certificate",
    )
    test_db_session.add(occupation)
    test_db_session.commit()

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeJobTitle == occupation.job_title
    assert eligibility_feed_record.employeeDateOfHire == occupation.date_of_hire
    assert eligibility_feed_record.employeeEndDate == occupation.date_job_ended
    assert eligibility_feed_record.employmentStatus == occupation.employment_status
    assert eligibility_feed_record.employeeOrgUnitName == occupation.org_unit_name
    assert eligibility_feed_record.employeeHoursWorkedPerWeek == occupation.hours_worked_per_week
    assert eligibility_feed_record.employeeDaysWorkedPerWeek == occupation.days_worked_per_week
    assert eligibility_feed_record.managerIdentifier == occupation.manager_id
    assert eligibility_feed_record.occupationQualifier == occupation.occupation_qualifier
    assert eligibility_feed_record.employeeWorkSiteId == occupation.worksite_id


def create_csv_dict(updates=None):
    csv_dict = {
        # required fields
        "employeeIdentifier": "",
        "employeeFirstName": "",
        "employeeLastName": "",
        # required fields: with defaults though
        "employeeDateOfBirth": ef.DEFAULT_DATE.strftime("%m/%d/%Y"),  # employee.date_of_birth,
        "employeeJobTitle": "DEFAULT",
        "employeeDateOfHire": ef.DEFAULT_HIRE_DATE.strftime("%m/%d/%Y"),
        "employmentStatus": "Active",
        "employeeHoursWorkedPerWeek": "0.00",
        # optional fields
        "employeeTitle": "",
        "employeeSecondName": "",
        "employeeThirdName": "",
        "employeeDateOfDeath": "",
        "employeeGender": "",
        "employeeMaritalStatus": "",
        "employeeNationalID": "",
        "employeeNationalIDType": "",
        "spouseIdentifier": "",
        "spouseReasonForChange": "",
        "spouseDateOfChange": "",
        "spouseTitle": "",
        "spouseFirstName": "",
        "spouseSecondName": "",
        "spouseThirdName": "",
        "spouseLastName": "",
        "spouseDateOfBirth": "",
        "spouseDateOfDeath": "",
        "spouseGender": "",
        "spouseNationalID": "",
        "spouseNationalIDType": "",
        "addressType": "",
        "addressState": "",
        "addressCity": "",
        "addressAddressLine1": "",
        "addressZipCode": "",
        "addressEffectiveDate": "",
        "addressCountry": "",
        "addressAddressLine2": "",
        "addressCounty": "",
        "telephoneIntCode": "",
        "telephoneAreaCode": "",
        "telephoneNumber": "",
        "cellIntCode": "",
        "cellAreaCode": "",
        "cellNumber": "",
        "employeeEmail": "",
        "employeeId": "",
        "employeeClassification": "",
        "employeeAdjustedDateOfHire": "",
        "employeeEndDate": "",
        "employmentStrength": "",
        "employmentCategory": "",
        "employmentType": "",
        "employeeOrgUnitName": "",
        "employeeCBACode": "",
        "keyEmployee": "",
        "employeeWorkAtHome": "",
        "employeeDaysWorkedPerWeek": "",
        "employeeHoursWorkedPerYear": "",
        "employee50EmployeesWithin75Miles": "",
        "employmentWorkState": "",
        "managerIdentifier": "",
        "occupationQualifier": "",
        "employeeWorkSiteId": "",
        "employeeEffectiveFromDate": "",
        "employeeEffectiveToDate": "",
        "employeeSalary": "",
        "employeeEarningFrequency": "",
    }

    if updates:
        csv_dict.update(updates)

    return csv_dict


def test_default_state():
    wages_and_contributions = WagesAndContributionsFactory.build()
    employee = wages_and_contributions.employee
    efr = ef.EligibilityFeedRecord(
        employeeIdentifier=employee.employee_id,
        employeeFirstName=employee.first_name,
        employeeLastName=employee.last_name,
    )
    assert efr.employmentWorkState == "MA"


def test_write_employees_to_csv(tmp_path, test_db_session, initialize_factories_session):
    employer = EmployerFactory.create()
    wages_for_single_employer_different_employees = WagesAndContributionsFactory.create_batch(
        size=2, employer=employer
    )
    address = AddressFactory.create()

    fineos_employer_id = employer.employer_id

    employees_with_most_recent_wages = list(
        map(lambda w: (w.employee, w), wages_for_single_employer_different_employees)
    )

    # remove phone number from record
    employees_with_most_recent_wages[1][0].phone_number = None

    # add an address
    employees_with_most_recent_wages[1][0].addresses = [
        EmployeeAddress(
            employee_id=employees_with_most_recent_wages[1][0].employee_id,
            address_id=address.address_id,
        )
    ]

    test_db_session.commit()

    number_of_employees = len(employees_with_most_recent_wages)

    dest_file = tmp_path / "test.csv"

    with open(dest_file, "w") as f:
        ef.write_employees_to_csv(
            employer, fineos_employer_id, number_of_employees, employees_with_most_recent_wages, f
        )

    with open(dest_file, "r") as f:
        file_content = f.readlines()

    assert file_content[0].strip() == f"EMPLOYER_ID:{fineos_employer_id}"
    assert file_content[1].strip() == f"NUMBER_OF_RECORDS:{number_of_employees}"
    assert file_content[2].strip() == "@DATABLOCK"

    employees = list(map(lambda ew: ew[0], employees_with_most_recent_wages))

    phone_number = ef.parse_phone_number(employees[0].phone_number)

    expected_rows = [
        create_csv_dict(
            {
                # required fields
                "employeeIdentifier": str(employees[0].employee_id),
                "employeeFirstName": employees[0].first_name,
                "employeeLastName": employees[0].last_name,
                # required fields: with defaults though
                "employeeDateOfBirth": ef.DEFAULT_DATE.strftime(
                    "%m/%d/%Y"
                ),  # employee.date_of_birth,
                # optional fields
                "employeeTitle": "",
                "employeeSecondName": employees[0].middle_name,
                "employeeNationalID": (
                    employees[0].tax_identifier.tax_identifier.to_unformatted_str()
                ),
                "employeeNationalIDType": ef.NationalIdType.ssn.value,
                "telephoneIntCode": phone_number.country_code,
                "telephoneAreaCode": phone_number.area_code,
                "telephoneNumber": phone_number.number,
                "employeeEmail": employees[0].email_address,
                "employmentWorkState": ef.DEFAULT_EMPLOYMENT_WORK_STATE,
            }
        ),
        create_csv_dict(
            {
                # required fields
                "employeeIdentifier": str(employees[1].employee_id),
                "employeeFirstName": employees[1].first_name,
                "employeeLastName": employees[1].last_name,
                # required fields: with defaults though
                "employeeDateOfBirth": ef.DEFAULT_DATE.strftime(
                    "%m/%d/%Y"
                ),  # employee.date_of_birth,
                # optional fields
                "employeeTitle": "",
                "employeeSecondName": employees[1].middle_name,
                "employeeNationalID": (
                    test_db_session.query(TaxIdentifier)
                    .filter(TaxIdentifier.tax_identifier_id == employees[1].tax_identifier_id)
                    .first()
                    .tax_identifier
                ).to_unformatted_str(),
                "employeeNationalIDType": ef.NationalIdType.ssn.value,
                "employeeEmail": employees[1].email_address,
                "addressType": "",
                "addressAddressLine1": "",
                "addressCity": "",
                "addressState": "",
                "addressZipCode": "",
                "employmentWorkState": ef.DEFAULT_EMPLOYMENT_WORK_STATE,
            }
        ),
    ]

    with open(dest_file, "r") as f:
        # skip header block in file
        next(f)
        next(f)
        next(f)
        # then start reading CSV
        reader = csv.DictReader(f)
        for (actual, expected) in zip(reader, expected_rows):
            for (actual, expected) in zip(actual.items(), expected.items()):
                assert actual == expected


def assert_number_of_data_lines_in_file(f, num_data_lines):
    number_of_lines = sum(1 for line in f)

    # datablock lines + csv header line + data rows
    expected_number_of_lines = 3 + 1 + num_data_lines

    assert number_of_lines == expected_number_of_lines


def assert_number_of_data_lines_in_each_file(directory, num_data_lines):
    with os.scandir(directory) as dir_iterator:
        for dir_entry in dir_iterator:
            with open(dir_entry.path) as f:
                assert_number_of_data_lines_in_file(f, num_data_lines)


def employer_file_exists(directory, fineos_employer_id):
    p = list(Path(directory).glob(f"*_{fineos_employer_id}.csv"))

    if not p:
        return False
    return True


def assert_employer_file_exists(directory, fineos_employer_id):
    assert employer_file_exists(directory, fineos_employer_id)


def assert_employer_file_does_not_exists(directory, fineos_employer_id):
    assert not employer_file_exists(directory, fineos_employer_id)


def make_test_db():
    import massgov.pfml.db as db

    return db.init(sync_lookups=False, check_migrations_current=False)


def make_fineos_client():
    return massgov.pfml.fineos.MockFINEOSClient()


def make_s3_session(_config):
    return None


def call_process_all_employers(monkeypatch, output_path):
    monkeypatch.setenv("OUTPUT_DIRECTORY_PATH", str(output_path))
    monkeypatch.setenv("FINEOS_AWS_IAM_ROLE_ARN", "foo")
    monkeypatch.setenv("FINEOS_AWS_IAM_ROLE_EXTERNAL_ID", "bar")

    return ef.process_all_employers(
        make_test_db, make_fineos_client, make_s3_session, ef.EligibilityFeedExportConfig()
    )


def test_process_all_employers_simple(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    WagesAndContributionsFactory.create()

    batch_output_dir = tmp_path / "absence-eligibility" / "upload"
    batch_output_dir.mkdir(parents=True)

    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(batch_output_dir, 1)


def test_process_all_employers_no_records(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 0
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 0


def test_process_all_employers_with_skip(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    WagesAndContributionsFactory.create()

    def mock(fineos, employer):
        return None

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 1
    assert process_results.employee_and_employer_pairs_total_count == 0


def test_process_all_employers_with_error(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    WagesAndContributionsFactory.create()

    def mock(fineos, employer):
        raise Exception

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 1
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 0


def test_process_all_employers_for_single_employee_different_employers(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    # wages_for_single_employee_different_employers
    WagesAndContributionsFactory.create_batch(size=5, employee=EmployeeFactory.create())

    batch_output_dir = tmp_path / "absence-eligibility" / "upload"
    batch_output_dir.mkdir(parents=True)

    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 5
    assert process_results.employers_success_count == 5
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(batch_output_dir, 1)


def test_process_all_employers_for_single_employer_different_employees(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    # wages_for_single_employer_different_employees
    WagesAndContributionsFactory.create_batch(size=5, employer=EmployerFactory.create())

    batch_output_dir = tmp_path / "absence-eligibility" / "upload"
    batch_output_dir.mkdir(parents=True)

    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(batch_output_dir, 5)


def test_process_all_employers_for_multiple_wages_for_single_employee_employer_pair(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    # multiple_wages_for_single_employee_employer_pair
    WagesAndContributionsFactory.create_batch(
        size=5, employee=EmployeeFactory.create(), employer=EmployerFactory.create()
    )

    batch_output_dir = tmp_path / "absence-eligibility" / "upload"
    batch_output_dir.mkdir(parents=True)

    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(batch_output_dir, 1)


def test_process_all_employers_skips_nonexistent_employer(
    local_test_db_session, local_initialize_factories_session, tmp_path, monkeypatch
):
    # Set fineos_employer_id to None for 'missing' employer to skip employer.
    missing_employer_fein = Fein("999999999")
    WagesAndContributionsFactory.create_batch(
        size=1,
        employer=EmployerFactory.create(
            employer_fein=missing_employer_fein, fineos_employer_id=None
        ),
    )
    # wages_for_single_employer_different_employees
    employer = EmployerFactory.create()
    WagesAndContributionsFactory.create_batch(size=5, employer=employer)

    batch_output_dir = tmp_path / "absence-eligibility" / "upload"
    batch_output_dir.mkdir(parents=True)

    process_results = call_process_all_employers(monkeypatch, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 2
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 1
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_employer_file_exists(batch_output_dir, employer.fineos_employer_id)
    assert_number_of_data_lines_in_each_file(batch_output_dir, 5)


def test_get_most_recent_employer_to_employee_info_for_single_employee_different_employers(
    local_test_db_session, local_initialize_factories_session, tmp_path,
):
    employee = EmployeeFactory.create()

    wages_for_single_employee_different_employers = WagesAndContributionsFactory.create_batch(
        size=5, employee=employee
    )

    employee_log_one = EmployeeLogFactory.create(
        employee_id=employee.employee_id,
        employer_id=wages_for_single_employee_different_employers[0].employer_id,
    )

    employee_log_two = EmployeeLogFactory.create(
        employee_id=employee.employee_id,
        employer_id=wages_for_single_employee_different_employers[1].employer_id,
    )

    sorted_wages = sorted(
        wages_for_single_employee_different_employers, key=lambda w: w.filing_period, reverse=True
    )

    most_recent_wages = sorted_wages[0]
    most_recent_employer = most_recent_wages.employer.employer_id

    employer_id_to_employee_ids = ef.get_most_recent_employer_and_employee_log_employers_to_employee_info(
        local_test_db_session, [employee.employee_id]
    )

    employer_id_set = {
        most_recent_employer,
        employee_log_one.employer_id,
        employee_log_two.employer_id,
    }

    assert len(employer_id_to_employee_ids) == len(employer_id_set)


def test_process_list_of_employers_simple(test_db_session, initialize_factories_session, tmp_path):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employers_to_process = [wages_and_contributions.employer.employer_id]

    process_results = ef.process_a_list_of_employers(
        employers_to_process, test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_list_of_employers_filter_correct_employers(
    test_db_session, initialize_factories_session, tmp_path
):
    wages_and_contributions_one = WagesAndContributionsFactory.create()
    employers_to_process = [wages_and_contributions_one.employer.employer_id]

    wages_and_contributions_two = WagesAndContributionsFactory.create()
    employers_to_process.append(wages_and_contributions_two.employer.employer_id)

    WagesAndContributionsFactory.create()
    WagesAndContributionsFactory.create()

    process_results = ef.process_a_list_of_employers(
        employers_to_process, test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 2
    assert process_results.employers_success_count == 2
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 2

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_simple(
    test_db_session, initialize_factories_session, tmp_path, create_triggers
):
    WagesAndContributionsFactory.create()

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_for_single_employee_different_employers(
    test_db_session, initialize_factories_session, tmp_path, create_triggers
):
    # wages_for_single_employee_different_employers
    WagesAndContributionsFactory.create_batch(size=5, employee=EmployeeFactory.create())

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.employers_total_count == 1
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_for_single_employer_different_employees(
    test_db_session, initialize_factories_session, tmp_path, create_triggers
):
    # wages_for_single_employer_different_employees
    WagesAndContributionsFactory.create_batch(size=5, employer=EmployerFactory.create())

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(tmp_path, 5)


def test_process_employee_updates_for_multiple_wages_for_single_employee_employer_pair(
    test_db_session, initialize_factories_session, tmp_path, create_triggers
):
    # multiple_wages_for_single_employee_employer_pair
    WagesAndContributionsFactory.create_batch(
        size=5, employee=EmployeeFactory.create(), employer=EmployerFactory.create()
    )

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_skips_nonexistent_employer(
    test_db_session, initialize_factories_session, tmp_path, create_triggers
):
    # Set fineos_employer_id to None for 'missing' employer to skip employer.
    missing_employer_fein = Fein("999999999")
    WagesAndContributionsFactory.create_batch(
        size=1,
        employer=EmployerFactory.create(
            employer_fein=missing_employer_fein, fineos_employer_id=None
        ),
    )
    # wages_for_single_employer_different_employees
    employer = EmployerFactory.create()
    WagesAndContributionsFactory.create_batch(size=5, employer=employer)

    fineos_client = massgov.pfml.fineos.MockFINEOSClient()
    process_results = ef.process_employee_updates(test_db_session, fineos_client, tmp_path)

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 2
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 1
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_employer_file_exists(tmp_path, employer.fineos_employer_id)
    assert_number_of_data_lines_in_each_file(tmp_path, 5)


def test_process_employee_updates_with_error(
    test_db_session, initialize_factories_session, tmp_path, create_triggers, monkeypatch
):
    WagesAndContributionsFactory.create()

    def mock(fineos, employer):
        raise Exception

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 1
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 0


def test_process_employee_updates_with_error_continues_processing_other_employers(
    test_db_session, initialize_factories_session, tmp_path, create_triggers, monkeypatch
):
    wages = WagesAndContributionsFactory.create_batch(size=2)

    def mock(fineos, employer):
        # error for the first employer
        if employer.employer_id == wages[0].employer_id:
            raise Exception

        # success for second one
        return "1234"

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    employee_log_entries_before = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_entries_before) == 2

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    employee_log_entries_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_entries_after) == 1

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 2
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 1
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1
    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_with_recovery(
    test_db_session, initialize_factories_session, tmp_path, create_triggers, monkeypatch
):
    WagesAndContributionsFactory.create_batch(size=2, employer=EmployerFactory.create())

    employees = test_db_session.query(Employee).all()

    # Simulate one recovery record
    ef.update_batch_to_processing(test_db_session, [employees[0].employee_id], 1)

    employee_log_entries_before = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_entries_before) == 2

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    employee_log_entries_after = test_db_session.query(EmployeeLog).all()
    assert len(employee_log_entries_after) == 0

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 2
    assert_number_of_data_lines_in_each_file(tmp_path, 2)


def test_process_employee_updates_export_file_number_limit(
    test_db_session, initialize_factories_session, tmp_path, create_triggers, mocker
):
    WagesAndContributionsFactory.create_batch(size=15)

    process_employee_batch_spy = mocker.spy(ef, "process_employee_batch")

    process_results = ef.process_employee_updates(
        test_db_session,
        massgov.pfml.fineos.MockFINEOSClient(),
        tmp_path,
        batch_size=10,
        export_file_number_limit=5,
    )

    process_employee_batch_spy.assert_called_once()

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 5
    assert process_results.employers_success_count == 5
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_export_file_number_limit_mismatched_batch_size(
    test_db_session, initialize_factories_session, tmp_path, create_triggers, mocker
):
    WagesAndContributionsFactory.create_batch(size=10)

    process_employee_batch_spy = mocker.spy(ef, "process_employee_batch")

    process_results = ef.process_employee_updates(
        test_db_session,
        massgov.pfml.fineos.MockFINEOSClient(),
        tmp_path,
        batch_size=2,
        export_file_number_limit=5,
    )

    assert process_employee_batch_spy.call_count == 3

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 5
    assert process_results.employers_success_count == 5
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_export_file_number_limit_fewer_than_limit_exist(
    test_db_session, initialize_factories_session, tmp_path, create_triggers
):
    WagesAndContributionsFactory.create_batch(size=2)

    process_results = ef.process_employee_updates(
        test_db_session,
        massgov.pfml.fineos.MockFINEOSClient(),
        tmp_path,
        batch_size=10,
        export_file_number_limit=5,
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 2
    assert process_results.employers_success_count == 2
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 2

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_export_file_number_limit_with_error_continues_processing_other_employers(
    test_db_session, initialize_factories_session, tmp_path, create_triggers, monkeypatch
):
    wages = WagesAndContributionsFactory.create_batch(size=5)

    def mock(fineos, employer):
        # error for the first employer
        if employer.employer_id == wages[0].employer_id:
            raise Exception

        # success for second one
        return "1234"

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    process_results = ef.process_employee_updates(
        test_db_session,
        massgov.pfml.fineos.MockFINEOSClient(),
        tmp_path,
        batch_size=10,
        export_file_number_limit=5,
    )

    assert process_results.start
    assert process_results.end
    assert process_results.employers_total_count == 5
    assert process_results.employers_success_count == 4
    assert process_results.employers_error_count == 1
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 4
    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_open_and_write_to_eligibility_file_delete_on_exception(
    tmp_path, mock_s3_bucket, monkeypatch
):
    def mock(employer, fineos_employer_id, number_of_employees, employees, output_file):
        raise SpecialTestException

    monkeypatch.setattr(ef, "write_employees_to_csv", mock)

    fineos_employer_id = 1

    with pytest.raises(SpecialTestException):
        ef.open_and_write_to_eligibility_file(
            tmp_path, fineos_employer_id, Employer(employer_id="foo"), 0, []
        )

    assert_employer_file_does_not_exists(tmp_path, fineos_employer_id)

    with pytest.raises(SpecialTestException):
        ef.open_and_write_to_eligibility_file(
            f"s3://{mock_s3_bucket}", fineos_employer_id, Employer(employer_id="foo"), 0, []
        )

    s3 = boto3.resource("s3")
    s3_bucket = s3.Bucket(mock_s3_bucket)
    assert list(s3_bucket.objects.all()) == []


def test_open_and_write_to_eligibility_file_delete_on_exception_on_create(
    tmp_path, mock_s3_bucket, monkeypatch
):
    def mock(output_file, mode, transport_params):
        raise SpecialTestException

    monkeypatch.setattr(ef.smart_open, "open", mock)

    fineos_employer_id = 1

    with pytest.raises(SpecialTestException):
        ef.open_and_write_to_eligibility_file(
            tmp_path, fineos_employer_id, Employer(employer_id="foo"), 0, []
        )

    assert_employer_file_does_not_exists(tmp_path, fineos_employer_id)

    with pytest.raises(SpecialTestException):
        ef.open_and_write_to_eligibility_file(
            f"s3://{mock_s3_bucket}", fineos_employer_id, Employer(employer_id="foo"), 0, []
        )

    s3 = boto3.resource("s3")
    s3_bucket = s3.Bucket(mock_s3_bucket)
    assert list(s3_bucket.objects.all()) == []


def test_determine_bundle_path():
    total = 500
    assert ef.determine_bundle_path("foo", 0, total) == "foo/absence-eligibility/upload"
    assert ef.determine_bundle_path("foo", 1, total) == "foo/absence-eligibility/upload"
    with pytest.raises(ValueError):
        assert ef.determine_bundle_path("foo", 501, total) == "foo/absence-eligibility/upload"

    total = 12000
    assert ef.determine_bundle_path("foo", 0, total) == "foo/absence-eligibility/upload"
    assert ef.determine_bundle_path("foo", 1, total) == "foo/absence-eligibility/upload"
    assert ef.determine_bundle_path("foo", 1000, total) == "foo/absence-eligibility2/upload"
    assert ef.determine_bundle_path("foo", 2000, total) == "foo/absence-eligibility3/upload"
    assert ef.determine_bundle_path("foo", 3000, total) == "foo/absence-eligibility4/upload"
    assert ef.determine_bundle_path("foo", 4000, total) == "foo/absence-eligibility5/upload"
    assert ef.determine_bundle_path("foo", 5000, total) == "foo/absence-eligibility6/upload"
    assert ef.determine_bundle_path("foo", 6000, total) == "foo/absence-eligibility7/upload"
    assert ef.determine_bundle_path("foo", 7000, total) == "foo/absence-eligibility8/upload"
    assert ef.determine_bundle_path("foo", 8000, total) == "foo/absence-eligibility9/upload"
    assert ef.determine_bundle_path("foo", 9000, total) == "foo/absence-eligibility10/upload"
    assert ef.determine_bundle_path("foo", 10000, total) == "foo/absence-eligibility11/upload"
    assert ef.determine_bundle_path("foo", 11000, total) == "foo/absence-eligibility12/upload"
    assert ef.determine_bundle_path("foo", 11999, total) == "foo/absence-eligibility12/upload"

    total = 250000
    assert ef.determine_bundle_path("foo", 0, total) == "foo/absence-eligibility/upload"
    assert ef.determine_bundle_path("foo", 1, total) == "foo/absence-eligibility/upload"
    assert ef.determine_bundle_path("foo", 999, total) == "foo/absence-eligibility/upload"
    assert ef.determine_bundle_path("foo", 1000, total) == "foo/absence-eligibility2/upload"
    assert ef.determine_bundle_path("foo", 1001, total) == "foo/absence-eligibility2/upload"
    assert ef.determine_bundle_path("foo", 23636, total) == "foo/absence-eligibility2/upload"
    assert ef.determine_bundle_path("foo", 23637, total) == "foo/absence-eligibility3/upload"
    assert ef.determine_bundle_path("foo", 46273, total) == "foo/absence-eligibility3/upload"
    assert ef.determine_bundle_path("foo", 46274, total) == "foo/absence-eligibility4/upload"
    assert ef.determine_bundle_path("foo", 68911, total) == "foo/absence-eligibility5/upload"
    assert ef.determine_bundle_path("foo", 91548, total) == "foo/absence-eligibility6/upload"
    assert ef.determine_bundle_path("foo", 114185, total) == "foo/absence-eligibility7/upload"
    assert ef.determine_bundle_path("foo", 136822, total) == "foo/absence-eligibility8/upload"
    assert ef.determine_bundle_path("foo", 159459, total) == "foo/absence-eligibility9/upload"
    assert ef.determine_bundle_path("foo", 182096, total) == "foo/absence-eligibility10/upload"
    assert ef.determine_bundle_path("foo", 204733, total) == "foo/absence-eligibility11/upload"
    assert ef.determine_bundle_path("foo", 227370, total) == "foo/absence-eligibility12/upload"
    assert ef.determine_bundle_path("foo", 249999, total) == "foo/absence-eligibility12/upload"

    # test different number of bundles from default of 12

    total = 5000
    bundle_count = 1
    assert (
        ef.determine_bundle_path("foo", 1, total, bundle_count) == "foo/absence-eligibility/upload"
    )
    assert (
        ef.determine_bundle_path("foo", 2000, total, bundle_count)
        == "foo/absence-eligibility/upload"
    )
    assert (
        ef.determine_bundle_path("foo", 4000, total, bundle_count)
        == "foo/absence-eligibility/upload"
    )

    total = 5000
    bundle_count = 5
    assert (
        ef.determine_bundle_path("foo", 1, total, bundle_count) == "foo/absence-eligibility/upload"
    )
    assert (
        ef.determine_bundle_path("foo", 1000, total, bundle_count)
        == "foo/absence-eligibility2/upload"
    )
    assert (
        ef.determine_bundle_path("foo", 2000, total, bundle_count)
        == "foo/absence-eligibility3/upload"
    )
    assert (
        ef.determine_bundle_path("foo", 3000, total, bundle_count)
        == "foo/absence-eligibility4/upload"
    )
    assert (
        ef.determine_bundle_path("foo", 4000, total, bundle_count)
        == "foo/absence-eligibility5/upload"
    )
