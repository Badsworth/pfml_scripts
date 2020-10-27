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
        "massgov.pfml.fineos": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
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
        extra={"hostname": platform.node()},
    )
    logger.info("invoked as: %s", " ".join(original_argv))

    atexit.register(exit_handler, program_name)

    network.init()


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


logger = get_logger(__name__)
original_argv = tuple(sys.argv)
