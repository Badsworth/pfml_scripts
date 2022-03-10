#
# Tests for massgov.pfml.dor.importer.import_dor.
#

import pathlib
from datetime import datetime
from decimal import Decimal

import boto3
import pytest

import massgov.pfml.dor.pending_filing.pending_filing_response as import_dor
from massgov.pfml.db.models.employees import (
    Employee,
    Employer,
    EmployerPushToFineosQueue,
    EmployerQuarterlyContribution,
    WagesAndContributions,
)
from massgov.pfml.db.models.factories import EmployeeFactory, EmployerFactory, TaxIdentifierFactory
from massgov.pfml.dor.importer.import_dor import PROCESSED_FOLDER, RECEIVED_FOLDER, ImportReport
from massgov.pfml.dor.importer.paths import (
    get_exemption_file_to_process,
    get_pending_filing_files_to_process,
)
from massgov.pfml.dor.pending_filing.pending_filing_response import (
    DFML_PROCESSED_FOLDER,
    DFML_RECEIVED_FOLDER,
)
from massgov.pfml.types import Fein, TaxId
from massgov.pfml.util.csv import CSVSourceWrapper
from massgov.pfml.util.encryption import GpgCrypt, Utf8Crypt

decrypter = Utf8Crypt()
TEST_FOLDER = pathlib.Path(__file__).parent.parent

EMPTY_SSN_TO_EMPLOYEE_ID_MAP = {}


@pytest.mark.timeout(25)
def test_decryption(monkeypatch, test_db_session):

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "importer" / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    employer_file_path = TEST_FOLDER / "importer" / "encryption" / "DORDUADFMLEMP_20211210131901"
    exemption_file_path = TEST_FOLDER / "importer" / "CompaniesReturningToStatePlan.csv"

    import_files = list()
    import_files.append(str(employer_file_path))

    reports = import_dor.process_pending_filing_employer_files(
        import_files=import_files,
        exemption_file_path=str(exemption_file_path),
        decrypt_files=True,
        optional_decrypter=decrypter,
        optional_db_session=test_db_session,
    )

    employer_count = 4
    employee_count = 4

    assert reports[0].created_employers_count == employer_count
    assert reports[0].created_employees_count == employee_count
    assert reports[0].created_wages_and_contributions_count == employee_count


def test_account_key_set_single_file(monkeypatch, test_db_session):
    employer_file_path = TEST_FOLDER / "importer" / "encryption" / "DORDUADFMLEMP_20211210131901"
    exemption_file_path = TEST_FOLDER / "importer" / "CompaniesReturningToStatePlan.csv"

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "importer" / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    report = ImportReport()
    exemption_data = CSVSourceWrapper(str(exemption_file_path))

    employers, employees = import_dor.parse_pending_filing_employer_file(
        str(employer_file_path), exemption_data, decrypter, report, test_db_session
    )

    assert employees[0]["account_key"] == employers[0]["account_key"]
    assert employers[0]["account_key"] != employers[3]["account_key"]
    assert employees[3]["account_key"] == employers[3]["account_key"]


def test_employer_multiple_wage_rows(initialize_factories_session, monkeypatch, test_db_session):
    monkeypatch.setenv("DECRYPT", "false")

    employer_file_path = TEST_FOLDER / "importer" / "DORDUADFML_SUBMISSION_20212216"
    exemption_file_path = TEST_FOLDER / "importer" / "CompaniesReturningToStatePlan.csv"

    import_files = list()
    import_files.append(str(employer_file_path))

    import_dor.process_pending_filing_employer_files(
        import_files=import_files,
        exemption_file_path=str(exemption_file_path),
        decrypt_files=True,
        optional_decrypter=decrypter,
        optional_db_session=test_db_session,
    )

    employer = test_db_session.query(Employer).filter(Employer.employer_fein == Fein("123456999")).first()

    employee = (
        test_db_session.query(Employee)
        .filter(Employee.first_name == "TEST" and Employee.last_name == "DOE")
        .first()
    )

    wages = (
        test_db_session.query(WagesAndContributions)
        .filter(
            WagesAndContributions.employee_id == employee.employee_id
            and WagesAndContributions.employer_id == employer.employer_id
        )
        .all()
    )

    assert len(wages) == 4

    employer = test_db_session.query(Employer).filter(Employer.employer_fein == Fein("123456789")).first()
    employer2 = (
        test_db_session.query(Employer).filter(Employer.employer_fein == Fein("123456799")).first()
    )
    employer3 = (
        test_db_session.query(Employer).filter(Employer.employer_fein == Fein("123456999")).first()
    )

    assert employer2.family_exemption is True
    assert employer2.medical_exemption is True

    assert employer3.family_exemption is True
    assert employer3.medical_exemption is True

    wage_rows = (
        test_db_session.query(EmployerQuarterlyContribution)
        .filter(EmployerQuarterlyContribution.employer_id == employer.employer_id)
        .all()
    )
    wage_rows2 = (
        test_db_session.query(EmployerQuarterlyContribution)
        .filter(EmployerQuarterlyContribution.employer_id == employer2.employer_id)
        .all()
    )
    wage_rows3 = (
        test_db_session.query(EmployerQuarterlyContribution)
        .filter(EmployerQuarterlyContribution.employer_id == employer3.employer_id)
        .all()
    )

    assert len(wage_rows) == 3
    assert len(wage_rows2) == 2
    assert len(wage_rows3) == 4

    queue_item = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(
            EmployerPushToFineosQueue.employer_id == employer2.employer_id
            and EmployerPushToFineosQueue.action == "INSERT"
        )
        .first()
    )

    cease_date = datetime.strptime("1/30/2022", "%m/%d/%Y").date()
    assert queue_item.exemption_cease_date == cease_date


