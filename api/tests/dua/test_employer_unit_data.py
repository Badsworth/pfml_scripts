import os

from freezegun import freeze_time

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.dua import DuaReportingUnitRaw
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.dua.config import get_moveit_config, get_transfer_config
from massgov.pfml.dua.employer_unit import (
    download_employer_unit_file_from_moveit,
    load_employer_unit_file,
)
from massgov.pfml.util.batch.log import LogEntry

from .helpers import get_mock_reference_file


def test_import_multiple_files_new_data(test_db_session, monkeypatch, mock_s3_bucket):
    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_reference_file("test_dua_employer_unit_data.csv")
        transfer_config = get_transfer_config()
        load_employer_unit_file(test_db_session, reference_file, log_entry, transfer_config)

        metrics = log_entry.metrics

        # 10 rows in the file (not counting headers)
        assert metrics["total_employer_unit_row_count"] == 10
        assert metrics["inserted_dua_employer_unit_row_count"] == 10
        assert metrics["successful_dua_employer_unit_reference_files_count"] == 1
        assert metrics["pending_dua_employer_unit_reference_files_count"] == 1

        found_data_to_validate = False

        processed_records = (test_db_session.query(DuaReportingUnitRaw)).all()
        for record in processed_records:
            if record.fineos_employer_id == "9826434":
                found_data_to_validate = True
                assert record.email == "test@test.com"
                assert record.phone_number == "555-222-1345"
                assert record.address_line_1 == "8401 manchester rd"
                assert record.address_city == "salt city"
                assert record.address_zip_code == "99803"
                assert record.address_state == "co"

        # Make sure we have validated at least one row
        assert found_data_to_validate
        assert len(processed_records) == 10

        reference_file_next = get_mock_reference_file("test_dua_employer_unit_data_other.csv")
        load_employer_unit_file(test_db_session, reference_file_next, log_entry, transfer_config)

        # 1 new rows in this file
        assert metrics["inserted_dua_employer_unit_row_count"] == 11


def test_update_employer_unit_file_mode(test_db_session, monkeypatch, mock_s3_bucket):
    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_reference_file("test_dua_employer_unit_data.csv")
        transfer_config = get_transfer_config()
        load_employer_unit_file(test_db_session, reference_file, log_entry, transfer_config)

        metrics = log_entry.metrics

        # 10 rows in the file (not counting headers)
        assert metrics["total_employer_unit_row_count"] == 10
        assert metrics["successful_dua_employer_unit_reference_files_count"] == 1
        assert metrics["pending_dua_employer_unit_reference_files_count"] == 1

        processed_records = (test_db_session.query(DuaReportingUnitRaw)).all()

        assert len(processed_records) == 10


@freeze_time("2020-12-07")
def test_update_employer_moveit_mode(
    initialize_factories_session,
    test_db_session,
    mock_s3_bucket,
    mock_sftp_client,
    mock_sftp_paths,
    setup_mock_sftp_client,
):

    paths = mock_sftp_paths

    with LogEntry(test_db_session, "test log entry") as log_entry:
        reference_file = get_mock_reference_file("test_dua_employer_unit_data.csv")
        filename = "DUA_DFML_EMP_UNIT202012070000.csv"
        filepath = os.path.join(paths["moveit_pickup_path"], filename)
        mock_sftp_client._add_file(filepath, file_util.read_file(reference_file.file_location))

        transfer_config = get_transfer_config()
        moveit_config = get_moveit_config()

        reference_files = (
            download_employer_unit_file_from_moveit(
                test_db_session,
                log_entry,
                transfer_config=transfer_config,
                moveit_config=moveit_config,
            ),
        )

        assert filename in file_util.list_files(paths["pending_directory"])
        assert filename not in file_util.list_files(paths["archive_directory"])
        assert len(reference_files) == 1

        reference_files = (
            test_db_session.query(ReferenceFile).filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.DUA_EMPLOYER_UNIT_FILE.reference_file_type_id
            )
        ).all()
        for file in reference_files:
            load_employer_unit_file(
                test_db_session, file, log_entry, move_files=True, transfer_config=transfer_config
            )

        assert filename not in file_util.list_files(paths["pending_directory"])
        assert filename in file_util.list_files(paths["archive_directory"])

        metrics = log_entry.metrics

        # 10 rows in the file (not counting headers)
        assert metrics["total_employer_unit_row_count"] == 10

        assert metrics["successful_dua_employer_unit_reference_files_count"] == 1
        assert metrics["pending_dua_employer_unit_reference_files_count"] == 1

        reference_files = download_employer_unit_file_from_moveit(
            test_db_session, log_entry, transfer_config=transfer_config, moveit_config=moveit_config
        )
        assert len(reference_files) == 0
