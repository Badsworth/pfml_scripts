#
# Exceptions for FINEOS client.
#
from typing import Optional


class FINEOSClientError(RuntimeError):
    """An exception occurred in an API call."""

    cause: Exception
    method_name: Optional[str]

    def __init__(self, cause: Exception, method_name: str = ""):
        self.cause = cause
        self.method_name = method_name

    def __str__(self) -> str:
        return "%s: %s" % (type(self.cause).__name__, self.cause)


class FINEOSClientBadResponse(FINEOSClientError):
    """An API call returned an unexpected HTTP status."""

    expected_status: int
    response_status: int
    method_name: Optional[str]

    def __init__(self, expected_status: int, response_status: int, method_name: str = ""):
        self.expected_status = expected_status
        self.response_status = response_status
        self.method_name = method_name

    def __str__(self) -> str:
        return "expected %s, but got %s" % (self.expected_status, self.response_status)


class FINEOSNotFound(FINEOSClientError):

    message: str

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message
