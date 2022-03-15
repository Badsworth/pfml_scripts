#
# Mock FINEOS field generators for use by MockFINEOSClient or in unit tests.
#

from typing import Union


def fake_customer_no(fein: Union[str, int]) -> int:
    """Generate a fake FINEOS employer id (a.k.a. CustomerNo) deterministically from a FEIN."""
    return int(fein) + 44000000
