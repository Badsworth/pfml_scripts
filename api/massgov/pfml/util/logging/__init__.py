#
# Utility functions for configuring and interfacing with logging.
#

import logging.config
import os
import platform
import pwd
import sys

from . import formatters

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {"json": {"()": formatters.JsonFormatter},},
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "json"},
    },
    "root": {"handlers": ["console"], "level": "INFO",},
    "loggers": {"massgov.pfml": {"handlers": ["console"], "level": "INFO", "propagate": False,},},
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


def get_logger(name):
    """Return a logger with the specified name, which must be a massgov module name."""
    if not name.startswith("massgov."):
        raise ValueError(
            "invalid logger name %r (try passing __package__ instead of __name__)" % name
        )
    return logging.getLogger(name)


logger = get_logger(__name__)
original_argv = tuple(sys.argv)
