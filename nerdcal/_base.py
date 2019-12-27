"""Abstract base classes for dates and datetimes in different calendar systems."""

from abc import ABC, abstractclassmethod, abstractmethod
from calendar import isleap
from datetime import date, datetime, time, timedelta, tzinfo
import time as _time
from typing import Any, List, Optional, Union


#####################
# HELPERS/CONSTANTS #
#####################

def check_int(value: Any) -> None:
    """Checks that a value is an integer, raising a ValueError otherwise."""
    if isinstance(value, int):
        return
    raise ValueError('an integer is required (got type {})'.format(type(value).__name__))

def days_before_year(year: int) -> int:
    """Given a year, returns number of days before the first day of that year."""
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400

DI400Y = days_before_year(401)    # number of days in 400 years
DI100Y = days_before_year(101)    # number of days in 100 years
DI4Y   = days_before_year(5)      # number of days in 4 years
DAYS_IN_YEAR = 365
MAX_ORDINAL = 3652059  # max ordinal of any day


###########
# CLASSES #
###########

class Date(ABC):
    """Abstract base class for dates, analogous to datetime.date."""

    # Accessors

    @abstractmethod
    def get_year(self) -> int:
        """Return the year."""

    # Weekday names

    @abstractclassmethod
    def weekday_names(cls) -> List[str]:
        """Full names of each weekday."""

    @abstractclassmethod
    def weekday_abbrevs(cls) -> List[str]:
        """Abbreviated names of each weekday (3 letters)."""

    # Additional constructors

    @classmethod
    def fromtimestamp(cls, t: float) -> 'Date':
        "Construct a Date from a POSIX timestamp (like time.time())."
        return cls.fromdate(date.fromtimestamp(t))

    @classmethod
    def today(cls) -> 'Date':
        "Construct a Date from time.time()."
        return cls.fromdate(date.today())

    @abstractclassmethod
    def _from_year_and_ordinal(cls, year: int, n: int) -> 'Date':
        """Construct a Date from a year and an ordinal number within the year, where 0 is the first day of the year."""
        raise NotImplementedError

    @classmethod
    def fromordinal(cls, n: int) -> 'Date':
        """Construct a Date from an ordinal number, where day 1 is January 1 of year 1."""
        n -= 1  # convert to 0-up
        n400, n = divmod(n, DI400Y)
        n100, n = divmod(n, DI100Y)
        n4, n = divmod(n, DI4Y)
        n1, n = divmod(n, DAYS_IN_YEAR)
        year = n400 * 400 + n100 * 100 + n4 * 4 + n1 + 1
        if (n1 == 4) or (n100 == 4):
            # last day of a leap year
            return cls._from_year_and_ordinal(year - 1, DAYS_IN_YEAR)
        leapyear = n1 == 3 and (n4 != 24 or n100 == 3)
        assert leapyear == isleap(year)
        return cls._from_year_and_ordinal(year, n)

    @classmethod
    def fromisoformat(cls, date_string: str) -> 'Date':
        """Construct a Date from ISO 8601 format string YYYY-MM-DD (in proleptic Gregorian calendar)"""
        return cls.fromdate(date.fromisoformat(date_string))

    @classmethod
    def fromdate(cls, date: date) -> 'Date':
        """Construct a Date from a datetime.date object."""
        return cls.fromordinal(date.toordinal())

    # Standard conversions

    def timetuple(self) -> _time.struct_time:
        "Return local time tuple compatible with time.localtime()."
        return self.todate().timetuple()

    @abstractmethod
    def toordinal(self) -> int:
        """Convert to an ordinal number, where day 1 is January 1 of year 1."""

    def todate(self) -> date:
        """Convert to a datetime.date object."""
        return date.fromordinal(self.toordinal())

    # Computations

    def __add__(self, other: timedelta) -> 'Date':
        "Add a Date to a timedelta."
        if isinstance(other, timedelta):
            o = self.toordinal() + other.days
            if 0 < o <= MAX_ORDINAL:
                return type(self).fromordinal(o)
            raise OverflowError("result out of range")
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other: Union['Date', timedelta]) -> timedelta:
        """Subtract two Dates, or a Date and a timedelta."""
        if isinstance(other, timedelta):
            return self + timedelta(-other.days)
        if isinstance(other, Date):
            days1 = self.toordinal()
            days2 = other.toordinal()
            return timedelta(days1 - days2)
        return NotImplemented

    def is_leap_year(self) -> bool:
        """Return True if the year is a leap year."""
        return isleap(self.get_year())

    @abstractmethod
    def weekday(self) -> int:
        """Return day of the week as a 0-up integer."""

    # String conversions

    def ctime(self) -> str:
        "Return ctime() style string."
        return self.todate().ctime()

    @abstractmethod
    def strftime(self, fmt: str) -> str:
        "Format using strftime()."

    def isoformat(self) -> str:
        """Return the date as an ISO 8601 format string YYYY-MM-DD (in proleptic Gregorian calendar)."""
        return self.todate().isoformat()

    @abstractmethod
    def __str__(self) -> str:
        """Standard string representation of the Date."""


