#
# Tests for massgov.pfml.api.eligibility.
#

import datetime
import decimal
import uuid

import pytest

from massgov.pfml.api.eligibility import eligibility


@pytest.mark.integration
def test_compute_financial_eligibility_no_data(test_db_session):
    result = eligibility.compute_financial_eligibility(
        test_db_session,
        uuid.UUID(int=1),
        uuid.UUID(int=2),
        "100000055",
        datetime.date(2021, 1, 1),
        datetime.date(2021, 1, 1),
        "Employed",
    )

    assert result == eligibility.EligibilityResponse(
        financially_eligible=False,
        description="Claimant wages under minimum",
        total_wages=decimal.Decimal("0"),
        state_average_weekly_wage=decimal.Decimal("1487.78"),
        unemployment_minimum=decimal.Decimal("5400"),
        employer_average_weekly_wage=decimal.Decimal("0"),
    )
