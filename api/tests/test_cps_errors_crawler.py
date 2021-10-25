import datetime

import boto3
import newrelic.agent

import massgov.pfml.fineos.etl.cps_errors_crawler as crawler


def create_mock_s3_files(bucket, *files):
    for key in files:
        boto3.client("s3").put_object(
            Bucket=bucket, Key=key, Body="header text\nline 2 text\nline 3 text"
        )


def test_reading_file_items(mock_s3_bucket):
    s3 = boto3.resource("s3")

    create_mock_s3_files(
        mock_s3_bucket,
        "received/2021-01-02-01-02-03/2021-04-02-04-04-04-filename.csv",
        "received/2021-01-02-01-02-03/2021-04-02-04-04-04-DifferentFile.csv",
        "received/2021-01-03-01-02-03-filename.csv",
        "received/2021-01-03-01-02-03-DifferentFile.csv",
    )

    received = f"s3://{mock_s3_bucket}/received/"
    processed = f"s3://{mock_s3_bucket}/processed/"

    # manually setting the env var
    config = crawler.CPSErrorsConfig(
        cps_error_reports_received_s3_path=received, cps_error_reports_processed_s3_path=processed
    )
    crawler.process_files(config)
    processed_items = set(map(lambda x: x.key, s3.Bucket(name=mock_s3_bucket).objects.all()))

    # assert files are moved
    assert processed_items == {
        "processed/2021-01-02-01-02-03/2021-04-02-04-04-04-filename.csv",
        "processed/2021-01-02-01-02-03/2021-04-02-04-04-04-DifferentFile.csv",
        "processed/2021-01-03-01-02-03-filename.csv",
        "processed/2021-01-03-01-02-03-DifferentFile.csv",
    }


def test_non_csv_file(caplog, mock_s3_bucket):
    create_mock_s3_files(
        mock_s3_bucket,
        "received/2021-01-03-01-02-03-filename.txt",
        "received/2021-01-03-01-02-03-filename2.txt",
    )

    received = f"s3://{mock_s3_bucket}/received/"
    processed = f"s3://{mock_s3_bucket}/processed/"

    config = crawler.CPSErrorsConfig(
        cps_error_reports_received_s3_path=received, cps_error_reports_processed_s3_path=processed
    )
    crawler.process_files(config)
    assert (
        "skipping non CSV file: s3://test_bucket/received/2021-01-03-01-02-03-filename.txt"
        in caplog.text
    )
    assert (
        "skipping non CSV file: s3://test_bucket/received/2021-01-03-01-02-03-filename2.txt"
        in caplog.text
    )


def test_calls_to_new_relic(mocker, mock_s3_bucket):
    create_mock_s3_files(
        mock_s3_bucket,
        "received/2021-01-03-01-02-03-filename.csv",
        "received/2021-01-03-01-02-03-DifferentFile.csv",
    )

    mock_newrelic = mocker.patch.object(newrelic.agent, "record_custom_event")

    received = f"s3://{mock_s3_bucket}/received/"
    processed = f"s3://{mock_s3_bucket}/processed/"

    config = crawler.CPSErrorsConfig(
        cps_error_reports_received_s3_path=received, cps_error_reports_processed_s3_path=processed
    )
    crawler.process_files(config)
    # update tests to have additional attributes
    mock_newrelic.assert_has_calls(
        [
            mocker.call(
                "FINEOSBatchError",
                {
                    "header text": "line 2 text",
                    "file_timestamp": datetime.datetime(2021, 1, 3, 1, 2, 3),
                    "file_type": "DifferentFile",
                    "environment": "local",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-DifferentFile.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header text": "line 3 text",
                    "file_timestamp": datetime.datetime(2021, 1, 3, 1, 2, 3),
                    "file_type": "DifferentFile",
                    "environment": "local",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-DifferentFile.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header text": "line 2 text",
                    "file_timestamp": datetime.datetime(2021, 1, 3, 1, 2, 3),
                    "file_type": "filename",
                    "environment": "local",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header text": "line 3 text",
                    "file_timestamp": datetime.datetime(2021, 1, 3, 1, 2, 3),
                    "file_type": "filename",
                    "environment": "local",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
        ]
    )


def create_mock_pii_files(bucket, *files):
    for key in files:
        boto3.client("s3").put_object(
            Bucket=bucket,
            Key=key,
            Body="RAWLINE,header 2,header 3\nshould be scrubbed,column stuff,more column stuff\nshould be scrubbed,column stuff,more column stuff",
        )


def test_removed_columns(mocker, mock_s3_bucket):
    # assert that RAWLINE rows are removed
    create_mock_pii_files(mock_s3_bucket, "received/2021-01-03-01-02-03-filename.csv")

    mock_newrelic = mocker.patch.object(newrelic.agent, "record_custom_event")

    received = f"s3://{mock_s3_bucket}/received/"
    processed = f"s3://{mock_s3_bucket}/processed/"

    config = crawler.CPSErrorsConfig(
        cps_error_reports_received_s3_path=received, cps_error_reports_processed_s3_path=processed
    )
    crawler.process_files(config)

    mock_newrelic.assert_has_calls(
        [
            mocker.call(
                "FINEOSBatchError",
                {
                    "header 2": "column stuff",
                    "header 3": "more column stuff",
                    "file_timestamp": datetime.datetime(2021, 1, 3, 1, 2, 3),
                    "file_type": "filename",
                    "environment": "local",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header 2": "column stuff",
                    "header 3": "more column stuff",
                    "file_timestamp": datetime.datetime(2021, 1, 3, 1, 2, 3),
                    "file_type": "filename",
                    "environment": "local",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
        ]
    )


def test_parsing_nonstandard_files(caplog, mocker, mock_s3_bucket):
    create_mock_s3_files(
        mock_s3_bucket,
        "received/2021-01-03-01-02-03-filename.csv",
        "received/f1le-with-a-b4d-name.csv",
    )

    received = f"s3://{mock_s3_bucket}/received/"
    processed = f"s3://{mock_s3_bucket}/processed/"

    config = crawler.CPSErrorsConfig(
        cps_error_reports_received_s3_path=received, cps_error_reports_processed_s3_path=processed
    )
    crawler.process_files(config)

    assert (
        "Failed to parse additional attributes from filename (s3://test_bucket/received/f1le-with-a-b4d-name.csv)"
        in caplog.text
    )
