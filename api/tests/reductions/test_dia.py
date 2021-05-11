import csv
import os
import random
import string
from datetime import date, datetime
from typing import Dict, Optional

import boto3
import factory
import faker
import pytest
import smart_open
import sqlalchemy

import massgov.pfml.reductions.dia as dia
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    DiaReductionPayment,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    EmployeeWithFineosNumberFactory,
    ReferenceFileFactory,
)
from massgov.pfml.reductions.dia import (
    Constants,
    _format_claimants_for_dia_claimant_list,
    _write_claimants_to_tempfile,
    create_list_of_claimants,
    download_payment_list_if_none_today,
    upload_claimant_list_to_moveit,
)

fake = faker.Faker()


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


def test_format_claimants_for_dia_claimant_list():
    employees_general = EmployeeWithFineosNumberFactory.build_batch(size=2)

    employee_with_comma_names = [
        EmployeeWithFineosNumberFactory.build(first_name="Jane", last_name="Doe, JR."),
        EmployeeWithFineosNumberFactory.build(first_name="Doe, Jane", last_name="Doe"),
        EmployeeWithFineosNumberFactory.build(first_name="Doe, Jane", last_name="Doe, JR."),
        EmployeeWithFineosNumberFactory.build(first_name="Fo,o,,,"),
    ]

    employees = employees_general + employee_with_comma_names

    claimants_dia_info = _format_claimants_for_dia_claimant_list(employees)

    assert len(claimants_dia_info) == len(employees)

    for employee, dia_claimant in zip(employees, claimants_dia_info):
        assert dia_claimant[Constants.CUSTOMER_NUMBER_FIELD] == employee.fineos_customer_number
        assert (
            dia_claimant[Constants.BENEFIT_START_DATE_FIELD]
            == Constants.TEMPORARY_BENEFIT_START_DATE
        )

        assert "," not in dia_claimant[Constants.FIRST_NAME_FIELD]
        assert dia_claimant[Constants.FIRST_NAME_FIELD] == employee.first_name.replace(",", "")

        assert "," not in dia_claimant[Constants.LAST_NAME_FIELD]
        assert dia_claimant[Constants.LAST_NAME_FIELD] == employee.last_name.replace(",", "")

        assert dia_claimant[Constants.BIRTH_DATE_FIELD] == employee.date_of_birth.strftime(
            Constants.DATE_OF_BIRTH_FORMAT
        )
        assert isinstance(dia_claimant[Constants.BIRTH_DATE_FIELD], str)
        assert dia_claimant[Constants.SSN_FIELD] == employee.tax_identifier.tax_identifier
        assert "-" not in dia_claimant[Constants.SSN_FIELD]


def test_write_claimants_to_tempfile_comma_error():
    employees = EmployeeWithFineosNumberFactory.build_batch(size=2, fineos_customer_number="test,")

    with pytest.raises(ValueError):
        claimants_dia_info = _format_claimants_for_dia_claimant_list(employees)
        _write_claimants_to_tempfile(claimants_dia_info)


def test_write_claimants_to_tempfile_quote_error():
    employees = EmployeeWithFineosNumberFactory.build_batch(
        size=2, first_name='Jane "The Unknown" Doe'
    )

    with pytest.raises(csv.Error):
        claimants_dia_info = _format_claimants_for_dia_claimant_list(employees)
        _write_claimants_to_tempfile(claimants_dia_info)


def _get_valid_dia_claimant_data() -> Dict[str, str]:
    return {
        "DFML_ID": str(fake.random_int(min=1000, max=9999)),
        "SSN": fake.ssn(),
        "FIRST_NAME": fake.first_name(),
        "LAST_NAME": fake.last_name(),
        "BIRTH_DATE": fake.date(pattern="%Y%m"),
        "START_DATE": fake.date(pattern="%Y%m"),
    }


