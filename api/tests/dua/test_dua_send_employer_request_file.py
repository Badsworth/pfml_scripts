import os

import boto3
import pytest

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.factories import EmployerFactory
from massgov.pfml.dua.config import get_transfer_config
from massgov.pfml.dua.dua_generate_employer_request_file import (
    _format_employers_for_outbound,
    copy_dua_files_from_s3_to_moveit,
    generate_and_upload_dua_employers_update_file,
    get_employers_for_outbound,
)
from massgov.pfml.util.batch.log import LogEntry


@pytest.fixture
def expected_fineos_employer_ids():
    return ("11111111", "22222222", "33333333", "44444444", "55555555")


@pytest.fixture
def add_test_employers(initialize_factories_session):
    EmployerFactory.create(fineos_employer_id="11111111")
    EmployerFactory.create(fineos_employer_id="22222222")
    EmployerFactory.create(fineos_employer_id="33333333")
    EmployerFactory.create(fineos_employer_id="44444444")
    EmployerFactory.create(fineos_employer_id="55555555")

    # employer with no fineos_employer_id
    EmployerFactory.create(fineos_employer_id=None)


def test_send_dua_employer_request_file(
    test_db_session,
    mock_s3_bucket,
    monkeypatch,
    add_test_employers,
    mock_sftp_client,
    setup_mock_sftp_client,
    expected_fineos_employer_ids,
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
    generate_and_upload_dua_employers_update_file(test_db_session, log_entry)

    s3 = boto3.client("s3")

    # Confirm that the file is uploaded to S3 with the expected filename.
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]
    assert object_list
    assert len(object_list) == 1
    s3_filename = object_list[0]["Key"]
    full_s3_filepath = os.path.join(s3_bucket_uri, s3_filename)
    dest_filepath_and_prefix = os.path.join(dest_dir, "DFML_DUA_EMP_")
    assert s3_filename.startswith(dest_filepath_and_prefix)

    file_content = list(file_util.read_file_lines(full_s3_filepath))
    assert 6 == len(file_content)  # 5 employers + header row

    for line in file_content[1::]:
        tax_id = line.split(",")[0]
        assert tax_id in expected_fineos_employer_ids

    ref_files = copy_dua_files_from_s3_to_moveit(test_db_session, log_entry)

    assert len(ref_files) == 1


def test_get_and_format_employers(
    test_db_session, add_test_employers, expected_fineos_employer_ids
):
    employers = get_employers_for_outbound(test_db_session)
    employer_info = _format_employers_for_outbound(employers)
    assert len(employer_info) == 5
    for employer in employer_info:
        assert employer["FINEOS Employer ID"] and employer["Employer EIN"]
        assert str(employer["FINEOS Employer ID"]) in expected_fineos_employer_ids
