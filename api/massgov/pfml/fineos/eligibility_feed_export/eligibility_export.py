#!/usr/bin/python3
#
# Lambda function to export eligibility feed to fineos.
#

import massgov.pfml.util.logging as logging
from massgov.pfml import db

logger = logging.get_logger("massgov.pfml.fineos.eligibility_feed_export")


def handler(event, context):
    """Lambda handler function."""
    logging.init(__name__)

    logger.info("Starting fineos eligibility feed export run")

    # TODO replace with real implementation below
    db_session_raw = get_raw_db_session()
    with db.session_scope(db_session_raw) as db_session:  # noqa: F841
        return {"status": "ok"}


def get_raw_db_session():
    config = db.get_config()
    db_session_raw = db.init(config)

    return db_session_raw
