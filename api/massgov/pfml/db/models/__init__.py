#
# Database ORM models.
#

import time
import inspect

import massgov.pfml.util.logging

from . import applications, employees, industry_codes, payments, verifications  # noqa: F401
from ..lookup import LookupTable

logger = massgov.pfml.util.logging.get_logger(__name__)


def init_lookup_tables(db_session):
    """Initialize models in the database if necessary."""
    start_time = time.monotonic()

    for module in applications, employees, industry_codes, payments, verifications:
        sync_lookup_tables(db_session, module)

    db_session.commit()
    logger.info("sync took %.2fs", time.monotonic() - start_time)


def sync_lookup_tables(db_session, module):
    lookups = inspect.getmembers(module, lambda v: inspect.isclass(v) and issubclass(v, LookupTable))

    for lookup_class_name, lookup_class in lookups:
        if lookup_class_name == 'LookupTable':
            continue

        logger.info(f"Syncing {lookup_class_name}")
        lookup_class.sync_to_database(db_session)
