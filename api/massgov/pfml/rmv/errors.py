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
