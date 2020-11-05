#
# Executable functionality to export Eligibility Feed to FINEOS.
#
import dataclasses
from enum import Enum

import boto3
from pydantic import BaseSettings, Field

import massgov.pfml.fineos.eligibility_feed as eligibility_feed
import massgov.pfml.util.aws.sts as aws_sts
import massgov.pfml.util.config as config
import massgov.pfml.util.logging as logging
from massgov.pfml import db, fineos

logging.init(__name__)
logger = logging.get_logger(__name__)

db_session_raw = db.init()

fineos_client_config = fineos.factory.FINEOSClientConfig.from_env()
if fineos_client_config.oauth2_client_secret is None:
    aws_ssm = boto3.client("ssm", region_name="us-east-1")
    fineos_client_config.oauth2_client_secret = config.get_secret_from_env(
        aws_ssm, "FINEOS_CLIENT_OAUTH2_CLIENT_SECRET"
    )

fineos_client = fineos.create_client(fineos_client_config)


class EligibilityFeedExportMode(Enum):
    FULL = "full"
    UPDATES = "updates"


class EligibilityFeedExportConfig(BaseSettings):
    output_directory_path: str = Field(..., min_length=1)
    fineos_aws_iam_role_arn: str = Field(..., min_length=1)
    fineos_aws_iam_role_external_id: str = Field(..., min_length=1)
    mode: EligibilityFeedExportMode = Field(
        EligibilityFeedExportMode.FULL, env="ELIGIBILITY_FEED_MODE"
    )


def handler(_event, _context):
    """Handler for Lambda function"""
    return main()


def main():
    logger.info("Starting FINEOS eligibility feed export run")

    config = EligibilityFeedExportConfig()
    output_transport_params = None

    # Note that the IAM role for the Eligibility Feed Export Lambda/ECS Task
    # does not have access to any S3 bucket in the PFML account by default. So
    # in order to test the functionality by writing to a non-FINEOS S3 location,
    # the IAM role needs updated for the test as well.
    is_fineos_output_location = config.output_directory_path.startswith("s3://fin-som")

    if is_fineos_output_location:
        session = aws_sts.assume_session(
            role_arn=config.fineos_aws_iam_role_arn,
            external_id=config.fineos_aws_iam_role_external_id,
            role_session_name="eligibility_feed",
            duration_seconds=3600,
            region_name="us-east-1",
        )

        output_transport_params = dict(session=session)

    with db.session_scope(db_session_raw, close=True) as db_session:
        if config.mode is EligibilityFeedExportMode.UPDATES:
            process_result = eligibility_feed.process_employee_updates(
                db_session, fineos_client, config.output_directory_path, output_transport_params
            )
        else:
            process_result = eligibility_feed.process_all_employers(
                db_session, fineos_client, config.output_directory_path, output_transport_params
            )

    return dataclasses.asdict(process_result)
