#
# Tests for massgov.pfml.dor.importer.import_dor.
#

import copy
import datetime
import decimal
import pathlib
import tempfile
from typing import List

import boto3
import botocore
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.elements import not_

import massgov.pfml.dor.importer.import_dor as import_dor
import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.dor.importer.paths
import massgov.pfml.dor.mock.generate as generator
import massgov.pfml.util.batch.log
from massgov.pfml.db.models.employees import (
    Address,
    AddressType,
    Employee,
    EmployeePushToFineosQueue,
    Employer,
    EmployerPushToFineosQueue,
    EmployerQuarterlyContribution,
    WagesAndContributions,
    WagesAndContributionsHistory,
)
from massgov.pfml.db.models.factories import EmployerQuarterlyContributionFactory
from massgov.pfml.db.models.geo import Country, GeoState
from massgov.pfml.dor.importer.import_dor import (
    PROCESSED_FOLDER,
    RECEIVED_FOLDER,
    move_file_to_processed,
)
from massgov.pfml.util.encryption import GpgCrypt, Utf8Crypt

from . import dor_test_data as test_data

decrypter = Utf8Crypt()
employee_file = "DORDFML_20200519120622"
employer_file = "DORDFMLEMP_20200519120622"

TEST_FOLDER = pathlib.Path(__file__).parent

EMPTY_SSN_TO_EMPLOYEE_ID_MAP = {}


@pytest.fixture
def test_fs_path(tmp_path):
    employer_quarter_line = test_data.get_employer_quarter_line()
    employee_quarter_line = test_data.get_employee_quarter_line()
    content1 = "{}\n{}".format(employer_quarter_line, employee_quarter_line)

    content2 = test_data.get_employer_info_line()

    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()
    test_file = test_folder / employee_file
    test_file.write_text(content1)
    test_file2 = test_folder / employer_file
    test_file2.write_text(content2)

    return test_folder


@pytest.fixture
def dor_employer_lookups(test_db_session):

    # setup employer expected lookup values
    GeoState.sync_to_database(test_db_session)
    state = GeoState.get_instance(test_db_session, template=GeoState.MA)

    Country.sync_to_database(test_db_session)
    country = Country.get_instance(test_db_session, template=Country.USA)

    return (state, country)


def test_employer_import(test_db_session, dor_employer_lookups):

    # perform import
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    report, report_log_entry = get_new_import_report(test_db_session)
    assert report_log_entry.import_log_id is not None

    import_dor.import_employers(test_db_session, employers, report, report_log_entry.import_log_id)

    # confirm expected columns are persisted
    persisted_employer = (
        test_db_session.query(Employer)
        .filter(Employer.account_key == employer_payload["account_key"])
        .one_or_none()
    )
    employer_id = persisted_employer.employer_id

    assert persisted_employer is not None

    validate_employer_persistence(
        employer_payload, persisted_employer, report_log_entry.import_log_id
    )

    persisted_employer_address = dor_persistence_util.get_employer_address(
        test_db_session, employer_id
    )
    assert persisted_employer_address is not None

    persisted_address = dor_persistence_util.get_address(
        test_db_session, persisted_employer_address.address_id
    )
    assert persisted_address is not None

    state, country = dor_employer_lookups
    validate_employer_address_persistence(
        employer_payload, persisted_address, AddressType.BUSINESS, state, country
    )

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 0
    assert report.unmodified_employers_count == 0

    # Verify Logs are correct
    employer_insert_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employer_insert_logs) == 1
    assert employer_insert_logs[0].employer_id == employer_id
    # ------
    employer_update_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs) == 0


