#
# Utilities for handling year quarters.
#

import datetime

QUARTER_ENDS = ((3, 31), (6, 30), (8, 30), (12, 31))


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

    def series(self, count):
        """Generate a series of Quarter objects starting with the current one."""
        year = self.year
        quarter = self.quarter
        for _i in range(count):
            yield Quarter(year, quarter)
            quarter = quarter + 1
            if quarter == 5:
                year = year + 1
                quarter = 1

    def __repr__(self):
        return "Quarter(%i, %i)" % (self.year, self.quarter)

    def __str__(self):
        return self.as_date().strftime("%Y%m%d")

    def __eq__(self, other):
        return self.year == other.year and self.quarter == other.quarter

    def as_date(self):
        return datetime.date(self.year, self.month, self.day_of_month)
