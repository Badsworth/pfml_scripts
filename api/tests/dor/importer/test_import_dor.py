import pathlib
import tempfile
from datetime import datetime

import boto3
import pytest
from sqlalchemy.exc import SQLAlchemyError

import dor_test_data as test_data
import massgov.pfml.dor.importer.import_dor as import_dor
import massgov.pfml.dor.importer.lib.dor_persistence_util as dor_persistence_util
import massgov.pfml.dor.mock.generate as generator
from massgov.pfml.db.models.employees import AddressType, Country, Employee, Employer, GeoState
from massgov.pfml.util.encryption import GpgCrypt, Utf8Crypt

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
    country = Country.get_instance(test_db_session, template=Country.US)

    return (state, country)


def test_employer_import(test_db_session, dor_employer_lookups):

    # perform import
    employer_payload = test_data.get_new_employer()
    employers = [employer_payload]
    report, report_log_entry = get_new_import_report(test_db_session)
    assert report_log_entry.import_log_id is not None

    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, employers, report, report_log_entry.import_log_id
    )

    # confirm expected columns are persisted
    employer_id = account_key_to_employer_id_map[employer_payload["account_key"]]
    persisted_employer = test_db_session.query(Employer).get(employer_id)
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

    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, [new_employer_payload], report, report_log_entry.import_log_id
    )
    employer_id = account_key_to_employer_id_map[new_employer_payload["account_key"]]

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 0

    # confirm unchanged update date will be skipped
    updated_employer_payload_to_skip = test_data.get_updated_employer_except_update_date()
    import_dor.import_employers(
        test_db_session, [updated_employer_payload_to_skip], report, report_log_entry.import_log_id
    )
    existing_employer = test_db_session.query(Employer).get(employer_id)

    with pytest.raises(AssertionError):
        validate_employer_persistence(
            updated_employer_payload_to_skip, existing_employer, report_log_entry.import_log_id
        )

    assert report.updated_employers_count == 0
    assert report.unmodified_employers_count == 1

    # confirm expected columns are now updated
    updated_employer_payload = test_data.get_updated_employer()
    import_dor.import_employers(
        test_db_session, [updated_employer_payload], report, report_log_entry.import_log_id
    )
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(
        updated_employer_payload, persisted_employer, report_log_entry.import_log_id
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

    assert report.updated_employers_count == 1


def test_employer_create_and_update_in_same_run(test_db_session):
    new_employer_payload = test_data.get_new_employer()
    updated_employer_payload = test_data.get_updated_employer()
    report, report_log_entry = get_new_import_report(test_db_session)

    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session,
        [new_employer_payload, updated_employer_payload],
        report,
        report_log_entry.import_log_id,
    )
    employer_id = account_key_to_employer_id_map[new_employer_payload["account_key"]]

    assert report.created_employers_count == 1
    assert report.updated_employers_count == 1
    assert report.unmodified_employers_count == 0

    # confirm expected columns are now updated
    persisted_employer = test_db_session.query(Employer).get(employer_id)
    assert persisted_employer is not None

    validate_employer_persistence(
        updated_employer_payload, persisted_employer, report_log_entry.import_log_id
    )


def get_new_import_report(test_db_session):
    report = import_dor.ImportReport()
    report_log_entry = dor_persistence_util.create_import_log_entry(test_db_session, report)

    return report, report_log_entry