def test_employer_update(test_db_session, dor_employer_lookups):
    # perform initial import
    new_employer_payload = test_data.get_new_employer()
    report, report_log_entry = get_new_import_report(test_db_session)

    import_dor.import_employers(
        test_db_session, [new_employer_payload], report, report_log_entry.import_log_id
    )
    persisted_employer = (
        test_db_session.query(Employer)
        .filter(Employer.account_key == new_employer_payload["account_key"])
        .one_or_none()
    )
    employer_id = persisted_employer.employer_id

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 0

    # Verify Logs are correct (1)
    employer_insert_logs1: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    employer_insert_logs_ids1 = [x.employer_push_to_fineos_queue_id for x in employer_insert_logs1]
    assert len(employer_insert_logs1) == 1
    assert employer_insert_logs1[0].employer_id == employer_id
    # ------
    employer_update_logs1: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs1) == 0
    # ------------

    # confirm unchanged update date will be skipped
    report2, report_log_entry2 = get_new_import_report(test_db_session)
    updated_employer_payload_to_skip = test_data.get_updated_employer_except_update_date()
    import_dor.import_employers(
        test_db_session,
        [updated_employer_payload_to_skip],
        report2,
        report_log_entry2.import_log_id,
    )
    existing_employer = test_db_session.query(Employer).get(employer_id)

    with pytest.raises(AssertionError):
        validate_employer_persistence(
            updated_employer_payload_to_skip, existing_employer, report_log_entry.import_log_id
        )

    assert report2.updated_employers_count == 0
    assert report2.unmodified_employers_count == 1
    assert existing_employer.latest_import_log_id == report_log_entry.import_log_id

    # Verify Logs are correct (2)
    employer_insert_logs2: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(
            EmployerPushToFineosQueue.action == "INSERT",
            not_(
                EmployerPushToFineosQueue.employer_push_to_fineos_queue_id.in_(
                    employer_insert_logs_ids1
                )
            ),
        )
        .all()
    )
    assert len(employer_insert_logs2) == 0
    # ------
    employer_update_logs2: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs2) == 0
    # ------------

    # confirm expected columns are now updated
    report3, report_log_entry3 = get_new_import_report(test_db_session)
    updated_employer_payload = test_data.get_updated_employer()
    import_dor.import_employers(
        test_db_session, [updated_employer_payload], report3, report_log_entry3.import_log_id
    )
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(
        updated_employer_payload, persisted_employer, report_log_entry3.import_log_id
    )

    persisted_employer_address = dor_persistence_util.get_employer_address(
        test_db_session, employer_id
    )
    assert persisted_employer_address is not None

    persisted_address = dor_persistence_util.get_address(
        test_db_session, persisted_employer_address.address_id
    )
    assert persisted_address is not None

    state, country = dor_employer_lookups
    validate_employer_address_persistence(
        updated_employer_payload, persisted_address, AddressType.BUSINESS, state, country
    )

    assert report3.updated_employers_count == 1

    # Verify Logs are correct (3)
    employer_insert_logs3: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(
            EmployerPushToFineosQueue.action == "INSERT",
            not_(
                EmployerPushToFineosQueue.employer_push_to_fineos_queue_id.in_(
                    employer_insert_logs_ids1
                )
            ),
        )
        .all()
    )
    assert len(employer_insert_logs3) == 0
    # ------
    employer_update_logs3: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs3) == 1
    assert employer_update_logs3[0].employer_id == persisted_employer.employer_id
    assert employer_update_logs3[0].family_exemption == new_employer_payload["family_exemption"]
    assert employer_update_logs3[0].medical_exemption == new_employer_payload["medical_exemption"]
    assert (
        employer_update_logs3[0].exemption_commence_date
        == new_employer_payload["exemption_commence_date"]
    )
    assert (
        employer_update_logs3[0].exemption_cease_date
        == new_employer_payload["exemption_cease_date"]
    )
    # ------------


def test_employer_create_and_update_in_same_run(test_db_session):
    new_employer_payload = test_data.get_new_employer()
    updated_employer_payload = test_data.get_updated_employer()
    report, report_log_entry = get_new_import_report(test_db_session)

    import_dor.import_employers(
        test_db_session,
        [new_employer_payload, updated_employer_payload],
        report,
        report_log_entry.import_log_id,
    )
    persisted_employer = (
        test_db_session.query(Employer)
        .filter(Employer.account_key == new_employer_payload["account_key"])
        .one_or_none()
    )
    employer_id = persisted_employer.employer_id

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 1
    assert report.unmodified_employers_count == 0

    # confirm expected columns are now updated
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(
        updated_employer_payload, persisted_employer, report_log_entry.import_log_id
    )

    # Verify Logs are correct
    employer_insert_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employer_insert_logs) == 1
    assert employer_insert_logs[0].employer_id == persisted_employer.employer_id

    # ------
    employer_update_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs) == 1
    assert employer_update_logs[0].employer_id == persisted_employer.employer_id

    assert employer_update_logs[0].family_exemption == new_employer_payload["family_exemption"]
    assert employer_update_logs[0].medical_exemption == new_employer_payload["medical_exemption"]
    assert (
        employer_update_logs[0].exemption_commence_date
        == new_employer_payload["exemption_commence_date"]
    )
    assert (
        employer_update_logs[0].exemption_cease_date == new_employer_payload["exemption_cease_date"]
    )
    # ------------


def test_employer_address(test_db_session):
    employer_international_address = test_data.get_employer_international_address()
    employer_invalid_country = test_data.get_employer_invalid_country()

    report, report_log_entry = get_new_import_report(test_db_session)

    import_dor.import_employers(
        test_db_session,
        [employer_international_address, employer_invalid_country],
        report,
        report_log_entry.import_log_id,
    )

    assert report.created_employers_count == 2

    invalid_country_employer = (
        test_db_session.query(Employer)
        .filter(Employer.account_key == employer_invalid_country["account_key"])
        .one()
    )
    assert invalid_country_employer.addresses[0].address.country_id is None

    # confirm expected columns are now updated
    valid_country_employer = (
        test_db_session.query(Employer)
        .filter(Employer.account_key == employer_international_address["account_key"])
        .one_or_none()
    )
    persisted_address = valid_country_employer.addresses[0].address

    assert persisted_address.geo_state_id is None
    assert (
        persisted_address.geo_state_text == employer_international_address["employer_address_state"]
    )
    assert persisted_address.country_id == Country.get_id(
        employer_international_address["employer_address_country"]
    )

    # Verify Logs are correct

    employer_insert_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employer_insert_logs) == 2

    found_employer_1 = next(
        x for x in employer_insert_logs if x.employer_id == invalid_country_employer.employer_id
    )
    assert found_employer_1

    found_employer_2 = next(
        x for x in employer_insert_logs if x.employer_id == valid_country_employer.employer_id
    )
    assert found_employer_2

    # ------
    employer_update_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs) == 0
    # ------------


