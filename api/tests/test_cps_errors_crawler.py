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
        "received/2021-01-02-01-02-03/2021-04-02-04-04-04-filename2.csv",
        "received/2021-01-03-01-02-03-filename.csv",
        "received/2021-01-03-01-02-03-filename2.csv",
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
        "processed/2021-01-02-01-02-03/2021-04-02-04-04-04-filename2.csv",
        "processed/2021-01-03-01-02-03-filename.csv",
        "processed/2021-01-03-01-02-03-filename2.csv",
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
        "received/2021-01-03-01-02-03-filename2.csv",
    )

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
                    "header text": "line 2 text",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header text": "line 3 text",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header text": "line 2 text",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename2.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header text": "line 3 text",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename2.csv",
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
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
            mocker.call(
                "FINEOSBatchError",
                {
                    "header 2": "column stuff",
                    "header 3": "more column stuff",
                    "s3_filename": "s3://test_bucket/received/2021-01-03-01-02-03-filename.csv",
                },
            ),
        ]
    )
