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