def test_employer_invalid_fein(test_db_session):
    employer_data_invalid_type = copy.deepcopy(test_data.new_employer)
    employer_data_invalid_length = copy.deepcopy(test_data.new_employer)
    employer_data_invalid_type["fein"] = "abcdefghi"
    employer_data_invalid_type["account_key"] = "00000000002"
    employer_data_invalid_length["fein"] = "12345678"

    before_employer_count = test_db_session.query(Employer).count()

    report, report_log_entry = get_new_import_report(test_db_session)
    import_dor.import_employers(
        test_db_session,
        [employer_data_invalid_type, employer_data_invalid_length],
        report,
        report_log_entry.import_log_id,
    )

    assert report.created_employers_count == 0
    assert len(report.invalid_employer_feins_by_account_key) == 2
    assert employer_data_invalid_type["account_key"] in report.invalid_employer_feins_by_account_key
    assert (
        employer_data_invalid_length["account_key"] in report.invalid_employer_feins_by_account_key
    )
    after_employer_count = test_db_session.query(Employer).count()
    assert before_employer_count == after_employer_count

    # Verify Logs are correct
    employer_insert_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employer_insert_logs) == 0
    # ------
    employer_update_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs) == 0
    # ------------


def test_log_employees_with_new_employers(test_db_session):

    # Employee generate helper
    def generate_employee_and_wage_item(id, employer):
        employee = next(generator.generate_single_employee(id, [employer]))
        # convert quarter to date
        employee["filing_period"] = employee["filing_period"].as_date()
        return employee

    # Create two employers
    employer1 = generator.generate_single_employer(1)
    employer2 = generator.generate_single_employer(2)
    employers = [employer1, employer2]

    report, report_log_entry = get_new_import_report(test_db_session)
    import_dor.import_employers(test_db_session, employers, report, report_log_entry.import_log_id)

    created_employers = test_db_session.query(Employer).all()
    assert len(created_employers) == 2

    # Verify Employer Logs are correct (1)
    employer_insert_logs1: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employer_insert_logs1) == 2

    found_employer_1 = next(
        x for x in employer_insert_logs1 if x.employer_id == created_employers[0].employer_id
    )
    assert found_employer_1

    found_employer_2 = next(
        x for x in employer_insert_logs1 if x.employer_id == created_employers[1].employer_id
    )
    assert found_employer_2

    # ------
    employer_update_logs1: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs1) == 0
    # ------------

    # Create two employees
    employee1 = generate_employee_and_wage_item(1, employer1)
    employee2 = generate_employee_and_wage_item(2, employer2)

    employee_ssns_to_id_created_in_current_import_run = {}

    report1, report_log_entry1 = get_new_import_report(test_db_session)
    import_dor.import_employees_and_wage_data(
        test_db_session,
        [employee1, employee2],
        employee_ssns_to_id_created_in_current_import_run,
        report1,
        report_log_entry1.import_log_id,
    )

    assert report1.created_employees_count == 2
    assert report1.logged_employees_for_new_employer == 0

    created_employees = test_db_session.query(Employee).all()
    assert len(created_employees) == 2

    created_wages = test_db_session.query(WagesAndContributions).all()
    assert len(created_wages) == 2

    # Verify Employee Logs are correct (1)
    employee_insert_logs1: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "INSERT")
        .all()
    )
    employee_insert_log_ids1 = [x.employee_push_to_fineos_queue_id for x in employee_insert_logs1]

    assert len(employee_insert_logs1) == 2

    found_employee_1 = next(
        x for x in employee_insert_logs1 if x.employee_id == created_employees[0].employee_id
    )
    assert found_employee_1

    found_employee_2 = next(
        x for x in employee_insert_logs1 if x.employee_id == created_employees[1].employee_id
    )
    assert found_employee_2
    # ------
    employee_update_logs1: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employee_update_logs1) == 0
    # ------
    employee_employer_logs1: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
        .all()
    )
    assert len(employee_employer_logs1) == 0
    # ------------

    # Simulate a wage entry for an existing employee with a new employer
    employee2_employer1 = generate_employee_and_wage_item(2, employer1)
    employee2_employer1_second_entry = generate_employee_and_wage_item(2, employer1)
    employee3 = generate_employee_and_wage_item(3, employer1)
    employee_ssns_to_id_created_in_current_import_run = {}

    report2, report_log_entry2 = get_new_import_report(test_db_session)
    import_dor.import_employees_and_wage_data(
        test_db_session,
        [employee1, employee2, employee2_employer1, employee2_employer1_second_entry, employee3],
        employee_ssns_to_id_created_in_current_import_run,
        report2,
        report_log_entry2.import_log_id,
    )

    assert report2.unmodified_employees_count == 2
    assert report2.created_employees_count == 1
    assert report2.logged_employees_for_new_employer == 1

    employee_with_new_employer = dor_persistence_util.get_employees_by_ssn(
        test_db_session, [employee2_employer1["employee_ssn"]]
    )[0]

    created_employee = dor_persistence_util.get_employees_by_ssn(
        test_db_session, [employee3["employee_ssn"]]
    )[0]

    # Verify Employee Logs are correct (2)
    employee_insert_logs2: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(
            EmployeePushToFineosQueue.action == "INSERT",
            not_(
                EmployeePushToFineosQueue.employee_push_to_fineos_queue_id.in_(
                    employee_insert_log_ids1
                )
            ),
        )
        .all()
    )
    assert len(employee_insert_logs2) == 1
    assert employee_insert_logs2[0].employee_id == created_employee.employee_id
    # ------
    employee_update_logs2: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employee_update_logs2) == 0
    # ------
    employee_employer_logs2: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
        .all()
    )
    assert len(employee_employer_logs2) == 1
    assert employee_employer_logs2[0].employer_id == found_employer_1.employer_id
    assert employee_employer_logs2[0].employee_id == employee_with_new_employer.employee_id
    # ------------


