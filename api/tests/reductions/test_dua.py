import datetime
import os
import random
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

import boto3
import factory
import faker
import pytest
import sqlalchemy

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.reductions.common as reductions_common
import massgov.pfml.reductions.dua as dua
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.datetime as datetime_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    AbsenceStatus,
    DuaReductionPayment,
    DuaReductionPaymentReferenceFile,
    LatestStateLog,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import (
    ClaimFactory,
    DuaReductionPaymentFactory,
    EmployeeFactory,
    EmployeeWithFineosNumberFactory,
    ReferenceFileFactory,
)
from massgov.pfml.util.batch.log import LogEntry

fake = faker.Faker()

EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS = list(
    dua.Constants.DUA_PAYMENT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP.keys()
)

DUA_PAYMENT_LIST_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%Y%m%d"),
}


def _dua_csv_filename() -> str:
    # Random filename. Types of characters and length of filename are not meaningful.
    return f"DUA_DFML_{random.randint(20210000000000, 22000000000000)}.csv"


def _create_dua_payment_list_reference_file(
    dir: str, file_location: Optional[str] = None
) -> ReferenceFile:
    if file_location is None:
        file_location = os.path.join(dir, _dua_csv_filename())

    return ReferenceFileFactory(
        file_location=file_location,
        reference_file_type_id=ReferenceFileType.DUA_PAYMENT_LIST.reference_file_type_id,
    )


def _create_other_reference_file(dir: str) -> ReferenceFile:
    file_location = os.path.join(dir, _dua_csv_filename())

    other_file_types_expected_in_same_s3_directory = [
        ReferenceFileType.DUA_CLAIMANT_LIST.reference_file_type_id,
        ReferenceFileType.DIA_CLAIMANT_LIST.reference_file_type_id,
        ReferenceFileType.DIA_PAYMENT_LIST.reference_file_type_id,
    ]
    reference_file_type_id = random.choice(other_file_types_expected_in_same_s3_directory)

    return ReferenceFileFactory(
        file_location=file_location, reference_file_type_id=reference_file_type_id,
    )


def _random_date_in_past_year() -> date:
    return date.today() - timedelta(days=fake.random_int(min=0, max=365))


def _get_valid_dua_payment_data() -> Dict[str, Any]:
    end_date = _random_date_in_past_year()
    begin_date = end_date - timedelta(days=365)  # Doesn't need to be exact. We don't check it.

    # Make sure customer number and FEIN are unique for each returned dict.
    return {
        "fineos_customer_number": str(fake.unique.random_int(min=1000, max=9999)),
        "employer_fein": str(fake.unique.random_int(min=100_000, max=999_999)),
        "payment_date": _random_date_in_past_year(),
        "request_week_begin_date": _random_date_in_past_year(),
        "gross_payment_amount_cents": fake.random_int(min=100, max=999),
        "payment_amount_cents": fake.random_int(min=10_000, max=99_999),
        "fraud_indicator": random.choice(["Y", None, None]),  # 1 in 3 chance of a fraud indicator.
        "benefit_year_begin_date": begin_date,
        "benefit_year_end_date": end_date,
    }


def _get_loaded_reference_file_in_s3(
    mock_s3_bucket, filename, source_directory_path, row_count, force_file_error=False
):
    # Create the ReferenceFile.
    pending_directory = os.path.join(f"s3://{mock_s3_bucket}", source_directory_path)
    source_filepath = os.path.join(pending_directory, filename)
    ref_file = _create_dua_payment_list_reference_file("", source_filepath)

    # Create some number of valid rows for our input file.
    body = ",".join(EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS) + "\n"
    for _i in range(row_count):
        db_data = _get_valid_dua_payment_data()
        csv_row = csv_util.encode_row(db_data, DUA_PAYMENT_LIST_ENCODERS)
        extra = ",123," if force_file_error else ""
        body = body + ",".join(list(csv_row.values())) + extra + "\n"

    # Add rows to the file in our mock S3 bucket.
    s3_key = os.path.join(source_directory_path, filename)
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=s3_key, Body=body)

    return ref_file


@pytest.mark.parametrize(
    "pending_ref_file_count",
    ((0), (1), (random.randint(2, 10)),),
    ids=["no_file", "one_file", "many_files"],
)
def test_get_pending_dua_payment_reference_files(
    initialize_factories_session, test_db_session, pending_ref_file_count
):
    pending_directory = "s3://test_bucket/path/to/dir"

    # Create some small random number of other ReferenceFiles that will be in the same directory.
    for _i in range(random.randint(1, 10)):
        _create_other_reference_file(pending_directory)

    for _i in range(pending_ref_file_count):
        _create_dua_payment_list_reference_file(pending_directory)

    ref_files = dua._get_pending_dua_payment_reference_files(pending_directory, test_db_session)
    assert len(ref_files) == pending_ref_file_count


