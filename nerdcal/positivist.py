from typing import List

from nerdcal._base import days_before_year, is_leap_year
from nerdcal.ifc import DAYS_IN_MONTH, DAYS_IN_WEEK, MIN_MONTH, MAX_MONTH, IFCDate, IFCDatetime


class PositivistDate(IFCDate):

    # Helpers

    @classmethod
    def _days_in_month(cls, year: int) -> List[int]:
        leap_year = is_leap_year(year)
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
            return 'Fest. Wom '
        weekday = self.weekday()
        weekday_name = self.weekday_abbrevs()[weekday]
        month_name = self.month_abbrevs()[self.month - 1]
        return '{} {} {:2d}'.format(weekday_name, month_name, self.day)


class PositivistDatetime(IFCDatetime):

    _date_class = PositivistDate