def get_new_import_report(test_db_session):
    report = import_dor.ImportReport()
    report_log_entry = massgov.pfml.util.batch.log.create_log_entry(
        test_db_session, __name__, "DOR", "Initial", report
    )

    return report, report_log_entry


def test_employee_wage_data_create(test_db_session, dor_employer_lookups):

    # create empty report
    report, report_log_entry = get_new_import_report(test_db_session)

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    account_key = employer_payload["account_key"]
    employers = [employer_payload]
    import_dor.import_employers(test_db_session, employers, report, report_log_entry.import_log_id)

    persisted_employer = (
        test_db_session.query(Employer).filter(Employer.account_key == account_key).one_or_none()
    )
    employer_id = persisted_employer.employer_id

    # Verify Employer Logs are correct
    employer_insert_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employer_insert_logs) == 1
    assert employer_insert_logs[0].employer_id == employer_id
    # ------
    employer_update_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs) == 0
    # ------------

    # perform employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()

    employee_id_by_ssn = {}
    import_dor.import_employees_and_wage_data(
        test_db_session,
        [employee_wage_data_payload],
        employee_id_by_ssn,
        report,
        report_log_entry.import_log_id,
    )

    employee_id = employee_id_by_ssn[employee_wage_data_payload["employee_ssn"]]
    persisted_employee = test_db_session.query(Employee).get(employee_id)

    assert persisted_employee is not None
    validate_employee_persistence(
        employee_wage_data_payload, persisted_employee, report_log_entry.import_log_id
    )

    persisted_wage_info = (
        dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
            test_db_session, employee_id, employer_id, employee_wage_data_payload["filing_period"]
        )
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(
        employee_wage_data_payload, persisted_wage_info, report_log_entry.import_log_id
    )

    assert report.created_employees_count == 1
    assert report.updated_employees_count == 0

    assert report.created_wages_and_contributions_count == 1
    assert report.updated_wages_and_contributions_count == 0

    # Verify Employee Logs are correct
    employee_insert_logs: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employee_insert_logs) == 1
    assert employee_insert_logs[0].employee_id == employee_id
    # ------
    employee_update_logs: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employee_update_logs) == 0
    # ------
    employee_employer_logs: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
        .all()
    )
    assert len(employee_employer_logs) == 0
    # ------------


