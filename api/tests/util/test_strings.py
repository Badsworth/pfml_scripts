from massgov.pfml.util.strings import split_str


def test_split_str_with_args():
    result = split_str("www.test.com,www.example.com")

    assert result == ["www.test.com", "www.example.com"]


def test_split_str_without_args():
    result = split_str()

    assert result == []
