"""The Seasonal Calendar

Devised by Galvin Industries, LLC.

See: https://thenewcalendar.com"""

from bisect import bisect
from calendar import isleap
from dataclasses import dataclass
from datetime import time, timedelta, tzinfo
from itertools import accumulate
from operator import add
from typing import Dict, List, Optional

from nerdcal._base import check_int, Date, Datetime, days_before_year


MIN_YEAR = 1
MAX_YEAR = 9999
MIN_SEASON = 1
MAX_SEASON = 5
DAYS_IN_SEASON = 73
MIDSEASON_DAY = 37
DAYS_IN_WEEK = 9


@dataclass(order = True, frozen = True)
class SeasonalDate(Date):
    """Concrete date type for the seasonal calendar.

    There are 5 seasons consisting of 73 days each.
    Each season is divided into two months of 36 days each, with an interceding "mid-season" day.
    Each month is divided into four weeks of 9 days each, named after the planets.
    The leap year occurs in the usual place (old Feb. 29), which is between Winter 70 and 71.
    For ease of representation, the leap day will be designated Winter 0."""
    year: int
    season: int
    day: int

    def __post_init__(self) -> None:
        """Perform validation on the year, season, and day.
        Raise a ValueError if any entries are invalid."""
        check_int(self.year)
        check_int(self.season)
        check_int(self.day)
        if not MIN_YEAR <= self.year <= MAX_YEAR:
            raise ValueError(f'year must be in {MIN_YEAR}..{MAX_YEAR}', self.year)
        if not MIN_SEASON <= self.season <= MAX_SEASON:
            raise ValueError(f'season must be in {MIN_SEASON}..{MAX_SEASON}', self.season)
        min_day = 0 if ((self.season == 1) and isleap(self.year)) else 1
        if not (min_day <= self.day <= DAYS_IN_SEASON):
            raise ValueError(f'day must be in {min_day}..{DAYS_IN_SEASON}', self.day)

    # Accessors

    def get_year(self) -> int:
        return self.year

    # Helpers

    @classmethod
    def _days_in_season(cls, year: int) -> List[int]:
        """List of number of days in each season."""
        return [DAYS_IN_SEASON + 1 if ((season == 1) and isleap(year)) else DAYS_IN_SEASON for season in range(MIN_SEASON, MAX_SEASON + 1)]

    @classmethod
    def _days_before_season(cls, year: int) -> List[int]:
        """List of number of days before the start of each season."""
        return list(accumulate([0] + cls._days_in_season(year), add))[:-1]

    # Month/weekday names

    @classmethod
    def month_names(cls) -> List[str]:
        # NB: these are actually season names
        return ['Winter', 'Spring', 'Summer', 'Autumn', 'Fall']

    @classmethod
    def month_abbrevs(cls) -> List[str]:
        return ['Win', 'Spr', 'Sum', 'Aut', 'Fal']

    @classmethod
    def weekday_names(cls) -> List[str]:
        return ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

    @classmethod
    def weekday_abbrevs(cls) -> List[str]:
        return ['Mer', 'Ven', 'Ear', 'Mar', 'Jup', 'Sat', 'Ura', 'Nep', 'Plu']

    # Additional constructors

    @classmethod
    def _from_year_and_ordinal(cls, year: int, n: int) -> 'SeasonalDate':
        dbs = cls._days_before_season(year)
        season = bisect(dbs, n)
        day = n - dbs[season - 1]
        if (season == 1):
            if (day == 70):
                day = -1
            elif (day > 70):
                day -= 1
        return cls(year, season, day + 1)

    @classmethod
    def fromordinal(cls, n: int) -> 'SeasonalDate':
        # override this to shift year start date earlier by 11 days
        return super(SeasonalDate, cls).fromordinal(n + 11)

    # Standard conversions

    def toordinal(self) -> int:
        day_offset = self.day
        if isleap(self.year) and (self.season == 1):
            if (self.day == 0):
                day_offset = 71
            elif (self.day >= 71):
                day_offset += 1
        o = days_before_year(self.year) + self._days_before_season(self.year)[self.season - 1] + day_offset
        # shift year start date later by 11 days
        return o - 11

    def replace(self, year: int = None, season: int = None, day: int = None) -> 'SeasonalDate':
        return type(self)(year or self.year, season or self.season, day or self.day)

    # Computations

    def weekday(self) -> int:
        """Return day of the week as a number 0..8 (if a proper weekday), 9 (if mid-season), or 10 (if Leap Day)."""
        if (self.day == 0):
            return 10
        if (self.day == MIDSEASON_DAY):
            return 9
        if (self.day > MIDSEASON_DAY):
            return (self.day - 2) % DAYS_IN_WEEK
        return (self.day - 1) % DAYS_IN_WEEK

    def day_of_year(self) -> int:
        return self.toordinal() - self.replace(season = 1, day = 1).toordinal()

    def week_of_year(self) -> int:
        if (self.day == 0):  # leap day
            # count leap day as part of the week it's within
            return 7
        elif (self.day == MIDSEASON_DAY):
            # count midseason day as part of the preceding week
            return 3
        elif (self.day > MIDSEASON_DAY):
            return (self.day - 2) // DAYS_IN_WEEK
        return (self.day - 1) // DAYS_IN_WEEK

    # Conversions to string

    def _strftime_dict(self) -> Dict[str, str]:
        weekday = self.weekday()
        season_name = self.month_names()[self.season - 1]
        season_abbrev = self.month_abbrevs()[self.season - 1]
        day = str(self.day).zfill(2)
        if (weekday >= 9):
            weekday_name = weekday_abbrev = '--'
            if (weekday == 10):  # leap day
                day = 'Lp'
        else:
            weekday_name = self.weekday_names()[weekday]
            weekday_abbrev = self.weekday_abbrevs()[weekday]
        week_of_year = str(self.week_of_year()).zfill(2)
        return {'%a' : weekday_abbrev, '%A' : weekday_name, '%w' : str(weekday), '%d' : day, '%b' : season_abbrev, '%B' : season_name, '%m' : str(self.season), '%j' : str(self.day_of_year() + 1).zfill(3), '%U' : week_of_year, '%W' : week_of_year}