def test_employee_wage_data_update(test_db_session, dor_employer_lookups):

    # create empty report
    report, report_log_entry = get_new_import_report(test_db_session)

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    account_key = employer_payload["account_key"]
    employers = [employer_payload]
    import_dor.import_employers(test_db_session, employers, report, report_log_entry.import_log_id)

    persisted_employer = (
        test_db_session.query(Employer).filter(Employer.account_key == account_key).one_or_none()
    )
    employer_id = persisted_employer.employer_id

    # Verify Employer Logs are correct
    employer_insert_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "INSERT")
        .all()
    )
    assert len(employer_insert_logs) == 1
    assert employer_insert_logs[0].employer_id == employer_id
    # ------
    employer_update_logs: List[EmployerPushToFineosQueue] = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employer_update_logs) == 0
    # ------------

    # perform initial employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()

    employee_id_by_ssn = {}
    import_dor.import_employees_and_wage_data(
        test_db_session,
        [employee_wage_data_payload],
        employee_id_by_ssn,
        report,
        report_log_entry.import_log_id,
    )
    employee_id = employee_id_by_ssn[employee_wage_data_payload["employee_ssn"]]

    assert report.created_employees_count == 1
    assert report.created_wages_and_contributions_count == 1
    assert report.updated_employees_count == 0
    assert report.unmodified_employees_count == 0
    assert report.updated_wages_and_contributions_count == 0

    # Verify no WagesAndContributionsHistory records exist
    assert test_db_session.query(WagesAndContributionsHistory).count() == 0
    # Verify Employee Logs are correct (1)
    employee_insert_logs1: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "INSERT")
        .all()
    )
    employee_insert_log_ids1 = [x.employee_push_to_fineos_queue_id for x in employee_insert_logs1]
    assert len(employee_insert_logs1) == 1
    assert employee_insert_logs1[0].employee_id == employee_id
    # ------
    employee_update_logs1: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employee_update_logs1) == 0
    # ------
    employee_employer_logs1: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
        .all()
    )
    assert len(employee_employer_logs1) == 0
    # ------------

    # confirm that existing employee info is not updated when there is no change
    report2, report_log_entry2 = get_new_import_report(test_db_session)

    import_dor.import_employees_and_wage_data(
        test_db_session,
        [employee_wage_data_payload],
        EMPTY_SSN_TO_EMPLOYEE_ID_MAP,
        report2,
        report_log_entry2.import_log_id,
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)
    assert persisted_employee is not None

    validate_employee_persistence(
        employee_wage_data_payload, persisted_employee, report_log_entry.import_log_id
    )

    assert report2.created_employees_count == 0
    assert report2.created_wages_and_contributions_count == 0
    assert report2.updated_employees_count == 0
    assert report2.unmodified_employees_count == 1
    assert report2.updated_wages_and_contributions_count == 0
    assert report2.unmodified_wages_and_contributions_count == 1

    # Verify Employee Logs are correct (2)
    employee_insert_logs2: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(
            EmployeePushToFineosQueue.action == "INSERT",
            not_(
                EmployeePushToFineosQueue.employee_push_to_fineos_queue_id.in_(
                    employee_insert_log_ids1
                )
            ),
        )
        .all()
    )
    assert len(employee_insert_logs2) == 0
    # ------
    employee_update_logs2: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employee_update_logs2) == 0
    # ------
    employee_employer_logs2: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
        .all()
    )
    assert len(employee_employer_logs2) == 0
    # ------------

    # confirm updates are persisted
    report3, report_log_entry3 = get_new_import_report(test_db_session)
    updated_employee_wage_data_payload = test_data.get_updated_employee_wage_data()
    import_dor.import_employees_and_wage_data(
        test_db_session,
        [updated_employee_wage_data_payload],
        EMPTY_SSN_TO_EMPLOYEE_ID_MAP,
        report3,
        report_log_entry3.import_log_id,
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)

    assert persisted_employee is not None
    validate_employee_persistence(
        updated_employee_wage_data_payload, persisted_employee, report_log_entry3.import_log_id
    )

    persisted_wage_info = (
        dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
            test_db_session,
            employee_id,
            employer_id,
            updated_employee_wage_data_payload["filing_period"],
        )
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(
        updated_employee_wage_data_payload, persisted_wage_info, report_log_entry3.import_log_id
    )

    assert report3.created_employees_count == 0
    assert report3.created_wages_and_contributions_count == 0
    assert report3.updated_employees_count == 1
    assert report3.unmodified_employees_count == 0
    assert report3.updated_wages_and_contributions_count == 1
    assert report3.unmodified_wages_and_contributions_count == 0

    # Verify WagesAndContributionsHistory has been persisted
    wage_history_records = test_db_session.query(WagesAndContributionsHistory).all()
    assert len(wage_history_records) == 1
    assert wage_history_records[0].wage_and_contribution == persisted_wage_info
    # Validate that the data captured is the previous data
    validate_wage_history_persistence(
        employee_wage_data_payload, wage_history_records[0], report_log_entry.import_log_id
    )

    # Verify Employee Logs are correct (3)
    employee_insert_logs3: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(
            EmployeePushToFineosQueue.action == "INSERT",
            not_(
                EmployeePushToFineosQueue.employee_push_to_fineos_queue_id.in_(
                    employee_insert_log_ids1
                )
            ),
        )
        .all()
    )
    assert len(employee_insert_logs3) == 0
    # ------
    employee_update_logs3: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE")
        .all()
    )
    assert len(employee_update_logs3) == 1
    assert employee_update_logs3[0].employee_id == employee_id
    # ------
    employee_employer_logs3: List[EmployeePushToFineosQueue] = (
        test_db_session.query(EmployeePushToFineosQueue)
        .filter(EmployeePushToFineosQueue.action == "UPDATE_NEW_EMPLOYER")
        .all()
    )
    assert len(employee_employer_logs3) == 0
    # ------------


# == Validation Helpers ==


def validate_employee_persistence(employee_wage_payload, employee_row, import_log_id):
    assert employee_row.tax_identifier.tax_identifier == employee_wage_payload["employee_ssn"]
    assert employee_row.first_name == employee_wage_payload["employee_first_name"]
    assert employee_row.last_name == employee_wage_payload["employee_last_name"]
    assert employee_row.latest_import_log_id == import_log_id


def validate_wage_persistence(employee_wage_payload, wage_row, import_log_id):
    assert wage_row.is_independent_contractor == employee_wage_payload["independent_contractor"]
    assert wage_row.is_opted_in == employee_wage_payload["opt_in"]
    assert wage_row.employee_ytd_wages == employee_wage_payload["employee_ytd_wages"]
    assert wage_row.employee_qtr_wages == employee_wage_payload["employee_qtr_wages"]
    assert wage_row.employee_med_contribution == employee_wage_payload["employee_medical"]
    assert wage_row.employer_med_contribution == employee_wage_payload["employer_medical"]
    assert wage_row.employee_fam_contribution == employee_wage_payload["employee_family"]
    assert wage_row.employer_fam_contribution == employee_wage_payload["employer_family"]
    assert wage_row.latest_import_log_id == import_log_id