def test_employee_wage_data_create(test_db_session, dor_employer_lookups):

    # create empty report
    report, report_log_entry = get_new_import_report(test_db_session)

    # create employer dependency
    employer_payload = test_data.get_new_employer()
    account_key = employer_payload["account_key"]
    employers = [employer_payload]
    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, employers, report, report_log_entry.import_log_id
    )

    # perform employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()

    employee_id_by_ssn = {}
    import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
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

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session,
        employee_id,
        account_key_to_employer_id_map[account_key],
        employee_wage_data_payload["filing_period"],
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
    account_key_to_employer_id_map = import_dor.import_employers(
        test_db_session, employers, report, report_log_entry.import_log_id
    )

    # perform initial employee and wage import
    employee_wage_data_payload = test_data.get_new_employee_wage_data()

    employee_id_by_ssn = {}
    import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employee_wage_data_payload],
        employee_id_by_ssn,
        report,
        report_log_entry.import_log_id,
    )
    employee_id = employee_id_by_ssn[employee_wage_data_payload["employee_ssn"]]

    assert report.created_employees_count == 1
    assert report.created_wages_and_contributions_count == 1
    assert report.updated_employees_count == 0
    assert report.updated_wages_and_contributions_count == 0

    # confirm that existing employee info is updated even without a change
    report, report_log_entry = get_new_import_report(test_db_session)

    import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [employee_wage_data_payload],
        EMPTY_SSN_TO_EMPLOYEE_ID_MAP,
        report,
        report_log_entry.import_log_id,
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)
    assert persisted_employee is not None

    validate_employee_persistence(
        employee_wage_data_payload, persisted_employee, report_log_entry.import_log_id
    )

    assert report.created_employees_count == 0
    assert report.created_wages_and_contributions_count == 0
    assert report.updated_employees_count == 1
    assert report.updated_wages_and_contributions_count == 1

    # confirm updates are persisted
    report, report_log_entry = get_new_import_report(test_db_session)

    updated_employee_wage_data_payload = test_data.get_updated_employee_wage_data()
    import_dor.import_employees_and_wage_data(
        test_db_session,
        account_key_to_employer_id_map,
        [updated_employee_wage_data_payload],
        EMPTY_SSN_TO_EMPLOYEE_ID_MAP,
        report,
        report_log_entry.import_log_id,
    )

    persisted_employee = test_db_session.query(Employee).get(employee_id)

    assert persisted_employee is not None
    validate_employee_persistence(
        updated_employee_wage_data_payload, persisted_employee, report_log_entry.import_log_id
    )

    persisted_wage_info = dor_persistence_util.get_wages_and_contributions_by_employee_id_and_filling_period(
        test_db_session,
        employee_id,
        account_key_to_employer_id_map[account_key],
        updated_employee_wage_data_payload["filing_period"],
    )

    assert persisted_wage_info is not None
    validate_wage_persistence(
        updated_employee_wage_data_payload, persisted_wage_info, report_log_entry.import_log_id
    )

    assert report.created_employees_count == 0
    assert report.created_wages_and_contributions_count == 0
    assert report.updated_employees_count == 1
    assert report.updated_wages_and_contributions_count == 1


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


def test_get_files_for_import_grouped_by_date(test_fs_path, mock_s3_bucket):
    # test file system paths
    (test_fs_path / "extra_file").touch()
    (test_fs_path / "DORDFMLEMP_20200519133333").touch()
    (test_fs_path / "DORDFML_20200519133333").touch()
    (test_fs_path / "DORDFML_20201001133333").touch()
    files_by_date = import_dor.get_files_for_import_grouped_by_date(str(test_fs_path))
    assert files_by_date == {
        "20200519120622": {
            "DORDFMLEMP_": str(test_fs_path / employer_file),
            "DORDFML_": str(test_fs_path / employee_file),
        },
        "20200519133333": {
            "DORDFMLEMP_": str(test_fs_path / "DORDFMLEMP_20200519133333"),
            "DORDFML_": str(test_fs_path / "DORDFML_20200519133333"),
        },
        "20201001133333": {"DORDFML_": str(test_fs_path / "DORDFML_20201001133333"),},
    }

    # test s3 paths
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key="extra_file", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFMLEMP_20200519133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20200519133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key="DORDFML_20201001133333", Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key=employer_file, Body="")
    s3.put_object(Bucket=mock_s3_bucket, Key=employee_file, Body="")

    files_by_date = import_dor.get_files_for_import_grouped_by_date(f"s3://{mock_s3_bucket}")
    s3_prefix = f"s3://{mock_s3_bucket}"
    assert files_by_date == {
        "20200519120622": {
            "DORDFMLEMP_": f"{s3_prefix}/{employer_file}",
            "DORDFML_": f"{s3_prefix}/{employee_file}",
        },
        "20200519133333": {
            "DORDFMLEMP_": f"{s3_prefix}/DORDFMLEMP_20200519133333",
            "DORDFML_": f"{s3_prefix}/DORDFML_20200519133333",
        },
        "20201001133333": {"DORDFML_": f"{s3_prefix}/DORDFML_20201001133333",},
    }


