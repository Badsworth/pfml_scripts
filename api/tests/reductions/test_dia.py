import os
import random
import string
from datetime import date
from typing import Any, Dict, Optional

import boto3
import faker
import pytest
import smart_open
import sqlalchemy

import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeFactory,
    ReferenceFileFactory,
    TaxIdentifierFactory,
)
from massgov.pfml.reductions.dia import (
    Constants,
    _format_claims_for_dia_claimant_list,
    _get_approved_claims,
    _write_approved_claims_to_tempfile,
    create_list_of_approved_claimants,
    upload_claimant_list_to_moveit,
)

fake = faker.Faker()


EXPECTED_DIA_PAYMENT_CSV_FILE_HEADERS = list(Constants.CLAIMAINT_LIST_FIELDS)


DIA_PAYMENT_LIST_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%Y%m%d"),
}


def _random_csv_filename() -> str:
    # Random filename. Types of characters and length of filename are not meaningful.
    return "".join(random.choices(string.ascii_lowercase, k=16)) + ".csv"


def _create_dia_payment_list_reference_file(
    dir: str, file_location: Optional[str] = None
) -> ReferenceFile:
    if file_location is None:
        file_location = os.path.join(dir, _random_csv_filename())

    return ReferenceFileFactory(
        file_location=file_location,
        reference_file_type_id=ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id,
    )


# every test in here requires real resources
pytestmark = pytest.mark.integration


@pytest.fixture
def set_up(test_db_session, initialize_factories_session):
    start_date = date(2021, 1, 28)
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee_info = {
        "date_of_birth": date(1979, 11, 12),
        "first_name": "John",
        "last_name": "Doe",
        "tax_identifier": tax_id,
    }

    employee1 = EmployeeFactory.create(**employee_info)
    employee2 = EmployeeFactory.create(**employee_info)
    ClaimFactory.create(
        employee=employee1,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=start_date,
    )
    ClaimFactory.create(
        employee=employee2,
        fineos_absence_status_id=AbsenceStatus.DECLINED.absence_status_id,
        absence_period_start_date=start_date,
    )

    approved_claims = _get_approved_claims(test_db_session)

    return approved_claims


@pytest.fixture
def set_up_invalid_data(test_db_session, initialize_factories_session):
    start_date = date(2021, 1, 28)
    tax_id = TaxIdentifierFactory.create(tax_identifier="088574541")
    employee_info = {
        "date_of_birth": date(1979, 11, 12),
        "first_name": "Jo,hn",
        "last_name": "Doe",
        "tax_identifier": tax_id,
    }

    employee1 = EmployeeFactory.create(**employee_info)
    employee2 = EmployeeFactory.create(**employee_info)
    ClaimFactory.create(
        employee=employee1,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        absence_period_start_date=start_date,
    )
    ClaimFactory.create(
        employee=employee2,
        fineos_absence_status_id=AbsenceStatus.DECLINED.absence_status_id,
        absence_period_start_date=start_date,
    )

    approved_claims = _get_approved_claims(test_db_session)

    return approved_claims


def test_get_approved_claims(set_up, test_db_session):
    approved_claims = set_up
    assert len(approved_claims) == 1


def test_format_claims_for_dia_claimant_list(set_up):
    approved_claims = set_up
    claim = approved_claims[0]
    employee = claim.employee
    approved_claims_dia_info = _format_claims_for_dia_claimant_list(approved_claims)

    for approved_claim in approved_claims_dia_info:
        assert approved_claim[Constants.CASE_ID_FIELD] == claim.fineos_absence_id
        assert (
            approved_claim[Constants.BENEFIT_START_DATE_FIELD]
            == Constants.TEMPORARY_BENEFIT_START_DATE
        )
        assert approved_claim[Constants.FIRST_NAME_FIELD] == employee.first_name
        assert approved_claim[Constants.LAST_NAME_FIELD] == employee.last_name
        assert approved_claim[Constants.BIRTH_DATE_FIELD] == employee.date_of_birth.strftime(
            Constants.DATE_OF_BIRTH_FORMAT
        )
        assert isinstance(approved_claim[Constants.BIRTH_DATE_FIELD], str)
        assert approved_claim[Constants.SSN_FIELD] == employee.tax_identifier.tax_identifier
        assert "-" not in approved_claim[Constants.SSN_FIELD]


def test_write_approved_claims_to_tempfile_invalid_data(set_up_invalid_data):
    approved_employees = set_up_invalid_data

    with pytest.raises(ValueError):
        approved_claims_dia_info = _format_claims_for_dia_claimant_list(approved_employees)
        _write_approved_claims_to_tempfile(approved_claims_dia_info)


def _random_date_in_past_year() -> date:
    return fake.date_between(start_date="-1y", end_date="today")


def _get_valid_dia_payment_data() -> Dict[str, Any]:
    return {
        "CASE_ID": "NTN-{}-ABS-01".format(fake.random_int(min=1000, max=9999)),
        "SSN": fake.ssn(),
        "FIRST_NAME": fake.first_name(),
        "LAST_NAME": fake.last_name(),
        "BIRTH_DATE": fake.date(pattern="%Y%m"),
        "START_DATE": fake.date(pattern="%Y%m"),
    }