def validate_wage_history_persistence(employee_wage_payload, wage_row, import_log_id):
    assert wage_row.is_independent_contractor == employee_wage_payload["independent_contractor"]
    assert wage_row.is_opted_in == employee_wage_payload["opt_in"]
    assert wage_row.employee_ytd_wages == employee_wage_payload["employee_ytd_wages"]
    assert wage_row.employee_qtr_wages == employee_wage_payload["employee_qtr_wages"]
    assert wage_row.employee_med_contribution == employee_wage_payload["employee_medical"]
    assert wage_row.employer_med_contribution == employee_wage_payload["employer_medical"]
    assert wage_row.employee_fam_contribution == employee_wage_payload["employee_family"]
    assert wage_row.employer_fam_contribution == employee_wage_payload["employer_family"]
    assert wage_row.import_log_id == import_log_id


def validate_employer_persistence(employer_payload, employer_row, import_log_id):
    assert employer_row.employer_fein == employer_payload["fein"]
    assert employer_row.employer_name == employer_payload["employer_name"]
    assert employer_row.family_exemption == employer_payload["family_exemption"]
    assert employer_row.medical_exemption == employer_payload["medical_exemption"]
    assert employer_row.exemption_commence_date == employer_payload["exemption_commence_date"]
    assert employer_row.exemption_cease_date == employer_payload["exemption_cease_date"]
    assert employer_row.dor_updated_date == employer_payload["updated_date"]
    assert employer_row.latest_import_log_id == import_log_id


def validate_employer_address_persistence(
    employer_payload, address_row, business_address_type, state, country
):
    assert address_row.address_type_id == business_address_type.address_type_id
    assert address_row.address_line_one == employer_payload["employer_address_street"]
    assert address_row.city == employer_payload["employer_address_city"]
    assert address_row.geo_state_id == state.geo_state_id
    assert address_row.zip_code == employer_payload["employer_address_zip"]
    assert address_row.country_id == country.country_id


def test_parse_employer_file(test_fs_path):
    employer_info = test_data.get_new_employer()
    employer_file_path = "{}/{}".format(str(test_fs_path), employer_file)

    report = import_dor.ImportReport(
        start=datetime.datetime.now().isoformat(),
        status="in progress",
        employer_file=employer_file_path,
        employee_file=employer_file_path,
    )

    employers_info = import_dor.parse_employer_file(employer_file_path, decrypter, report)
    assert employers_info[0] == employer_info


## == full import ==


@pytest.mark.timeout(60)
def test_e2e_parse_and_persist(test_db_session, dor_employer_lookups):
    # generate files for import
    employer_count = 100

    employer_file_path = get_temp_file_path()
    employee_file_path = get_temp_file_path()

    employer_file = open(employer_file_path, "w")
    employee_file = open(employee_file_path, "w")

    generator.generate(employer_count, employer_file, employee_file)
    employer_file.close()
    employee_file.close()

    employer_lines = open(employer_file_path, "r").readlines()
    assert len(employer_lines) == employer_count

    employee_lines = open(employee_file_path, "r").readlines()
    employee_a_lines = tuple(filter(lambda s: s.startswith("A"), employee_lines))
    employee_b_lines = tuple(filter(lambda s: s.startswith("B"), employee_lines))

    # Test scenario where already created tax ID will pass.
    dor_persistence_util.create_tax_id(test_db_session, "250000001")

    assert len(employee_a_lines) == employer_count * 4
    wages_contributions_count = len(employee_b_lines)
    assert wages_contributions_count >= employer_count

    # import
    import_batches = [
        massgov.pfml.dor.importer.paths.ImportBatch(
            upload_date="20200805", employer_file=employer_file_path, employee_file=""
        ),
        massgov.pfml.dor.importer.paths.ImportBatch(
            upload_date="20200805", employer_file="", employee_file=employee_file_path
        ),
    ]

    reports = import_dor.process_import_batches(
        import_batches=import_batches, decrypt_files=False, optional_db_session=test_db_session
    )

    report_one = reports[0]
    assert report_one.created_employers_count == employer_count

    report_two = reports[1]
    assert report_two.created_employees_count >= employer_count
    assert report_two.created_wages_and_contributions_count == wages_contributions_count

    assert report_two.created_employer_quarters_count == len(employee_a_lines)