def test_parse_employee_file(test_fs_path):
    employee_wage_data = test_data.get_new_employee_wage_data()
    employee_file_path = "{}/{}".format(str(test_fs_path), employee_file)

    report = import_dor.ImportReport(
        start=datetime.now().isoformat(),
        status="in progress",
        employer_file=test_fs_path,
        employee_file=test_fs_path,
    )

    employees_info = import_dor.parse_employee_file(employee_file_path, decrypter, report)
    assert employees_info[0] == employee_wage_data


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
    employer_count = 20
    employee_count = employer_count * generator.EMPLOYER_TO_EMPLOYEE_RATIO

    employer_file_path = get_temp_file_path()
    employee_file_path = get_temp_file_path()

    employer_file = open(employer_file_path, "w")
    employee_file = open(employee_file_path, "w")

    generator.process(employer_count, employer_file, employee_file, [1])
    employer_file.close()
    employee_file.close()

    employer_lines = open(employer_file_path, "r").readlines()
    assert len(employer_lines) == employer_count

    employee_lines = open(employee_file_path, "r").readlines()
    employee_a_lines = tuple(filter(lambda s: s.startswith("A"), employee_lines))
    employee_b_lines = tuple(filter(lambda s: s.startswith("B"), employee_lines))

    assert len(employee_a_lines) == employer_count * 4
    wages_contributions_count = len(employee_b_lines)
    assert wages_contributions_count >= employee_count * 4

    # import
    import_batches = [
        import_dor.ImportBatch(
            upload_date="20200805",
            employer_file=employer_file_path,
            employee_file=employee_file_path,
        )
    ]

    reports = import_dor.process_import_batches(
        import_batches=import_batches, decrypt_files=False, optional_db_session=test_db_session
    )

    report = reports[0]
    assert report.created_employers_count == employer_count
    assert report.created_employees_count == employee_count
    assert report.created_wages_and_contributions_count == wages_contributions_count


@pytest.mark.timeout(25)
def test_decryption(monkeypatch, test_db_session, dor_employer_lookups):

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    employer_file_path = TEST_FOLDER / "encryption" / "DORDFMLEMP_20201006205131"
    employee_file_path = TEST_FOLDER / "encryption" / "DORDFML_20201006205131"

    report = import_dor.process_daily_import(
        employer_file_path=str(employer_file_path),
        employee_file_path=str(employee_file_path),
        decrypter=decrypter,
        db_session=test_db_session,
    )

    employer_count = 20
    employee_count = employer_count * generator.EMPLOYER_TO_EMPLOYEE_RATIO

    assert report.created_employers_count == employer_count
    assert report.created_employees_count == employee_count
    assert report.created_wages_and_contributions_count >= employee_count


@pytest.mark.timeout(25)
def test_decryption_invalid_employer_lines(monkeypatch, test_db_session, dor_employer_lookups):

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    employer_file_path = TEST_FOLDER / "encryption" / "DORDFMLEMP_20201006205131_invalid_emp"
    employee_file_path = TEST_FOLDER / "encryption" / "DORDFML_20201006205131_invalid_emp"

    report = import_dor.process_daily_import(
        employer_file_path=str(employer_file_path),
        employee_file_path=str(employee_file_path),
        decrypter=decrypter,
        db_session=test_db_session,
    )

    # one employer will contain a parse error and be skipped
    employer_count = 21

    # one employer will contain a state error and be created, but the address will not
    employee_count = (employer_count - 1) * generator.EMPLOYER_TO_EMPLOYEE_RATIO

    assert report.created_employers_count == 19
    assert report.parsed_employers_exception_line_nums == [22]
    assert report.invalid_employer_lines_count == 1
    assert report.invalid_address_state_and_account_keys == {
        "00000000020": "BC",
        "00000000021": "10",
    }
    assert report.created_employees_count == employee_count
    assert report.created_wages_and_contributions_count >= employee_count


def test_get_discreet_db_exception_message():
    original_exception_message = 'sqlalchemy.exc.InvalidRequestError: This Session\'s transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"\nDETAIL:  Key (tax_identifier)=(123456789) already exists.'
    expected_discreet_message = 'DB Exception: sqlalchemy.exc.InvalidRequestError: This Session\'s transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"\n, exception type: SQLAlchemyError'
    exception = SQLAlchemyError(original_exception_message)
    discreet_message = import_dor.get_discreet_db_exception_message(exception)
    assert "123456789" not in discreet_message
    assert expected_discreet_message == discreet_message


def get_temp_file_path():
    handle, path = tempfile.mkstemp()
    return path
