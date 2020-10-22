#
# Listen for SQLAlchemy handle_error events and sanitize the exception text.
#
# This is a protection to reduce the chance of data values appearing in logs.
#
# For details, see
# https://docs.sqlalchemy.org/en/13/core/events.html#sqlalchemy.events.ConnectionEvents.handle_error
#

import sqlalchemy
from sqlalchemy.engine.base import Engine

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


@sqlalchemy.event.listens_for(Engine, "handle_error")
def sqlalchemy_event_handle_error(exception_context: sqlalchemy.engine.ExceptionContext) -> None:
    """Listen for the "handle_error" event and remove detail from exception text"""
    logger.info(
        "sqlalchemy exception %s, original exception %s",
        type(exception_context.sqlalchemy_exception),
        type(exception_context.original_exception),
    )
    remove_detail_from_exception(exception_context.original_exception)
    remove_detail_from_exception(exception_context.sqlalchemy_exception)


def remove_detail_from_exception(exception):
    """Remove text following "DETAIL" from an exception.

    Error messages from PostgreSQL look like this:
        duplicate key value violates unique constraint "tax_identifier_tax_identifier_key"
        DETAIL:  Key (tax_identifier)=(999999999) already exists.

    This removes the DETAIL section to reduce the chance of data values appearing in logs.
    """
    if exception is None:
        return
    # Normally args is a single element tuple containing the error text, but process the entire
    # tuple just in case.
    exception.args = tuple(remove_detail_from_arg(arg) for arg in exception.args)


def remove_detail_from_arg(arg):
    """Remove text following "DETAIL" from a string, passing through non-strings unmodified."""
    if type(arg) == str:
        return arg.partition("DETAIL")[0].strip()
    return arg