class Datetime(ABC):
    """Date/time type for arbitrary calendar, analogous to datetime.datetime."""

    # Associated types
    _date_class = Date  # subclass should set this
    _time_class = time

    # Additional constructors

    @classmethod
    def fromtimestamp(cls, t: float, tz: Optional[tzinfo] = None) -> 'Datetime':
        """Construct a Datetime from a POSIX timestamp (like time.time()).

        A timezone info object may be passed in as well."""
        return cls.fromdatetime(datetime.fromtimestamp(t, tz = tz))

    @classmethod
    def utcfromtimestamp(cls, t: float) -> 'Datetime':
        """Construct a naive UTC Datetime from a POSIX timestamp."""
        return cls.fromdatetime(datetime.utcfromtimestamp(t))

    @classmethod
    def now(cls, tz: Optional[tzinfo] = None) -> 'Datetime':
        "Construct a Datetime from time.time() and optional time zone info."
        return cls.fromdatetime(datetime.now(tz))

    @classmethod
    def utcnow(cls) -> 'Datetime':
        "Construct a UTC Datetime from time.time()."
        return cls.fromdatetime(datetime.utcnow())

    @abstractclassmethod
    def _combine(cls, date: Date, time: time, tzinfo: Optional[tzinfo] = None) -> 'Datetime':
        """Subclass should override this to construct a Datetime from a Date and time."""

    @classmethod
    def combine(cls, date: 'Date', time: time, tzinfo: Optional[tzinfo] = None) -> 'Datetime':
        "Construct a Datetime from a given date and time."
        if not isinstance(date, cls._date_class):
            raise TypeError(f"date argument must be a {cls._date_class} instance")
        if not isinstance(time, cls._time_class):
            raise TypeError(f"time argument must be a {cls._time_class} instance")
        if tzinfo is None:
            tzinfo = time.tzinfo
        return cls._combine(date, time, tzinfo)

    @classmethod
    def fromisoformat(cls, date_string: str) -> 'Datetime':
        """Construct a Datetime from the output of Datetime.isoformat()."""
        if not isinstance(date_string, str):
            raise TypeError('fromisoformat: argument must be str')
        # Split this at the separator
        dstr = date_string[0:10]
        tstr = date_string[11:]
        date = cls._date_class.fromisoformat(dstr)
        time = cls._time_class.fromisoformat(tstr)
        return cls.combine(date, time)

    @classmethod
    def fromdatetime(cls, dt: datetime) -> 'Datetime':
        """Construct a Datetime from a datetime.datetime object."""
        date = cls._date_class.fromdate(dt.date())
        return cls.combine(date, dt.timetz())

    @abstractclassmethod
    def strptime(cls, date_string: str, format: str) -> 'Datetime':
        """string, format -> new Datetime parsed from a string (like time.strptime())."""

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

    @abstractmethod
    def date(self) -> 'Date':
        """Return the Date part."""

    @abstractmethod
    def time(self) -> time:
        """Return the time part, with tzinfo None."""

    @abstractmethod
    def timetz(self) -> time:
        """Return the time part, with same tzinfo."""

    def todatetime(self) -> datetime:
        """Convert to a datetime.datetime object."""
        return datetime.combine(self.date().todate(), self.timetz())

    @abstractmethod
    def replace(self, year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None, second: int = None, microsecond: int = None, tzinfo: tzinfo = None) -> 'Datetime':
        """Return a new Datetime with new values for the specified fields."""

    def astimezone(self, tz: Optional[tzinfo] = None) -> 'Datetime':
        """Convert to a different timezone (by default, the local one)."""
        return type(self).fromdatetime(self.todatetime().astimezone())

    # Computations

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

    def __add__(self, other: timedelta) -> 'Datetime':
        """Add a Datetime and a timedelta."""
        return type(self).fromdatetime(self.todatetime() + other)

    __radd__ = __add__

    def __sub__(self, other: Union['Datetime', timedelta]) -> 'Datetime':
        """Subtract two Datetimes, or a Datetime and a timedelta."""
        if isinstance(other, Datetime):
            return self.todatetime() - other.todatetime()
        elif isinstance(other, timedelta):
            return self + -other
        return NotImplemented

    # Conversions to string

    def ctime(self) -> str:
        "Return ctime() style string."
        return self.todatetime().ctime()

    def isoformat(self, sep: str = 'T', timespec: str = 'auto') -> str:
        """Return the time formatted according to ISO 8601.

        The full format looks like 'YYYY-MM-DD HH:MM:SS.mmmmmm'.
        This uses the proleptic Gregorian calendar date.
        By default, the fractional part of the time is omitted if self.microsecond == 0.

        If self.tzinfo is not None, the UTC offset is also attached, giving
        giving a full format of 'YYYY-MM-DD HH:MM:SS.mmmmmm+HH:MM'.

        Optional argument sep specifies the separator between date and
        time, default 'T'.

        The optional argument timespec specifies the number of additional
        terms of the time to include.
        """
        return self.todatetime().isoformat()

    def __str__(self) -> str:
        "Standard string representation of the datetime."""
        return str(self.date()) + ' ' + str(self.time())