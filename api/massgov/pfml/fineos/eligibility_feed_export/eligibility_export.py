#
# Executable functionality to export Eligibility Feed to FINEOS.
#
import dataclasses

import boto3

import massgov.pfml.fineos.eligibility_feed as eligibility_feed
import massgov.pfml.util.aws.sts as aws_sts
import massgov.pfml.util.config as config
import massgov.pfml.util.logging as logging
from massgov.pfml import db, fineos

logging.init(__name__)
logger = logging.get_logger(__name__)


def make_fineos_client() -> fineos.AbstractFINEOSClient:
    fineos_client_config = fineos.factory.FINEOSClientConfig.from_env()
    if fineos_client_config.oauth2_client_secret is None:
        aws_ssm = boto3.client("ssm", region_name="us-east-1")
        fineos_client_config.oauth2_client_secret = config.get_secret_from_env(
            aws_ssm, "FINEOS_CLIENT_OAUTH2_CLIENT_SECRET"
        )

    fineos_client = fineos.create_client(fineos_client_config)
    return fineos_client


def make_db_session() -> db.Session:
    return db.init()


def make_fineos_boto_session(config: eligibility_feed.EligibilityFeedExportConfig) -> boto3.Session:
    return aws_sts.assume_session(
        role_arn=config.fineos_aws_iam_role_arn,
        external_id=config.fineos_aws_iam_role_external_id,
        role_session_name="eligibility_feed",
        region_name="us-east-1",
    )


def handler(_event, _context):
    """Handler for Lambda function"""
    return main_with_return()


def main():
    """Entry point for ECS task

    For an ECS task, the return value is taken as a status code, so should not
    return anything (or anything non-zero) from this function.
    """
    main_with_return()
    return 0


def main_with_return():
    logger.info("Starting FINEOS eligibility feed export run")

    config = eligibility_feed.EligibilityFeedExportConfig()
    output_transport_params = None

    if config.mode is eligibility_feed.EligibilityFeedExportMode.UPDATES:
        # Note that the IAM role for the Eligibility Feed Export Lambda/ECS Task
        # does not have access to any S3 bucket in the PFML account by default. So
        # in order to test the functionality by writing to a non-FINEOS S3 location,
        # the IAM role needs updated for the test as well.
        if eligibility_feed.is_fineos_output_location(config.output_directory_path):
            session = make_fineos_boto_session(config)
            output_transport_params = dict(session=session)

        fineos_client = make_fineos_client()
        with db.session_scope(make_db_session(), close=True) as db_session:
            process_result = eligibility_feed.process_employee_updates(
                db_session, fineos_client, config.output_directory_path, output_transport_params
            )
    else:
        process_result = eligibility_feed.process_all_employers(
            make_db_session, make_fineos_client, make_fineos_boto_session, config
        )

    logger.info(
        "Finished writing all eligibility feeds",
        extra={"report": dataclasses.asdict(process_result)},
    )

    return dataclasses.asdict(process_result)
