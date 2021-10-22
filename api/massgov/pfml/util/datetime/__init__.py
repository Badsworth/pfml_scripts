import math
from datetime import date, datetime, time, timezone
from typing import NamedTuple, Optional, Union


class HoursAndMinutes(NamedTuple):
    hours: Optional[int]
    minutes: Optional[int]


def convert_minutes_to_hours_minutes(minutes: Optional[int]) -> HoursAndMinutes:
    """API manages time at the most granular level we expect (minutes), and
    converts this time at the interface level (e.g FINEOS API calls).

    For example: Portal can send 1.5 hours to the API in one field as 90 minutes,
    but FINEOS accepts this as two fields (1 hour, 30 minutes) so this utility
    supports this necessary conversion.
    """
    (hours, mins) = divmod(minutes, 60) if minutes is not None else (None, None)
    return HoursAndMinutes(hours=hours, minutes=mins)


def parse_date_YMD(value: Optional[Union[str, date]]) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, date):
        return value

    return datetime.strptime(value, "%Y%m%d").date()


def utcnow() -> datetime:
    """Current time in UTC tagged with timezone info marking it as UTC, unlike datetime.utcnow().

    See https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow
    """
    return datetime.now(timezone.utc)


def to_datetime(date_or_datetime: date) -> datetime:
    """Convert a date or datetime to a datetime, setting time to 00:00:00 UTC."""
    return datetime.combine(date_or_datetime, time.min, tzinfo=timezone.utc)


def get_period_in_days(period_start: date, period_end: date) -> int:
    period_start_date = period_start.date() if isinstance(period_start, datetime) else period_start
    period_end_date = period_end.date() if isinstance(period_end, datetime) else period_end

    # We add 1 to the period in days because we want to consider a week to be
    # 7 days inclusive. For example:
    #    Jan 1st - Jan 1st is 1 day even though no time passes.
    #    Jan 1st - Jan 2nd is 2 days
    #    Jan 1st - Jan 7th is 7 days (eg. Monday -> Sunday)
    #    Jan 1st - Jan 8th is 8 days (eg. Monday -> the next Monday)

    return (period_end_date - period_start_date).days + 1


def get_period_in_weeks(period_start: date, period_end: date) -> int:
    """
    Get the length of a period of time in weeks, rounded up (eg. 5 days -> 1 week, 8 days -> 2 weeks)
    """
    weeks = math.ceil(get_period_in_days(period_start, period_end) / 7.0)
    return weeks