@pytest.mark.parametrize(
    "existing_db_record_count, new_rows, duplicate_rows",
    (
        # Existing values in the database but nothing in the input file.
        (random.randint(2, 10), [], []),
        # General case with some existing, some new, and some duplicates.
        (
            random.randint(1, 5),
            [_get_valid_dua_payment_data() for _i in range(random.randint(1, 5))],
            [_get_valid_dua_payment_data() for _i in range(random.randint(1, 5))],
        ),
        # General case with no existing rows, some new, and some duplicates.
        (
            0,
            [_get_valid_dua_payment_data() for _i in range(random.randint(1, 5))],
            [_get_valid_dua_payment_data() for _i in range(random.randint(1, 5))],
        ),
        # Some rows in the database and only duplicates in the input file.
        (
            random.randint(1, 5),
            [],
            [_get_valid_dua_payment_data() for _i in range(random.randint(1, 5))],
        ),
        # Some rows in the database and only a single new row with no benefit_year_end_date.
        (
            random.randint(1, 5),
            [{**_get_valid_dua_payment_data(), "benefit_year_end_date": None}],
            [],
        ),
        # Some rows in the database and two rows in the input file (one new, one duplicate) that
        # have all optional values empty.
        (
            random.randint(1, 5),
            [
                {
                    **_get_valid_dua_payment_data(),
                    "employer_fein": None,
                    "payment_date": None,
                    "request_week_begin_date": None,
                    "gross_payment_amount_cents": None,
                    "payment_amount_cents": None,
                    "fraud_indicator": None,
                    "benefit_year_begin_date": None,
                    "benefit_year_end_date": None,
                }
            ],
            [
                {
                    **_get_valid_dua_payment_data(),
                    "employer_fein": None,
                    "payment_date": None,
                    "request_week_begin_date": None,
                    "gross_payment_amount_cents": None,
                    "payment_amount_cents": None,
                    "fraud_indicator": None,
                    "benefit_year_begin_date": None,
                    "benefit_year_end_date": None,
                }
            ],
        ),
    ),
    ids=[
        "some_existing-no_new-no_dupes",
        "some_existing-some_new-some_dupes",
        "no_existing-some_new-some_dupes",
        "some_existing-no_new-some_dupes",
        "some_existing-one_new-no_dupes",
        "some_existing-one_new-one_dupe",
    ],
)
def test_load_new_rows_from_file_success(
    dua_reduction_payment_unique_index,
    test_db_session,
    existing_db_record_count,
    new_rows,
    duplicate_rows,
):
    csv_file = tempfile.TemporaryFile(mode="w+")
    csv_file.write(",".join(EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS) + "\n")

    for _i in range(existing_db_record_count):
        data = _get_valid_dua_payment_data()
        dua_reduction_payment = DuaReductionPayment(**data)
        test_db_session.add(dua_reduction_payment)
    test_db_session.commit()

    for db_data in new_rows:
        csv_row = csv_util.encode_row(db_data, DUA_PAYMENT_LIST_ENCODERS)
        csv_file.write(",".join(list(csv_row.values())) + "\n")

    for db_data in duplicate_rows:
        csv_row = csv_util.encode_row(db_data, DUA_PAYMENT_LIST_ENCODERS)
        csv_file.write(",".join(list(csv_row.values())) + "\n")
        dua_reduction_payment = DuaReductionPayment(**db_data)
        test_db_session.add(dua_reduction_payment)
    test_db_session.commit()

    total_row_count_before = existing_db_record_count + len(duplicate_rows)
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == total_row_count_before
    )

    csv_file.seek(0)

    dua._load_new_rows_from_file(csv_file, test_db_session)
    test_db_session.commit()

    total_row_count_after = total_row_count_before + len(new_rows)
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == total_row_count_after
    )

    if len(new_rows) > 0:
        random_new_row = random.choice(new_rows)
        assert len(dua._get_matching_dua_reduction_payments(random_new_row, test_db_session)) > 0

    if len(duplicate_rows) > 0:
        random_duplicate_row = random.choice(duplicate_rows)
        assert (
            len(dua._get_matching_dua_reduction_payments(random_duplicate_row, test_db_session)) > 0
        )


def test_load_new_rows_from_file_dua_example(dua_reduction_payment_unique_index, test_db_session):
    data_row_count = 180
    filepath = os.path.join(
        os.path.dirname(__file__), "test_files", "DUA_DFML_20210128094801535.csv"
    )
    csv_file = file_util.open_stream(filepath)

    # Expect table to be empty before we run this function.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == 0
    )

    dua._load_new_rows_from_file(csv_file, test_db_session)

    # Expect to have added all rows to the database.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == data_row_count
    )


