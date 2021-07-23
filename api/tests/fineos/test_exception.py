#
# Tests for massgov.pfml.fineos.exception.
#

import massgov.pfml.fineos.exception


def test_fineos_fatal_error_str_cause():
    cause = RuntimeError("test")
    method_name = "Test"
    message = "Failed"
    exception = massgov.pfml.fineos.exception.FINEOSFatalError(method_name, cause, message=message)

    assert str(exception) == "(Test) RuntimeError: test: Failed"


def test_fineos_fatal_error_str_status():
    method_name = "Test"
    message = "FatalError"
    exception = massgov.pfml.fineos.exception.FINEOSFatalError(
        method_name, response_status=500, message=message
    )

    assert str(exception) == "(Test) FINEOSFatalError: 500: FatalError"


def test_fineos_client_bad_response_str():
    method_name = "Test"
    exception = massgov.pfml.fineos.exception.FINEOSClientBadResponse(
        method_name, 200, 500, "Internal Server Error"
    )

    assert str(exception) == "(Test) expected 200, but got 500: Internal Server Error"
