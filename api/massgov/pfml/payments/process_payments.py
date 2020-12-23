import argparse
import json

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
    db_session = massgov.pfml.db.init()

    try:
        with massgov.pfml.util.batch.log.log_entry(
            db_session, "Payments regenerate", ""
        ) as log_entry:
            log_entry.report = json.dumps({"batch_id": args.batch})
            massgov.pfml.payments.regenerate.regenerate_batch(args.batch, config, db_session)
    except RuntimeError as ex:
        logger.error("%s", ex)
    except Exception as ex:
        logger.exception("%s", ex)


def regenerate_parse_args():
    """Parse command line arguments for regenerate."""
    parser = argparse.ArgumentParser(description="Regenerate a payments file")
    parser.add_argument("batch", type=str, help="Batch identifier to regenerate")
    return parser.parse_args()


if __name__ == "__main__":
    ctr_process()
