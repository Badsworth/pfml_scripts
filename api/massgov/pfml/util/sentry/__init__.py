import logging as python_logging  # noqa: B1
import os
import sys
from types import TracebackType
from typing import Dict, Optional, Tuple, Union

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)


def sanitize_sentry_event(event, hint):
    """ Remove parameter and local variable values from exception stacktraces.
        Sensitive values may be passed into methods -- we don't want them
        exposed in Sentry.
    """
    for exception in event.get("exception", {}).get("values", []):
        for frame in exception.get("stacktrace", {}).get("frames", []):
            frame.pop("vars", None)

    for exception in event.get("threads", {}).get("values", []):
        for frame in exception.get("stacktrace", {}).get("frames", []):
            frame.pop("vars", None)

    return event


# This is a util for initializing Sentry before all ECS tasks
def initialize_sentry():
    if os.environ.get("ENABLE_SENTRY", "0") == "1":
        sentry_logging = LoggingIntegration(
            # Send logs to Sentry as breadcrumbs, but don't capture them as error events.
            level=python_logging.INFO,  # noqa: B1
            event_level=None,
        )

        sentry_sdk.init(
            "https://624337ca44e9405f8884c4a3f5acc0c0@o514801.ingest.sentry.io/5628495",
            traces_sample_rate=1.0,
            before_send=sanitize_sentry_event,
            integrations=[sentry_logging],
        )


def log_and_capture_exception(msg: str, extra: Optional[Dict] = None) -> None:
    """ Sentry displays the error message in the UI, so injecting a new exception with a human-readable
        error message is the only way for errors to receive custom messages. This is important for easily
        distinguishing certain errors in the Sentry error dashboard.

        This does not affect the traceback or any other visible attribute in Sentry. Everything else,
        including the original exception class name, is retained and displayed.
    """

    info = sys.exc_info()
    info_with_readable_msg: Union[
        BaseException, Tuple[type, BaseException, Optional[TracebackType]]
    ]

    if info[0] is None:
        info_with_readable_msg = Exception(msg)
    else:
        info_with_readable_msg = (info[0], Exception(msg), info[2])

    logger.error(msg, extra=extra, exc_info=info_with_readable_msg)
