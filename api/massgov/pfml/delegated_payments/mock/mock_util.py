from typing import Optional

from massgov.pfml.util.routing_number_validation import compute_checksum


def generate_routing_nbr_from_ssn(ssn: str) -> Optional[str]:
    if len(ssn) != 9 or not ssn.isnumeric():
        return None  # This'll cause issues for a test if you want this set

    # Routing numbers are validated via a checksum. Any place in
    # the code that requires a valid routing number and wants to maintain
    # consistency can do so by passing in the test SSN and consistently calculating
    # the routing number from it.

    checksum = compute_checksum(ssn)
    modulo = checksum % 10

    # SSN already passes and has a valid checksum, can reuse as-is
    if modulo == 0:
        return ssn

    # The modulo says how far over we are from the intended value.
    # The last digit of the routing number is simply added as-is
    # so we can calculate a new final digit to make it valid.

    last_digit = int(ssn[-1])
    if last_digit < modulo:
        last_digit += 10

    new_last_digit = last_digit - modulo

    return ssn[0:-1] + str(new_last_digit)