def _get_valid_dia_payment_data() -> Dict[str, str]:
    return {
        "DFML_ID": str(fake.random_int(min=1000, max=9999)),
        "BOARD_NO": str(fake.random_int(min=100000, max=999999)),
        "EVENT_ID": str(fake.random_int(min=100000, max=999999)),
        "INS_FORM_OR_MEET": fake.random_element(elements=("PC", "LUMP")),
        "EVE_CREATED_DATE": fake.date(pattern="%Y%m%d"),
        "FORM_RECEIVED_OR_DISPOSITION": fake.date(pattern="%Y%m%d"),
        "AWARD_ID": str(fake.random_int(min=5, max=2000)),
        "AWARD_CODE": str(fake.random_int(min=10, max=4000)),
        "AWARD_AMOUNT": str(fake.random_int(min=100, max=10000)),
        "AWARD_DATE": fake.date(pattern="%Y%m%d"),
        "START_DATE": fake.date(pattern="%Y%m%d"),
        "END_DATE": fake.date(pattern="%Y%m%d"),
        "WEEKLY_AMOUNT": str(fake.random_int(min=0.0, max=100.0)),
        "AWARD_CREATED_DATE": fake.date(pattern="%Y%m%d"),
    }


def _get_loaded_reference_file_in_s3(mock_s3_bucket, filename, source_directory_path, row_count):
    # Create the ReferenceFile.
    pending_directory = os.path.join(f"s3://{mock_s3_bucket}", source_directory_path)
    source_filepath = os.path.join(pending_directory, filename)
    ref_file = _create_dia_payment_list_reference_file("", source_filepath)

    # Create some number of valid rows for our input file.
    body = ""
    for _i in range(row_count):
        db_data = _get_valid_dia_claimant_data()
        csv_row = csv_util.encode_row(db_data, DIA_PAYMENT_LIST_ENCODERS)
        body = body + ",".join(list(csv_row.values())) + "\n"

    # Add rows to the file in our mock S3 bucket.
    s3_key = os.path.join(source_directory_path, filename)
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=s3_key, Body=body)

    return ref_file


def _make_loaded_payment_reference_file_in_s3(
    mock_s3_bucket, filename, source_directory_path, rows
):
    # Create the ReferenceFile.
    pending_directory = os.path.join(f"s3://{mock_s3_bucket}", source_directory_path)
    source_filepath = os.path.join(pending_directory, filename)
    ref_file = _create_dia_payment_list_reference_file("", source_filepath)

    # Create some number of valid rows for our input file.
    body = ""
    for db_data in rows:
        csv_row = csv_util.encode_row(db_data, DIA_PAYMENT_LIST_ENCODERS)
        body = body + ",".join(list(csv_row.values())) + "\n"

    # Add rows to the file in our mock S3 bucket.
    s3_key = os.path.join(source_directory_path, filename)
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=s3_key, Body=body)

    return (rows, ref_file)


def _get_loaded_payment_reference_file_in_s3(
    mock_s3_bucket, filename, source_directory_path, row_count
):
    rows = [_get_valid_dia_payment_data() for _ in range(row_count)]

    return _make_loaded_payment_reference_file_in_s3(
        mock_s3_bucket, filename, source_directory_path, rows
    )


@pytest.mark.integration
def test_copy_to_sftp_and_archive_s3_files(
    local_initialize_factories_session,
    local_test_db_session,
    local_test_db_other_session,
    mock_s3_bucket,
    mock_sftp_client,
    setup_mock_sftp_client,
    monkeypatch,
):
    # Mock out S3 and MoveIt configs.
    s3_bucket_uri = f"s3://{mock_s3_bucket}"
    source_directory_path = "reductions/dia/outbound"
    archive_directory_path = "reductions/dia/archive"
    moveit_dia_outbound_path = "/DFML/DIA/Inbound"

    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DIA_OUTBOUND_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DIA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)
    monkeypatch.setenv("MOVEIT_DIA_OUTBOUND_PATH", moveit_dia_outbound_path)

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
    local_test_db_session.commit()

    s3_source_directory_uri = os.path.join(s3_bucket_uri, source_directory_path)
    s3_archive_directory_uri = os.path.join(s3_bucket_uri, archive_directory_path)
    assert len(file_util.list_files(s3_source_directory_uri)) == len(filenames)
    assert len(file_util.list_files(s3_archive_directory_uri)) == 0

    upload_claimant_list_to_moveit(local_test_db_session)

    # Expect to have moved all files from the source to the archive directory of S3.
    assert len(file_util.list_files(s3_source_directory_uri)) == 0
    assert len(file_util.list_files(s3_archive_directory_uri)) == len(filenames)

    # Get files in the MoveIt server and s3 archive directory.
    files_in_moveit = mock_sftp_client.listdir(moveit_dia_outbound_path)
    files_in_s3_archive_dir = file_util.list_files(s3_archive_directory_uri)

    # Confirm that we've moved every ReferenceFile, created a StateLog record, and updated the db.
    for filename in filenames:
        file_loc = os.path.join(s3_archive_directory_uri, filename)

        ref_file = (
            local_test_db_session.query(ReferenceFile)
            .filter(ReferenceFile.file_location == file_loc)
            .one_or_none()
        )
        assert ref_file
        assert filename in files_in_s3_archive_dir
        assert filename in files_in_moveit

        # Use test_db_other_session so we query against the database instead of just the in-memory
        # cache of test_db_session.
        assert (
            local_test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
            .filter(StateLog.end_state_id == State.DIA_CLAIMANT_LIST_SUBMITTED.state_id)
            .filter(StateLog.reference_file_id == ref_file.reference_file_id)
            .scalar()
            == 1
        )