@pytest.mark.timeout(60)
def test_e2e_parse_and_persist_empty_dba_city(test_db_session, dor_employer_lookups):
    # generate files for import
    employer_count = 100

    employer_file_path = get_temp_file_path()
    employee_file_path = get_temp_file_path()

    employer_file = open(employer_file_path, "w")
    employee_file = open(employee_file_path, "w")

    generator.generate(
        employer_count, employer_file, employee_file, set_empty_dba=True, set_empty_city=True
    )
    employer_file.close()
    employee_file.close()

    employer_lines = open(employer_file_path, "r").readlines()
    assert len(employer_lines) == employer_count

    employee_lines = open(employee_file_path, "r").readlines()
    employee_a_lines = tuple(filter(lambda s: s.startswith("A"), employee_lines))
    employee_b_lines = tuple(filter(lambda s: s.startswith("B"), employee_lines))

    # Test scenario where already created tax ID will pass.
    dor_persistence_util.create_tax_id(test_db_session, "250000001")

    assert len(employee_a_lines) == employer_count * 4
    wages_contributions_count = len(employee_b_lines)
    assert wages_contributions_count >= employer_count

    # import
    import_batches = [
        massgov.pfml.dor.importer.paths.ImportBatch(
            upload_date="20200805", employer_file=employer_file_path, employee_file=""
        ),
        massgov.pfml.dor.importer.paths.ImportBatch(
            upload_date="20200805", employer_file="", employee_file=employee_file_path
        ),
    ]

    reports = import_dor.process_import_batches(
        import_batches=import_batches, decrypt_files=False, optional_db_session=test_db_session
    )

    report_one = reports[0]
    assert report_one.created_employers_count == employer_count

    report_two = reports[1]
    assert report_two.created_employees_count >= employer_count
    assert report_two.created_wages_and_contributions_count == wages_contributions_count

    assert report_two.created_employer_quarters_count == len(employee_a_lines)

    # all employers came in as "" dba, check to make sure the first one is None (they all will be)
    employer_in_db = test_db_session.query(Employer).first()
    assert employer_in_db.employer_dba is None

    first_address_in_db = test_db_session.query(Address).first()
    assert first_address_in_db.city is None

    # make sure every address was created
    address_count = test_db_session.query(Address).count()
    assert address_count == employer_count


@pytest.mark.timeout(25)
def test_decryption(monkeypatch, test_db_session, dor_employer_lookups):

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    employer_file_path = TEST_FOLDER / "encryption" / "DORDFMLEMP_20201118193421"
    employee_file_path = TEST_FOLDER / "encryption" / "DORDFML_20201118193421"

    report = import_dor.process_daily_import(
        employer_file_path=str(employer_file_path),
        employee_file_path=str(employee_file_path),
        decrypter=decrypter,
        db_session=test_db_session,
    )

    employer_count = 100
    employee_count = employer_count * generator.EMPLOYER_TO_EMPLOYEE_RATIO

    assert report.created_employers_count == employer_count
    assert report.created_employees_count == employee_count
    assert report.created_wages_and_contributions_count >= employee_count


def test_get_discreet_db_exception_message():
    original_exception_message = 'sqlalchemy.exc.InvalidRequestError: This Session\'s transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"\nDETAIL:  Key (tax_identifier)=(123456789) already exists.'
    expected_discreet_message = 'DB Exception: sqlalchemy.exc.InvalidRequestError: This Session\'s transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"\n, exception type: SQLAlchemyError'
    exception = SQLAlchemyError(original_exception_message)
    discreet_message = import_dor.get_discreet_db_exception_message(exception)
    assert "123456789" not in discreet_message
    assert expected_discreet_message == discreet_message


def test_move_file_to_processed(mock_s3_bucket):
    file_name = "test.txt"

    key = "{}{}".format(RECEIVED_FOLDER, file_name)
    moved_key = "{}{}".format(PROCESSED_FOLDER, file_name)
    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="line 1 text\nline 2 text\nline 3 text")

    should_exist_1 = s3.head_object(Bucket=mock_s3_bucket, Key=key)
    assert should_exist_1 is not None

    move_file_to_processed(full_path, s3)

    try:
        s3.head_object(Bucket=mock_s3_bucket, Key=key)
        raise AssertionError("This file should have been deleted.")
    except botocore.exceptions.ClientError:
        """No Op"""

    should_exist_1 = s3.head_object(Bucket=mock_s3_bucket, Key=moved_key)
    assert should_exist_1 is not None


def get_temp_file_path():
    handle, path = tempfile.mkstemp()
    return path


employer_quarterly_info_list = [
    # This employer / filing period combination is repeated below.
    {
        "record_type": "A",
        "account_key": "44100000001",
        "filing_period": datetime.date(2020, 3, 31),
        "employer_name": "Boone PLC",
        "employer_fein": "100000001",
        "amended_flag": False,
        "pfm_account_id": "100000001",
        "total_pfml_contribution": decimal.Decimal("46723.66"),
        "received_date": datetime.date(2020, 4, 7),
        "updated_date": datetime.datetime(2020, 9, 17, 23, 0, tzinfo=datetime.timezone.utc),
    },
    {
        "record_type": "A",
        "account_key": "44100000002",
        "filing_period": datetime.date(2019, 6, 30),
        "employer_name": "Gould, Brown & Miller",
        "employer_fein": "100000002",
        "amended_flag": False,
        "pfm_account_id": "100000002",
        "total_pfml_contribution": decimal.Decimal("57034.87"),
        "received_date": datetime.date(2019, 7, 18),
        "updated_date": datetime.datetime(2020, 10, 12, 23, 0, tzinfo=datetime.timezone.utc),
    },
    # Repeat of 1st record above.
    {
        "record_type": "A",
        "account_key": "44100000001",
        "filing_period": datetime.date(2020, 3, 31),
        "employer_name": "Boone PLC",
        "employer_fein": "100000001",
        "amended_flag": False,
        "pfm_account_id": "100000001",
        "total_pfml_contribution": decimal.Decimal("46723.66"),
        "received_date": datetime.date(2020, 4, 7),
        "updated_date": datetime.datetime(2020, 9, 17, 23, 0, tzinfo=datetime.timezone.utc),
    },
    {
        "record_type": "A",
        "account_key": "44100000003",
        "filing_period": datetime.date(2019, 6, 30),
        "employer_name": "Stephens LLC",
        "employer_fein": "100000003",
        "amended_flag": True,
        "pfm_account_id": "100000003",
        "total_pfml_contribution": decimal.Decimal("15493.23"),
        "received_date": datetime.date(2019, 7, 28),
        "updated_date": datetime.datetime(2020, 10, 5, 23, 0, tzinfo=datetime.timezone.utc),
    },
]


