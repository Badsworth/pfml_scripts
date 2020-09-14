#
# Lambda function to export eligibility feed to FINEOS.
#
import dataclasses
import os

import massgov.pfml.fineos.eligibility_feed as eligibility_feed
import massgov.pfml.util.logging as logging
from massgov.pfml import db, fineos

logging.init(__name__)
logger = logging.get_logger(__name__)

db_session_raw = db.init()
fineos_client = fineos.create_client()


def handler(_event, _context):
    logger.info("Starting FINEOS eligibility feed export run")

    output_dir_path = os.getenv("OUTPUT_DIRECTORY_PATH")

    if not output_dir_path:
        logger.warning("OUTPUT_DIRECTORY_PATH environment variable not set. Aborting run.")
        raise Exception("OUTPUT_DIRECTORY_PATH environment variable not set. Aborting run.")

    with db.session_scope(db_session_raw, close=True) as db_session:
        process_result = eligibility_feed.process_updates(
            db_session, fineos_client, output_dir_path
        )

    return dataclasses.asdict(process_result)
