import boto3
import pytest
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import massgov.pfml.reductions.reports.dia_payments.send as dia_payments_reports_send
from massgov.pfml.db.models.employees import ReferenceFileType
from massgov.pfml.db.models.factories import ReferenceFileFactory


def _setup_reductions_reporting(
    test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
):
    monkeypatch.setenv(
        "S3_BUCKET", "s3://test_bucket",
    )

    monkeypatch.setenv(
        "S3_DFML_OUTBOUND_DIRECTORY_PATH", "reductions/dfml/outbound",
    )

    monkeypatch.setenv(
        "S3_DFML_ARCHIVE_DIRECTORY_PATH", "reductions/dfml/archive",
    )

    s3 = boto3.client("s3")
    file_name = "test_file.csv"

    folder_name = "reductions/dfml/outbound"
    key = "{}/{}".format(folder_name, file_name)

    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="Filler text\n")

    return full_path


def test_send_dia_reductions_report(
    test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
):

    full_path = _setup_reductions_reporting(
        test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
    )

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.DIA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id,
    )

    # current number of State Logs
    state_logs_num = len(ref_file.state_logs)

    dia_payments_reports_send.send_dia_reductions_report(test_db_session)

    # check that a State Log has been created
    assert len(ref_file.state_logs) == state_logs_num + 1

    # check that the reference file location has changed, and that it is now in the archive dir
    assert ref_file.file_location != full_path
    assert "archive" in ref_file.file_location

    # inspect mock_ses response meta data
    mock_ses_response_meta_data = mock_ses.get_send_quota()["ResponseMetadata"]

    assert mock_ses_response_meta_data["RequestId"] is not None
    assert mock_ses_response_meta_data["HTTPStatusCode"] == 200


def test_send_dia_reductions_report_no_result(
    test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
):

    _setup_reductions_reporting(
        test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
    )

    with pytest.raises(NoResultFound):
        dia_payments_reports_send.send_dia_reductions_report(test_db_session)


def test_send_dia_reductions_report_multiple_results(
    test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
):

    full_path = _setup_reductions_reporting(
        test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
    )

    ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.DIA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id,
    )

    ReferenceFileFactory.create(
        file_location="s3://test_bucket/reductions/dfml/outbound/test_file2.csv",
        reference_file_type_id=ReferenceFileType.DIA_REDUCTION_REPORT_FOR_DFML.reference_file_type_id,
    )

    with pytest.raises(MultipleResultsFound):
        dia_payments_reports_send.send_dia_reductions_report(test_db_session)
