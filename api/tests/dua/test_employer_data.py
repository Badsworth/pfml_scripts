import os

from freezegun import freeze_time

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.dua import DuaEmployer
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.dua.config import get_moveit_config, get_transfer_config
from massgov.pfml.dua.employer import download_employer_file_from_moveit, load_employer_file
from massgov.pfml.util.batch.log import LogEntry

from .helpers import get_mock_reference_file


def test_import_multiple_files_new_data(test_db_session, monkeypatch, mock_s3_bucket):
    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_reference_file("test_dua_employer_data.csv")
        transfer_config = get_transfer_config()
        load_employer_file(test_db_session, reference_file, log_entry, transfer_config)

        metrics = log_entry.metrics

        # 9 rows in the file (not counting headers)
        assert metrics["total_dua_employer_row_count"] == 9
        assert metrics["inserted_dua_employer_row_count"] == 9
        assert metrics["successful_dua_employer_reference_files_count"] == 1
        assert metrics["pending_dua_employer_reference_files_count"] == 1

        found_data_to_validate = False

        processed_records = (test_db_session.query(DuaEmployer)).all()
        for record in processed_records:
            if record.fineos_employer_id == "1234567":
                found_data_to_validate = True
                assert record.email == "abc@abc.com"
                assert record.phone_number == "123-456-7890"
                assert record.address_line_1 == "123 main st"
                assert record.address_city == "boston"
                assert record.address_zip_code == "03323"
                assert record.address_state == "ma"
                assert record.naics_code == "809245"
                assert record.naics_description == "Teacher registries"

        # Make sure we have validated at least one row
        assert found_data_to_validate
        assert len(processed_records) == 9

        reference_file_next = get_mock_reference_file("test_dua_employer_data_other.csv")
        load_employer_file(test_db_session, reference_file_next, log_entry, transfer_config)

        # 1 new rows in this file
        assert metrics["inserted_dua_employer_row_count"] == 10


def test_update_employer_file_mode(test_db_session, monkeypatch, mock_s3_bucket):
    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_reference_file("test_dua_employer_data.csv")
        transfer_config = get_transfer_config()
        load_employer_file(test_db_session, reference_file, log_entry, transfer_config)

        metrics = log_entry.metrics

        # 9 rows in the file (not counting headers)
        assert metrics["total_dua_employer_row_count"] == 9
        assert metrics["successful_dua_employer_reference_files_count"] == 1
        assert metrics["pending_dua_employer_reference_files_count"] == 1

        processed_records = (test_db_session.query(DuaEmployer)).all()

        assert len(processed_records) == 9


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
        reference_file = get_mock_reference_file("test_dua_employer_data.csv")
        filename = "DUA_DFML_EMP_202012070000.csv"
        filepath = os.path.join(paths["moveit_pickup_path"], filename)
        mock_sftp_client._add_file(filepath, file_util.read_file(reference_file.file_location))

        transfer_config = get_transfer_config()
        moveit_config = get_moveit_config()

        reference_files = (
            download_employer_file_from_moveit(
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
                == ReferenceFileType.DUA_EMPLOYER_FILE.reference_file_type_id
            )
        ).all()
        for file in reference_files:
            load_employer_file(
                test_db_session, file, log_entry, move_files=True, transfer_config=transfer_config
            )

        assert filename not in file_util.list_files(paths["pending_directory"])
        assert filename in file_util.list_files(paths["archive_directory"])

        metrics = log_entry.metrics

        # 9 rows in the file (not counting headers)
        assert metrics["total_dua_employer_row_count"] == 9

        assert metrics["successful_dua_employer_reference_files_count"] == 1
        assert metrics["pending_dua_employer_reference_files_count"] == 1

        reference_files = download_employer_file_from_moveit(
            test_db_session, log_entry, transfer_config=transfer_config, moveit_config=moveit_config
        )
        assert len(reference_files) == 0
