from massgov.pfml.util.strings import join_with_coordinating_conjunction, split_str


def test_split_str_with_args():
    result = split_str("www.test.com,www.example.com")

    assert result == ["www.test.com", "www.example.com"]


def test_split_str_without_args():
    result = split_str()

    assert result == []


def test_join_with_coordinating_conjunction():
    assert join_with_coordinating_conjunction([]) == ""

    assert join_with_coordinating_conjunction(["foo"]) == "foo"

    assert join_with_coordinating_conjunction(["foo", "bar"]) == "foo and bar"

    assert join_with_coordinating_conjunction(["foo", "bar", "baz"]) == "foo, bar, and baz"