@pytest.mark.parametrize(
    "headers, csv_rows",
    (
        # Incorrect field type.
        (
            EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS,
            [{**_get_valid_dua_payment_data(), "payment_date": "STRING INSTEAD OF DATE"}],
        ),
        # Single invalid row prevents previous valid rows from being added to the database.
        (
            EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS,
            [
                _get_valid_dua_payment_data(),
                _get_valid_dua_payment_data(),
                _get_valid_dua_payment_data(),
                {**_get_valid_dua_payment_data(), "payment_date": "STRING INSTEAD OF DATE"},
            ],
        ),
        # Invalid headers but valid rows.
        (
            ["some", "invalid", "column", "names"],
            [_get_valid_dua_payment_data(), _get_valid_dua_payment_data()],
        ),
        # Extra column in the file.
        (
            EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS + ["addl_field"],
            [{**_get_valid_dua_payment_data(), "addl_field": "additional value"}],
        ),
    ),
)
def test_load_new_rows_from_file_error(
    dua_reduction_payment_unique_index, test_db_session, headers, csv_rows
):
    # Write to the csv_file directly instead of through a csv.DictWriter or similar so that we can
    # insert invalid rows into the file.
    csv_file = tempfile.TemporaryFile(mode="w+")
    csv_file.write(",".join(headers) + "\n")

    for csv_row in csv_rows:
        stringified_dict = csv_util.encode_row(csv_row, DUA_PAYMENT_LIST_ENCODERS)
        csv_file.write(",".join(list(stringified_dict.values())) + "\n")

    csv_file.seek(0)

    with pytest.raises(Exception):
        with test_db_session.begin_nested():
            dua._load_new_rows_from_file(csv_file, test_db_session)

    # We do not expect any rows to be added to the database when _load_new_rows_from_file() fails.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == 0
    )


def test_load_new_dua_payments_success(
    dua_reduction_payment_unique_index, test_db_session, mock_s3_bucket, monkeypatch
):
    source_directory_path = "reductions/dua/pending"
    archive_directory_path = "reductions/dua/archive"

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    monkeypatch.setenv("S3_DUA_PENDING_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DUA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)

    # Define the full paths to the directories.
    pending_directory = f"s3://{mock_s3_bucket}/{source_directory_path}"
    archive_directory = f"s3://{mock_s3_bucket}/{archive_directory_path}"

    # Create some number of ReferenceFiles
    total_row_count = 0
    ref_file_count = random.randint(1, 5)
    for _i in range(ref_file_count):
        row_count = random.randint(1, 5)
        total_row_count = total_row_count + row_count
        _get_loaded_reference_file_in_s3(
            mock_s3_bucket, _dua_csv_filename(), source_directory_path, row_count
        )

    # Expect no rows in the database before.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == 0
    )

    # Expect files to be in pending directory before.
    assert len(file_util.list_files(pending_directory)) == ref_file_count
    assert len(file_util.list_files(archive_directory)) == 0

    log_entry = LogEntry(test_db_session, "Test")
    load_result = dua.load_new_dua_payments(test_db_session, log_entry)
    assert load_result.found_pending_files is True

    # Expect to have loaded some rows to the database.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == total_row_count
    )

    # Expect files to be in archive directory after.
    assert len(file_util.list_files(pending_directory)) == 0
    assert len(file_util.list_files(archive_directory)) == ref_file_count

    # Expect to have created a StateLog for each ReferenceFile.
    assert (
        test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.DUA_PAYMENT_LIST_SAVED_TO_DB.state_id)
        .scalar()
        == ref_file_count
    )


def test_load_new_dua_payments_error(
    dua_reduction_payment_unique_index, test_db_session, mock_s3_bucket, monkeypatch
):
    source_directory_path = "reductions/dua/pending"
    error_directory_path = "reductions/dfml/error"

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    monkeypatch.setenv("S3_DUA_PENDING_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DUA_ERROR_DIRECTORY_PATH", error_directory_path)

    # Define the full paths to the directories.
    pending_directory = f"s3://{mock_s3_bucket}/{source_directory_path}"
    error_directory = f"s3://{mock_s3_bucket}/{error_directory_path}"

    # Create some number of ReferenceFiles
    total_row_count = 0
    ref_file_count = random.randint(1, 5)
    for _i in range(ref_file_count):
        row_count = random.randint(1, 5)
        total_row_count = total_row_count + row_count

        _get_loaded_reference_file_in_s3(
            mock_s3_bucket,
            _dua_csv_filename(),
            source_directory_path,
            row_count,
            force_file_error=True,
        )

    # Expect no rows in the database before.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == 0
    )

    # Expect files to be in pending directory before.
    assert len(file_util.list_files(pending_directory)) == ref_file_count
    assert len(file_util.list_files(error_directory)) == 0

    log_entry = LogEntry(test_db_session, "Test")
    load_result = dua.load_new_dua_payments(test_db_session, log_entry)
    # We still found pending files, even if they errored.
    assert load_result.found_pending_files is True

    # Expect files to be in error directory after.
    assert len(file_util.list_files(pending_directory)) == 0
    assert len(file_util.list_files(error_directory)) == ref_file_count

    # Expect to have created a StateLog for each ReferenceFile.
    assert (
        test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.DUA_PAYMENT_LIST_ERROR_SAVE_TO_DB.state_id)
        .scalar()
        == ref_file_count
    )


