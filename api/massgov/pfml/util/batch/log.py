#
# Write a log of batch job progress and results to the database.
#

import contextlib
import json
from dataclasses import asdict

import massgov.pfml.util.datetime
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import ImportLog

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_log_entry(db_session, source, import_type, report=None):
    """Creating a a report log entry in the database"""
    import_log = ImportLog(
        source=source,
        import_type=import_type,
        status="in progress",
        start=massgov.pfml.util.datetime.utcnow(),
        end=None,
    )
    if report:
        import_log.report = json.dumps(asdict(report), indent=2)
    db_session.add(import_log)
    db_session.flush()
    db_session.commit()
    db_session.refresh(import_log)
    logger.info("Added report to import log")
    return import_log


def update_log_entry(db_session, existing_import_log, status, report):
    """Update an existing import log entry with the supplied report"""
    existing_import_log.status = status
    existing_import_log.report = json.dumps(asdict(report), indent=2)
    existing_import_log.end = massgov.pfml.util.datetime.utcnow()
    db_session.merge(existing_import_log)
    db_session.commit()
    logger.info("Finished saving import report in log")


@contextlib.contextmanager
def log_entry(db_session, source, import_type):
    import_log = create_log_entry(db_session, source, import_type)

    try:
        yield import_log
        import_log.status = "success"
    except Exception as ex:
        import_log.status = "error"
        import_log.report = "%s: %s" % (type(ex).__name__, str(ex))
        raise
    finally:
        import_log.end = massgov.pfml.util.datetime.utcnow()
        db_session.commit()
