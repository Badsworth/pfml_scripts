#
# Utility functions for configuring and interfacing with logging.
#

import atexit
import logging.config  # noqa: B1
import os
import platform
import pwd
import resource
import sys
import time
from datetime import datetime
from typing import Any, Dict, Generator, Iterable, Optional, TypeVar

from massgov.pfml.util.datetime import utcnow

from . import formatters, network

start_time = time.monotonic()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": formatters.JsonFormatter},},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"},},
    "root": {"handlers": ["console"], "level": "WARN"},
    "loggers": {
        "alembic": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "gunicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "gunicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "massgov.pfml": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "massgov.pfml.fineos": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "newrelic": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "werkzeug": {"handlers": ["console"], "level": "WARN", "propagate": False},
        # Log DB pool connection invalidations and recycle events. At DEBUG
        # level includes all connection checkin/checkouts to the pool.
        #
        # https://docs.sqlalchemy.org/en/13/core/engines.html#configuring-logging
        "sqlalchemy.pool": {"handlers": ["console"], "level": "INFO", "propagate": False,},
        # Log PostgreSQL NOTICE messages
        # https://docs.sqlalchemy.org/en/13/dialects/postgresql.html#notice-logging
        "sqlalchemy.dialects.postgresql": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def init(program_name):
    """Initialize the logging system."""
    logging.config.dictConfig(LOGGING)
    logger.info(
        "start %s: %s %s %s, hostname %s, pid %i, user %i(%s)",
        program_name,
        platform.python_implementation(),
        platform.python_version(),
        platform.system(),
        platform.node(),
        os.getpid(),
        os.getuid(),
        pwd.getpwuid(os.getuid()).pw_name,
        extra={
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
            "cpu_usable": (
                len(os.sched_getaffinity(0)) if "sched_getaffinity" in dir(os) else "unknown"
            ),
        },
    )
    logger.info("invoked as: %s", " ".join(original_argv))

    override_logging_levels()

    atexit.register(exit_handler, program_name)

    network.init()


def override_logging_levels():
    """Override default logging levels using settings in LOGGING_LEVEL environment variable.

    The format is "name1=level,name2=level". For example:

      LOGGING_LEVEL="massgov.pfml.fineos=DEBUG,sqlalchemy=INFO"
    """
    for override in os.environ.get("LOGGING_LEVEL", "").split(","):
        if "=" not in override:
            continue
        logger_name, _separator, logging_level = override.partition("=")
        logger.info("set level for %s to %s", logger_name, logging_level)
        logging.getLogger(logger_name).setLevel(logging_level)


def exit_handler(program_name):
    """Log a message at program exit."""
    t = time.monotonic() - start_time
    ru = resource.getrusage(resource.RUSAGE_SELF)
    logger.info(
        "exit %s: pid %i, real %.3fs, user %.2fs, system %.2fs, peak rss %iK",
        program_name,
        os.getpid(),
        t,
        ru.ru_utime,
        ru.ru_stime,
        ru.ru_maxrss,
    )


def get_logger(name):
    """Return a logger with the specified name, which must be a massgov module name."""
    if not name.startswith("massgov."):
        raise ValueError(
            "invalid logger name %r (try passing __package__ instead of __name__)" % name
        )
    return logging.getLogger(name)


_T = TypeVar("_T")


def log_every(
    log: Any,
    items: Iterable[_T],
    *,
    count: int = 100,
    total_count: Optional[int] = None,
    start_time: Optional[datetime] = None,
    item_name: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Generator[_T, Any, Any]:
    """Every `count` items, log a message about progress through `items`."""

    if not extra:
        extra = {}

    for index, item in enumerate(items, 1):
        if count and not index % count:
            if start_time:
                elapsed = (utcnow() - start_time).total_seconds()
                extra["start_time"] = start_time
                extra["elapsed_seconds"] = elapsed
                if elapsed != 0:
                    extra["rate_per_second"] = round(index / elapsed, 2)

            if total_count:
                extra["total_count"] = total_count
                extra["percent_complete"] = round((index / total_count) * 100, 2)

            if item_name:
                extra["item_name"] = item_name

            log.info(
                f"Processing {item_name or 'item'} {index} of {total_count or 'unknown total'}",
                extra=extra,
            )

        yield item


logger = get_logger(__name__)
original_argv = tuple(sys.argv)