def _get_loaded_reference_file_in_s3(mock_s3_bucket, filename, source_directory_path, row_count):
    # Create the ReferenceFile.
    pending_directory = os.path.join(f"s3://{mock_s3_bucket}", source_directory_path)
    source_filepath = os.path.join(pending_directory, filename)
    ref_file = _create_dia_payment_list_reference_file("", source_filepath)

    # Create some number of valid rows for our input file.
    body = ",".join(EXPECTED_DIA_PAYMENT_CSV_FILE_HEADERS) + "\n"
    for _i in range(row_count):
        db_data = _get_valid_dia_payment_data()
        csv_row = csv_util.encode_row(db_data, DIA_PAYMENT_LIST_ENCODERS)
        body = body + ",".join(list(csv_row.values())) + "\n"

    # Add rows to the file in our mock S3 bucket.
    s3_key = os.path.join(source_directory_path, filename)
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=s3_key, Body=body)

    return ref_file


def test_copy_to_sftp_and_archive_s3_files(
    initialize_factories_session,
    test_db_session,
    test_db_other_session,
    mock_s3_bucket,
    mock_sftp_client,
    setup_mock_sftp_client,
    monkeypatch,
):
    # Mock out S3 and MoveIt configs.
    s3_bucket_uri = f"s3://{mock_s3_bucket}"
    source_directory_path = "reductions/dia/outbound"
    archive_directory_path = "reductions/dia/archive"
    moveit_dia_inbound_path = "/DFML/DIA/Inbound"

    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DIA_OUTBOUND_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DIA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)
    monkeypatch.setenv("MOVEIT_DIA_INBOUND_PATH", moveit_dia_inbound_path)

    filenames = []
    file_count = random.randint(1, 8)
    for _i in range(file_count):
        filename = _random_csv_filename()
        row_count = random.randint(1, 5)
        ref_file = _get_loaded_reference_file_in_s3(
            mock_s3_bucket, filename, source_directory_path, row_count
        )
        ref_file.reference_file_type_id = ReferenceFileType.DIA_CLAIMANT_LIST.reference_file_type_id

        filenames.append(filename)

    # Save the changes to the reference file types.
    test_db_session.commit()

    s3_source_directory_uri = os.path.join(s3_bucket_uri, source_directory_path)
    s3_archive_directory_uri = os.path.join(s3_bucket_uri, archive_directory_path)
    assert len(file_util.list_files(s3_source_directory_uri)) == len(filenames)
    assert len(file_util.list_files(s3_archive_directory_uri)) == 0

    upload_claimant_list_to_moveit(test_db_session)

    # Expect to have moved all files from the source to the archive directory of S3.
    assert len(file_util.list_files(s3_source_directory_uri)) == 0
    assert len(file_util.list_files(s3_archive_directory_uri)) == len(filenames)

    # Get files in the MoveIt server and s3 archive directory.
    files_in_moveit = mock_sftp_client.listdir(moveit_dia_inbound_path)
    files_in_s3_archive_dir = file_util.list_files(s3_archive_directory_uri)

    # Confirm that we've moved every ReferenceFile, created a StateLog record, and updated the db.
    for filename in filenames:
        file_loc = os.path.join(s3_archive_directory_uri, filename)

        ref_file = (
            test_db_session.query(ReferenceFile)
            .filter(ReferenceFile.file_location == file_loc)
            .one_or_none()
        )
        assert ref_file
        assert filename in files_in_s3_archive_dir
        assert filename in files_in_moveit

        # Use test_db_other_session so we query against the database instead of just the in-memory
        # cache of test_db_session.
        assert (
            test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
            .filter(StateLog.end_state_id == State.DIA_CLAIMANT_LIST_SUBMITTED.state_id)
            .filter(StateLog.reference_file_id == ref_file.reference_file_id)
            .scalar()
            == 1
        )


def test_create_list_of_approved_claimants(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "reductions/dia/outbound"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DIA_OUTBOUND_DIRECTORY_PATH", dest_dir)

    # Set up some small random number of claims.
    claims = []
    for _i in range(random.randint(3, 8)):
        claim = ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id
        )
        claim.employee.date_of_birth = fake.date_between(start_date="-100y", end_date="-18y")
        claims.append(claim)

    create_list_of_approved_claimants(test_db_session)

    # Expect that the file to appear in the mock_s3_bucket.
    s3 = boto3.client("s3")

    # Confirm that the file is uploaded to S3 with the expected filename.
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    assert len(object_list) == 1
    s3_filename = object_list[0]["Key"]
    full_s3_filepath = os.path.join(s3_bucket_uri, s3_filename)
    dest_filepath_and_prefix = os.path.join(dest_dir, Constants.CLAIMAINT_LIST_FILENAME_PREFIX)
    assert s3_filename.startswith(dest_filepath_and_prefix)

    # Confirm the file we uploaded to S3 contains a single row for each claim and no header row.
    with smart_open.open(full_s3_filepath) as s3_file:
        assert len(claims) == len(list(s3_file))

    ref_file = (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DIA_CLAIMANT_LIST.reference_file_type_id
        )
        .all()
    )
    state_log = (
        test_db_session.query(StateLog)
        .filter_by(end_state_id=State.DIA_CLAIMANT_LIST_CREATED.state_id)
        .all()
    )

    assert len(ref_file) == 1
    assert len(state_log) == 1
    assert ref_file[0].file_location == full_s3_filepath
