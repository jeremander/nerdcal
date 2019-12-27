from nerdcal.ifc import IFCDate, IFCDatetime
import pytest


@pytest.mark.parametrize(
    "year,month,day",
    [
        (2019, 1, 1),
        (2019, 13, 1),
        (2019, 13, 28),
        (1, 1, 1),
        (9999, 13, 28),
        (2019, 13, 29),
        (2000, 6, 29),
    ],
)
def test_create_valid_ifc_date(year, month, day):
    ifc = IFCDate(year, month, day)
    assert ifc


@pytest.mark.parametrize(
    "year,month,day",
    [
        (0, 1, 1),
        (2019, 14, 1),
        (2019, 0, 1),
        (2019, 13, 30),
        (2019, 5, 29),
        (10000, 13, 28),
        (2019, 13, 0),
        (2001, 6, 29),
    ],
)
def test_create_invalid_ifc_date(year, month, day):
    with pytest.raises(ValueError):
        IFCDate(year, month, day)
