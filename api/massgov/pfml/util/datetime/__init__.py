from datetime import date, datetime, timezone
from typing import Optional, Union


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
