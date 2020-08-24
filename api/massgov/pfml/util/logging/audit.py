#
# Application-level audit logging
#

import logging  # noqa: B1
import sys

from massgov.pfml.util.logging import get_logger

logger = get_logger(__name__)


def init_security_logging():
    sys.addaudithook(audit_hook)


IGNORE_AUDIT_EVENTS = (
    "builtins.id",
    "os.listdir",
    "os.scandir",
    "compile",
    "import",
    "object.__getattr__",
    "object.__setattr__",
    "exec",
    "sys._getframe",
    "sys.settrace",  # interferes with PyCharm debugger
)


AUDIT_EVENT_TO_LEVEL = {"open": logging.INFO}  # noqa: B1


def audit_hook(event_name, args):
    if event_name in IGNORE_AUDIT_EVENTS:
        return
    if event_name == "open" and isinstance(args[0], str) and "/__pycache__/" in args[0]:
        return

    logger.log(
        AUDIT_EVENT_TO_LEVEL.get(event_name, logging.INFO),  # noqa: B1
        "pfml-audit-%s %r",
        event_name,
        args,
    )
