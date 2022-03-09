from datetime import datetime, timedelta
from typing import Tuple

BusinessDayMask = Tuple[int, int, int, int, int, int, int]


class BusinessDay:
    def __init__(self, date: datetime, mask: BusinessDayMask = (1, 1, 1, 1, 1, 0, 0)):
        self.mask = mask
        self._date = date

    def days_between(self, date: datetime) -> int:
        current_date = self._date.date()
        end_date = date.date()

        if current_date > end_date:
            current_date = date.date()
            end_date = self._date.date()

        business_days_since_last_import = 0
        while current_date < end_date:
            day_i = current_date.weekday()
            if self.mask[day_i] == 1:
                business_days_since_last_import += 1
            current_date = current_date + timedelta(days=1)

        return business_days_since_last_import
