import os
import uuid

import boto3
import pytest
import smart_open

from massgov.pfml.db.models.factories import EmployeeFactory
from massgov.pfml.dua.dua_generate_employee_request_file import (
    Constants,
    _format_employees_for_outbound,
    copy_dua_files_from_s3_to_moveit,
    generate_and_upload_dua_employee_update_file,
    get_employees_for_outbound,
)
from massgov.pfml.util.batch.log import LogEntry


@pytest.fixture
def add_test_employees(initialize_factories_session):
    EmployeeFactory.create(fineos_customer_number=str(uuid.uuid4()))
    EmployeeFactory.create(fineos_customer_number=str(uuid.uuid4()))
    EmployeeFactory.create(fineos_customer_number=str(uuid.uuid4()))
    EmployeeFactory.create(fineos_customer_number=str(uuid.uuid4()))
    EmployeeFactory.create(fineos_customer_number=str(uuid.uuid4()))


def test_send_dua_employee_request_file(
    test_db_session,
    mock_s3_bucket,
    monkeypatch,
    add_test_employees,
    mock_sftp_client,
    setup_mock_sftp_client,
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = Constants.S3_DFML_OUTBOUND_PATH
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("S3_DUA_OUTBOUND_DIRECTORY_PATH", dest_dir)
    monkeypatch.setenv("S3_DUA_ARCHIVE_DIRECTORY_PATH", Constants.S3_DFML_ARCHIVE_PATH)
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

    with smart_open.open(full_s3_filepath) as s3_file:
        assert 6 == len(list(s3_file))  # 5 employees + header row

    ref_files = copy_dua_files_from_s3_to_moveit(test_db_session, log_entry)

    assert len(ref_files) == 1


def test_get_and_format_employees(test_db_session, add_test_employees):
    employees = get_employees_for_outbound(test_db_session)
    employee_info = _format_employees_for_outbound(employees)
    assert len(employee_info) == 5
    for employee in employee_info:
        assert employee["FINEOS Customer ID"] and employee["SSN"]
