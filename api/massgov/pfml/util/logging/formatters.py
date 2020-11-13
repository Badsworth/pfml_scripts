#
# Custom logging formatters.
#

import json
import logging  # noqa: B1
import re

import flask

# Attributes of LogRecord to exclude from the JSON formatted lines. An exclusion list approach is
# used so that all "extra" attributes can be included in a line.
EXCLUDE_ATTRIBUTES = {
    "args",
    "exc_info",
    "filename",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "msg",
    "pathname",
    "processName",
    "relativeCreated",
}

# Attributes of LogRecord to allow through without masking suspected PII.
ALLOW_NO_MASK = {"count", "created", "process", "thread", "account_key"}

# Regular expression to match a tax identifier, 9 digits with optional dashes.
TIN_RE = re.compile(r"\b(\d-?){8}\d\b", re.ASCII)

MOST_COMPACT_JSON_SEPARATORS = (",", ":")


class JsonFormatter(logging.Formatter):  # noqa: B1
    """A logging formatter which formats each line as JSON."""

    def format(self, record):
        # Inject Flask request information. See
        # https://flask.palletsprojects.com/en/1.1.x/logging/#injecting-request-information
        if flask.has_request_context():
            record.method = flask.request.method
            record.path = flask.request.path
            record.request_id = flask.request.headers.get("x-amzn-requestid", "")
        super(JsonFormatter, self).format(record)
        output = {
            key: str_mask_pii(key, value)
            for key, value in record.__dict__.items()
            if key not in EXCLUDE_ATTRIBUTES and value is not None
        }
        return json.dumps(output, separators=MOST_COMPACT_JSON_SEPARATORS)


def str_mask_pii(key, value):
    """Convert value to str and replace suspected PII with placeholder text."""
    if key in ALLOW_NO_MASK:
        return str(value)
    return TIN_RE.sub("*********", str(value))
