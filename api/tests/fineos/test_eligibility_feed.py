import csv
import os
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import boto3
import pytest

import massgov.pfml.fineos
import massgov.pfml.fineos.eligibility_feed as ef
from massgov.pfml.db.models.employees import EmployeeAddress, Employer, GeoState, TaxIdentifier
from massgov.pfml.db.models.factories import (
    AddressFactory,
    EmployeeFactory,
    EmployerFactory,
    WagesAndContributionsFactory,
)
from massgov.pfml.util.pydantic.types import TaxIdUnformattedStr


class SpecialTestException(Exception):
    """Exception only defined here for ensure mocked exception is bubbled up"""

    pass


@pytest.fixture
def geo_state_lookup(test_db_session):
    GeoState.sync_to_database(test_db_session)
    return GeoState.get_instance(test_db_session, template=GeoState.MA)


@pytest.fixture
def address_model(initialize_factories_session, geo_state_lookup):
    return AddressFactory.create(geo_state=geo_state_lookup)


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

    # TODO: assert other fields?
    assert eligibility_feed_record.employeeIdentifier == employee.employee_id
    assert eligibility_feed_record.employeeFirstName == employee.first_name
    assert eligibility_feed_record.employeeLastName == employee.last_name
    assert eligibility_feed_record.employeeEffectiveFromDate == most_recent_wages.filing_period
    assert eligibility_feed_record.employeeSalary == most_recent_wages.employee_ytd_wages
    assert eligibility_feed_record.employeeEarningFrequency == ef.EarningFrequency.yearly
    assert eligibility_feed_record.employeeDateOfBirth == ef.DEFAULT_DATE

    assert eligibility_feed_record.employeeNationalID == employee.tax_identifier.tax_identifier
    assert eligibility_feed_record.employeeNationalIDType == ef.NationalIdType.ssn
    assert eligibility_feed_record.employeeEmail == employee.email_address

    if employee.phone_number:
        assert eligibility_feed_record.telephoneIntCode == "1"
        assert eligibility_feed_record.telephoneAreaCode == employee.phone_number[:3]
        assert eligibility_feed_record.telephoneNumber == employee.phone_number[4:].replace("-", "")


def test_employee_to_eligibility_feed_record_with_itin(
    test_db_session, initialize_factories_session
):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer
    employee.tax_identifier = TaxIdentifier(
        tax_identifier=TaxIdUnformattedStr.validate_type("999887777")
    )
    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeNationalIDType == ef.NationalIdType.itin


def test_employee_to_eligibility_feed_record_with_date_of_birth(
    test_db_session, initialize_factories_session
):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.date_of_birth = date(2020, 7, 6)

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeDateOfBirth == employee.date_of_birth


def test_employee_to_eligibility_feed_record_with_address(
    initialize_factories_session, test_db_session, address_model
):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.addresses = [
        EmployeeAddress(employee_id=employee.employee_id, address_id=address_model.address_id)
    ]

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.addressType == ef.AddressType.home
    assert eligibility_feed_record.addressAddressLine1 == address_model.address_line_one
    assert eligibility_feed_record.addressCity == address_model.city
    assert eligibility_feed_record.addressState == address_model.geo_state.geo_state_description
    assert eligibility_feed_record.addressZipCode == address_model.zip_code


def test_employee_to_eligibility_feed_record_with_no_tax_identifier(
    test_db_session, initialize_factories_session
):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    employer = wages_and_contributions.employer

    employee.tax_identifier = None

    eligibility_feed_record = ef.employee_to_eligibility_feed_record(
        employee, wages_and_contributions, employer
    )

    assert eligibility_feed_record.employeeNationalID is None
    assert eligibility_feed_record.employeeNationalIDType is None


def create_csv_dict(updates=None):
    csv_dict = {
        # required fields
        "employeeIdentifier": "",
        "employeeFirstName": "",
        "employeeLastName": "",
        "employeeEffectiveFromDate": "",
        "employeeSalary": "",
        "employeeEarningFrequency": ef.EarningFrequency.yearly.value,
        # required fields: with defaults though
        "employeeDateOfBirth": ef.DEFAULT_DATE.strftime("%m/%d/%Y"),  # employee.date_of_birth,
        "employeeJobTitle": "DEFAULT",
        "employeeDateOfHire": ef.DEFAULT_HIRE_DATE.strftime("%m/%d/%Y"),
        "employmentStatus": "Active",
        "employeeHoursWorkedPerWeek": "0",
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
        "employeeEffectiveToDate": "",
    }

    if updates:
        csv_dict.update(updates)

    return csv_dict


