import os

import boto3
import pytest

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.dua.config import get_transfer_config
from massgov.pfml.dua.dua_generate_employee_request_file import (
    Constants,
    _format_employees_for_outbound,
    copy_dua_files_from_s3_to_moveit,
    generate_and_upload_dua_employee_update_file,
    get_employees_for_outbound,
)
from massgov.pfml.util.batch.log import LogEntry


@pytest.fixture
def expected_fineos_customer_numbers():
    return (
        "7c4bb5a5-095d-414a-a8b7-3a9c13f86c7d",
        "c30298fe-838f-478d-9c74-79b3c4343d3e",
        "165f188e-086b-4021-ac6c-897336e755e9",
        "68d0c146-5a1e-4c1b-8755-f7255c97e66c",
        "c08792b7-5281-4468-befe-7e918e7e7977",
    )


@pytest.fixture
def add_test_employees(initialize_factories_session):
    EmployeeFactory.create(fineos_customer_number="7c4bb5a5-095d-414a-a8b7-3a9c13f86c7d")
    EmployeeFactory.create(fineos_customer_number="c30298fe-838f-478d-9c74-79b3c4343d3e")
    EmployeeFactory.create(fineos_customer_number="165f188e-086b-4021-ac6c-897336e755e9")
    EmployeeFactory.create(fineos_customer_number="68d0c146-5a1e-4c1b-8755-f7255c97e66c")
    EmployeeFactory.create(fineos_customer_number="c08792b7-5281-4468-befe-7e918e7e7977")

    # employee with no fineos_customer_number
    EmployeeFactory.create()


def test_send_dua_employee_request_file(
    test_db_session,
    mock_s3_bucket,
    monkeypatch,
    add_test_employees,
    mock_sftp_client,
    setup_mock_sftp_client,
    expected_fineos_customer_numbers,
):
    transfer_config = get_transfer_config()

    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = transfer_config.outbound_directory_path
    monkeypatch.setenv("DUA_TRANSFER_BASE_PATH", s3_bucket_uri)
    monkeypatch.setenv("OUTBOUND_DIRECTORY_PATH", dest_dir)
    monkeypatch.setenv("ARCHIVE_DIRECTORY_PATH", transfer_config.archive_directory_path)
    monkeypatch.setenv("MOVEIT_SFTP_URI", "sftp://foo@bar.com")
    monkeypatch.setenv("MOVEIT_SSH_KEY", "foo")

    log_entry = LogEntry(test_db_session, "Test")
    generate_and_upload_dua_employee_update_file(test_db_session, log_entry)

    s3 = boto3.client("s3")

    # Confirm that the file is uploaded to S3 with the expected filename.
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    assert len(object_list) == 1
    s3_filename = object_list[0]["Key"]
    full_s3_filepath = os.path.join(s3_bucket_uri, s3_filename)
    dest_filepath_and_prefix = os.path.join(dest_dir, Constants.FILE_PREFIX)
    assert s3_filename.startswith(dest_filepath_and_prefix)

    file_content = list(file_util.read_file_lines(full_s3_filepath))
    assert 6 == len(file_content)  # 5 employees + header row

    for line in file_content[1::]:
        tax_id = line.split(",")[0]
        assert tax_id in expected_fineos_customer_numbers

    ref_files = copy_dua_files_from_s3_to_moveit(test_db_session, log_entry)

    assert len(ref_files) == 1


def test_get_and_format_employees(test_db_session, add_test_employees):
    employees = get_employees_for_outbound(test_db_session)
    employee_info = _format_employees_for_outbound(employees)
    assert len(employee_info) == 5
    for employee in employee_info:
        assert employee["FINEOS Customer ID"] and employee["SSN"]
