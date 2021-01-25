#
# Eligibility - base period calculations.
#

from typing import Container, Tuple

from massgov.pfml.util.datetime import quarter


def compute_base_period(
    effective_quarter: quarter.Quarter, quarters_with_wage_data: Container[quarter.Quarter]
) -> Tuple[quarter.Quarter, ...]:
    """Compute the "base period" for the given effective quarter and container of quarters.

    Returns a tuple of the 4 Quarters in the base period.
    """
    if effective_quarter in quarters_with_wage_data:
        base_period_end = effective_quarter
    elif effective_quarter.previous_quarter() in quarters_with_wage_data:
        base_period_end = effective_quarter.previous_quarter()
    else:
        base_period_end = effective_quarter.subtract_quarters(2)

    return tuple(base_period_end.series_backwards(4))
