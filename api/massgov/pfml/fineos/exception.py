#
# Exceptions for FINEOS client.
#


class FINEOSClientError(RuntimeError):
    """An exception occurred in an API call."""

    def __init__(self, cause=None):
        self.cause = cause

    def __str__(self):
        return "%s: %s" % (type(self.cause).__name__, self.cause)


class FINEOSClientBadResponse(FINEOSClientError):
    """An API call returned an unexpected HTTP status."""

    def __init__(self, expected_status, response_status):
        self.expected_status = expected_status
        self.response_status = response_status

    def __str__(self):
        return "expected %s, but got %s" % (self.expected_status, self.response_status)
