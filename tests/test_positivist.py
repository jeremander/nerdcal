from nerdcal.positivist import PositivistDate, PositivistDatetime


def test_create_positivist_date():
    pos = PositivistDate(2019, 1, 1)
    assert pos
