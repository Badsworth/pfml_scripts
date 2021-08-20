import copy
import pathlib
import tempfile
from datetime import datetime

import boto3
import botocore
import pytest
from sqlalchemy.exc import SQLAlchemyError

import massgov.pfml.dor.importer.import_dor as import_dor
import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.dor.importer.paths
import massgov.pfml.dor.mock.generate as generator
import massgov.pfml.util.batch.log
from massgov.pfml.db.models.employees import (
    AddressType,
    Country,
    Employee,
    EmployeeLog,
    Employer,
    GeoState,
    WagesAndContributions,
)
from massgov.pfml.dor.importer.import_dor import (
    PROCESSED_FOLDER,
    RECEIVED_FOLDER,
    move_file_to_processed,
)
from massgov.pfml.types import TaxId
from massgov.pfml.util.encryption import GpgCrypt, Utf8Crypt

from . import dor_test_data as test_data

# every test in here requires real resources
pytestmark = pytest.mark.integration

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
        [employer_data_invalid_type, employer_data_invalid_length,],
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

    created_employee_logs = (
        test_db_session.query(EmployeeLog).filter(EmployeeLog.action == "UPDATE_NEW_EMPLOYER").all()
    )
    assert len(created_employee_logs) == 1

    expected_logged_employee = dor_persistence_util.get_employees_by_ssn(
        test_db_session, [employee2_employer1["employee_ssn"]]
    )[0]
    assert created_employee_logs[0].employee_id == expected_logged_employee.employee_id


def get_new_import_report(test_db_session):
    report = import_dor.ImportReport()
    report_log_entry = massgov.pfml.util.batch.log.create_log_entry(
        test_db_session, "DOR", "Initial", report
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

    persisted_employer = (
        test_db_session.query(Employer).filter(Employer.account_key == account_key).one_or_none()
    )
    employer_id = persisted_employer.employer_id

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session, employee_id, employer_id, employee_wage_data_payload["filing_period"],
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(
        employee_wage_data_payload, persisted_wage_info, report_log_entry.import_log_id
    )

    assert report.created_employees_count == 1
    assert report.updated_employees_count == 0

    assert report.created_wages_and_contributions_count == 1
    assert report.updated_wages_and_contributions_count == 0


def test_employee_wage_data_update(test_db_session, dor_employer_lookups):

    # create empty report
    report, report_log_entry = get_new_import_report(test_db_session)

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    account_key = employer_payload["account_key"]
    employers = [employer_payload]
    import_dor.import_employers(test_db_session, employers, report, report_log_entry.import_log_id)

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

    persisted_employer = (
        test_db_session.query(Employer).filter(Employer.account_key == account_key).one_or_none()
    )
    employer_id = persisted_employer.employer_id

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session,
        employee_id,
        employer_id,
        updated_employee_wage_data_payload["filing_period"],
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


# == Validation Helpers ==


def validate_employee_persistence(employee_wage_payload, employee_row, import_log_id):
    assert employee_row.tax_identifier.tax_identifier == TaxId(
        employee_wage_payload["employee_ssn"]
    )
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


def validate_employer_persistence(employer_payload, employer_row, import_log_id):
    assert employer_row.employer_fein.to_unformatted_str() == employer_payload["fein"]
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
        start=datetime.now().isoformat(),
        status="in progress",
        employer_file=employer_file_path,
        employee_file=employer_file_path,
    )

    employers_info = import_dor.parse_employer_file(employer_file_path, decrypter, report)
    assert employers_info[0] == employer_info


## == full import ==


@pytest.mark.timeout(20)
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
            upload_date="20200805", employer_file=employer_file_path, employee_file="",
        ),
        massgov.pfml.dor.importer.paths.ImportBatch(
            upload_date="20200805", employer_file="", employee_file=employee_file_path,
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
