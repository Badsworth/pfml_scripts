#
# Write a log of batch job progress and results to the database.
#

import contextlib
import json
import time
from dataclasses import asdict

import massgov.pfml.util.datetime
import massgov.pfml.util.logging
import massgov.pfml.util.newrelic.events
from massgov.pfml.db.models.employees import ImportLog

logger = massgov.pfml.util.logging.get_logger(__name__)


def create_log_entry(db_session, source, import_type, report=None):
    """Creating a report log entry in the database"""
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
    logger.info("Added report to import log", extra={"import_log_id": import_log.import_log_id})
    return import_log


def update_log_entry(db_session, existing_import_log, status, report):
    """Update an existing import log entry with the supplied report, and send that entry as event data to New Relic"""
    existing_import_log.status = status
    existing_import_log.report = json.dumps(asdict(report), indent=2)
    existing_import_log.end = massgov.pfml.util.datetime.utcnow()

    db_session.merge(existing_import_log)
    db_session.commit()
    logger.info("Finished saving import report in log")

    log_report_to_newrelic(existing_import_log)


METRIC_COMMIT_INTERVAL = 5  # Seconds between writes to import_log.


class LogEntry:
    """Context manager for writing batch job progress and results to the database."""

    def __init__(self, db_session, source, import_type=""):
        self.db_session = db_session
        self.import_log = create_log_entry(db_session, source, import_type)
        self.metrics = {}
        self.last_commit = 0.0

    def __enter__(self):
        """Enter the runtime context, returning this object as a context manager.

        For example:
            with LogEntry(...) as log_entry:
                ...
                log_entry.set_metrics({"total": 100})
                ...
                log_entry.increment("ok")

        See https://docs.python.org/3/library/stdtypes.html#typecontextmanager
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context, committing final import log to database."""
        logger.info(
            "final metrics",
            extra={
                "import_log_id": self.import_log.import_log_id,
                "source": self.import_log.source,
                **self.metrics,
            },
        )

        if exc_type is None:
            self.import_log.status = "success"
            self._set_metrics_import_log_report()
        else:
            self.import_log.status = "error"
            self._set_metrics_import_log_report()

            error_message = "%s: %s" % (exc_type.__name__, str(exc_val))
            set_import_log_with_error_message(self.import_log, error_message)

        self.import_log.end = massgov.pfml.util.datetime.utcnow()
        self.db_session.commit()

        log_report_to_newrelic(self.import_log)

        # Continue propagating the exception after this method.
        return False

    def set_metrics(self, metrics):
        """Set name/value pairs in the report. Commits to database at time intervals."""
        self.metrics.update(**metrics)
        self._commit_metrics()

    def increment(self, name):
        """Increment an integer count in the report. Commits to database at time intervals."""
        if name not in self.metrics:
            self.metrics[name] = 0
        self.metrics[name] += 1
        self._commit_metrics()

    def _commit_metrics(self):
        """Commit current state to the database at a limited frequency."""
        # Only commit if some time has passed so that every call to set_metrics() or increment()
        # isn't slow.
        if time.monotonic() - self.last_commit < METRIC_COMMIT_INTERVAL:
            return
        self._set_metrics_import_log_report()
        self.db_session.commit()
        self.last_commit = time.monotonic()
        logger.info(
            "progress metrics",
            extra={"import_log_id": self.import_log.import_log_id, **self.metrics},
        )

    def _set_metrics_import_log_report(self):
        """Set the import_log.report string from member variables."""
        self.import_log.report = json.dumps(self.metrics, indent=2)


@contextlib.contextmanager
def log_entry(db_session, source, import_type):
    import_log = create_log_entry(db_session, source, import_type)

    try:
        yield import_log
        import_log.status = "success"
    except Exception as ex:
        import_log.status = "error"

        error_message = "%s: %s" % (type(ex).__name__, str(ex))
        set_import_log_with_error_message(import_log, error_message)

        raise
    finally:
        import_log.end = massgov.pfml.util.datetime.utcnow()
        db_session.commit()

        log_report_to_newrelic(import_log)


def set_import_log_with_error_message(import_log: ImportLog, error_message: str) -> None:
    existing_report = json.loads(import_log.report) if import_log.report is not None else {}
    import_log.report = json.dumps({"message": error_message, **existing_report}, indent=2)


def log_report_to_newrelic(import_log: ImportLog) -> None:
    if import_log.report:
        report_with_metadata = json.loads(import_log.report)
    else:
        report_with_metadata = {}

    report_with_metadata.update(
        {
            "job.id": import_log.import_log_id,
            "job.data_source": import_log.source,
            "job.job_type": import_log.import_type,
            "job.start": import_log.start if import_log.start else None,
            "job.end": import_log.end if import_log.end else None,
        }
    )
    massgov.pfml.util.newrelic.events.log_newrelic_event(report_with_metadata)
