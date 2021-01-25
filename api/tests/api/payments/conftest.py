import boto3
import pytest

import massgov.pfml.util.files as file_util


@pytest.fixture
def mock_fineos_s3_bucket(mock_s3_bucket):
    # This relies on the context manager setup in the mock_s3_bucket fixture
    # which remains open because it uses yield rather than return
    s3 = boto3.resource("s3")
    bucket_name = "fineos_bucket"
    s3.create_bucket(Bucket=bucket_name)
    yield bucket_name


@pytest.fixture
def setup_mock_sftp_client(monkeypatch, mock_sftp_client):
    # Mock SFTP client so we can inspect the method calls we make later in the test.
    monkeypatch.setattr(
        file_util, "get_sftp_client", lambda uri, ssh_key_password, ssh_key: mock_sftp_client,
    )


@pytest.fixture
def set_exporter_env_vars(mock_s3_bucket, mock_fineos_s3_bucket, mock_sftp_client, monkeypatch):
    monkeypatch.setenv("FINEOS_DATA_EXPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataexports/")
    monkeypatch.setenv("PFML_FINEOS_INBOUND_PATH", f"s3://{mock_s3_bucket}/cps/inbound/")
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataimports/")
    monkeypatch.setenv("PFML_FINEOS_OUTBOUND_PATH", f"s3://{mock_s3_bucket}/cps/outbound/")

    monkeypatch.setenv("PFML_CTR_INBOUND_PATH", f"s3://{mock_s3_bucket}/ctr/inbound/")
    monkeypatch.setenv("PFML_CTR_OUTBOUND_PATH", f"s3://{mock_s3_bucket}/ctr/outbound/")

    monkeypatch.setenv("PFML_ERROR_REPORTS_PATH", f"s3://{mock_s3_bucket}/error_reports/outbound")

    monkeypatch.setenv("CTR_MOVEIT_INCOMING_PATH", "pfml/inbox")
    monkeypatch.setenv("CTR_MOVEIT_OUTGOING_PATH", "source/outbox")
    monkeypatch.setenv("CTR_MOVEIT_ARCHIVE_PATH", "archive")
    monkeypatch.setenv("EOLWD_MOVEIT_SFTP_URI", "sftp://api_user@mass.gov")
    monkeypatch.setenv("CTR_MOVEIT_SSH_KEY", "No ssh_key_password used during mocked tests")
    monkeypatch.setenv("CTR_MOVEIT_SSH_KEY_PASSWORD", "No ssh_key used during mocked tests")

    monkeypatch.setenv("DFML_PROJECT_MANAGER_EMAIL_ADDRESS", "test@test.gov")
    monkeypatch.setenv("PFML_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("BOUNCE_FORWARDING_EMAIL_ADDRESS", "noreplypfml@mass.gov")
    monkeypatch.setenv("CTR_GAX_BIEVNT_EMAIL_ADDRESS", "test1@test.com")
    monkeypatch.setenv("CTR_VCC_BIEVNT_EMAIL_ADDRESS", "test2@test.com")
    monkeypatch.setenv("DFML_BUSINESS_OPERATIONS_EMAIL_ADDRESS", "test3@test.com")


def upload_file_to_s3(file_path, s3_bucket, key):
    s3 = boto3.client("s3")
    s3.upload_file(file_path.__str__(), s3_bucket, key)