@pytest.mark.integration
def test_create_list_of_claimants(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "reductions/dia/outbound"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DIA_OUTBOUND_DIRECTORY_PATH", dest_dir)

    # Set up some claims.
    claims = ClaimFactory.create_batch(
        size=5,
        fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
        employee=factory.SubFactory(EmployeeWithFineosNumberFactory),
    )

    create_list_of_claimants(test_db_session)

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


def test_create_list_of_claimants_skips_claims_with_missing_data(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "reductions/dia/outbound"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DIA_OUTBOUND_DIRECTORY_PATH", dest_dir)

    # Set up a small number of claims.
    claims = []

    claims.append(
        ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
            employee=EmployeeWithFineosNumberFactory.create(date_of_birth=None),
        )
    )

    claims.append(
        ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
            employee=EmployeeWithFineosNumberFactory.create(fineos_customer_number=None),
        )
    )

    claims.append(
        ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.APPROVED.absence_status_id,
            employee=EmployeeWithFineosNumberFactory.create(
                tax_identifier_id=None, tax_identifier=None
            ),
        )
    )

    create_list_of_claimants(test_db_session)

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
        assert 0 == len(list(s3_file))

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


@pytest.mark.parametrize(
    "moveit_file_count",
    (
        # No files waiting for use in MoveIt.
        0,
        # Single payment list waiting for us in MoveIt.
        1,
        # We expect there to never be more than 1 file in MoveIt, but we should properly handle
        # cases when there is more than 1 file.
        3,
    ),
)
@pytest.mark.integration
def test_download_payment_list_if_none_today(
    local_initialize_factories_session,
    local_test_db_session,
    local_test_db_other_session,
    mock_s3_bucket,
    mock_sftp_client,
    setup_mock_sftp_client,
    monkeypatch,
    moveit_file_count,
):
    # Mock out S3 and MoveIt configs.
    s3_bucket_uri = f"s3://{mock_s3_bucket}"
    s3_dest_path = "reductions/dia/pending"
    moveit_pickup_path = "/DFML/DIA/Outbound"
    moveit_archive_path = "/DFML/DIA/Archive"

    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DIA_PENDING_DIRECTORY_PATH", s3_dest_path)
    monkeypatch.setenv("MOVEIT_DIA_INBOUND_PATH", moveit_pickup_path)
    monkeypatch.setenv("MOVEIT_DIA_ARCHIVE_PATH", moveit_archive_path)

    full_s3_dest_path = os.path.join(s3_bucket_uri, s3_dest_path)

    moveit_filenames = []
    for _i in range(moveit_file_count):
        filename = _random_csv_filename()
        filepath = os.path.join(moveit_pickup_path, filename)
        mock_sftp_client._add_file(filepath, "")
        moveit_filenames.append(filename)

    # Confirm that the SFTP and S3 directories contain the expected number of files before testing.
    assert len(mock_sftp_client.listdir(moveit_pickup_path)) == moveit_file_count
    assert len(mock_sftp_client.listdir(moveit_archive_path)) == 0
    assert len(file_util.list_files(full_s3_dest_path)) == 0

    download_payment_list_if_none_today(local_test_db_session)

    # Expect to have moved all files from the source to the archive directory of MoveIt.
    files_in_moveit_archive_dir = mock_sftp_client.listdir(moveit_archive_path)
    assert len(files_in_moveit_archive_dir) == moveit_file_count
    assert len(mock_sftp_client.listdir(moveit_pickup_path)) == 0

    # Expect to have saved files to S3.
    files_in_s3 = file_util.list_files(full_s3_dest_path)
    assert len(files_in_s3) == moveit_file_count

    assert (
        local_test_db_other_session.query(sqlalchemy.func.count(ReferenceFile.reference_file_id))
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id
        )
        .scalar()
        == moveit_file_count
    )

    assert (
        local_test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.DIA_PAYMENT_LIST_SAVED_TO_S3.state_id)
        .scalar()
        == moveit_file_count
    )

    # Validate details match our expectations.
    for filename in moveit_filenames:
        assert filename in files_in_moveit_archive_dir
        assert filename in files_in_s3

        file_loc = os.path.join(full_s3_dest_path, filename)

        ref_file = (
            local_test_db_session.query(ReferenceFile)
            .filter(ReferenceFile.file_location == file_loc)
            .one_or_none()
        )
        assert (
            ref_file.reference_file_type_id
            == ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id
        )

        assert (
            local_test_db_other_session.query(sqlalchemy.func.count(StateLog.state_log_id))
            .filter(StateLog.end_state_id == State.DIA_PAYMENT_LIST_SAVED_TO_S3.state_id)
            .filter(StateLog.reference_file_id == ref_file.reference_file_id)
            .scalar()
            == 1
        )


