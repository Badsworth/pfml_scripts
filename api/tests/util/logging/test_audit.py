#
# Tests for massgov.pfml.util.logging.audit.
#

import logging  # noqa: B1

from massgov.pfml.util.logging import audit


def test_audit_hook(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    # Should appear in audit log.
    audit.audit_hook("open", ("/dev/null", None, 123000))

    # Various common cases that should not appear in audit log (normal behaviour & too noisy).
    audit.audit_hook("compile", (b"def _(): pass", "<unknown>"))
    audit.audit_hook(
        "open", ("/app/massgov/pfml/api/__pycache__/status.cpython-38.pyc", "r", 500010)
    )
    audit.audit_hook("os.chmod", (7, 1, -1))
    audit.audit_hook(
        "open", ("/app/.venv/lib/python3.8/site-packages/pytz/zoneinfo/US/Eastern", "r", 524288)
    )

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        ("audit_log", "AUDIT", "open ('/dev/null', None, 123000)")
    ]


def test_audit_log_repeated_message(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    for _i in range(500):
        audit.audit_log("abc")

    assert [(r.funcName, r.levelname, r.message, r.count) for r in caplog.records] == [
        ("audit_log", "AUDIT", "abc", 1),
        ("audit_log", "AUDIT", "abc", 2),
        ("audit_log", "AUDIT", "abc", 3),
        ("audit_log", "AUDIT", "abc", 4),
        ("audit_log", "AUDIT", "abc", 5),
        ("audit_log", "AUDIT", "abc", 6),
        ("audit_log", "AUDIT", "abc", 7),
        ("audit_log", "AUDIT", "abc", 8),
        ("audit_log", "AUDIT", "abc", 9),
        ("audit_log", "AUDIT", "abc", 10),
        ("audit_log", "AUDIT", "abc", 20),
        ("audit_log", "AUDIT", "abc", 30),
        ("audit_log", "AUDIT", "abc", 40),
        ("audit_log", "AUDIT", "abc", 50),
        ("audit_log", "AUDIT", "abc", 60),
        ("audit_log", "AUDIT", "abc", 70),
        ("audit_log", "AUDIT", "abc", 80),
        ("audit_log", "AUDIT", "abc", 90),
        ("audit_log", "AUDIT", "abc", 100),
        ("audit_log", "AUDIT", "abc", 200),
        ("audit_log", "AUDIT", "abc", 300),
        ("audit_log", "AUDIT", "abc", 400),
        ("audit_log", "AUDIT", "abc", 500),
    ]
