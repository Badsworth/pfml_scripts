#
# Database ORM models.
#

from . import applications, employees


def init_lookup_tables(db_session):
    """Initialize models in the database if necessary."""
    applications.sync_lookup_tables(db_session)
    employees.sync_lookup_tables(db_session)
