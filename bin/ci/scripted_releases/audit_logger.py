import logging
import sys
from datetime import datetime


def setup(file_loc):
    """
    Fancy wizardry for configuring an audit logger on top of the regular stdout logger.
    See https://docs.python.org/3/howto/logging-cookbook.html#multiple-handlers-and-formatters.

    :param file_loc: The absolute path where audit logs will be stored.
    """

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # write ALL logs to this file
    audit_logger = logging.FileHandler(
        f"{file_loc}/scripted_releases_audit_log_{datetime.now().strftime('%Y-%m-%d.%H:%M:%S')}.txt"
    )
    audit_logger.setLevel(logging.DEBUG)

    # write any log that's INFO or above to regular old stdout
    regular_logger = logging.StreamHandler(stream=sys.stdout)
    regular_logger.setLevel(logging.INFO)

    log_fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    for handler in [audit_logger, regular_logger]:
        handler.setFormatter(log_fmt)
        logger.addHandler(handler)

    logger.debug(f"Audit logger configured; writing logs to '{file_loc}'")
