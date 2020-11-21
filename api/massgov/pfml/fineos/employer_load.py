from dataclasses import asdict

import massgov.pfml.fineos.employers
import massgov.pfml.util.batch.log
import massgov.pfml.util.logging as logging
from massgov.pfml import db, fineos
from massgov.pfml.util.logging import audit

logger = logging.get_logger(__name__)


def handler():
    """ECS handler function."""
    audit.init_security_logging()
    logging.init(__name__)

    db_session_raw = db.init()

    fineos_client = fineos.create_client()

    logger.info("Starting loading employers to FINEOS.")

    with db.session_scope(db_session_raw, close=True) as db_session:
        report_log_entry = massgov.pfml.util.batch.log.create_log_entry(
            db_session, "Employer load", "full"
        )

        report = massgov.pfml.fineos.employers.load_all(db_session, fineos_client)

        massgov.pfml.util.batch.log.update_log_entry(
            db_session, report_log_entry, "success", report
        )

    logger.info("Finished loading employers to FINEOS.", extra={"report": asdict(report)})
