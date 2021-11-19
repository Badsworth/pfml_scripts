import boto3
import mock
import pytest
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import massgov.pfml.reductions.reports.consolidated_dia_payments.send as send_report
from massgov.pfml.db.models.employees import ReferenceFileType, State
from massgov.pfml.db.models.factories import ReferenceFileFactory
from massgov.pfml.util.aws.ses import send_email


def _setup_reductions_reporting(mock_s3_bucket, monkeypatch, file_name="test_file.csv"):
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

    folder_name = "reductions/dfml/outbound"
    key = "{}/{}".format(folder_name, file_name)

    full_path = "s3://{}/{}".format(mock_s3_bucket, key)

    s3.put_object(Bucket=mock_s3_bucket, Key=key, Body="Filler text\n")

    return full_path


def test_send_dia_reductions_report(
    test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
):

    full_path = _setup_reductions_reporting(mock_s3_bucket, monkeypatch)

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id,
    )

    assert len(ref_file.state_logs) == 0

    send_email_mock = mock.Mock(wraps=send_email)
    send_report.send_email = send_email_mock

    send_report.send_consolidated_dia_reductions_report(test_db_session)

    # check that a State Log has been created
    assert len(ref_file.state_logs) == 1
    assert ref_file.state_logs[0].end_state.state_id == State.DIA_CONSOLIDATED_REPORT_SENT.state_id

    # check that the reference file location has changed, and that it is now in the archive dir
    assert ref_file.file_location != full_path
    assert ref_file.file_location == "s3://test_bucket/reductions/dfml/archive/test_file.csv"

    # inspect mock_ses response meta data
    mock_ses_response_meta_data = mock_ses.get_send_quota()["ResponseMetadata"]

    assert mock_ses_response_meta_data["RequestId"] is not None
    assert mock_ses_response_meta_data["HTTPStatusCode"] == 200

    expected_body = (
        "Attached please find a report that includes the consolidated DIA reductions payments."
    )

    assert send_email_mock.call_args.kwargs["body_text"] == expected_body


def test_send_dia_reductions_report_no_result(test_db_session, mock_s3_bucket, monkeypatch):

    _setup_reductions_reporting(mock_s3_bucket, monkeypatch)

    with pytest.raises(NoResultFound):
        send_report.send_consolidated_dia_reductions_report(test_db_session)


def test_send_dia_reductions_report_multiple_results(
    test_db_session, mock_s3_bucket, monkeypatch, initialize_factories_session
):

    full_path = _setup_reductions_reporting(mock_s3_bucket, monkeypatch)

    ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id,
    )

    ReferenceFileFactory.create(
        file_location="s3://test_bucket/reductions/dfml/outbound/test_file2.csv",
        reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id,
    )

    with pytest.raises(MultipleResultsFound):
        send_report.send_consolidated_dia_reductions_report(test_db_session)


def test_send_dia_reductions_report_unknown_exception(
    test_db_session, mock_s3_bucket, monkeypatch, initialize_factories_session
):

    full_path = _setup_reductions_reporting(mock_s3_bucket, monkeypatch)

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id,
    )

    error_path = _setup_reductions_reporting(mock_s3_bucket, monkeypatch, "test_error_report.csv")

    error_ref_file = ReferenceFileFactory.create(
        file_location=error_path,
        reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT_ERRORS.reference_file_type_id,
    )

    assert len(ref_file.state_logs) == 0

    def mock(report_file_path):
        raise Exception

    monkeypatch.setattr(send_report, "_send_consolidated_dia_payments_email", mock)

    with pytest.raises(Exception):
        send_report.send_consolidated_dia_reductions_report(test_db_session)

    # check that a State Log has been created
    assert len(ref_file.state_logs) == 1
    assert ref_file.state_logs[0].end_state.state_id == State.DIA_CONSOLIDATED_REPORT_ERROR.state_id

    # check that the reference file location has changed, and that it is now in the archive dir
    assert ref_file.file_location != full_path
    assert ref_file.file_location == "s3://test_bucket/reductions/dfml/error/test_file.csv"

    assert error_ref_file.file_location != error_path
    assert (
        error_ref_file.file_location
        == "s3://test_bucket/reductions/dfml/error/test_error_report.csv"
    )


def test_send_dia_reductions_report_with_error_report(
    test_db_session, mock_s3_bucket, mock_ses, monkeypatch, initialize_factories_session
):

    full_path = _setup_reductions_reporting(mock_s3_bucket, monkeypatch)

    ref_file = ReferenceFileFactory.create(
        file_location=full_path,
        reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT.reference_file_type_id,
    )

    error_path = _setup_reductions_reporting(mock_s3_bucket, monkeypatch, "test_error_report.csv")

    error_ref_file = ReferenceFileFactory.create(
        file_location=error_path,
        reference_file_type_id=ReferenceFileType.DIA_CONSOLIDATED_REDUCTION_REPORT_ERRORS.reference_file_type_id,
    )
    assert len(ref_file.state_logs) == 0

    send_email_mock = mock.Mock(wraps=send_email)
    send_report.send_email = send_email_mock

    send_report.send_consolidated_dia_reductions_report(test_db_session)

    # check that a State Log has been created
    assert len(ref_file.state_logs) == 1
    assert ref_file.state_logs[0].end_state.state_id == State.DIA_CONSOLIDATED_REPORT_SENT.state_id

    # check that the reference file location has changed, and that it is now in the archive dir
    assert ref_file.file_location != full_path
    assert ref_file.file_location == "s3://test_bucket/reductions/dfml/archive/test_file.csv"

    assert error_ref_file.file_location != error_path
    assert (
        error_ref_file.file_location
        == "s3://test_bucket/reductions/dfml/archive/test_error_report.csv"
    )

    # inspect mock_ses response meta data
    mock_ses_response_meta_data = mock_ses.get_send_quota()["ResponseMetadata"]

    assert mock_ses_response_meta_data["RequestId"] is not None
    assert mock_ses_response_meta_data["HTTPStatusCode"] == 200

    expected_body = "Attached please find a report that includes the consolidated DIA reductions payments. See records which could not be merged in a separately attached file."

    assert send_email_mock.call_args.kwargs["body_text"] == expected_body
