def sanitize_sentry_event(event, hint):
    """ Remove parameter and local variable values from exception stacktraces.
        Sensitive values may be passed into methods -- we don't want them
        exposed in Sentry.
    """

    for exception in event.get("exception", {}).get("values", []):
        for frame in exception.get("stacktrace", {}).get("frames", []):
            frame.pop("vars", None)

    for exception in event.get("threads", {}).get("values", []):
        for frame in exception.get("stacktrace", {}).get("frames", []):
            frame.pop("vars", None)

    return event
