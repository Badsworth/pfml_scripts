from typing import NoReturn


def assert_never(value: NoReturn) -> NoReturn:
    """Meant only as a typechecking aid.

    See https://github.com/python/mypy/issues/6366

    Should become unnecessary in Python 3.10 with
    https://www.python.org/dev/peps/pep-0634/ implemented.
    """
    assert False, f"Unhandled value: {value} ({type(value).__name__})"  # noqa: B011