def test_update_existing_employer_cease_date(
    initialize_factories_session, monkeypatch, test_db_session
):
    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "importer" / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    cease_date = datetime.strptime("1/1/2025", "%m/%d/%Y").date()
    employer = EmployerFactory.create(employer_fein=Fein("100000001"), exemption_cease_date=cease_date)

    employer_file_path = TEST_FOLDER / "importer" / "encryption" / "DORDUADFMLEMP_20211210131901"
    exemption_file_path = TEST_FOLDER / "importer" / "CompaniesReturningToStatePlan.csv"

    import_files = list()
    import_files.append(str(employer_file_path))

    import_dor.process_pending_filing_employer_files(
        import_files=import_files,
        exemption_file_path=str(exemption_file_path),
        decrypt_files=True,
        optional_decrypter=decrypter,
        optional_db_session=test_db_session,
    )

    queue_item = (
        test_db_session.query(EmployerPushToFineosQueue)
        .filter(EmployerPushToFineosQueue.employer_id == employer.employer_id)
        .first()
    )

    cease_date = datetime.strptime("1/1/2022", "%m/%d/%Y").date()
    assert queue_item.exemption_cease_date == cease_date


def test_get_csv_regex(monkeypatch, mock_dfml_s3_bucket):
    exemption_file_name = "CompaniesReturningToStatePlan1.csv"

    exemption_file_path = TEST_FOLDER / "importer" / "CompaniesReturningToStatePlan.csv"
    exemption_file = open(exemption_file_path, "rb")
    exemption_key = "{}{}".format(DFML_RECEIVED_FOLDER, exemption_file_name)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_dfml_s3_bucket, Key=exemption_key, Body=exemption_file.read())
    full_dfml_received_folder_path = "s3://{}/{}".format(mock_dfml_s3_bucket, DFML_RECEIVED_FOLDER)

    exception_file_found = get_exemption_file_to_process(full_dfml_received_folder_path)
    assert (
        exception_file_found
        == "s3://test_dfml_bucket/dfml/received/CompaniesReturningToStatePlan1.csv"
    )


@pytest.fixture
def mock_s3_bucket_resource(mock_s3):
    bucket = mock_s3.Bucket("test_dfml_bucket")
    bucket.create()
    yield bucket


@pytest.fixture
def mock_dfml_s3_bucket(mock_s3_bucket_resource):
    yield mock_s3_bucket_resource.name


