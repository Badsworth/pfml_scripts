#
# Logging of function or method calls.
#

import functools


def log_function_calls(fn, logger):
    """Wrapper to log all calls and return values of the given function."""

    @functools.wraps(fn)
    def function_call_log(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
            logger.info(
                "%s ⇒ %s",
                fn.__qualname__,
                type(result).__qualname__,
                extra={
                    "call.function": fn.__qualname__,
                    "call.args": args,
                    "call.kwargs": kwargs,
                    "call.return": repr(result),
                },
            )
            return result
        except Exception as err:
            logger.warning(
                "%s ⇒ exception %s",
                fn.__qualname__,
                type(err).__qualname__,
                extra={
                    "call.function": fn.__qualname__,
                    "call.args": args,
                    "call.kwargs": kwargs,
                    "call.exception": repr(err),
                },
            )
            raise

    return function_call_log


def log_all_method_calls(cls, logger):
    """Log all method calls in the given class."""
    for attr in cls.__dict__:
        if callable(getattr(cls, attr)):
            setattr(cls, attr, log_function_calls(getattr(cls, attr), logger))