def test_import_employer_pfml_contributions_repeated_record(test_db_session, employers):
    report, log_entry = get_new_import_report(test_db_session)

    import_dor.import_employer_pfml_contributions(
        test_db_session, employer_quarterly_info_list, report, log_entry.import_log_id
    )

    def row(index, period, total, account, received, updated, log_id=log_entry.import_log_id):
        return (
            employers[index].employer_id,
            datetime.date.fromisoformat(period),
            decimal.Decimal(total),
            account,
            datetime.datetime.fromisoformat(f"{received} 00:00+00:00"),
            datetime.datetime.fromisoformat(f"{updated}+00:00"),
            log_id,
        )

    rows = (
        test_db_session.query(
            EmployerQuarterlyContribution.employer_id,
            EmployerQuarterlyContribution.filing_period,
            EmployerQuarterlyContribution.employer_total_pfml_contribution,
            EmployerQuarterlyContribution.pfm_account_id,
            EmployerQuarterlyContribution.dor_received_date,
            EmployerQuarterlyContribution.dor_updated_date,
            EmployerQuarterlyContribution.latest_import_log_id,
        )
        .order_by(EmployerQuarterlyContribution.dor_received_date)
        .all()
    )
    assert rows == [
        row(1, "2019-06-30", "57034.87", "100000002", "2019-07-18", "2020-10-12 23:00"),
        row(2, "2019-06-30", "15493.23", "100000003", "2019-07-28", "2020-10-05 23:00"),
        row(0, "2020-03-31", "46723.66", "100000001", "2020-04-07", "2020-09-17 23:00"),
    ]


def test_import_employer_pfml_contributions_with_updates(test_db_session, employers):
    EmployerQuarterlyContributionFactory.create(
        employer=employers[1],
        filing_period=datetime.date(2019, 6, 30),
        employer_total_pfml_contribution=decimal.Decimal("1000.00"),
        dor_received_date=datetime.date(2019, 6, 10),
    )
    EmployerQuarterlyContributionFactory.create(
        employer=employers[0],
        filing_period=datetime.date(2020, 3, 31),
        employer_total_pfml_contribution=decimal.Decimal("2000.00"),
        dor_received_date=datetime.date(2020, 3, 20),
    )
    EmployerQuarterlyContributionFactory.create(
        employer=employers[0],
        filing_period=datetime.date(2019, 9, 30),
        employer_total_pfml_contribution=decimal.Decimal("3000.00"),
        dor_received_date=datetime.date(2019, 9, 30),
        dor_updated_date=datetime.datetime(2019, 8, 30, 3, 30, tzinfo=datetime.timezone.utc),
        pfm_account_id="300000",
    )

    report, log_entry = get_new_import_report(test_db_session)

    import_dor.import_employer_pfml_contributions(
        test_db_session, employer_quarterly_info_list, report, log_entry.import_log_id
    )

    def row(index, period, total, account, received, updated, log_id=log_entry.import_log_id):
        return (
            employers[index].employer_id,
            datetime.date.fromisoformat(period),
            decimal.Decimal(total),
            account,
            datetime.datetime.fromisoformat(f"{received} 00:00+00:00"),
            datetime.datetime.fromisoformat(f"{updated}+00:00"),
            log_id,
        )

    rows = (
        test_db_session.query(
            EmployerQuarterlyContribution.employer_id,
            EmployerQuarterlyContribution.filing_period,
            EmployerQuarterlyContribution.employer_total_pfml_contribution,
            EmployerQuarterlyContribution.pfm_account_id,
            EmployerQuarterlyContribution.dor_received_date,
            EmployerQuarterlyContribution.dor_updated_date,
            EmployerQuarterlyContribution.latest_import_log_id,
        )
        .order_by(EmployerQuarterlyContribution.dor_received_date)
        .all()
    )
    assert rows == [
        row(1, "2019-06-30", "57034.87", "100000002", "2019-07-18", "2020-10-12 23:00"),
        row(2, "2019-06-30", "15493.23", "100000003", "2019-07-28", "2020-10-05 23:00"),
        row(0, "2019-09-30", "3000.00", "300000", "2019-09-30", "2019-08-30 03:30", None),
        row(0, "2020-03-31", "46723.66", "100000001", "2020-04-07", "2020-09-17 23:00"),
    ]
