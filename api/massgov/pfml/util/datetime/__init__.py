from datetime import date, datetime
from typing import Optional, Union


def parse_date_YMD(value: Optional[Union[str, date]]) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, date):
        return value

    return datetime.strptime(value, "%Y%m%d").date()
