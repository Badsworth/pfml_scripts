#
# Utility functions for configuring and interfacing with logging.
#

import logging.config  # noqa: B1
import os
import platform
import pwd
import sys

from . import formatters, network

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": formatters.JsonFormatter},},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"},},
    "root": {"handlers": ["console"], "level": "WARN"},
    "loggers": {
        "alembic": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "massgov.pfml": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "massgov.pfml.fineos": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "werkzeug": {"handlers": ["console"], "level": "WARN", "propagate": False},
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

    network.init()


def get_logger(name):
    """Return a logger with the specified name, which must be a massgov module name."""
    if not name.startswith("massgov."):
        raise ValueError(
            "invalid logger name %r (try passing __package__ instead of __name__)" % name
        )
    return logging.getLogger(name)


logger = get_logger(__name__)
original_argv = tuple(sys.argv)
