#
# Database ORM models.
#

import time

import massgov.pfml.util.logging

from . import (  # noqa: F401
    applications,
    azure,
    employees,
    flags,
    geo,
    industry_codes,
    payments,
    state,
    verifications,
)

logger = massgov.pfml.util.logging.get_logger(__name__)


def init_lookup_tables(db_session):
    """Initialize models in the database if necessary."""
    start_time = time.monotonic()
    applications.sync_lookup_tables(db_session)
    geo.sync_lookup_tables(db_session)
    state.sync_lookup_tables(db_session)
    employees.sync_lookup_tables(db_session)
    flags.sync_lookup_tables(db_session)
    verifications.sync_lookup_tables(db_session)
    industry_codes.sync_lookup_tables(db_session)
    azure.sync_lookup_tables(db_session)
    logger.info("sync took %.2fs", time.monotonic() - start_time)
