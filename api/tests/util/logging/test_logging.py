#
# Tests for massgov.pfml.util.logging.
#
import collections
import json
import logging
import logging.config
import re

import flask
import pytest

import massgov.pfml.util.logging


def test_init(caplog, monkeypatch):
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(logging.config, "dictConfig", lambda config: None)

    massgov.pfml.util.logging.init("test_logging_1234")

    assert len(caplog.record_tuples) == 2
    start_entry = caplog.record_tuples[0]
    invoked_as_entry = caplog.record_tuples[1]
    assert start_entry[0] == "massgov.pfml.util.logging"
    assert invoked_as_entry[0] == "massgov.pfml.util.logging"
    assert start_entry[1] == logging.INFO
    assert invoked_as_entry[1] == logging.INFO
    assert start_entry[2].startswith("start test_logging_1234:")
    assert re.match(
        r"^start test_logging_1234: \w+ [0-9.]+ \w+, hostname \S+, pid \d+, user \d+\(\w+\)$",
        start_entry[2],
    )
    assert re.match(r"^invoked as:", invoked_as_entry[2])


def test_get_logger():
    logger = massgov.pfml.util.logging.get_logger("massgov.pfml.test.logging")
    assert logger.name == "massgov.pfml.test.logging"


def test_get_logger_invalid_name():
    with pytest.raises(ValueError):
        massgov.pfml.util.logging.get_logger("test_logging_5678")


def test_log_message_with_extra(capsys):
    massgov.pfml.util.logging.init("test_logging_1234")

    logger = massgov.pfml.util.logging.get_logger("massgov.pfml.test.logging")
    logger.info("hello test %i", 3456, extra={"request_id": "xxyyzz99"})

    stderr = capsys.readouterr().err
    lines = stderr.split("\n")
    last_line = json.loads(lines[-2])
    assert last_line.keys() == {
        "name",
        "levelname",
        "funcName",
        "created",
        "thread",
        "threadName",
        "process",
        "request_id",
        "message",
    }
    assert last_line["name"] == "massgov.pfml.test.logging"
    assert last_line["levelname"] == "INFO"
    assert last_line["funcName"] == "test_log_message_with_extra"
    assert last_line["threadName"] == "MainThread"
    assert last_line["request_id"] == "xxyyzz99"
    assert last_line["message"] == "hello test 3456"


def test_log_message_with_circular_extra(capsys):
    massgov.pfml.util.logging.init("test_logging_1234")
    circular_dict = {0: "hello"}
    circular_dict[1] = circular_dict

    logger = massgov.pfml.util.logging.get_logger("massgov.pfml.test.logging")
    logger.info("hello test %i", 5678, extra={"cd": circular_dict})

    stderr = capsys.readouterr().err
    lines = stderr.split("\n")
    last_line = json.loads(lines[-2])
    assert last_line.keys() == {
        "name",
        "levelname",
        "funcName",
        "created",
        "thread",
        "threadName",
        "process",
        "cd",
        "message",
    }
    assert last_line["name"] == "massgov.pfml.test.logging"
    assert last_line["levelname"] == "INFO"
    assert last_line["funcName"] == "test_log_message_with_circular_extra"
    assert last_line["threadName"] == "MainThread"
    assert last_line["cd"] == "{0: 'hello', 1: {...}}"
    assert last_line["message"] == "hello test 5678"


def test_log_message_with_exception(capsys):
    massgov.pfml.util.logging.init("test_logging_1234")

    logger = massgov.pfml.util.logging.get_logger("massgov.pfml.test.logging")

    try:
        non_existent_function()
    except NameError:
        logger.exception("test exception")

    stderr = capsys.readouterr().err
    lines = stderr.split("\n")
    last_line = json.loads(lines[-2])
    assert last_line.keys() == {
        "name",
        "levelname",
        "exc_text",
        "funcName",
        "created",
        "thread",
        "threadName",
        "process",
        "message",
    }
    assert last_line["name"] == "massgov.pfml.test.logging"
    assert last_line["levelname"] == "ERROR"
    assert re.match(
        """^Traceback \\(most recent call last\\):
  File ".*", line \\d+, in test_log_message_with_exception
    non_existent_function\\(\\)
NameError: name 'non_existent_function' is not defined$""",
        last_line["exc_text"],
    )
    assert last_line["funcName"] == "test_log_message_with_exception"
    assert last_line["threadName"] == "MainThread"
    assert last_line["message"] == "test exception"


FakeRequest = collections.namedtuple("FakeRequest", ("method", "path"))


def test_log_message_with_flask_request_context(capsys, monkeypatch):
    massgov.pfml.util.logging.init("test_logging_1234")
    monkeypatch.setattr(flask, "has_request_context", lambda: True)
    monkeypatch.setattr(flask, "request", FakeRequest("POST", "/test/path"))

    logger = massgov.pfml.util.logging.get_logger("massgov.pfml.test.logging")
    logger.info("test request context")

    stderr = capsys.readouterr().err
    lines = stderr.split("\n")
    last_line = json.loads(lines[-2])
    assert last_line.keys() == {
        "name",
        "levelname",
        "funcName",
        "created",
        "thread",
        "threadName",
        "process",
        "method",
        "path",
        "message",
    }
    assert last_line["name"] == "massgov.pfml.test.logging"
    assert last_line["levelname"] == "INFO"
    assert last_line["funcName"] == "test_log_message_with_flask_request_context"
    assert last_line["threadName"] == "MainThread"
    assert last_line["method"] == "POST"
    assert last_line["path"] == "/test/path"
    assert last_line["message"] == "test request context"
