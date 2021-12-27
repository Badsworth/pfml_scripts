#
# Tests for massgov.pfml.dor.importer.import_dor.
#

import pathlib
from datetime import datetime

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
from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.dor.importer.import_dor import PROCESSED_FOLDER, RECEIVED_FOLDER, ImportReport
from massgov.pfml.dor.importer.paths import get_pending_filing_files_to_process
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

    import_files = list()
    import_files.append(str(employer_file_path))

    reports = import_dor.process_pending_filing_employer_files(
        import_files=import_files,
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

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "importer" / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    report = ImportReport()
    employers, employees = import_dor.parse_pending_filing_employer_file(
        str(employer_file_path), decrypter, report
    )

    assert employees[0]["account_key"] == employers[0]["account_key"]
    assert employers[0]["account_key"] != employers[3]["account_key"]
    assert employees[3]["account_key"] == employers[3]["account_key"]


def test_employer_multiple_wage_rows(initialize_factories_session, monkeypatch, test_db_session):
    monkeypatch.setenv("DECRYPT", "false")

    employer_file_path = TEST_FOLDER / "importer" / "DORDUADFML_SUBMISSION_20212216"

    import_files = list()
    import_files.append(str(employer_file_path))

    import_dor.process_pending_filing_employer_files(
        import_files=import_files,
        decrypt_files=True,
        optional_decrypter=decrypter,
        optional_db_session=test_db_session,
    )

    employer = test_db_session.query(Employer).filter(Employer.employer_fein == "123456999").first()

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

    employer = test_db_session.query(Employer).filter(Employer.employer_fein == "123456789").first()
    employer2 = (
        test_db_session.query(Employer).filter(Employer.employer_fein == "123456799").first()
    )
    employer3 = (
        test_db_session.query(Employer).filter(Employer.employer_fein == "123456999").first()
    )

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


def test_update_existing_employer_cease_date(
    initialize_factories_session, monkeypatch, test_db_session
):
    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "importer" / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    cease_date = datetime.strptime("1/1/2025", "%m/%d/%Y").date()

    employer = EmployerFactory.create(employer_fein="100000001", exemption_cease_date=cease_date)

    employer_file_path = TEST_FOLDER / "importer" / "encryption" / "DORDUADFMLEMP_20211210131901"

    import_files = list()
    import_files.append(str(employer_file_path))

    import_dor.process_pending_filing_employer_files(
        import_files=import_files,
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


@pytest.mark.timeout(60)
def test_e2e(monkeypatch, test_db_session, mock_s3_bucket):
    file_name = "DORDUADFMLEMP_20211210131901"

    employer_file_path = TEST_FOLDER / "importer" / "encryption" / "DORDUADFMLEMP_20211210131901"
    employer_file = open(employer_file_path, "rb")

    monkeypatch.setenv("DECRYPT", "true")

    decryption_key = open(TEST_FOLDER / "importer" / "encryption" / "test_private.key").read()
    passphrase = "bb8d58fa-d781-11ea-87d0-0242ac130003"
    test_email = "pfml-test@example.com"

    decrypter = GpgCrypt(decryption_key, passphrase, test_email)

    key = "{}{}".format(RECEIVED_FOLDER, file_name)
    moved_key = "{}{}".format(PROCESSED_FOLDER, file_name)
    full_received_folder_path = "s3://{}/{}".format(mock_s3_bucket, RECEIVED_FOLDER)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body=employer_file.read())

    should_exist_1 = s3.head_object(Bucket=mock_s3_bucket, Key=key)
    assert should_exist_1 is not None

    import_files = get_pending_filing_files_to_process(full_received_folder_path)
    assert len(import_files) == 1

    reports = import_dor.process_pending_filing_employer_files(
        import_files=import_files,
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

    should_exist_2 = s3.head_object(Bucket=mock_s3_bucket, Key=moved_key)
    assert should_exist_2 is not None
