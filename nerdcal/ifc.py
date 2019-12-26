"""International Fixed Calendar (IFC)

See: https://en.wikipedia.org/wiki/International_Fixed_Calendar"""

from bisect import bisect
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, tzinfo
import time as _time
from typing import List, Optional, Union

from nerdcal.utils import *

MIN_YEAR = 1
MAX_YEAR = 9999
MAX_ORDINAL = 3652059  # IFCDate.max.toordinal()
DAYS_IN_YEAR = 365
MIN_MONTH = 1
MAX_MONTH = 13
DAYS_IN_MONTH = 28
DAYS_IN_WEEK = 7


def _days_in_month(year: int, month: int) -> int:
    "year, month -> number of days in that month in that year."
    assert MIN_MONTH <= month <= MAX_MONTH, month
    if (month == 6 and is_leap_year(year)) or (month == 13):
        return DAYS_IN_MONTH + 1
    return DAYS_IN_MONTH

def _days_before_month(is_leap: bool) -> List[int]:
    """Gives list of number of days before the start of each month."""
    if is_leap:
        return [28 * i for i in range(6)] + [28 * i + 1 for i in range(6, 13)]
    return [28 * i for i in range(13)]


@dataclass(order = True, frozen = True)
class IFCDate:
    """Concrete date type for IFC, analogous to datetime.date.

    There are 13 months consisting of 28 days each.
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
        if not 1 <= self.month <= 13:
            raise ValueError(f'month must be in {MIN_MONTH}..{MAX_MONTH}', self.month)
        dim = _days_in_month(self.year, self.month)
        if not 1 <= self.day <= dim:
            raise ValueError(f'day must be in 1..{dim}', self.day)

    # Month and weekday names

    @classmethod
    def month_names(cls) -> List[str]:
        """Full names of each month."""
        return ['January', 'February', 'March', 'April', 'May', 'June', 'Sol', 'July', 'August', 'September', 'October', 'November', 'December']

    @classmethod
    def month_abbrevs(cls) -> List[str]:
        """Abbreviated names of each month."""
        return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Sol', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    @classmethod
    def weekday_names(cls) -> List[str]:
        """Full names of each weekday."""
        return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    @classmethod
    def weekday_abbrevs(cls) -> List[str]:
        """Abbreviated names of each weekday."""
        return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    # Additional constructors

    @classmethod
    def fromtimestamp(cls, t: float) -> 'IFCDate':
        "Construct a date from a POSIX timestamp (like time.time())."
        return cls.fromordinal(datetime.fromtimestamp(t).toordinal())

    @classmethod
    def today(cls) -> 'IFCDate':
        "Construct a date from time.time()."
        return cls.fromtimestamp(_time.time())

    @classmethod
    def fromordinal(cls, n: int) -> 'IFCDate':
        """Construct an IFCDate from an ordinal number, where day 1 is January 1 of year 1."""
        n -= 1  # convert to 0-up
        n400, n = divmod(n, DI400Y)
        n100, n = divmod(n, DI100Y)
        n4, n = divmod(n, DI4Y)
        n1, n = divmod(n, DAYS_IN_YEAR)
        year = n400 * 400 + n100 * 100 + n4 * 4 + n1 + 1
        if (n1 == 4) or (n100 == 4):
            return cls(year - 1, 13, 29)
        leapyear = n1 == 3 and (n4 != 24 or n100 == 3)
        assert leapyear == is_leap_year(year)
        dbm = _days_before_month(leapyear)
        month = bisect(dbm, n)
        day = n - dbm[month - 1]
        return cls(year, month, day + 1)

    @classmethod
    def fromisoformat(cls, date_string: str) -> 'IFCDate':
        """Construct an IFCDate from the output of IFCDate.isoformat()."""
        if not isinstance(date_string, str):
            raise TypeError('fromisoformat: argument must be str')
        try:
            (year, month, day) = parse_isoformat_date(date_string)
        except:
            raise ValueError(f'Invalid isoformat string: {date_string!r}')
        return cls(year, month, day)

    @classmethod
    def fromdate(cls, date: date) -> 'IFCDate':
        """Construct an IFCDate from a datetime.date object."""
        return cls.fromordinal(date.toordinal())

    # Standard conversions

    def timetuple(self) -> _time.struct_time:
        "Return local time tuple compatible with time.localtime()."
        return self.todate().timetuple()

    def toordinal(self) -> int:
        """Convert to an ordinal number, where day 1 is January 1 of year 1."""
        return days_before_year(self.year) + _days_before_month(is_leap_year(self.year))[self.month - 1] + self.day

    def todate(self) -> date:
        """Convert to a datetime.date object."""
        return date.fromordinal(self.toordinal())

    def replace(self, year: int = None, month: int = None, day: int = None) -> 'IFCDate':
        """Return a new IFCDate with new values for the specified fields."""
        return type(self)(year or self.year, month or self.month, day or self.day)

    # Computations

    def __add__(self, other: timedelta) -> 'IFCDate':
        "Add an IFCDate to a timedelta."
        if isinstance(other, timedelta):
            o = self.toordinal() + other.days
            if 0 < o <= MAX_ORDINAL:
                return IFCDate.fromordinal(o)
            raise OverflowError("result out of range")
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other: Union[IFCDate, timedelta]) -> timedelta:
        """Subtract two IFCDates, or an IFCDate and a timedelta."""
        if isinstance(other, timedelta):
            return self + timedelta(-other.days)
        if isinstance(other, IFCDate):
            days1 = self.toordinal()
            days2 = other.toordinal()
            return timedelta(days1 - days2)
        return NotImplemented

    def is_leap_year(self) -> bool:
        """Return True if the year is a leap year."""
        return is_leap_year(self.year)

    def weekday(self) -> int:
        "Return day of the week as a number 0..6 (if a proper weekday), 7 (if Year Day), or 8 (if Leap Day)."""
        if (self.month, self.day) == (13, 29):
            return 7
        elif (self.month, self.day) == (6, 29):
            return 8
        day_of_year = self.toordinal() - days_before_year(self.year)
        if (self.month >= 7) and self.is_leap_year():
            return day_of_year % DAYS_IN_WEEK
        return (day_of_year - 1) % DAYS_IN_WEEK

    # Conversions to string

    def _ctime_date(self) -> str:
        if (self.month, self.day) == (6, 29):
            return 'Leap Day  '
        elif (self.month, self.day) == (13, 29):
            return 'Year Day  '
        else:
            weekday = self.weekday()
            weekday_name = self.weekday_abbrevs()[weekday]
            month_name = self.month_abbrevs()[self.month - 1]
            return '{} {} {:2d}'.format(weekday_name, month_name, self.day)

    def ctime(self) -> str:
        "Return ctime() style string."
        date_str = self._ctime_date()
        return '{} 00:00:00 {:04d}'.format(date_str, self.year)

    def strftime(self, fmt: str) -> str:
        "Format using strftime()."
        # TODO: revamp strftime to handle IFC month/day numbers/names
        raise NotImplementedError

    def isoformat(self) -> str:
        """Return the date formatted according to ISO.

        This is 'YYYY-MM-DD'."""
        return f'{self.year:04d}-{self.month:02d}-{self.day:02d}'

    __str__ = isoformat

