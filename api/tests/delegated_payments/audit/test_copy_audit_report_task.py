import os

import boto3
import pytest

import massgov.pfml.util.files as file_util
from massgov.pfml.db.models.employees import ReferenceFile, ReferenceFileType
from massgov.pfml.delegated_payments.audit.copy_audit_report_task import (
    _copy_audit_report_to_inbound_path,
)


def test_copy_audit_report(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "dfml-responses/"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("ENVIRONMENT", "test")
    dfml_response_inbound_path = f"s3://{mock_s3_bucket}/dfml-responses"
    monkeypatch.setenv("DFML_RESPONSE_INBOUND_PATH", dfml_response_inbound_path)

    # Create original file to be copied
    timestamp_file_prefix = "2021-01-15-12-00-00"
    original_filename = f"{timestamp_file_prefix}-Payment-Audit-Report.csv"
    original_filepath = "reports/sent/2021-01-15"
    original_location = os.path.join(s3_bucket_uri, original_filepath, original_filename)

    test_csv_string = "Test,1"
    with file_util.write_file(original_location) as output_file:
        output_file.write(test_csv_string)  # Contents don't matter for this test

    s3 = boto3.client("s3")

    # The destination folder is initially empty
    initial_object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir).get(
        "Contents", None
    )
    assert initial_object_list is None

    ref_file = ReferenceFile(
        reference_file_type_id=ReferenceFileType.DELEGATED_PAYMENT_AUDIT_REPORT.reference_file_type_id,
        file_location=original_location,
    )
    test_db_session.add(ref_file)
    test_db_session.commit()

    # Run the task
    _copy_audit_report_to_inbound_path(test_db_session)

    # The destination folder should now have one file
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir)["Contents"]

    assert object_list
    assert len(object_list) == 1

    assert object_list[0]["Key"].startswith(dest_dir)

    uploaded_csv = s3.get_object(Bucket=mock_s3_bucket, Key=object_list[0]["Key"])["Body"].read()
    assert uploaded_csv.decode() == test_csv_string


def test_copy_audit_report_raises_if_prod(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.delenv("ENVIRONMENT")

    with pytest.raises(Exception) as exception:
        _copy_audit_report_to_inbound_path(test_db_session)

    assert (
        str(exception.value)
        == "Unable to run copy-audit-report task in production or when env not set"
    )


def test_copy_audit_report_returns_early_if_no_file_found(
    initialize_factories_session, monkeypatch, mock_s3_bucket, test_db_session
):
    s3_bucket_uri = "s3://" + mock_s3_bucket
    dest_dir = "dfml-responses/"
    monkeypatch.setenv("S3_BUCKET", s3_bucket_uri)
    monkeypatch.setenv("ENVIRONMENT", "test")
    dfml_response_inbound_path = f"s3://{mock_s3_bucket}/dfml-responses"
    monkeypatch.setenv("DFML_RESPONSE_INBOUND_PATH", dfml_response_inbound_path)

    # Create original file to be copied
    timestamp_file_prefix = "2021-01-15-12-00-00"
    original_filename = f"{timestamp_file_prefix}-Payment-Audit-Report.csv"
    original_filepath = "reports/sent/2021-01-15"
    original_location = os.path.join(s3_bucket_uri, original_filepath, original_filename)

    test_csv_string = "Test,1"
    with file_util.write_file(original_location) as output_file:
        output_file.write(test_csv_string)  # Contents don't matter for this test

    s3 = boto3.client("s3")

    # The destination folder is initially empty
    initial_object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir).get(
        "Contents", None
    )
    assert initial_object_list is None

    # Run the task
    _copy_audit_report_to_inbound_path(test_db_session)

    # The destination folder should still be empty
    object_list = s3.list_objects(Bucket=mock_s3_bucket, Prefix=dest_dir).get("Contents", None)

    assert object_list is None
