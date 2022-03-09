from datetime import date, timedelta

import pytest

from massgov.pfml.api.eligibility.benefit_year_dates import get_benefit_year_dates


@pytest.mark.parametrize(
    "claim_start_date",
    [
        date(2021, 1, 4),  # M
        date(2021, 1, 5),  # Tue
        date(2021, 1, 6),  # W
        date(2021, 1, 7),  # Th
        date(2021, 1, 8),  # F
        date(2021, 1, 9),  # Sat
    ],
)
def test_get_benefit_year_dates_when_claim_is_monday_to_saturday(claim_start_date: date):

    dates = get_benefit_year_dates(claim_start_date)

    previous_sunday = claim_start_date - timedelta(days=(1 + claim_start_date.weekday()))
    assert dates.start_date == previous_sunday

    fifty_two_weeks_from_start = previous_sunday + timedelta(weeks=52, days=-1)
    assert dates.end_date == fifty_two_weeks_from_start


@pytest.mark.parametrize(
    "claim_start_date",
    [
        date(2021, 1, 10),  # Sun
        date(2021, 1, 17),  # Sun
        date(2021, 1, 24),  # Sun
        date(2021, 1, 31),  # Sun
        date(2021, 2, 7),  # Sun
        date(2021, 2, 14),  # Sun
    ],
)
def test_get_benefit_year_dates_when_claim_is_sunday(claim_start_date: date):
    dates = get_benefit_year_dates(claim_start_date)

    assert dates.start_date == claim_start_date

    fifty_two_weeks_from_start = claim_start_date + timedelta(weeks=52, days=-1)
    assert dates.end_date == fifty_two_weeks_from_start
