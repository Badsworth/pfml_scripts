from datetime import date, timedelta

from massgov.pfml.util.pydantic import PydanticBaseModel


class BenefitYearDateRange(PydanticBaseModel):
    start_date: date
    end_date: date


# Given the start date for a claim, a new benefit year will start on the Sunday before the leave starts
# and runs for 52 weeks
def get_benefit_year_dates(claim_start_date: date) -> BenefitYearDateRange:
    # Sunday is weekday 6 https://docs.python.org/3/library/datetime.html#datetime.date.weekday
    # If the claim starts on a Sunday, no adjustment is needed. Otherwise we need to
    # subtract 1 + the weekday number to get back to the previous Sunday
    # (e.g. Tuesday is weekday 1, and we need to subtract two days to get back to Sunday).
    start_date = claim_start_date
    if start_date.weekday() != 6:
        start_date = start_date - timedelta(days=(1 + start_date.weekday()))

    # To prevent a benefit year from starting on the same day another ends
    # The end date should be 52 weeks minus 1 day. On exactly 52 weeks a
    # new benefit year will start.
    end_date = start_date + timedelta(weeks=52, days=-1)
    return BenefitYearDateRange(start_date=start_date, end_date=end_date)