def test_insert_wage_rows_existing_employee(
    initialize_factories_session, monkeypatch, test_db_session
):
    monkeypatch.setenv("DECRYPT", "false")

    employer_file_path = TEST_FOLDER / "importer" / "DORDUADFML_SUBMISSION_20212216"
    exemption_file_path = TEST_FOLDER / "importer" / "CompaniesReturningToStatePlan.csv"

    account_key = "123456999"
    employer = EmployerFactory.create(account_key=account_key, employer_fein=Fein("123456999"))
    tax_identifier = TaxIdentifierFactory.create(tax_identifier=TaxId("111111111"))
    employee = EmployeeFactory.create(tax_identifier=tax_identifier, email_address="foo@bar.com")
    filing_period = datetime.strptime("9/30/2020", "%m/%d/%Y").date()
    wage_row = WagesAndContributions()
    wage_row.account_key = account_key
    wage_row.is_independent_contractor = False
    wage_row.is_opted_in = False
    wage_row.employer_med_contribution = Decimal(12345)
    wage_row.employer_fam_contribution = Decimal(67890)
    wage_row.employee_med_contribution = Decimal(12345)
    wage_row.employee_fam_contribution = Decimal(67890)
    wage_row.employee_ytd_wages = Decimal(100)
    wage_row.employee_qtr_wages = Decimal(100)
    wage_row.filing_period = filing_period
    wage_row.employer_id = employer.employer_id
    wage_row.employee_id = employee.employee_id
    test_db_session.add(wage_row)

    test_db_session.commit()

    wages = (
        test_db_session.query(WagesAndContributions)
        .filter(
            WagesAndContributions.employee_id == employee.employee_id
            and WagesAndContributions.employer_id == employer.employer_id
        )
        .all()
    )

    assert len(wages) == 1

    import_files = list()
    import_files.append(str(employer_file_path))

    import_dor.process_pending_filing_employer_files(
        import_files=import_files,
        exemption_file_path=str(exemption_file_path),
        decrypt_files=True,
        optional_decrypter=decrypter,
        optional_db_session=test_db_session,
    )

    employer = test_db_session.query(Employer).filter(Employer.employer_fein == "123456999").first()

    assert employer.account_key == account_key

    employee = (
        test_db_session.query(Employee)
        .filter(Employee.tax_identifier_id == tax_identifier.tax_identifier_id)
        .first()
    )

    wages = (
        test_db_session.query(WagesAndContributions)
        .filter(
            WagesAndContributions.employee_id == employee.employee_id
            and WagesAndContributions.employer_id == employer.employer_id
        )
        .all()
    )

    # this means 3 new wages rows were created and the previously created one was unmodified
    assert len(wages) == 4

    assert wages[0].filing_period == filing_period
    assert wages[0].employer_med_contribution == Decimal(12345)
    assert wages[0].employer_fam_contribution == Decimal(67890)

    unmodified_employee = (
        test_db_session.query(Employee)
        .filter(Employee.employee_id == employee.employee_id)
        .one_or_none()
    )

    assert unmodified_employee.email_address == "foo@bar.com"


@pytest.mark.timeout(60)
def test_e2e(monkeypatch, test_db_session, mock_s3_bucket, mock_dfml_s3_bucket):
    file_name = "DORDUADFMLEMP_20211210131901"
    exemption_file_name = "CompaniesReturningToStatePlan.csv"

    employer_file_path = TEST_FOLDER / "importer" / "encryption" / "DORDUADFMLEMP_20211210131901"
    exemption_file_path = TEST_FOLDER / "importer" / "CompaniesReturningToStatePlan.csv"

    employer_file = open(employer_file_path, "rb")
    exemption_file = open(exemption_file_path, "rb")

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "importer" / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    key = "{}{}".format(RECEIVED_FOLDER, file_name)
    exemption_key = "{}{}".format(DFML_RECEIVED_FOLDER, exemption_file_name)

    moved_key = "{}{}".format(PROCESSED_FOLDER, file_name)
    moved_exemption_key = "{}{}".format(DFML_PROCESSED_FOLDER, exemption_file_name)
    full_received_folder_path = "s3://{}/{}".format(mock_s3_bucket, RECEIVED_FOLDER)
    full_dfml_received_folder_path = "s3://{}/{}".format(mock_dfml_s3_bucket, DFML_RECEIVED_FOLDER)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body=employer_file.read())
    s3.put_object(Bucket=mock_dfml_s3_bucket, Key=exemption_key, Body=exemption_file.read())

    should_exist_1 = s3.head_object(Bucket=mock_s3_bucket, Key=key)
    assert should_exist_1 is not None

    should_exist_2 = s3.head_object(Bucket=mock_dfml_s3_bucket, Key=exemption_key)
    assert should_exist_2 is not None

    import_files = get_pending_filing_files_to_process(full_received_folder_path)
    assert import_files[0] == "s3://test_dfml_bucket/dor/received/DORDUADFMLEMP_20211210131901"

    path_without_slash = full_received_folder_path[:-1]
    assert path_without_slash == "s3://test_dfml_bucket/dor/received"
    import_files_without_slash = get_pending_filing_files_to_process(path_without_slash)
    assert (
        import_files_without_slash[0]
        == "s3://test_dfml_bucket/dor/received/DORDUADFMLEMP_20211210131901"
    )

    assert len(import_files) == 1

    exception_file = get_exemption_file_to_process(full_dfml_received_folder_path)

    reports = import_dor.process_pending_filing_employer_files(
        import_files=import_files,
        exemption_file_path=exception_file,
        decrypt_files=True,
        optional_decrypter=decrypter,
        optional_db_session=test_db_session,
        optional_s3=s3,
    )

    employer_count = 4
    employee_count = 4

    assert reports[0].created_employers_count == employer_count
    assert reports[0].created_employees_count == employee_count
    assert reports[0].created_wages_and_contributions_count == employee_count

    should_exist_3 = s3.head_object(Bucket=mock_s3_bucket, Key=moved_key)
    assert should_exist_3 is not None

    should_exist_4 = s3.head_object(Bucket=mock_dfml_s3_bucket, Key=moved_exemption_key)
    assert should_exist_4 is not None