def test_load_dua_payment_from_reference_file_success(
    dua_reduction_payment_unique_index, test_db_session, mock_s3_bucket
):
    # Create the ReferenceFile.
    filename = _dua_csv_filename()
    source_directory_path = "path/to/source"
    row_count = random.randint(1, 5)
    ref_file = _get_loaded_reference_file_in_s3(
        mock_s3_bucket, filename, source_directory_path, row_count
    )

    pending_directory = f"s3://{mock_s3_bucket}/{source_directory_path}"

    # Define the destination file paths.
    archive_directory = f"s3://{mock_s3_bucket}/path/to/archive"
    dest_filepath = os.path.join(archive_directory, filename)

    # Expect no rows in the database before.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == 0
    )

    # Expect file to be in pending directory before.
    assert file_util.list_files(pending_directory) == [filename]
    assert file_util.list_files(archive_directory) == []

    dua._load_dua_payment_from_reference_file(ref_file, archive_directory, test_db_session)

    # Expect to have loaded some rows to the database.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == row_count
    )

    # Expect file to be in archive directory after.
    assert file_util.list_files(pending_directory) == []
    assert file_util.list_files(archive_directory) == [filename]

    # Expect to have updated the ReferenceFile's file location.
    assert ref_file.file_location == dest_filepath

    # Expect to have created a StateLog for this ReferenceFile.
    assert (
        state_log_util.get_latest_state_log_in_end_state(
            ref_file, State.DUA_PAYMENT_LIST_SAVED_TO_DB, test_db_session
        )
        is not None
    )


def test_load_dua_payment_from_reference_file_existing_dest_filepath_error(
    dua_reduction_payment_unique_index, test_db_session, mock_s3_bucket
):
    # Create the ReferenceFile.
    filename = _dua_csv_filename()
    source_directory_path = "path/to/source"
    row_count = random.randint(1, 5)
    ref_file = _get_loaded_reference_file_in_s3(
        mock_s3_bucket, filename, source_directory_path, row_count
    )

    # Define the destination file paths.
    archive_directory = f"s3://{mock_s3_bucket}/path/to/archive"
    dest_filepath = os.path.join(archive_directory, filename)

    # Create the ReferenceFile that will cause the conflict after the operation.
    _create_dua_payment_list_reference_file("", dest_filepath)

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        with test_db_session.begin_nested():
            dua._load_dua_payment_from_reference_file(ref_file, archive_directory, test_db_session)

    # Expect no rows in the database after because the reference_file.file_location conflict will
    # prevent the database from committing the changes.
    assert (
        test_db_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == 0
    )

    # Expect no StateLog to have been created.
    assert (
        test_db_session.query(sqlalchemy.func.count(LatestStateLog.latest_state_log_id)).scalar()
        == 0
    )


