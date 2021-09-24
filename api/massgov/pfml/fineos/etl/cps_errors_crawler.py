from typing import Any
import boto3
import newrelic.agent
from pydantic import BaseSettings, Field

import massgov.pfml.util.files as file_util
import massgov.pfml.util.logging
from massgov.pfml.util.bg import background_task
from massgov.pfml.util.csv import CSVSourceWrapper

logger = massgov.pfml.util.logging.get_logger(__name__)


class CPSErrorsConfig(BaseSettings):
    cps_error_reports_received_s3_path: str = Field(
        ..., min_length=1, env="CPS_ERROR_REPORTS_RECEIVED_S3_PATH"
    )
    cps_error_reports_processed_s3_path: str = Field(
        ..., min_length=1, env="CPS_ERROR_REPORTS_PROCESSED_S3_PATH"
    )


@background_task("cps-errors-crawler")
def main():
    """ECS Task entrypoint"""
    config = CPSErrorsConfig()

    process_files(config)


def process_files(config):
    """Main method: collects and parses items csv files from an s3 bucket before reporting those items to New Relic"""
    client = boto3.client("s3")

    file_list = massgov.pfml.util.files.list_files(
        path=config.cps_error_reports_received_s3_path, recursive=True, boto_session=boto3
    )

    for file in file_list:
        try:
            send_rows_to_nr(config, client, file)
            move_file_to_processed(client, file, config)
        except Exception as e:
            logger.error("Error encountered while processing %s: %s" % (file, e))
            newrelic.agent.record_exception(e)


def send_rows_to_nr(config, client, file):
    # reads the items in the supplied filepath, and reports it to New Relic
    received_file = f"{config.cps_error_reports_received_s3_path}{file}"
    count = 0

    if received_file.endswith(".csv"):
        logger.info("file to be processed --> %s", received_file)

        for row in CSVSourceWrapper(received_file):
            count += 1
            row["s3_filename"] = received_file

            # Avoid sending RAWLINE data, as it often contains PII
            if row.get("RAWLINE"):
                del row["RAWLINE"]

            newrelic.agent.record_custom_event("FINEOSBatchError", row)
    else:
        logger.warning("skipping non CSV file: %s", received_file)

    logger.info(f"{count}rows sent to New Relic from {received_file}")


def move_file_to_processed(client: Any, file: str, config: CPSErrorsConfig) -> None:
    dest_bucket = config.cps_error_reports_processed_s3_path
    source = f"{config.cps_error_reports_received_s3_path}{file}"
    destination = f"{dest_bucket}{file}"

    source_bucket, source_path = massgov.pfml.util.files.split_s3_url(source)
    dest_bucket, dest_path = massgov.pfml.util.files.split_s3_url(destination)

    logger.info("renaming: %s to --> %s", source, destination)
    copy_source = {"Bucket": source_bucket, "Key": source_path}

    logger.info("COPY_SOURCE: %s", copy_source)
    logger.info("DEST_BUCKET: %s, DEST_PATH: %s", dest_bucket, dest_path)
    client.copy(copy_source, dest_bucket, dest_path)

    file_util.delete_file(source)
