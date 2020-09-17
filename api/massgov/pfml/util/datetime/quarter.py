#
# Utilities for handling year quarters.
#

import datetime
import math

QUARTER_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))


class Quarter:
    """Representation of a year / quarter (e.g. 2020-Q1)."""

    def __init__(self, year, quarter):
        if quarter not in (1, 2, 3, 4):
            raise ValueError("Invalid quarter, must be 1-4")
        self.year = year
        self.quarter = quarter
        end_date = QUARTER_ENDS[quarter - 1]
        self.month = end_date[0]
        self.day_of_month = end_date[1]

    @classmethod
    def from_date(cls, date: datetime.date) -> "Quarter":
        """Construct the Quarter that contains the given date."""
        quarter = math.ceil(date.month / 3)
        return Quarter(date.year, quarter)

    def series(self, count):
        """Generate a series of Quarter objects starting with the current one."""
        current = self
        for _i in range(count):
            yield current
            current = current.next_quarter()

    def series_backwards(self, count):
        """Generate a series of Quarter objects going backwards starting with the current one."""
        current = self
        for _i in range(count):
            yield current
            current = current.previous_quarter()

    def __repr__(self):
        return "Quarter(%i, %i)" % (self.year, self.quarter)

    def __str__(self):
        return self.as_date().strftime("%Y%m%d")

    def __eq__(self, other):
        return self.year == other.year and self.quarter == other.quarter

    def __hash__(self):
        return self.year * 4 + self.quarter

    def as_date(self):
        """Return the last day of the quarter as a date."""
        return datetime.date(self.year, self.month, self.day_of_month)

    def start_date(self):
        """Return the first day of the quarter as a date."""
        return datetime.date(self.year, (self.quarter - 1) * 3 + 1, 1)

    def next_quarter(self):
        """Return the Quarter following this one."""
        year = self.year
        quarter = self.quarter + 1
        if quarter == 5:
            year += 1
            quarter = 1
        return Quarter(year, quarter)

    def previous_quarter(self):
        """Return the Quarter before this one."""
        year = self.year
        quarter = self.quarter - 1
        if quarter == 0:
            year -= 1
            quarter = 4
        return Quarter(year, quarter)

    def subtract_quarters(self, count):
        """Return the Quarter count quarters before this one."""
        result = self
        for entry in self.series_backwards(count + 1):
            result = entry
        return result
