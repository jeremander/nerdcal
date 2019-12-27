from nerdcal.ifc import IFCDate, IFCDatetime


def test_create_ifc_date():
    ifc = IFCDate(2019, 1, 1)
    assert ifc
