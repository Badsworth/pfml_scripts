#
# Tests for massgov.pfml.util.logging.wrapper.
#

import logging  # noqa: B1

import pytest

import massgov.pfml.util.logging.wrapper


class DummyClass:
    def alpha(self):
        return 1234

    def bravo(self, x, y, z):
        raise RuntimeError("failure")


def test_log_all_method_calls(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    logger = logging.getLogger("test_log_all_method_calls")  # noqa: B1
    massgov.pfml.util.logging.wrapper.log_all_method_calls(DummyClass, logger)

    instance = DummyClass()
    instance.alpha()
    other_instance = DummyClass()
    with pytest.raises(RuntimeError):
        other_instance.bravo(1, 2, 3)

    assert [
        (
            r.funcName,
            r.levelname,
            r.message,
            getattr(r, "call.function"),
            getattr(r, "call.args"),
            getattr(r, "call.kwargs"),
            getattr(r, "call.return", None),
            getattr(r, "call.exception", None),
        )
        for r in caplog.records
    ] == [
        (
            "function_call_log",
            "INFO",
            "DummyClass.alpha ⇒ int",
            "DummyClass.alpha",
            (instance,),
            {},
            "1234",
            None,
        ),
        (
            "function_call_log",
            "WARNING",
            "DummyClass.bravo ⇒ exception RuntimeError",
            "DummyClass.bravo",
            (other_instance, 1, 2, 3),
            {},
            None,
            "RuntimeError('failure')",
        ),
    ]