@pytest.mark.integration
def test_assert_dia_payments_are_stored_correctly(
    test_db_session, mock_s3_bucket, monkeypatch, initialize_factories_session
):
    source_directory_path = "reductions/dia/pending"
    archive_directory_path = "reductions/dia/archive"

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    monkeypatch.setenv("S3_DIA_PENDING_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DIA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)

    # Define the full paths to the directories.
    pending_directory = f"s3://{mock_s3_bucket}/{source_directory_path}"
    archive_directory = f"s3://{mock_s3_bucket}/{archive_directory_path}"

    # A new reference to a ReferenceFile
    (params, ref_file) = _get_loaded_payment_reference_file_in_s3(
        mock_s3_bucket, _random_csv_filename(), source_directory_path, 1
    )

    # Check on the file directory stats
    assert len(file_util.list_files(pending_directory)) == 1
    assert len(file_util.list_files(archive_directory)) == 0

    dia.load_new_dia_payments(test_db_session)

    # Files should have been moved.
    assert len(file_util.list_files(pending_directory)) == 0
    assert len(file_util.list_files(archive_directory)) == 1

    test_db_session.flush()

    # Expect to have loaded some rows to the database.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DiaReductionPayment.dia_reduction_payment_id)
        ).scalar()
        == 1
    )

    def parse_date(date_str):
        return datetime.strptime(date_str, "%Y%m%d").date()

    # Expect that the inserted row is what we expect.
    record = test_db_session.query(DiaReductionPayment).all()[0]
    assert record.fineos_customer_number == params[0]["DFML_ID"]
    assert str(record.award_amount) == params[0]["AWARD_AMOUNT"]
    assert record.award_code == params[0]["AWARD_CODE"]
    assert record.award_created_date == parse_date(params[0]["AWARD_CREATED_DATE"])
    assert record.award_date == parse_date(params[0]["AWARD_DATE"])
    assert record.award_id == params[0]["AWARD_ID"]
    assert record.board_no == params[0]["BOARD_NO"]
    assert record.end_date == parse_date(params[0]["END_DATE"])
    assert record.eve_created_date == parse_date(params[0]["EVE_CREATED_DATE"])
    assert record.event_description == params[0]["INS_FORM_OR_MEET"]
    assert record.event_id == params[0]["EVENT_ID"]
    assert record.start_date == parse_date(params[0]["START_DATE"])
    assert str(record.weekly_amount) == params[0]["WEEKLY_AMOUNT"]

    # Expect to have created a StateLog for each ReferenceFile.
    assert (
        test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.DIA_PAYMENT_LIST_SAVED_TO_DB.state_id)
        .scalar()
        == 1
    )


