"""Positivist Calendar

Devised by the philosopher Auguste Comte in 1849.

See: https://en.wikipedia.org/wiki/Positivist_calendar"""

from calendar import isleap
from typing import List

from nerdcal._base import days_before_year
from nerdcal.ifc import DAYS_IN_MONTH, DAYS_IN_WEEK, MIN_MONTH, MAX_MONTH, IFCDate, IFCDatetime


class PositivistDate(IFCDate):
    """Concrete date type for Comte's positivist calendar.

    There are 13 months, consisting of 28 days each.
    The months are all named after prominent historic figures (e.g. religious leaders, philosophers, authors).
    At the end of the year is an intercalary day, the Festival of the Dead.
    On leap years, an additional day is added, the Festival of Holy Women.
    For simplicity, these days will be represented as Bichat (the last month) 29 and 30."""

    # Helpers

    @classmethod
    def _days_in_month(cls, year: int) -> List[int]:
        leap_year = isleap(year)
        return [DAYS_IN_MONTH + 1 + (1 if leap_year else 0) if (month == 13) else DAYS_IN_MONTH for month in range(MIN_MONTH, MAX_MONTH + 1)]

    # Month and weekday names

    @classmethod
    def month_names(cls) -> List[str]:
        return ['Moses', 'Homer', 'Aristotle', 'Archimedes', 'Caesar', 'Saint Paul', 'Charlemagne', 'Dante', 'Gutenberg', 'Shakespeare', 'Descartes', 'Frederic', 'Bichat']

    @classmethod
    def month_abbrevs(cls) -> List[str]:
        return ['Mos', 'Hom', 'Ari', 'Arc', 'Csr', 'Spl', 'Chl', 'Dan', 'Gut', 'Shk', 'Des', 'Fre', 'Bic']

    @classmethod
    def weekday_names(cls) -> List[str]:
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    @classmethod
    def weekday_abbrevs(cls) -> List[str]:
        return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Computations

    def weekday(self) -> int:
        if (self.month, self.day) == (13, 29):
            return 7
        elif (self.month, self.day) == (13, 30):
            return 8
        day_of_year = self.toordinal() - days_before_year(self.year)
        return (day_of_year - 1) % DAYS_IN_WEEK

    # Conversions to string

    def _ctime_date(self) -> str:
        if (self.month, self.day) == (13, 29):
            # Festival of the Dead
            return 'Fest. Dead'
        elif (self.month, self.day) == (13, 30):
            # Festival of Holy Women
            return 'Fest. Wom.'
        weekday = self.weekday()
        weekday_name = self.weekday_abbrevs()[weekday]
        month_name = self.month_abbrevs()[self.month - 1]
        return '{} {} {:2d}'.format(weekday_name, month_name, self.day)


class PositivistDatetime(IFCDatetime):
    """Concrete datetime type for Comte's positivist calendar."""

    _date_class = PositivistDate