def test_copy_to_sftp_and_archive_s3_files(
    initialize_factories_session,
    test_db_session,
    mock_s3_bucket,
    mock_sftp_client,
    setup_mock_sftp_client,
    monkeypatch,
):
    # Mock out S3 and MoveIt configs.
    s3_bucket_uri = f"s3://{mock_s3_bucket}"
    source_directory_path = "reductions/dua/outbound"
    archive_directory_path = "reductions/dua/archive"
    moveit_dua_outbound_path = "/DFML/DUA/Inbound"

    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DUA_OUTBOUND_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DUA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)
    monkeypatch.setenv("MOVEIT_SFTP_URI", "sftp://foo@bar.com")
    monkeypatch.setenv("MOVEIT_SSH_KEY", "foo")
    monkeypatch.setenv("MOVEIT_DUA_OUTBOUND_PATH", moveit_dua_outbound_path)

    filenames = []
    file_count = random.randint(1, 8)
    for _i in range(file_count):
        filename = _dua_csv_filename()
        row_count = random.randint(1, 5)
        ref_file = _get_loaded_reference_file_in_s3(
            mock_s3_bucket, filename, source_directory_path, row_count
        )
        ref_file.reference_file_type_id = ReferenceFileType.DUA_CLAIMANT_LIST.reference_file_type_id

        filenames.append(filename)

    # Save the changes to the reference file types.
    test_db_session.commit()

    s3_source_directory_uri = os.path.join(s3_bucket_uri, source_directory_path)
    s3_archive_directory_uri = os.path.join(s3_bucket_uri, archive_directory_path)
    assert len(file_util.list_files(s3_source_directory_uri)) == len(filenames)
    assert len(file_util.list_files(s3_archive_directory_uri)) == 0

    dua.copy_claimant_list_to_moveit(test_db_session)

    # Expect to have moved all files from the source to the archive directory of S3.
    assert len(file_util.list_files(s3_source_directory_uri)) == 0
    assert len(file_util.list_files(s3_archive_directory_uri)) == len(filenames)

    # Get files in the MoveIt server and s3 archive directory.
    files_in_moveit = mock_sftp_client.listdir(moveit_dua_outbound_path)
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

        assert (
            test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
            .filter(StateLog.end_state_id == State.DUA_CLAIMANT_LIST_SUBMITTED.state_id)
            .filter(StateLog.reference_file_id == ref_file.reference_file_id)
            .scalar()
            == 1
        )


@pytest.mark.parametrize(
    "claims_count",
    (
        # No relevant claims
        0,
        # General case: Some small number of valid relevant claims.
        5,
    ),
)
def test_format_claimants_for_dua_claimant_list_expected_structure_is_generated(claims_count):
    employees = EmployeeWithFineosNumberFactory.build_batch(size=claims_count)

    formatted_rows = dua._format_claimants_for_dua_claimant_list(employees)
    expected_rows = [
        {
            dua.Constants.CASE_ID_FIELD: employee.fineos_customer_number,
            dua.Constants.BENEFIT_START_DATE_FIELD: dua.Constants.TEMPORARY_BENEFIT_START_DATE,
            dua.Constants.SSN_FIELD: employee.tax_identifier.tax_identifier.replace("-", ""),
        }
        for employee in employees
    ]

    assert len(formatted_rows) == len(employees)
    assert formatted_rows == expected_rows


def test_format_claimants_for_dua_claimant_list_null_fineos_customer_number_id():
    employees_no_fineos_id = EmployeeFactory.build_batch(size=3, fineos_customer_number=None)
    employees_no_tax_id = EmployeeFactory.build_batch(
        size=3, tax_identifier=None, tax_identifier_id=None
    )

    employees = employees_no_fineos_id + employees_no_tax_id

    formatted_rows = dua._format_claimants_for_dua_claimant_list(employees)

    assert len(formatted_rows) == 0


@pytest.mark.parametrize(
    "claims_count",
    (
        # No relevant claims
        0,
        # General case: Some small number of relevant claims.
        3,
    ),
)
def test_create_list_of_claimants_uploads_csv_to_s3_and_adds_state_log(
    initialize_factories_session, test_db_session, mock_s3_bucket, monkeypatch, claims_count,
):
    # Set up environment variables.
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "pfml/outbound-dir"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DUA_OUTBOUND_DIRECTORY_PATH", dest_dir)

    claims = ClaimFactory.create_batch(
        size=claims_count,
        employee=factory.SubFactory(EmployeeWithFineosNumberFactory),
        fineos_absence_status_id=factory.Iterator(reductions_common.OUTBOUND_STATUSES),
    )

    # ReferenceFile.file_location uniqueness errors are possible but unlikely because the
    # file_location values will include the current time in hours and minutes and we don't expect
    # to run this function more than once each day. Not adding a test.
    assert (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DUA_CLAIMANT_LIST.reference_file_type_id
        )
        .all()
    ) == []

    log_entry = LogEntry(test_db_session, "Test")
    dua.create_list_of_claimants(test_db_session, log_entry)

    # We always expect this function to create a single DUA_CLAIMANT_LIST every time it runs.
    claim_files_created_count = 1

    ref_file = (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DUA_CLAIMANT_LIST.reference_file_type_id
        )
        .all()
    )
    state_log = (
        test_db_session.query(StateLog)
        .filter_by(end_state_id=State.DUA_CLAIMANT_LIST_CREATED.state_id)
        .all()
    )

    # Expect a ReferenceFile and StateLog entry for each claim file created.
    assert len(ref_file) == claim_files_created_count
    assert len(state_log) == claim_files_created_count

    # StateLog is properly associated with ReferenceFile.
    assert state_log[0].reference_file == ref_file[0]

    s3 = boto3.client("s3")

    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert len(object_list) == claim_files_created_count

    object_in_s3 = object_list[0]
    dest_filepath = os.path.join(s3_bucket_uri, object_in_s3["Key"])
    assert dest_filepath == ref_file[0].file_location

    csv_file_lines = list(file_util.read_file_lines(dest_filepath))
    header_line = csv_file_lines.pop(0)

    # The CSV file should always have an header in it
    assert header_line == ",".join(dua.Constants.CLAIMANT_LIST_FIELDS)

    # We've removed the header line so the line counts should match.
    assert len(csv_file_lines) == claims_count

    for i, csv_line in enumerate(csv_file_lines):
        claim = claims[i]
        # This manual check against the CSV line is to make sure that the columns and
        # data aren't misaligned. A parser can unintentionally give a false positive here.
        assert csv_line == ",".join(
            [
                claim.employee.fineos_customer_number,
                claim.employee.tax_identifier.tax_identifier.replace("-", ""),
                dua.Constants.TEMPORARY_BENEFIT_START_DATE,
            ]
        )


