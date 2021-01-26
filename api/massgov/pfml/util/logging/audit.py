#
# Application-level audit logging.
#
# See https://docs.python.org/3/library/audit_events.html
# https://docs.python.org/3/library/sys.html#sys.addaudithook
# https://www.python.org/dev/peps/pep-0578/
#

import sys

import massgov.pfml.util.collections.dict
import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


def init_security_logging():
    sys.addaudithook(audit_hook)


IGNORE_AUDIT_EVENTS = {
    "builtins.id",
    "code.__new__",
    "compile",
    "exec",
    "import",
    "object.__getattr__",
    "object.__setattr__",
    "os.listdir",
    "os.scandir",
    "socket.__new__",
    "sys._current_frames",
    "sys._getframe",
    "sys.settrace",  # interferes with PyCharm debugger
}


def audit_hook(event_name, args):
    if event_name in IGNORE_AUDIT_EVENTS:
        return
    if event_name == "open" and isinstance(args[0], str) and "/__pycache__/" in args[0]:
        return
    if event_name == "os.chmod" and type(args[0]) is int:
        # Gunicorn generates a high volume of these events in normal operation (see workertmp.py)
        return
    # Disable audit log for timezone files. See API-1290
    if event_name == "open" and isinstance(args[0], str) and "/pytz/" in args[0]:
        return

    audit_log("%s %r" % (event_name, args))


def audit_log(message):
    """Log a message but only log recently repeated messages at intervals."""
    count = audit_message_count[message] = audit_message_count[message] + 1
    if count <= 10 or (count <= 100 and (count % 10) == 0) or (count % 100) == 0:
        logger.info(message, extra={"count": count})  # noqa: B1


audit_message_count = massgov.pfml.util.collections.dict.LeastRecentlyUsedDict()
