import dataclasses

import pytest

from massgov.pfml.util.compare import compare_attributes


@dataclasses.dataclass
class ForTestCompareAttributes:
    something: str = ""
    another_thing: int = 42


@pytest.mark.parametrize(
    "first, second, field, expected",
    (
        (
            ForTestCompareAttributes(something="hello", another_thing=22),
            ForTestCompareAttributes(something="hello", another_thing=22),
            "something",
            True,
        ),
        (
            ForTestCompareAttributes(something="blech", another_thing=50),
            ForTestCompareAttributes(something="hello", another_thing=22),
            "another_thing",
            False,
        ),
        (
            ForTestCompareAttributes(something=" HELLO ", another_thing=22),
            ForTestCompareAttributes(something="hello", another_thing=22),
            "something",
            True,
        ),
    ),
)
def test_compare_attributes(first, second, field, expected):
    assert compare_attributes(first, second, field) == expected
