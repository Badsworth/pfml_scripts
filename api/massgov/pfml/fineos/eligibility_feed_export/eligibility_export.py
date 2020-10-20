#
# Lambda function to export eligibility feed to FINEOS.
#
import dataclasses
import os

import boto3

import massgov.pfml.fineos.eligibility_feed as eligibility_feed
import massgov.pfml.util.config as config
import massgov.pfml.util.logging as logging
from massgov.pfml import db, fineos

logging.init(__name__)
logger = logging.get_logger(__name__)

db_session_raw = db.init()

fineos_client_config = fineos.factory.FINEOSClientConfig.from_env()
if fineos_client_config is not None:
    aws_ssm = boto3.client("ssm", region_name="us-east-1")
    fineos_client_secret = config.get_secret_from_env(aws_ssm, "FINEOS_CLIENT_OAUTH2_CLIENT_SECRET")
    fineos_client_config.oauth2_client_secret = fineos_client_secret
fineos_client = fineos.create_client(fineos_client_config)


def handler(_event, _context):
    logger.info("Starting FINEOS eligibility feed export run")

    output_dir_path = os.getenv("OUTPUT_DIRECTORY_PATH")

    if not output_dir_path:
        logger.warning("OUTPUT_DIRECTORY_PATH environment variable not set. Aborting run.")
        raise Exception("OUTPUT_DIRECTORY_PATH environment variable not set. Aborting run.")

    with db.session_scope(db_session_raw, close=True) as db_session:
        eligibility_feed_mode = os.environ.get("ELIGIBILITY_FEED_MODE", "full")
        if eligibility_feed_mode == "updates":
            process_result = eligibility_feed.process_employee_updates(
                db_session, fineos_client, output_dir_path
            )
        else:
            process_result = eligibility_feed.process_all_employers(
                db_session, fineos_client, output_dir_path
            )

    return dataclasses.asdict(process_result)
