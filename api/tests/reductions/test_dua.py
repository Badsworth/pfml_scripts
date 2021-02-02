import os
import random
import string
import tempfile
from datetime import date, timedelta
from typing import Any, Dict, Optional

import boto3
import faker
import pytest
import sqlalchemy

import massgov.pfml.api.util.state_log_util as state_log_util
import massgov.pfml.reductions.dua as dua
import massgov.pfml.util.csv as csv_util
import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    DuaReductionPayment,
    LatestStateLog,
    ReferenceFile,
    ReferenceFileType,
    State,
    StateLog,
)
from massgov.pfml.db.models.factories import ReferenceFileFactory

fake = faker.Faker()


EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS = list(
    dua.DUA_PAYMENT_CSV_COLUMN_TO_TABLE_DATA_FIELD_MAP.keys()
)


DUA_PAYMENT_LIST_ENCODERS: csv_util.Encoders = {
    date: lambda d: d.strftime("%Y%m%d"),
}


def _random_csv_filename() -> str:
    # Random filename. Types of characters and length of filename are not meaningful.
    return "".join(random.choices(string.ascii_lowercase, k=16)) + ".csv"


def _create_dua_payment_list_reference_file(
    dir: str, file_location: Optional[str] = None
) -> ReferenceFile:
    if file_location is None:
        file_location = os.path.join(dir, _random_csv_filename())

    return ReferenceFileFactory(
        file_location=file_location,
        reference_file_type_id=ReferenceFileType.DUA_PAYMENT_LIST.reference_file_type_id,
    )


def _create_other_reference_file(dir: str) -> ReferenceFile:
    file_location = os.path.join(dir, _random_csv_filename())

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

    # Make sure Case ID and FEIN are unique for each returned dict.
    return {
        "absence_case_id": "NTN-{}-ABS-01".format(fake.unique.random_int(min=1000, max=9999)),
        "employer_fein": str(fake.unique.random_int(min=100_000, max=999_999)),
        "payment_date": _random_date_in_past_year(),
        "request_week_begin_date": _random_date_in_past_year(),
        "gross_payment_amount_cents": fake.random_int(min=100, max=999),
        "payment_amount_cents": fake.random_int(min=10_000, max=99_999),
        "fraud_indicator": random.choice(["Y", None, None]),  # 1 in 3 chance of a fraud indicator.
        "benefit_year_begin_date": begin_date,
        "benefit_year_end_date": end_date,
    }


def _get_loaded_reference_file_in_s3(mock_s3_bucket, filename, source_directory_path, row_count):
    # Create the ReferenceFile.
    pending_directory = os.path.join(f"s3://{mock_s3_bucket}", source_directory_path)
    source_filepath = os.path.join(pending_directory, filename)
    ref_file = _create_dua_payment_list_reference_file("", source_filepath)

    # Create some number of valid rows for our input file.
    body = ",".join(EXPECTED_DUA_PAYMENT_CSV_FILE_HEADERS) + "\n"
    for _i in range(row_count):
        db_data = _get_valid_dua_payment_data()
        csv_row = csv_util.encode_row(db_data, DUA_PAYMENT_LIST_ENCODERS)
        body = body + ",".join(list(csv_row.values())) + "\n"

    # Add rows to the file in our mock S3 bucket.
    s3_key = os.path.join(source_directory_path, filename)
    s3 = boto3.client("s3")
    s3.put_object(Bucket=mock_s3_bucket, Key=s3_key, Body=body)

    return ref_file


@pytest.mark.parametrize(
    "pending_ref_file_count", ((0), (1), (random.randint(2, 10)),),
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
    dua_reduction_payment_unique_index, test_db_session, test_db_other_session, headers, csv_rows
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
        dua._load_new_rows_from_file(csv_file, test_db_session)

    # We do not expect any rows to be added to the database when _load_new_rows_from_file() fails.
    # Use test_db_other_session because test_db_session ends up in a fuss after it fails to add
    # the rows within dua._load_new_rows_from_file()
    assert (
        test_db_other_session.query(
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
            mock_s3_bucket, _random_csv_filename(), source_directory_path, row_count
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

    dua.load_new_dua_payments(test_db_session)

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


def test_load_dua_payment_from_reference_file_success(
    dua_reduction_payment_unique_index, test_db_session, mock_s3_bucket
):
    # Create the ReferenceFile.
    filename = _random_csv_filename()
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

    dua.load_dua_payment_from_reference_file(ref_file, archive_directory, test_db_session)

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
    dua_reduction_payment_unique_index, test_db_session, test_db_other_session, mock_s3_bucket
):
    # Create the ReferenceFile.
    filename = _random_csv_filename()
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
        dua.load_dua_payment_from_reference_file(ref_file, archive_directory, test_db_session)

    # Expect no rows in the database after because the reference_file.file_location conflict will
    # prevent the datbase from committing the changes.
    # Use test_db_other_session because test_db_session ends up in a fuss after it hits the
    # IntegrityError.
    assert (
        test_db_other_session.query(
            sqlalchemy.func.count(DuaReductionPayment.dua_reduction_payment_id)
        ).scalar()
        == 0
    )

    # Expect no StateLog to have been created.
    assert (
        test_db_other_session.query(
            sqlalchemy.func.count(LatestStateLog.latest_state_log_id)
        ).scalar()
        == 0
    )
