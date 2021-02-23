#
# Tests for massgov.pfml.fineos.exception.
#

import massgov.pfml.fineos.exception


def test_fineos_fatal_error_str_cause():
    cause = RuntimeError("test")
    exception = massgov.pfml.fineos.exception.FINEOSFatalError(cause)

    assert str(exception) == "RuntimeError: test"


def test_fineos_fatal_error_str_status():
    exception = massgov.pfml.fineos.exception.FINEOSFatalError(response_status=500)

    assert str(exception) == "FINEOSFatalError: 500"


def test_fineos_client_bad_response_str():
    exception = massgov.pfml.fineos.exception.FINEOSClientBadResponse(200, 500)

    assert str(exception) == "expected 200, but got 500"
