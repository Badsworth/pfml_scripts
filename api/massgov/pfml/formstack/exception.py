class FormstackClientError(RuntimeError):
    cause: Exception

    def __init__(self, cause: Exception):
        self.cause = cause

    def __str__(self) -> str:
        return "%s: %s" % (type(self.cause).__name__, self.cause)


class FormstackBadResponse(FormstackClientError):
    expected_status: int
    response_status: int

    def __init__(self, expected_status: int, response_status: int):
        self.expected_status = expected_status
        self.response_status = response_status

    def __str__(self) -> str:
        return "expected %s, but got %s" % (self.expected_status, self.response_status)
