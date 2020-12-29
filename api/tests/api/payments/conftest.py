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
    monkeypatch.setenv("FINEOS_DATA_EXPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataexports/")
    monkeypatch.setenv("PFML_FINEOS_INBOUND_PATH", f"s3://{mock_s3_bucket}/cps/inbound/")
    monkeypatch.setenv("FINEOS_DATA_IMPORT_PATH", f"s3://{mock_fineos_s3_bucket}/DT2/dataimports/")
    monkeypatch.setenv("PFML_FINEOS_OUTBOUND_PATH", f"s3://{mock_s3_bucket}/cps/outbound/")
