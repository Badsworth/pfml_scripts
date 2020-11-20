#
# Database ORM models.
#

import time

import massgov.pfml.util.logging

from . import applications, employees, verifications

logger = massgov.pfml.util.logging.get_logger(__name__)


def init_lookup_tables(db_session):
    """Initialize models in the database if necessary."""
    start_time = time.monotonic()
    applications.sync_lookup_tables(db_session)
    employees.sync_lookup_tables(db_session)
    verifications.sync_lookup_tables(db_session)
    logger.info("sync took %.2fs", time.monotonic() - start_time)