def test_default_state(test_db_session, initialize_factories_session):
    wages_and_contributions = WagesAndContributionsFactory.create()
    employee = wages_and_contributions.employee
    efr = ef.EligibilityFeedRecord(
        employeeIdentifier=employee.employee_id,
        employeeFirstName=employee.first_name,
        employeeLastName=employee.last_name,
        employeeEffectiveFromDate=(
            employee.wages_and_contributions[0].filing_period.strftime("%m/%d/%Y")
        ),
        employeeSalary=round(employee.wages_and_contributions[0].employee_ytd_wages, 6),
        employeeEarningFrequency=ef.EarningFrequency.yearly.value,
    )
    assert efr.employmentWorkState == "MA"


def test_write_employees_to_csv(
    tmp_path, initialize_factories_session, test_db_session, address_model
):
    employer = EmployerFactory.create()
    wages_for_single_employer_different_employees = WagesAndContributionsFactory.create_batch(
        size=2, employer=employer
    )

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
            address_id=address_model.address_id,
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

    expected_rows = [
        create_csv_dict(
            {
                # required fields
                "employeeIdentifier": str(employees[0].employee_id),
                "employeeFirstName": employees[0].first_name,
                "employeeLastName": employees[0].last_name,
                "employeeEffectiveFromDate": (
                    employees[0].wages_and_contributions[0].filing_period.strftime("%m/%d/%Y")
                ),
                "employeeSalary": str(
                    round(employees[0].wages_and_contributions[0].employee_ytd_wages, 6)
                ),
                "employeeEarningFrequency": ef.EarningFrequency.yearly.value,
                # required fields: with defaults though
                "employeeDateOfBirth": ef.DEFAULT_DATE.strftime(
                    "%m/%d/%Y"
                ),  # employee.date_of_birth,
                # optional fields
                "employeeTitle": "",
                "employeeSecondName": employees[0].middle_name,
                "employeeNationalID": employees[0].tax_identifier.tax_identifier,
                "employeeNationalIDType": ef.NationalIdType.ssn.value,
                "telephoneIntCode": "1",
                "telephoneAreaCode": employees[0].phone_number[:3],
                "telephoneNumber": employees[0].phone_number[4:].replace("-", ""),
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
                "employeeEffectiveFromDate": (
                    employees[1].wages_and_contributions[0].filing_period.strftime("%m/%d/%Y")
                ),
                "employeeSalary": str(
                    round(employees[1].wages_and_contributions[0].employee_ytd_wages, 6)
                ),
                "employeeEarningFrequency": ef.EarningFrequency.yearly.value,
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
                ),
                "employeeNationalIDType": ef.NationalIdType.ssn.value,
                "employeeEmail": employees[1].email_address,
                "addressType": "Home",
                "addressAddressLine1": employees[1].addresses[0].address.address_line_one,
                "addressCity": employees[1].addresses[0].address.city,
                "addressState": employees[1].addresses[0].address.geo_state.geo_state_description,
                "addressZipCode": employees[1].addresses[0].address.zip_code,
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


def test_process_all_employers_simple(test_db_session, tmp_path, initialize_factories_session):
    WagesAndContributionsFactory.create()

    process_results = ef.process_all_employers(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_all_employers_no_records(test_db_session, tmp_path, initialize_factories_session):
    process_results = ef.process_all_employers(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 0
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 0


def test_process_all_employers_with_skip(
    test_db_session, tmp_path, initialize_factories_session, monkeypatch
):
    WagesAndContributionsFactory.create()

    def mock(fineos, employer):
        return None

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    process_results = ef.process_all_employers(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 1
    assert process_results.employee_and_employer_pairs_total_count == 0


def test_process_all_employers_with_error(
    test_db_session, tmp_path, initialize_factories_session, monkeypatch
):
    WagesAndContributionsFactory.create()

    def mock(fineos, employer):
        raise Exception

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    process_results = ef.process_all_employers(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 1
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 0


def test_process_all_employers_for_single_employee_different_employers(
    test_db_session, tmp_path, initialize_factories_session
):
    # wages_for_single_employee_different_employers
    WagesAndContributionsFactory.create_batch(size=5, employee=EmployeeFactory.create())

    process_results = ef.process_all_employers(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 5
    assert process_results.employers_success_count == 5
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_all_employers_for_single_employer_different_employees(
    test_db_session, tmp_path, initialize_factories_session
):
    # wages_for_single_employer_different_employees
    WagesAndContributionsFactory.create_batch(size=5, employer=EmployerFactory.create())

    process_results = ef.process_all_employers(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(tmp_path, 5)


def test_process_all_employers_for_multiple_wages_for_single_employee_employer_pair(
    test_db_session, tmp_path, initialize_factories_session
):
    # multiple_wages_for_single_employee_employer_pair
    WagesAndContributionsFactory.create_batch(
        size=5, employee=EmployeeFactory.create(), employer=EmployerFactory.create()
    )

    process_results = ef.process_all_employers(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_all_employers_skips_nonexistent_employer(
    test_db_session, tmp_path, initialize_factories_session
):
    # Set fineos_employer_id to None for 'missing' employer to skip employer.
    missing_employer_fein = "999999999"
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
    process_results = ef.process_all_employers(test_db_session, fineos_client, tmp_path)

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 2
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 1
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_employer_file_exists(tmp_path, employer.fineos_employer_id)
    assert_number_of_data_lines_in_each_file(tmp_path, 5)


def test_get_latest_employer_for_updates():
    @dataclass
    class QueryRecord:
        employer_id: uuid
        employee_id: uuid
        maxdate: date

    employee_with_two_employers = [
        QueryRecord(
            employer_id=uuid.UUID("64665f09-9e00-48d4-94da-a4f58f759012"),
            employee_id=uuid.UUID("0009d8b3-cf7c-4ed2-85ff-acfefb017525"),
            maxdate=date(2020, 9, 30),
        ),
        QueryRecord(
            employer_id=uuid.UUID("64665f09-9e00-48d4-94da-a4f58f759012"),
            employee_id=uuid.UUID("0009d8b3-cf7c-4ed2-85ff-acfefb017525"),
            maxdate=date(2020, 6, 30),
        ),
        QueryRecord(
            employer_id=uuid.UUID("64665f09-9e00-48d4-94da-a4f58f759012"),
            employee_id=uuid.UUID("0009d8b3-cf7c-4ed2-85ff-acfefb017525"),
            maxdate=date(2020, 3, 31),
        ),
        QueryRecord(
            employer_id=uuid.UUID("0c0232c8-6741-42f9-9afa-bb7c42a3ca13"),
            employee_id=uuid.UUID("0009d8b3-cf7c-4ed2-85ff-acfefb017525"),
            maxdate=date(2019, 12, 31),
        ),
        QueryRecord(
            employer_id=uuid.UUID("0c0232c8-6741-42f9-9afa-bb7c42a3ca13"),
            employee_id=uuid.UUID("0009d8b3-cf7c-4ed2-85ff-acfefb017525"),
            maxdate=date(2019, 9, 30),
        ),
    ]

    latest_employer_for_employee = ef.get_latest_employer_for_updates(employee_with_two_employers)

    assert len(latest_employer_for_employee) == 1
    assert latest_employer_for_employee[0].maxdate == date(2020, 9, 30)


def test_process_employee_updates_simple(
    test_db_session, tmp_path, initialize_factories_session, create_triggers
):
    WagesAndContributionsFactory.create()

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_for_single_employer_different_employees(
    test_db_session, tmp_path, initialize_factories_session, create_triggers
):
    # wages_for_single_employer_different_employees
    WagesAndContributionsFactory.create_batch(size=5, employer=EmployerFactory.create())

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_number_of_data_lines_in_each_file(tmp_path, 5)


def test_process_employee_updates_for_multiple_wages_for_single_employee_employer_pair(
    test_db_session, tmp_path, initialize_factories_session, create_triggers
):
    # multiple_wages_for_single_employee_employer_pair
    WagesAndContributionsFactory.create_batch(
        size=5, employee=EmployeeFactory.create(), employer=EmployerFactory.create()
    )

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 1

    assert_number_of_data_lines_in_each_file(tmp_path, 1)


def test_process_employee_updates_skips_nonexistent_employer(
    test_db_session, tmp_path, initialize_factories_session, create_triggers
):
    # Set fineos_employer_id to None for 'missing' employer to skip employer.
    missing_employer_fein = "999999999"
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

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 2
    assert process_results.employers_success_count == 1
    assert process_results.employers_error_count == 0
    assert process_results.employers_skipped_count == 1
    assert process_results.employee_and_employer_pairs_total_count == 5

    assert_employer_file_exists(tmp_path, employer.fineos_employer_id)
    assert_number_of_data_lines_in_each_file(tmp_path, 5)


def test_process_employee_updates_with_error(
    test_db_session, tmp_path, initialize_factories_session, create_triggers, monkeypatch
):
    WagesAndContributionsFactory.create()

    def mock(fineos, employer):
        raise Exception

    monkeypatch.setattr(ef, "get_fineos_employer_id", mock)

    process_results = ef.process_employee_updates(
        test_db_session, massgov.pfml.fineos.MockFINEOSClient(), tmp_path
    )

    assert process_results.started_at
    assert process_results.completed_at
    assert process_results.employers_total_count == 1
    assert process_results.employers_success_count == 0
    assert process_results.employers_error_count == 1
    assert process_results.employers_skipped_count == 0
    assert process_results.employee_and_employer_pairs_total_count == 0


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
