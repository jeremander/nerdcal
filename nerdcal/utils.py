from typing import Any, Tuple

def check_int(value: Any) -> None:
    """Checks that a value is an integer, raising a ValueError otherwise."""
    if isinstance(value, int):
        return
    raise ValueError('an integer is required (got type {})'.format(type(value).__name__))

def is_leap_year(year: int) -> bool:
    """Returns True if the given year is a leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def days_before_year(year: int) -> int:
    """Given a year, returns number of days before the first day of that year."""
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400

DI400Y = days_before_year(401)    # number of days in 400 years
DI100Y = days_before_year(101)    # number of days in 100 years
DI4Y   = days_before_year(5)      # number of days in 4 years

def parse_isoformat_date(date_str: str) -> Tuple[int, int, int]:
    """Parses a (year, month, day) tuple from a string of the form YYYY-MM-DD."""
    assert len(date_str) == 10
    year = int(date_str[0:4])
    if date_str[4] != '-':
        raise ValueError(f'Invalid date separator: {date_str[4]}')
    month = int(date_str[5:7])
    if date_str[7] != '-':
        raise ValueError(f'Invalid date separator: {date_str[7]}')
    day = int(date_str[8:10])
    return (year, month, day)