@pytest.mark.integration
def test_load_new_dia_payments_sucessfully(
    test_db_session, mock_s3_bucket, monkeypatch, initialize_factories_session
):
    source_directory_path = "reductions/dia/pending"
    archive_directory_path = "reductions/dia/archive"

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    monkeypatch.setenv("S3_DIA_PENDING_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DIA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)

    # Define the full paths to the directories.
    pending_directory = f"s3://{mock_s3_bucket}/{source_directory_path}"
    archive_directory = f"s3://{mock_s3_bucket}/{archive_directory_path}"

    # Create some number of ReferenceFiles
    total_row_count = 0
    ref_file_count = random.randint(1, 5)
    for _i in range(ref_file_count):
        row_count = random.randint(1, 5)
        total_row_count = total_row_count + row_count
        _get_loaded_payment_reference_file_in_s3(
            mock_s3_bucket, _random_csv_filename(), source_directory_path, row_count
        )

    # Expect no rows in the database before.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DiaReductionPayment.dia_reduction_payment_id)
        ).scalar()
        == 0
    )

    # Expect files to be in pending directory before.
    assert len(file_util.list_files(pending_directory)) == ref_file_count
    assert len(file_util.list_files(archive_directory)) == 0

    dia.load_new_dia_payments(test_db_session)

    # Expect to have loaded some rows to the database.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DiaReductionPayment.dia_reduction_payment_id)
        ).scalar()
        == total_row_count
    )

    # Expect files to be in archive directory after.
    assert len(file_util.list_files(pending_directory)) == 0
    assert len(file_util.list_files(archive_directory)) == ref_file_count

    # Expect to have created a StateLog for each ReferenceFile.
    assert (
        test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.DIA_PAYMENT_LIST_SAVED_TO_DB.state_id)
        .scalar()
        == ref_file_count
    )


@pytest.mark.integration
def test_load_new_dia_payments_handles_duplicates(
    test_db_session, mock_s3_bucket, monkeypatch, initialize_factories_session
):
    source_directory_path = "reductions/dia/pending"
    archive_directory_path = "reductions/dia/archive"

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    monkeypatch.setenv("S3_DIA_PENDING_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DIA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)

    # Define the full paths to the directories.
    pending_directory = f"s3://{mock_s3_bucket}/{source_directory_path}"
    archive_directory = f"s3://{mock_s3_bucket}/{archive_directory_path}"

    # Create file with duplicate row
    file_one_rows = [_get_valid_dia_payment_data() for _ in range(3)]
    dupe_data = file_one_rows[0]

    file_one_rows.append(dupe_data)
    _make_loaded_payment_reference_file_in_s3(
        mock_s3_bucket, _random_csv_filename(), source_directory_path, file_one_rows
    )

    # Create second file with data that also exists in first file
    file_two_rows = [_get_valid_dia_payment_data() for _ in range(3)]
    file_two_rows.append(dupe_data)
    _make_loaded_payment_reference_file_in_s3(
        mock_s3_bucket, _random_csv_filename(), source_directory_path, file_two_rows
    )

    total_rows = len(file_one_rows) + len(file_two_rows)
    unique_rows = total_rows - 2

    # Expect no rows in the database before.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DiaReductionPayment.dia_reduction_payment_id)
        ).scalar()
        == 0
    )

    # Expect files to be in pending directory before.
    assert len(file_util.list_files(pending_directory)) == 2
    assert len(file_util.list_files(archive_directory)) == 0

    dia.load_new_dia_payments(test_db_session)

    # Expect to have loaded some rows to the database.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DiaReductionPayment.dia_reduction_payment_id)
        ).scalar()
        == unique_rows
    )

    assert (
        test_db_session.query(DiaReductionPayment)
        .filter(
            DiaReductionPayment.fineos_customer_number == dupe_data["DFML_ID"],
            DiaReductionPayment.award_date == dupe_data["AWARD_DATE"],
        )
        .count()
        == 1
    )

    # Expect files to be in archive directory after.
    assert len(file_util.list_files(pending_directory)) == 0
    assert len(file_util.list_files(archive_directory)) == 2

    # Expect to have created a StateLog for each ReferenceFile.
    assert (
        test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.DIA_PAYMENT_LIST_SAVED_TO_DB.state_id)
        .scalar()
        == 2
    )