@pytest.mark.parametrize(
    "moveit_file_count",
    (
        # No files waiting for use in MoveIt.
        (0),
        # Single payment list waiting for us in MoveIt.
        (1),
        # We expect there to never be more than 1 file in MoveIt, but we should properly handle
        # cases when there is more than 1 file.
        (random.randint(2, 5)),
    ),
    ids=["no_files", "one_waiting", "multiple_files"],
)
def test_download_payment_list_from_moveit(
    initialize_factories_session,
    test_db_session,
    mock_s3_bucket,
    mock_sftp_client,
    setup_mock_sftp_client,
    monkeypatch,
    moveit_file_count,
):
    # Mock out S3 and MoveIt configs.
    s3_bucket_uri = f"s3://{mock_s3_bucket}"
    s3_dest_path = "reductions/dua/pending"
    moveit_pickup_path = "/DFML/DUA/Outbound"
    moveit_archive_path = "/DFML/DUA/Archive"

    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DUA_PENDING_DIRECTORY_PATH", s3_dest_path)
    monkeypatch.setenv("MOVEIT_SFTP_URI", "sftp://foo@bar.com")
    monkeypatch.setenv("MOVEIT_SSH_KEY", "foo")
    monkeypatch.setenv("MOVEIT_DUA_INBOUND_PATH", moveit_pickup_path)
    monkeypatch.setenv("MOVEIT_DUA_ARCHIVE_PATH", moveit_archive_path)

    full_s3_dest_path = os.path.join(s3_bucket_uri, s3_dest_path)

    moveit_filenames = []
    for _i in range(moveit_file_count):
        filename = _dua_csv_filename()
        filepath = os.path.join(moveit_pickup_path, filename)
        mock_sftp_client._add_file(filepath, "")
        moveit_filenames.append(filename)

    # Add an unrelated file to the same directory
    claimant_demographics_filename = "DUA_DFML_CLM_DEM_20210827120544765.csv"
    claimant_demographics_path = os.path.join(moveit_pickup_path, claimant_demographics_filename)
    mock_sftp_client._add_file(claimant_demographics_path, "")

    # Confirm that the SFTP and S3 directories contain the expected number of files before testing.
    assert len(mock_sftp_client.listdir(moveit_pickup_path)) == moveit_file_count + 1
    assert len(mock_sftp_client.listdir(moveit_archive_path)) == 0
    assert len(file_util.list_files(full_s3_dest_path)) == 0

    log_entry = LogEntry(test_db_session, "Test")
    dua.download_payment_list_from_moveit(test_db_session, log_entry)

    # Expect to have moved all files from the source to the archive directory of MoveIt.
    files_in_moveit_archive_dir = mock_sftp_client.listdir(moveit_archive_path)
    assert len(files_in_moveit_archive_dir) == moveit_file_count

    # Expect to have saved files to S3.
    files_in_s3 = file_util.list_files(full_s3_dest_path)
    assert len(files_in_s3) == moveit_file_count

    # Expect the unrelated file has not moved
    files_in_moveit_pickup_dir = mock_sftp_client.listdir(moveit_pickup_path)
    assert len(files_in_moveit_pickup_dir) == 1

    assert claimant_demographics_filename not in files_in_moveit_archive_dir
    assert claimant_demographics_filename not in files_in_s3
    claimant_demographics_file_loc = os.path.join(full_s3_dest_path, claimant_demographics_filename)

    assert (
        test_db_session.query(ReferenceFile)
        .filter(ReferenceFile.file_location == claimant_demographics_file_loc)
        .one_or_none()
    ) is None

    assert (
        test_db_session.query(sqlalchemy.func.count(ReferenceFile.reference_file_id))
        .filter(
            ReferenceFile.reference_file_type_id
            == ReferenceFileType.DUA_PAYMENT_LIST.reference_file_type_id
        )
        .scalar()
        == moveit_file_count
    )

    assert (
        test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
        .filter(StateLog.end_state_id == State.DUA_PAYMENT_LIST_SAVED_TO_S3.state_id)
        .scalar()
        == moveit_file_count
    )

    # Validate details match our expectations.
    for filename in moveit_filenames:
        assert filename in files_in_moveit_archive_dir
        assert filename in files_in_s3

        file_loc = os.path.join(full_s3_dest_path, filename)

        ref_file = (
            test_db_session.query(ReferenceFile)
            .filter(ReferenceFile.file_location == file_loc)
            .one_or_none()
        )
        assert (
            ref_file.reference_file_type_id
            == ReferenceFileType.DUA_PAYMENT_LIST.reference_file_type_id
        )

        assert (
            test_db_session.query(sqlalchemy.func.count(StateLog.state_log_id))
            .filter(StateLog.end_state_id == State.DUA_PAYMENT_LIST_SAVED_TO_S3.state_id)
            .filter(StateLog.reference_file_id == ref_file.reference_file_id)
            .scalar()
            == 1
        )


