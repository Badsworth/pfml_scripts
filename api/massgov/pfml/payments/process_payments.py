import argparse
import json
import sys

import massgov.pfml.db
import massgov.pfml.payments.payments_util
import massgov.pfml.payments.regenerate
import massgov.pfml.util.batch.log
import massgov.pfml.util.logging as logging
from massgov.pfml.payments import payments_util
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


def ctr_process():
    """ Run the whole program """
    audit.init_security_logging()
    logging.init(__name__)

    logger.info("Payments CTR Process placeholder ECS task")


def fineos_process():
    """Process FINEOS Payment Exports"""
    audit.init_security_logging()
    logging.init(__name__)

    logger.info("Payments FINEOS Process placeholder ECS task")


def regenerate():
    """Entry point for task to regenerate a new VCC or GAX for a Batch ID."""
    audit.init_security_logging()
    logging.init("payments_regenerate")

    args = regenerate_parse_args()
    config = payments_util.get_s3_config()
    db_session_raw = massgov.pfml.db.init()

    try:
        with massgov.pfml.util.batch.log.log_entry(
            db_session_raw, "Payments regenerate", ""
        ) as log_entry, massgov.pfml.db.session_scope(db_session_raw) as db_session:
            log_entry.report = json.dumps({"year": args.year, "batch_id": args.batch})
            massgov.pfml.payments.regenerate.regenerate_batch(
                args.year, args.batch, config.pfml_ctr_outbound_path, db_session
            )
    except Exception as ex:
        logger.exception("%s", ex)
        sys.exit(1)


def regenerate_parse_args():
    """Parse command line arguments for regenerate."""
    parser = argparse.ArgumentParser(description="Regenerate a payments file")
    parser.add_argument("year", type=batch_year, help="Year of batch to regenerate")
    parser.add_argument("batch", type=str, help="Batch identifier to regenerate")
    return parser.parse_args()


def batch_year(arg):
    """Parse a batch year command line argument."""
    value = int(arg)
    if not 2020 <= value < 3000:
        raise argparse.ArgumentTypeError("must be a valid year after 2020")
    return value


if __name__ == "__main__":
    ctr_process()
