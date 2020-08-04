class RmvError(RuntimeError):
    pass


class RmvUnknownError(RmvError):
    """An exception occurred in an API call."""

    def __init__(self, cause=None):
        self.cause = cause

    def __str__(self):
        if self.cause:
            return "%s: %s" % (type(self.cause).__name__, self.cause)
        else:
            return self.__class__.__name__


class RmvValidationError(RmvError):
    """An exception occurred due to serverside validation."""

    def __str__(self):
        return f"{self.__class__.__name__}: Validation failed for RMV request"


class RmvMultipleCustomersError(RmvError):
    """An exception occurred due to multiple matching identities."""

    def __str__(self):
        return f"{self.__class__.__name__}: Multiple customers found."


class RmvNoCredentialError(RmvError):
    """An exception occurred due to multiple matching identities."""

    def __str__(self):
        return f"{self.__class__.__name__}: No driver account or license/permit found."


class RmvUnexpectedResponseError(RmvError):
    """An unexpected server response was received."""

    def __init__(self, acknowledgement):
        self.acknowledgement = acknowledgement

    def __str__(self):
        return f"{self.__class__.__name__}: {self.acknowledgement}"