def test_generate_reduction_payment_report_information_optional_fields_empty(
    initialize_factories_session, test_db_session
):
    # Set one of the optional fields to None.
    dua_reduction_payment = DuaReductionPaymentFactory.create(created_at=datetime_util.utcnow())

    dua_reduction_payment.request_week_begin_date = None
    employee = EmployeeFactory.create(
        fineos_customer_number=dua_reduction_payment.fineos_customer_number
    )
    claim = ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id, employee=employee
    )

    # Expect that this will not raise an error.
    formatted_rows = dua._format_reduction_payments_for_report([[dua_reduction_payment, claim]])

    assert formatted_rows[0][dua.Constants.RQST_WK_DT_OUTBOUND_DFML_REPORT_FIELD] == ""


def test_generate_reduction_payment_report_information_with_no_new_payments():
    no_reduction_payments = []
    report = dua._format_reduction_payments_for_report(no_reduction_payments)

    for info in report:
        assert info.keys() == dua.Constants.DFML_REPORT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP.keys()
        for _k, v in info.items():
            assert v == "NO NEW PAYMENTS"


def test_convert_cent_to_dollars():
    assert dua._convert_cent_to_dollars(123456) == Decimal("1234.56")
    assert dua._convert_cent_to_dollars(256) == Decimal("2.56")
    assert dua._convert_cent_to_dollars(12) == Decimal("0.12")
    assert dua._convert_cent_to_dollars(5) == Decimal("0.05")
    assert dua._convert_cent_to_dollars(0) == Decimal("0.0")
    assert dua._convert_cent_to_dollars(None) == Decimal("0.0")
    assert dua._convert_cent_to_dollars() == Decimal("0.0")


def test_generate_reduction_payment_report_information_with_payments(
    initialize_factories_session, test_db_session
):
    dua_reduction_payment = DuaReductionPaymentFactory.create(created_at=datetime_util.utcnow())
    employee = EmployeeFactory.create(
        fineos_customer_number=dua_reduction_payment.fineos_customer_number
    )
    claim = ClaimFactory.create(
        fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
        employee_id=employee.employee_id,
        absence_period_start_date=datetime.date(2019, 3, 19),
        absence_period_end_date=datetime.date(2019, 3, 21),
        created_at=datetime.date(2019, 4, 1),
    )
    report = dua._format_reduction_payments_for_report([[dua_reduction_payment, claim]])

    # We hard-code this report's information for simplicity.
    expected_report = {
        "CUSTOMER_ID": dua_reduction_payment.fineos_customer_number,
        "PAYMENT_DATE": dua_reduction_payment.payment_date.strftime(
            dua.Constants.PAYMENT_REPORT_TIME_FORMAT
        ),
        "BENEFIT_WEEK_START_DATE": dua_reduction_payment.request_week_begin_date.strftime(
            dua.Constants.PAYMENT_REPORT_TIME_FORMAT
        ),
        "GROSS_PAYMENT_AMOUNT": dua._convert_cent_to_dollars(
            dua_reduction_payment.gross_payment_amount_cents
        ),
        "NET_PAYMENT_AMOUNT": dua._convert_cent_to_dollars(
            dua_reduction_payment.payment_amount_cents
        ),
        "FRAUD_IND": dua_reduction_payment.fraud_indicator,
        "BYB_DT": dua_reduction_payment.benefit_year_begin_date.strftime(
            dua.Constants.PAYMENT_REPORT_TIME_FORMAT
        ),
        "BYE_DT": dua_reduction_payment.benefit_year_end_date.strftime(
            dua.Constants.PAYMENT_REPORT_TIME_FORMAT
        ),
        "DATE_PAYMENT_ADDED_TO_REPORT": dua_reduction_payment.created_at.strftime(
            dua.Constants.PAYMENT_REPORT_TIME_FORMAT
        ),
        "ABSENCE_CASE_ID": claim.fineos_absence_id,
        "ABSENCE_CASE_STATUS": claim.fineos_absence_status.absence_status_description,
        "ABSENCE_PERIOD_START_DATE": "03/19/2019",
        "ABSENCE_PERIOD_END_DATE": "03/21/2019",
    }

    assert report[0] == expected_report


