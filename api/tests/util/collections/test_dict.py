#
# Unit tests for massgov.pfml.util.collections.dict.
#

import massgov.pfml.util.collections.dict as dict_util
from massgov.pfml.util.collections.dict import filter_dict, make_keys_lowercase


def test_least_recently_used_dict():
    lru_dict = dict_util.LeastRecentlyUsedDict(maxsize=4)

    assert lru_dict["a"] == 0
    assert len(lru_dict) == 0

    lru_dict["a"] = 10
    lru_dict["b"] = 20
    lru_dict["c"] = 30
    lru_dict["d"] = 40

    assert len(lru_dict) == 4
    assert tuple(lru_dict.items()) == (("a", 10), ("b", 20), ("c", 30), ("d", 40))
    assert lru_dict["a"] == 10
    assert lru_dict["b"] == 20
    assert lru_dict["c"] == 30
    assert lru_dict["d"] == 40
    assert lru_dict["e"] == 0
    assert len(lru_dict) == 4

    lru_dict["a"] += 1  # Write existing a, move to end
    assert len(lru_dict) == 4
    assert tuple(lru_dict.items()) == (("b", 20), ("c", 30), ("d", 40), ("a", 11))

    lru_dict["f"] = 50  # Write new key f, and evict oldest b
    lru_dict["c"] += 1  # Write existing c, move to end, and evict oldest d
    lru_dict["g"] = 60  # Write new key g, and evict oldest d
    assert len(lru_dict) == 4
    assert tuple(lru_dict.items()) == (("a", 11), ("f", 50), ("c", 31), ("g", 60))


def test_make_keys_lowercase():
    example = {"foo": "BAR", "Bar": "baz"}
    expected = {"foo": "BAR", "bar": "baz"}
    assert make_keys_lowercase(example) == expected


def test_filter_dict():
    example = {"foo": "bar", "notAllowed": "removeMe"}
    allowed_keys = {"foo", "permitted"}
    expected = {"foo": "bar"}

    assert filter_dict(dict=example, allowed_keys=allowed_keys) == expected


def test_flatten():
    assert dict_util.flatten({"foo": {"bar": "baz"}}) == {"foo.bar": "baz"}

    assert dict_util.flatten({"foo": {"bar": "baz"}}, key_prefix="oof") == {"oof.foo.bar": "baz"}

    assert dict_util.flatten({"foo": {"bar": "baz"}}, separator=":") == {"foo:bar": "baz"}

    # doesn't really make sense to call it with `max_depth=0`, but...
    assert dict_util.flatten({"foo": {"bar": {"baz": 1}}}, max_depth=0) == {
        "foo": "{'bar': {'baz': 1}}"
    }
    assert dict_util.flatten({"foo": {"bar": {"baz": 1}}}, max_depth=1) == {"foo.bar": "{'baz': 1}"}
