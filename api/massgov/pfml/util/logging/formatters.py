#
# Custom logging formatters.
#

import datetime
import json
import logging  # noqa: B1
import re

import flask
import newrelic.api.time_trace

from . import decodelog

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
            record.mass_pfml_agent_id = flask.request.headers.get("Mass-PFML-Agent-ID", "")

        super(JsonFormatter, self).format(record)

        output = {
            key: str_mask_pii(key, value)
            for key, value in record.__dict__.items()
            if key not in EXCLUDE_ATTRIBUTES and value is not None
        }

        # Inject user metadata without PII masking
        if flask.has_request_context():
            # Warning: do not access current_user as that may result in SQLAlchemy calls, but this
            # logging call may have happened due to a database failure.

            user_attributes = flask.g.get("current_user_log_attributes")
            azure_user_sub_id = flask.g.get("azure_user_sub_id")

            if user_attributes:
                output.update(user_attributes)
            if azure_user_sub_id:
                output.update({"azure_user.sub_id": azure_user_sub_id})

        # Inject New Relic tracing metadata for Logs in Context features.
        # This is not the suggested way to implement it, but the NewRelicContextFormatter
        # has a bunch of stuff we probably don't want, some of which we explicitly exclude
        # in our own formatter.
        #
        # Instead, just grab the linking metadata and pop it into our output.
        #
        # Reference:
        # https://github.com/newrelic/newrelic-python-agent/blob/main/newrelic/api/log.py
        #
        output.update(newrelic.api.time_trace.get_linking_metadata())
        return json.dumps(output, separators=MOST_COMPACT_JSON_SEPARATORS)


def str_mask_pii(key, value):
    """Convert value to str and replace suspected PII with placeholder text."""
    if key in ALLOW_NO_MASK:
        return str(value)
    return TIN_RE.sub("*********", str(value))


class DevelopFormatter(logging.Formatter):  # noqa: B1
    """A logging formatter which formats each line as text."""

    def format(self, record):
        super(DevelopFormatter, self).format(record)

        return decodelog.format_line(
            datetime.datetime.utcfromtimestamp(record.created),
            record.name,
            record.funcName,
            record.levelname,
            record.message,
            record.__dict__,
        )