def test_create_report_new_dua_payments_to_dfml(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "reductions/dfml/outbound"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DFML_OUTBOUND_DIRECTORY_PATH", dest_dir)

    log_entry = LogEntry(test_db_session, "Test")
    # Build up payment records
    new_reduction_payments = DuaReductionPaymentFactory.create_batch(
        size=5, created_at=datetime_util.utcnow()
    )

    # Insert entries older than 90 days to test if they are ignored.
    old_reduction_payments = DuaReductionPaymentFactory.create_batch(
        size=2, created_at=datetime_util.utcnow() - timedelta(days=91)
    )

    reduction_payments = new_reduction_payments + old_reduction_payments

    employees = [
        EmployeeFactory.create(fineos_customer_number=reduction_payment.fineos_customer_number)
        for reduction_payment in reduction_payments
    ]
    [
        ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
            created_at=datetime_util.utcnow(),
            employee=employee,
        )
        for employee in employees
    ]

    dua.create_report_new_dua_payments_to_dfml(test_db_session, log_entry)

    # Expect that the file to appear in the mock_s3_bucket.
    s3 = boto3.client("s3")

    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    assert len(object_list) == 1
    dest_filepath_prefix = os.path.join(dest_dir, dua.Constants.PAYMENT_LIST_FILENAME_PREFIX)
    assert object_list[0]["Key"].startswith(dest_filepath_prefix)

    ref_file = (
        test_db_session.query(ReferenceFile)
        .filter_by(
            reference_file_type_id=ReferenceFileType.DUA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id
        )
        .all()
    )
    state_log = (
        test_db_session.query(StateLog)
        .filter_by(end_state_id=State.DUA_REPORT_FOR_DFML_CREATED.state_id)
        .all()
    )

    assert len(ref_file) == 1
    assert len(state_log) == 1
    assert ref_file[0].file_location == os.path.join(s3_bucket_uri, object_list[0]["Key"])

    for payment in new_reduction_payments:
        _ref_file = ref_file[0]
        dua_reduction_ref_file = (
            test_db_session.query(DuaReductionPaymentReferenceFile)
            .filter_by(
                dua_reduction_payment_id=payment.dua_reduction_payment_id,
                reference_file_id=_ref_file.reference_file_id,
            )
            .one_or_none()
        )
        assert dua_reduction_ref_file is not None

    # Payments older than 90 days should be ignored
    for payment in old_reduction_payments:
        _ref_file = ref_file[0]
        dua_reduction_ref_file = (
            test_db_session.query(DuaReductionPaymentReferenceFile)
            .filter_by(
                dua_reduction_payment_id=payment.dua_reduction_payment_id,
                reference_file_id=_ref_file.reference_file_id,
            )
            .one_or_none()
        )
        assert dua_reduction_ref_file is None


def test__get_non_submitted_reduction_payments_filters_old_records(
    test_db_session, initialize_factories_session
):
    new_reduction_payments = DuaReductionPaymentFactory.create_batch(
        size=2, created_at=datetime_util.utcnow() - timedelta(days=90)
    )

    old_reduction_payments = DuaReductionPaymentFactory.create_batch(
        size=2, created_at=datetime_util.utcnow() - timedelta(days=91)
    )

    reduction_payments = new_reduction_payments + old_reduction_payments

    employees = [
        EmployeeFactory.create(fineos_customer_number=reduction_payment.fineos_customer_number)
        for reduction_payment in reduction_payments
    ]
    [
        ClaimFactory.create(
            fineos_absence_status_id=AbsenceStatus.COMPLETED.absence_status_id,
            created_at=datetime_util.utcnow(),
            employee=employee,
        )
        for employee in employees
    ]

    payment_records = dua._get_non_submitted_reduction_payments(test_db_session)

    assert len(payment_records) == 2

    retrieved_ids = [record.dua_reduction_payment_id for record, _ in payment_records]

    # Newer payments should match what is returned
    assert all(
        [payment.dua_reduction_payment_id in retrieved_ids for payment in new_reduction_payments]
    )
    # Older payments excluded
    assert all(
        [
            payment.dua_reduction_payment_id not in retrieved_ids
            for payment in old_reduction_payments
        ]
    )
