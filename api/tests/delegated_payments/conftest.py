import boto3
import pytest


@pytest.fixture
def mock_fineos_s3_bucket(mock_s3_bucket):
    # This relies on the context manager setup in the mock_s3_bucket fixture
    # which remains open because it uses yield rather than return
    s3 = boto3.resource("s3")
    bucket_name = "fineos_bucket"
    s3.create_bucket(Bucket=bucket_name)
    yield bucket_name


@pytest.fixture
def set_exporter_env_vars(mock_s3_bucket, mock_fineos_s3_bucket, mock_sftp_client, monkeypatch):
    monkeypatch.setenv("FINEOS_DATA_EXPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataexports/")
    monkeypatch.setenv("PFML_FINEOS_EXTRACT_ARCHIVE_PATH", f"s3://{mock_s3_bucket}/cps/inbound/")
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataimports/")
    monkeypatch.setenv("PFML_FINEOS_WRITEBACK_ARCHIVE_PATH", f"s3://{mock_s3_bucket}/cps/outbound/")

    monkeypatch.setenv("DFML_REPORT_OUTBOUND_PATH", f"s3://{mock_s3_bucket}/dfml-reports/")
    monkeypatch.setenv(
        "PFML_ERROR_REPORTS_ARCHIVE_PATH", f"s3://{mock_s3_bucket}/error_reports/outbound"
    )
    monkeypatch.setenv(
        "PFML_PAYMENT_REJECTS_ARCHIVE_PATH", f"s3://{mock_s3_bucket}/rejects/inbound"
    )
    monkeypatch.setenv("PFML_PUB_CHECK_ARCHIVE_PATH", f"s3://{mock_s3_bucket}/pub/check")
    monkeypatch.setenv("PFML_PUB_ACH_ARCHIVE_PATH", f"s3://{mock_s3_bucket}/pub/ach")
    monkeypatch.setenv("PUB_MOVEIT_OUTBOUND_PATH", f"s3://{mock_s3_bucket}/pub/outbound")
    monkeypatch.setenv("PUB_MOVEIT_INBOUND_PATH", f"s3://{mock_s3_bucket}/pub/inbound")


def upload_file_to_s3(file_path, s3_bucket, key):
    s3 = boto3.client("s3")
    s3.upload_file(file_path.__str__(), s3_bucket, key)