IFCDate.min = IFCDate(1, 1, 1)
IFCDate.max = IFCDate(9999, 13, 29)
IFCDate.resolution = timedelta(days = 1)


@dataclass(order = True, frozen = True)
class IFCDatetime:
    """Concrete datetime type for IFC, analogous to datetime.datetime.

    IFCDatetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    The year, month and day arguments are required."""

    # define associated types
    _date_class = IFCDate
    _time_class = time

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
    def fromtimestamp(cls, t: float, tz: Optional[tzinfo] = None) -> 'IFCDatetime':
        """Construct an IFCDatetime from a POSIX timestamp (like time.time()).

        A timezone info object may be passed in as well."""
        return cls.fromdatetime(datetime.fromtimestamp(t, tz = tz))

    @classmethod
    def utcfromtimestamp(cls, t: float) -> 'IFCDatetime':
        """Construct a naive UTC IFCDatetime from a POSIX timestamp."""
        return cls.fromdatetime(datetime.utcfromtimestamp(t))

    @classmethod
    def now(cls, tz: Optional[tzinfo] = None) -> 'IFCDatetime':
        "Construct an IFCDatetime from time.time() and optional time zone info."
        return cls.fromdatetime(datetime.now(tz))

    @classmethod
    def utcnow(cls) -> 'IFCDatetime':
        "Construct a UTC IFCDatetime from time.time()."
        return cls.fromdatetime(datetime.utcnow())

    @classmethod
    def combine(cls, date: IFCDate, time: time, tzinfo: Optional[tzinfo] = None) -> 'IFCDatetime':
        "Construct an IFCDatetime from a given IFCDate and a given time."
        if not isinstance(date, cls._date_class):
            raise TypeError(f"date argument must be a {cls._date_class} instance")
        if not isinstance(time, cls._time_class):
            raise TypeError(f"time argument must be a {cls._time_class} instance")
        if tzinfo is None:
            tzinfo = time.tzinfo
        return cls(date.year, date.month, date.day, time.hour, time.minute, time.second, time.microsecond, tzinfo)

    @classmethod
    def fromisoformat(cls, date_str: str) -> 'IFCDatetime':
        """Construct an IFCDatetime from the output of IFCDatetime.isoformat()."""
        if not isinstance(date_str, str):
            raise TypeError('fromisoformat: argument must be str')
        # Split this at the separator
        dstr = date_str[0:10]
        tstr = date_str[11:]
        date = cls._date_class.fromisoformat(dstr)
        time = cls._time_class.fromisoformat(tstr)
        return cls.combine(date, time)

    @classmethod
    def fromdatetime(cls, dt: datetime) -> 'IFCDatetime':
        """Construct an IFCDatetime from a datetime.datetime object."""
        date = cls._date_class.fromdate(dt.date())
        return cls.combine(date, dt.timetz())

    @classmethod
    def strptime(cls, date_str: str, format: str) -> 'IFCDatetime':
        'string, format -> new IFCDatetime parsed from a string (like time.strptime()).'
        import _strptime
        # TODO: implement this
        raise NotImplementedError

    # Standard conversions

    def timetuple(self) -> _time.struct_time:
        """Return local time tuple compatible with time.localtime()."""
        return self.todatetime().timetuple()

    def timestamp(self) -> float:
        """Return POSIX timestamp as float."""
        return self.todatetime().timestamp()

    def utctimetuple(self):
        """Return UTC time tuple compatible with time.gmtime()."""
        return self.todatetime().utctimetuple()

    def date(self) -> IFCDate:
        """Return the IFCDate part."""
        return self._date_class(self.year, self.month, self.day)

    def time(self) -> time:
        """Return the time part, with tzinfo None."""
        return self._time_class(self.hour, self.minute, self.second, self.microsecond)

    def timetz(self) -> time:
        """Return the time part, with same tzinfo."""
        return self._time_class(self.hour, self.minute, self.second, self.microsecond, self.tzinfo)

    def todatetime(self) -> datetime:
        """Convert to a datetime.datetime object."""
        return datetime.combine(self.date().todate(), self.timetz())

    def replace(self, year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None, second: int = None, microsecond: int = None, tzinfo: tzinfo = None) -> 'IFCDatetime':
        """Return a new IFCDatetime with new values for the specified fields."""
        return type(self)(year or self.year, month or self.month, day or self.day, hour or self.hour, minute or self.minute, second or self.second, microsecond or self.microsecond, tzinfo or self.tzinfo)

    def astimezone(self, tz: Optional[tzinfo] = None) -> 'IFCDatetime':
        """Convert to a different timezone (by default, the local one)."""
        return type(self).fromdatetime(self.todatetime().astimezone())

    def utcoffset(self) -> Optional[timedelta]:
        """Return the timezone offset as timedelta positive east of UTC (negative west of UTC)."""
        return self.todatetime().utcoffset()

    def tzname(self) -> str:
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        return self.todatetime().tzname()

    def __add__(self, other: timedelta) -> 'IFCDatetime':
        """Add an IFCDatetime and a timedelta."""
        return type(self).fromdatetime(self.todatetime() + other)

    __radd__ = __add__

    def __sub__(self, other: Union['IFCDatetime', timedelta]):
        """Subtract two IFCDatetimes, or an IFCDatetime and a timedelta."""
        if isinstance(other, IFCDatetime):
            return self.todatetime() - other.todatetime()
        elif isinstance(other, timedelta):
            return self + -other
        return NotImplemented

    # Conversions to string

    def ctime(self) -> str:
        "Return ctime() style string."
        date_str = self.date()._ctime_date()
        return '{} {:02d}:{:02d}:{:02d} {:04d}'.format(date_str, self.hour, self.minute, self.second, self.year)

    def isoformat(self, sep: str = 'T', timespec: str = 'auto') -> str:
        """Return the time formatted according to ISO.

        The full format looks like 'YYYY-MM-DD HH:MM:SS.mmmmmm'.
        By default, the fractional part is omitted if self.microsecond == 0.

        If self.tzinfo is not None, the UTC offset is also attached, giving
        giving a full format of 'YYYY-MM-DD HH:MM:SS.mmmmmm+HH:MM'.

        Optional argument sep specifies the separator between date and
        time, default 'T'.

        The optional argument timespec specifies the number of additional
        terms of the time to include.
        """
        s = self.todatetime().isoformat(sep = sep, timespec = timespec)
        return self.date().isoformat() + s[10:]

    def __str__(self) -> str:
        "Convert to string, for str()."
        return self.isoformat(sep = ' ')

IFCDatetime.min = IFCDatetime(1, 1, 1)
IFCDatetime.max = IFCDatetime(9999, 13, 29, 23, 59, 59, 999999)
IFCDatetime.resolution = timedelta(microseconds=1)