#
# Exceptions for FINEOS client.
#
from typing import Optional


class FINEOSClientError(RuntimeError):
    """An exception occurred in an API call. This is the parent exception for all other FINEOSClient errors."""

    method_name: Optional[str]
    message: str


# FINEOS Fatal Errors
#
class FINEOSFatalError(FINEOSClientError):
    """Only a cause or status_code is expected. If a cause is provided, it should be
       a client-side error (client-side timeout.) Otherwise, it indicates a FINEOS response issue.
    """

    cause: Optional[Exception]
    response_status: Optional[int]

    def __init__(
        self,
        method_name: str,
        cause: Optional[Exception] = None,
        response_status: Optional[int] = None,
        message: str = "",
    ):
        self.cause = cause
        self.response_status = response_status
        self.method_name = method_name
        self.message = message

    def __str__(self) -> str:
        if self.cause:
            return "(%s) %s: %s: %s" % (
                self.method_name,
                type(self.cause).__name__,
                self.cause,
                self.message,
            )
        elif self.response_status:
            return "(%s) %s: %s: %s" % (
                self.method_name,
                type(self).__name__,
                self.response_status,
                self.message,
            )
        else:
            return "(%s) %s: %s" % (self.method_name, type(self).__name__, self.message)


class FINEOSFatalClientSideError(FINEOSFatalError):
    """A fatal exception occurred during an API call before we could receive a FINEOS response."""


class FINEOSFatalResponseError(FINEOSFatalError):
    """A fatal exception was received from the FINEOS API."""


class FINEOSFatalUnavailable(FINEOSFatalError):
    """The FINEOS API was unavailable during this request."""


# Non-fatal Errors
#
class FINEOSClientBadResponse(FINEOSClientError):
    """An API call returned an unexpected, but non-fatal, HTTP status."""

    expected_status: int
    response_status: int
    method_name: str
    message: str

    def __init__(
        self, method_name: str, expected_status: int, response_status: int, message: str = ""
    ):
        self.method_name = method_name
        self.expected_status = expected_status
        self.response_status = response_status
        self.message = message

    def __str__(self) -> str:
        return "(%s) expected %s, but got %s: %s" % (
            self.method_name,
            self.expected_status,
            self.response_status,
            self.message,
        )


# NOTE: This is currently only thrown manually for missing employers in read_employer,
#       and for missing employee occupations in register_api_user.
class FINEOSNotFound(FINEOSClientBadResponse):
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message


class FINEOSForbidden(FINEOSClientBadResponse):
    """The FINEOS API returned an authorization error"""
