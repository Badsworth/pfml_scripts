#
# Exceptions for ServiceNow client.
#
from typing import Dict, Optional, Type

import requests


class ServiceNowError(RuntimeError):
    """An exception occurred in an API call. This is the parent exception for all other ServiceNowClient errors."""

    message: Optional[str]
    response_status: Optional[int]
    url: str

    def __init__(self, url: str, response_status: Optional[int] = None, message: str = ""):
        self.response_status = response_status
        self.url = url
        self.message = message

    def __str__(self) -> str:
        return "(%s) %s: %s: %s" % (
            self.url,
            type(self).__name__,
            self.response_status,
            self.message,
        )


class ServiceNowFatalError(RuntimeError):
    """Exception when Service Now call failed without returning a status_code"""

    url: str
    cause: Exception

    def __init__(self, url: str, cause: Exception):
        self.url = url
        self.cause = cause

    def __str__(self) -> str:
        return "(%s) %s: %s" % (self.url, type(self.cause).__name__, self.cause)


class ServiceNowUnavailable(ServiceNowError):
    """The ServiceNow API was unavailable during this request."""


MAP_SERVICE_NOW_ERROR_REQUEST_STATUS_CODE: Dict[int, Type[ServiceNowError]] = {
    requests.codes.SERVICE_UNAVAILABLE: ServiceNowUnavailable,
    requests.codes.GATEWAY_TIMEOUT: ServiceNowUnavailable,
}
