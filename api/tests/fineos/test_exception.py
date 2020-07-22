#
# Tests for massgov.pfml.fineos.exception.
#

import massgov.pfml.fineos.exception


def test_fineos_client_error_str():
    cause = RuntimeError("test")
    exception = massgov.pfml.fineos.exception.FINEOSClientError(cause)

    assert str(exception) == "RuntimeError: test"


def test_fineos_client_bad_response_str():
    exception = massgov.pfml.fineos.exception.FINEOSClientBadResponse(200, 500)

    assert str(exception) == "expected 200, but got 500"
