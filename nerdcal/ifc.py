"""International Fixed Calendar (IFC)

See: https://en.wikipedia.org/wiki/International_Fixed_Calendar"""

from bisect import bisect
from calendar import isleap
from dataclasses import dataclass
from datetime import time, timedelta, tzinfo
from itertools import accumulate
from operator import add
from typing import List, Optional

from nerdcal._base import check_int, Date, Datetime, days_before_year

MIN_YEAR = 1
MAX_YEAR = 9999
MAX_ORDINAL = 3652059  # IFCDate.max.toordinal()
MIN_MONTH = 1
MAX_MONTH = 13
DAYS_IN_MONTH = 28
DAYS_IN_WEEK = 7


@dataclass(order = True, frozen = True)
class IFCDate(Date):
    """Concrete date type for IFC.

    There are 13 months, consisting of 28 days each.
    The additional month, Sol, occurs between June and July.
    However, for simplicity, Year Day will be represented as December 29, and Leap Day will be represented as June 29."""
    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        """Perform validation on the year, month, and day.
        Raise a ValueError if any entries are invalid."""
        check_int(self.year)
        check_int(self.month)
        check_int(self.day)
        if not MIN_YEAR <= self.year <= MAX_YEAR:
            raise ValueError(f'year must be in {MIN_YEAR}..{MAX_YEAR}', self.year)
        if not MIN_MONTH <= self.month <= MAX_MONTH:
            raise ValueError(f'month must be in {MIN_MONTH}..{MAX_MONTH}', self.month)
        dim = self._days_in_month(self.year)[self.month - 1]
        if not (1 <= self.day <= dim):
            raise ValueError(f'day must be in 1..{dim}', self.day)

    # Accessors

    def get_year(self) -> int:
        return self.year

    # Helpers

    @classmethod
    def _days_in_month(cls, year: int) -> List[int]:
        """List of number of days in each month."""
        return [DAYS_IN_MONTH + 1 if ((month == 6) and isleap(year)) or (month == 13) else DAYS_IN_MONTH for month in range(MIN_MONTH, MAX_MONTH + 1)]

    @classmethod
    def _days_before_month(cls, year: int) -> List[int]:
        """List of number of days before the start of each month."""
        return list(accumulate([0] + cls._days_in_month(year), add))[:-1]

    # Month and weekday names

    @classmethod
    def month_names(cls) -> List[str]:
        """Full names of each month."""
        return ['January', 'February', 'March', 'April', 'May', 'June', 'Sol', 'July', 'August', 'September', 'October', 'November', 'December']

    @classmethod
    def month_abbrevs(cls) -> List[str]:
        """Abbreviated names of each month (3 letters, for use with ctime())."""
        return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Sol', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    @classmethod
    def weekday_names(cls) -> List[str]:
        return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    @classmethod
    def weekday_abbrevs(cls) -> List[str]:
        return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    # Additional constructors

    @classmethod
    def _from_year_and_ordinal(cls, year: int, n: int) -> 'IFCDate':
        dbm = cls._days_before_month(year)
        month = bisect(dbm, n)
        day = n - dbm[month - 1]
        return cls(year, month, day + 1)

    # Standard conversions

    def toordinal(self) -> int:
        return days_before_year(self.year) + self._days_before_month(self.year)[self.month - 1] + self.day

    def replace(self, year: int = None, month: int = None, day: int = None) -> 'IFCDate':
        """Return a new IFCDate with new values for the specified fields."""
        return type(self)(year or self.year, month or self.month, day or self.day)

    # Computations

    def weekday(self) -> int:
        """Return day of the week as a number 0..6 (if a proper weekday), 7 (if Year Day), or 8 (if Leap Day)."""
        if (self.month, self.day) == (13, 29):
            return 7
        elif (self.month, self.day) == (6, 29):
            return 8
        day_of_year = self.toordinal() - days_before_year(self.year)
        if (self.month >= 7) and self.is_leap_year():
            return day_of_year % DAYS_IN_WEEK
        return (day_of_year - 1) % DAYS_IN_WEEK

    # Conversions to string

    def strftime(self, fmt: str) -> str:
        # TODO: revamp strftime to handle IFC month/day numbers/names
        raise NotImplementedError

    def __str__(self) -> str:
        if (self.month, self.day) == (6, 29):
            return 'Leap Day  '
        elif (self.month, self.day) == (13, 29):
            return 'Year Day  '
        weekday = self.weekday()
        weekday_name = self.weekday_abbrevs()[weekday]
        month_name = self.month_abbrevs()[self.month - 1]
        return '{} {} {:2d}'.format(weekday_name, month_name, self.day)

IFCDate.min = IFCDate(1, 1, 1)
IFCDate.max = IFCDate(9999, 13, 29)
IFCDate.resolution = timedelta(days = 1)


@dataclass(order = True, frozen = True)
class IFCDatetime(Datetime):
    """Concrete datetime type for IFC.

    IFCDatetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    The year, month, and day arguments are required."""
    _date_class = IFCDate

    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    second: int = 0
    microsecond: int = 0
    tzinfo: Optional[tzinfo] = None

    def __post_init__(self) -> None:
        """Perform validation on the entries.
        Raise a ValueError if any entries are invalid."""
        # validate by constructing sub-objects
        self._date_class(self.year, self.month, self.day)
        self._time_class(self.hour, self.minute, self.second, self.microsecond, self.tzinfo)

    # Additional constructors

    @classmethod
    def _combine(cls, date: IFCDate, time: time, tzinfo: Optional[tzinfo] = None) -> 'IFCDatetime':
        return cls(date.year, date.month, date.day, time.hour, time.minute, time.second, time.microsecond, tzinfo)

    @classmethod
    def strptime(cls, date_string: str, format: str) -> 'IFCDatetime':
        import _strptime
        # TODO: implement this
        raise NotImplementedError

    # Standard conversions

    def date(self) -> 'IFCDate':
        return self._date_class(self.year, self.month, self.day)

    def time(self) -> time:
        return self._time_class(self.hour, self.minute, self.second, self.microsecond)

    def timetz(self) -> time:
        return self._time_class(self.hour, self.minute, self.second, self.microsecond, self.tzinfo)

    def replace(self, year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None, second: int = None, microsecond: int = None, tzinfo: tzinfo = None) -> 'IFCDatetime':
        return type(self)(year or self.year, month or self.month, day or self.day, hour or self.hour, minute or self.minute, second or self.second, microsecond or self.microsecond, tzinfo or self.tzinfo)

IFCDatetime.min = IFCDatetime(1, 1, 1)
IFCDatetime.max = IFCDatetime(9999, 13, 29, 23, 59, 59, 999999)
IFCDatetime.resolution = timedelta(microseconds = 1)