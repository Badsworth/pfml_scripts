import os

import pytest
from freezegun import freeze_time

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import (
    DuaEmployeeDemographics,
    Gender,
    ReferenceFile,
    ReferenceFileType,
)
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.dua.config import get_moveit_config, get_s3_config
from massgov.pfml.dua.demographics import (
    download_demographics_file_from_moveit,
    load_demographics_file,
)
from massgov.pfml.util.batch.log import LogEntry


def get_mock_data():
    return ReferenceFile(
        file_location=os.path.join(
            os.path.dirname(__file__), "test_files", "test_dua_demographic_data.csv"
        )
    )


def get_mock_data_next():
    return ReferenceFile(
        file_location=os.path.join(
            os.path.dirname(__file__), "test_files", "test_dua_demographic_data_other.csv"
        )
    )


@pytest.fixture
def add_test_employees(initialize_factories_session):
    return [
        EmployeeFactory.create(fineos_customer_number="1234567"),
        EmployeeFactory.create(fineos_customer_number="7654321"),
        EmployeeFactory.create(fineos_customer_number="1111111"),
        EmployeeFactory.create(fineos_customer_number="2222222", gender_id=Gender.WOMAN.gender_id),
        EmployeeFactory.create(fineos_customer_number="3333333"),
        EmployeeFactory.create(fineos_customer_number="4444444"),
        EmployeeFactory.create(fineos_customer_number="5555555"),
        EmployeeFactory.create(fineos_customer_number="6666666"),
        EmployeeFactory.create(fineos_customer_number="7777777"),
        EmployeeFactory.create(fineos_customer_number="8888888"),
        EmployeeFactory.create(fineos_customer_number="9999999"),
    ]


def test_import_multiple_files_new_data(test_db_session, monkeypatch, mock_s3_bucket):
    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_data()
        s3_config = get_s3_config()
        load_demographics_file(test_db_session, reference_file, log_entry, s3_config=s3_config)

        metrics = log_entry.metrics

        # 11 rows in the file (not counting headers)
        assert metrics["total_dua_demographics_row_count"] == 11
        assert metrics["inserted_dua_demographics_row_count"] == 10
        assert metrics["successful_dua_demographics_reference_files_count"] == 1
        assert metrics["pending_dua_demographics_reference_files_count"] == 1

        found_data_to_validate = False

        processed_records = (test_db_session.query(DuaEmployeeDemographics)).all()
        for record in processed_records:
            if record.fineos_customer_number == "1234567":
                found_data_to_validate = True
                assert record.gender_code == "F"
                assert record.occupation_code == "1120"
                assert record.occupation_description == "Sales Managers"
                assert record.employer_fein == ""
                assert record.employer_reporting_unit_number == ""

        # Make sure we are validate at least one row
        assert found_data_to_validate
        assert len(processed_records) == 10

        reference_file_next = get_mock_data_next()
        load_demographics_file(test_db_session, reference_file_next, log_entry, s3_config=s3_config)

        # 2 new rows in this file
        assert metrics["inserted_dua_demographics_row_count"] == 12


def test_update_employee_demographics_file_mode(test_db_session, monkeypatch, mock_s3_bucket):

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    with LogEntry(test_db_session, "test log entry") as log_entry:

        reference_file = get_mock_data()
        s3_config = get_s3_config()
        load_demographics_file(test_db_session, reference_file, log_entry, s3_config=s3_config)

        metrics = log_entry.metrics

        # 11 rows in the file (not counting headers)
        assert metrics["total_dua_demographics_row_count"] == 11
        assert metrics["successful_dua_demographics_reference_files_count"] == 1
        assert metrics["pending_dua_demographics_reference_files_count"] == 1

        processed_records = (test_db_session.query(DuaEmployeeDemographics)).all()

        assert len(processed_records) == 10


@freeze_time("2020-12-07")
def test_update_employee_demographics_moveit_mode(
    initialize_factories_session,
    test_db_session,
    monkeypatch,
    mock_s3_bucket,
    mock_sftp_client,
    setup_mock_sftp_client,
):

    source_directory_path = "dua/pending"
    archive_directory_path = "dua/archive"
    moveit_pickup_path = "/DFML/DUA/Outbound"

    monkeypatch.setenv("S3_BUCKET", f"s3://{mock_s3_bucket}")
    monkeypatch.setenv("S3_DUA_OUTBOUND_DIRECTORY_PATH", source_directory_path)
    monkeypatch.setenv("S3_DUA_ARCHIVE_DIRECTORY_PATH", archive_directory_path)
    monkeypatch.setenv("MOVEIT_SFTP_URI", "sftp://foo@bar.com")
    monkeypatch.setenv("MOVEIT_SSH_KEY", "foo")

    pending_directory = f"s3://{mock_s3_bucket}/{source_directory_path}"
    archive_directory = f"s3://{mock_s3_bucket}/{archive_directory_path}"

    with LogEntry(test_db_session, "test log entry") as log_entry:
        reference_file = get_mock_data()
        filename = "DUA_DFML_CLM_DEM_202012070000.csv"
        filepath = os.path.join(moveit_pickup_path, filename)
        mock_sftp_client._add_file(filepath, file_util.read_file(reference_file.file_location))

        s3_config = get_s3_config()
        moveit_config = get_moveit_config()

        reference_files = (
            download_demographics_file_from_moveit(
                test_db_session, log_entry, s3_config=s3_config, moveit_config=moveit_config
            ),
        )

        assert len(file_util.list_files(pending_directory)) == 1
        assert len(file_util.list_files(archive_directory)) == 0
        assert len(reference_files) == 1

        reference_files = (
            test_db_session.query(ReferenceFile).filter(
                ReferenceFile.reference_file_type_id
                == ReferenceFileType.DUA_DEMOGRAPHICS_FILE.reference_file_type_id
            )
        ).all()
        for file in reference_files:
            load_demographics_file(
                test_db_session, file, log_entry, move_files=True, s3_config=s3_config
            )

        assert len(file_util.list_files(pending_directory)) == 0
        assert len(file_util.list_files(archive_directory)) == 1

        metrics = log_entry.metrics

        # 10 rows in the file (not counting headers)
        assert metrics["total_dua_demographics_row_count"] == 11

        assert metrics["successful_dua_demographics_reference_files_count"] == 1
        assert metrics["pending_dua_demographics_reference_files_count"] == 1

        reference_files = download_demographics_file_from_moveit(
            test_db_session, log_entry, s3_config=s3_config, moveit_config=moveit_config
        )
        assert len(reference_files) == 0
