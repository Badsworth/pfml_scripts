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
def set_exporter_env_vars(mock_s3_bucket, mock_fineos_s3_bucket, monkeypatch):
    # fineos inbound
    monkeypatch.setenv("FINEOS_DATA_EXPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataexports")
    monkeypatch.setenv("PFML_FINEOS_INBOUND_PATH", f"s3://{mock_s3_bucket}/cps/inbound")

    # fineos outbound
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataimports")
    monkeypatch.setenv("PFML_FINEOS_OUTBOUND_PATH", f"s3://{mock_s3_bucket}/cps/outbound")

    # pub folders
    monkeypatch.setenv("PFML_PUB_INBOUND_PATH", f"s3://{mock_s3_bucket}/pub/outbound")
    monkeypatch.setenv("PFML_PUB_OUTBOUND_PATH", f"s3://{mock_s3_bucket}/pub/inbound")

    # reports
    monkeypatch.setenv("PFML_ERROR_REPORTS_PATH", f"s3://{mock_s3_bucket}/error-reports/outbound")
    monkeypatch.setenv(
        "PFML_ERROR_REPORTS_ARCHIVE_PATH", f"s3://{mock_s3_bucket}/error-reports/sent"
    )

    # audit / rejects report
    monkeypatch.setenv(
        "PAYMENT_AUDIT_REPORT_OUTBOUND_FOLDER_PATH", f"s3://{mock_s3_bucket}/audit/outbound"
    )
    monkeypatch.setenv("PAYMENT_AUDIT_REPORT_SENT_FOLDER_PATH", f"s3://{mock_s3_bucket}/audit/sent")

    monkeypatch.setenv(
        "PAYMENT_REJECTS_RECEIVED_FOLDER_PATH", f"s3://{mock_s3_bucket}/rejects/inbound"
    )
    monkeypatch.setenv(
        "PAYMENT_REJECTS_PROCESSED_FOLDER_PATH", f"s3://{mock_s3_bucket}/rejects/processed"
    )


def upload_file_to_s3(file_path, s3_bucket, key):
    s3 = boto3.client("s3")
    s3.upload_file(file_path.__str__(), s3_bucket, key)
