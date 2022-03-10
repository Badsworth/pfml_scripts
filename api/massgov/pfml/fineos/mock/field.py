#
# Mock FINEOS field generators for use by MockFINEOSClient or in unit tests.
#

from typing import Union

from massgov.pfml.types import Fein

def fake_customer_no(fein: Union[Fein, str, int]) -> int:
    if isinstance(fein, Fein):
        return int(fein.to_unformatted_str()) + 44000000

    """Generate a fake FINEOS employer id (a.k.a. CustomerNo) deterministically from a FEIN."""
    return int(fein) + 44000000
