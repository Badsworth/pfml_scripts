import massgov.pfml.util.csv as csv_util


def test_encode_row_with_empty_dict():
    assert csv_util.encode_row({}) == {}
