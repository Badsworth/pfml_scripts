from typing import Optional

import pytest

from massgov.pfml.util.pydantic import PydanticBaseModel


class Sample(PydanticBaseModel):
    first_name: str
    middle_name: Optional[str]


def test_reject_empty_string_value():
    with pytest.raises(ValueError):
        Sample(first_name="", middle_name="test")

    with pytest.raises(ValueError):
        Sample(first_name="test", middle_name="")

    with pytest.raises(ValueError):
        Sample(first_name="test", middle_name=" ")

    with pytest.raises(ValueError):
        Sample(first_name=" ")


def test_strip_whitespaces_from_string_value():
    sample1 = Sample(first_name=" first ")
    sample2 = Sample(first_name="first", middle_name=" middle ")
    sample3 = Sample(first_name="first ", middle_name=" middle")

    assert sample1.first_name == "first"
    assert sample2.first_name == "first"
    assert sample2.middle_name == "middle"
    assert sample3.first_name == "first"
    assert sample3.middle_name == "middle"