SeasonalDate.min = SeasonalDate(1, 1, 1)
SeasonalDate.max = SeasonalDate(9999, 5, 73)
SeasonalDate.resolution = timedelta(days = 1)


@dataclass(order = True, frozen = True)
class SeasonalDatetime(Datetime):
    """Concrete datetime type for the seasonal calendar.

    SeasonalDatetime(year, season, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    The year, season, and day arguments are required."""
    _date_class = SeasonalDate

    year: int
    season: int
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
        self._date_class(self.year, self.season, self.day)
        self._time_class(self.hour, self.minute, self.second, self.microsecond, self.tzinfo)

    # Additional constructors

    @classmethod
    def _combine(cls, date: SeasonalDate, time: time, tzinfo: Optional[tzinfo] = None) -> 'SeasonalDatetime':
        return cls(date.year, date.season, date.day, time.hour, time.minute, time.second, time.microsecond, tzinfo)

    # Standard conversions

    def date(self) -> 'SeasonalDate':
        return self._date_class(self.year, self.season, self.day)

    def time(self) -> time:
        return self._time_class(self.hour, self.minute, self.second, self.microsecond)

    def timetz(self) -> time:
        return self._time_class(self.hour, self.minute, self.second, self.microsecond, self.tzinfo)

    def replace(self, year: int = None, season: int = None, day: int = None, hour: int = None, minute: int = None, second: int = None, microsecond: int = None, tzinfo: tzinfo = None) -> 'SeasonalDatetime':
        return type(self)(year or self.year, season or self.season, day or self.day, hour or self.hour, minute or self.minute, second or self.second, microsecond or self.microsecond, tzinfo or self.tzinfo)

SeasonalDatetime.min = SeasonalDatetime(1, 1, 1)
SeasonalDatetime.max = SeasonalDatetime(9999, 5, 73, 23, 59, 59, 999999)
SeasonalDatetime.resolution = timedelta(microseconds = 1)